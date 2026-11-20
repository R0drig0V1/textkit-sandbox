"""Tests for the tool registry of the command line, ``textkit/cli/registry.py`` (plan task T3.1).

A fake ``Command`` is registered and run through ``_main`` in process. The registry is
process-wide state, so every test starts from ``_load_tools()`` (the real tool modules of
``textkit/cli/`` imported, whatever ran before) and a snapshot of the registry, and
``tearDown`` restores the snapshot: no fake command leaks into other tests and no real tool
is lost. ``test_registry_is_restored_after_a_registry_test`` checks exactly that, also when
this file runs alone.

Tool discovery (``pkgutil`` over ``textkit/cli/``) is tested with a tool module written to a
``tempfile`` directory that is added to ``textkit.cli.__path__`` for the test: nothing is
written inside the repository, so parallel runs of the checks cannot see each other's files.
"""

import argparse
import contextlib
import dataclasses
import importlib
import io
import pathlib
import sys
import tempfile
import unittest
from typing import Dict, List, Tuple
from unittest import mock

import textkit.cli
import textkit.cli.main as cli
from textkit.cli import registry
from textkit.cli.registry import PROG, Command
from textkit.errors import InvalidValueError

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLI_DIR = ROOT / "textkit" / "cli"


def _main_captured(argv: List[str]) -> Tuple[int, str, str]:
    """Call ``cli._main(argv)`` in process; return (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli._main(argv)
    return code, out.getvalue(), err.getvalue()


def _help_block(help_text: str, header: str) -> Dict[str, str]:
    """Parse the ``<header>:`` block of ``--help`` into name -> summary ({} when absent)."""
    lines = help_text.splitlines()
    if f"{header}:" not in lines:
        return {}
    rows = {}
    for line in lines[lines.index(f"{header}:") + 1 :]:
        if not line.strip():
            break
        name, _, summary = line.strip().partition(" ")
        rows[name] = summary.strip()
    return rows


def _tool_modules_on_disk() -> List[str]:
    """The tool modules of ``textkit/cli/``, read from the file system, not from the code.

    A tool module is ``textkit/cli/<name>.py`` with ``<name>`` not starting with ``_`` and
    not one of the command line's own modules; its subcommand is named ``<name>``.
    """
    machinery = {"functions", "main", "registry"}
    return sorted(
        path.stem
        for path in CLI_DIR.glob("*.py")
        if not path.stem.startswith("_") and path.stem not in machinery
    )


def _configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("word")
    parser.add_argument("--times", type=int, default=1)


def _run(args: argparse.Namespace) -> int:
    sys.stdout.write(args.word * args.times)
    # An exit code that neither argparse nor the function commands use, so seeing it proves
    # that _main returned Command.run's value as is.
    return 7


FAKE = Command(
    name="zz-fake-tool",
    summary="Repeat a word (a fake tool of the registry tests)",
    configure=_configure,
    run=_run,
)


class RegistryTestCase(unittest.TestCase):
    """Snapshot the registry, with the real tools loaded, and restore it after each test."""

    def setUp(self) -> None:
        cli._load_tools()
        self._snapshot = dict(registry._REGISTRY)

    def tearDown(self) -> None:
        registry._REGISTRY.clear()
        registry._REGISTRY.update(self._snapshot)


class RegisterTest(RegistryTestCase):
    """``register`` and ``commands``."""

    def test_register_returns_the_command(self) -> None:
        self.assertIs(registry.register(FAKE), FAKE)
        self.assertIn(FAKE, registry.commands())

    def test_registering_the_same_command_twice_is_a_no_op(self) -> None:
        registry.register(FAKE)
        before = registry.commands()
        self.assertIs(registry.register(FAKE), FAKE)
        self.assertEqual(registry.commands(), before)
        self.assertEqual([c.name for c in registry.commands()].count(FAKE.name), 1)

    def test_a_different_command_with_the_same_name_raises(self) -> None:
        registry.register(FAKE)
        other = dataclasses.replace(FAKE, summary="Another tool with the same name")
        with self.assertRaises(RuntimeError) as caught:
            registry.register(other)
        self.assertIn(FAKE.name, str(caught.exception))
        # The first registration stays.
        self.assertIn(FAKE, registry.commands())
        self.assertNotIn(other, registry.commands())

    def test_commands_are_sorted_by_name(self) -> None:
        for name in ("zz-b", "zz-c", "zz-a"):
            registry.register(dataclasses.replace(FAKE, name=name))
        names = [c.name for c in registry.commands()]
        self.assertEqual(names, sorted(names))

    def test_commands_returns_a_copy(self) -> None:
        registry.commands().append(FAKE)
        self.assertNotIn(FAKE, registry.commands())

    def test_command_is_frozen(self) -> None:
        with self.assertRaises(dataclasses.FrozenInstanceError):
            FAKE.name = "other"  # type: ignore[misc]

    def test_prog(self) -> None:
        self.assertEqual(PROG, "python3 -m textkit")


class MainWithToolsTest(RegistryTestCase):
    """A registered tool through ``_main``."""

    def test_fake_command_is_listed_under_tools(self) -> None:
        registry.register(FAKE)
        code, out, err = _main_captured(["--help"])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(_help_block(out, "tools").get(FAKE.name), FAKE.summary)
        # Function commands stay under "commands:"; the tools block follows a blank line.
        self.assertNotIn(FAKE.name, _help_block(out, "commands"))
        lines = out.splitlines()
        self.assertEqual(lines[lines.index("tools:") - 1], "")
        self.assertLess(lines.index("commands:"), lines.index("tools:"))

    def test_fake_command_runs_and_its_exit_code_comes_back(self) -> None:
        registry.register(FAKE)
        self.assertEqual(_main_captured([FAKE.name, "ab"]), (7, "ab", ""))
        # configure added --times; the whole namespace reached run.
        self.assertEqual(_main_captured([FAKE.name, "ab", "--times", "3"]), (7, "ababab", ""))

    def test_tool_usage_error_exits_2_with_the_tool_prefix(self) -> None:
        registry.register(FAKE)
        code, out, err = _main_captured([FAKE.name])
        self.assertEqual((code, out), (2, ""))
        self.assertIn(f"{PROG} {FAKE.name}: error:", err)

    def test_tool_description_is_its_summary(self) -> None:
        registry.register(FAKE)
        code, out, _ = _main_captured([FAKE.name, "--help"])
        self.assertEqual(code, 0)
        self.assertIn(FAKE.summary, out)

    def test_textkit_error_from_a_tool_is_not_caught(self) -> None:
        # _main catches TextkitError around function commands only: a tool handles its own.
        def run(args: argparse.Namespace) -> int:
            raise InvalidValueError("not caught")

        registry.register(dataclasses.replace(FAKE, run=run))
        with self.assertRaises(InvalidValueError):
            _main_captured([FAKE.name, "x"])

    def test_no_tools_block_without_tools(self) -> None:
        registry._REGISTRY.clear()
        code, out, _ = _main_captured(["--help"])
        self.assertEqual(code, 0)
        self.assertNotIn("tools:", out.splitlines())
        self.assertIn("<function>", out)

    def test_a_tool_named_like_a_function_command_raises_on_every_run(self) -> None:
        registry.register(dataclasses.replace(FAKE, name="slugify"))
        for argv in (["--help"], ["--version"], ["slugify", "x"], ["word_count", "a b"]):
            with self.subTest(argv=argv), self.assertRaises(RuntimeError) as caught:
                _main_captured(argv)
            self.assertIn("slugify", str(caught.exception))


class LoadToolsTest(RegistryTestCase):
    """``_load_tools``: tool modules found with ``pkgutil`` and imported on demand."""

    MODULE = "zz_tmp_tool"

    def setUp(self) -> None:
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        source = (
            "from textkit.cli.registry import Command, register\n"
            "def _configure(parser): parser.add_argument('text')\n"
            "def _run(args):\n"
            "    print(args.text[::-1])\n"
            "    return 0\n"
            f"COMMAND = register(Command({self.MODULE!r}, 'Reverse a text', _configure, _run))\n"
        )
        (pathlib.Path(tmp.name) / f"{self.MODULE}.py").write_text(source, encoding="utf-8")
        # Machinery-like and private names in the extra directory must be skipped too.
        (pathlib.Path(tmp.name) / "_zz_private.py").write_text("raise AssertionError\n")
        path = list(textkit.cli.__path__) + [tmp.name]
        patcher = mock.patch.object(textkit.cli, "__path__", path)
        patcher.start()
        self.addCleanup(patcher.stop)
        # Forget the imported module (and the attribute the import set on the package), so a
        # later test starts from a module that was never imported.
        self.addCleanup(sys.modules.pop, f"textkit.cli.{self.MODULE}", None)
        self.addCleanup(lambda: textkit.cli.__dict__.pop(self.MODULE, None))

    def test_tool_modules_are_found_and_machinery_is_skipped(self) -> None:
        names = cli._tool_module_names()
        self.assertIn(f"textkit.cli.{self.MODULE}", names)
        for skipped in ("functions", "main", "registry", "_zz_private", "__init__"):
            self.assertNotIn(f"textkit.cli.{skipped}", names)

    def test_import_of_main_does_not_load_tools(self) -> None:
        importlib.reload(cli)
        self.assertNotIn(f"textkit.cli.{self.MODULE}", sys.modules)
        self.assertNotIn(self.MODULE, [c.name for c in registry.commands()])

    def test_main_loads_and_runs_a_discovered_tool(self) -> None:
        code, out, _ = _main_captured(["--help"])
        self.assertEqual(code, 0)
        self.assertEqual(_help_block(out, "tools").get(self.MODULE), "Reverse a text")
        self.assertEqual(_main_captured([self.MODULE, "abc"]), (0, "cba\n", ""))

    def test_load_tools_is_idempotent(self) -> None:
        cli._load_tools()
        cli._load_tools()
        self.assertEqual([c.name for c in registry.commands()].count(self.MODULE), 1)


class RegistryIsolationTest(unittest.TestCase):
    """The registry tests leave the real tools as they found them."""

    def test_registry_is_restored_after_a_registry_test(self) -> None:
        # Run a test that registers a fake command, setUp and tearDown included, then check
        # the help: the fake is gone and every tool module of textkit/cli/ is listed. Run
        # here rather than relying on test order, so it holds when this file runs alone.
        result = unittest.TestResult()
        MainWithToolsTest("test_fake_command_runs_and_its_exit_code_comes_back").run(result)
        self.assertTrue(result.wasSuccessful(), result.errors + result.failures)
        code, out, _ = _main_captured(["--help"])
        self.assertEqual(code, 0)
        tools = _help_block(out, "tools")
        self.assertNotIn(FAKE.name, tools)
        self.assertEqual(sorted(tools), _tool_modules_on_disk())


if __name__ == "__main__":
    unittest.main()
