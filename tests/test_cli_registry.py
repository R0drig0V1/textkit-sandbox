"""Tests for the tool registry of the command line, ``textkit/cli/registry.py`` (plan task T3.1).

A tool adds a subcommand by registering a ``Command`` from its own module
``textkit/cli/<name>.py``; ``textkit.cli.main._main`` lists it under ``tools:`` in ``--help``,
lets it configure its parser and returns its exit code. These tests register fake commands
in process, so they never add files under ``textkit/`` (the checks run in parallel).

The registry is process-wide. ``RegistryTestCase`` loads the real tools first
(``_load_tools``), then snapshots the registry in ``setUp`` and restores it in ``tearDown``,
so no fake command leaks into other tests and no real tool is lost, also when this file runs
alone; ``ToolsSurviveTest`` checks exactly that.
"""

import argparse
import contextlib
import dataclasses
import io
import os
import pathlib
import subprocess
import sys
import unittest
from typing import List, Optional, Set, Tuple
from unittest import mock

import textkit.cli
import textkit.cli.main as cli
from textkit.cli import registry

ROOT = pathlib.Path(__file__).resolve().parents[1]

# The modules of textkit/cli/ that are the command line itself, not tools. Every other module
# there whose name does not start with "_" is a tool, named like its subcommand (phase 3 rule
# "The command line": a tool's subcommand is the module textkit/cli/<name>.py).
_INFRASTRUCTURE = {"functions", "main", "registry"}


def _tool_module_names() -> Set[str]:
    """The tool modules under ``textkit/cli/``, read from the directory, not from the code."""
    return {
        path.stem
        for path in (ROOT / "textkit" / "cli").glob("*.py")
        if not path.stem.startswith("_") and path.stem not in _INFRASTRUCTURE
    }


def _main_captured(argv: List[str]) -> Tuple[int, str, str]:
    """Call ``cli._main(argv)`` in process; return (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli._main(argv)
    return code, out.getvalue(), err.getvalue()


def _help_block(help_text: str, header: str) -> Optional[List[Tuple[str, str]]]:
    """Parse the block of ``--help`` under ``header`` into (name, summary) rows, in order.

    Returns ``None`` when there is no such block.
    """
    lines = help_text.splitlines()
    if header not in lines:
        return None
    rows = []
    for line in lines[lines.index(header) + 1 :]:
        if not line.strip():
            break
        name, _, summary = line.strip().partition(" ")
        rows.append((name, summary.strip()))
    return rows


def _fake(name: str, code: int = 0, seen: Optional[list] = None) -> registry.Command:
    """A fake tool: one ``path`` argument and a ``--loud`` flag; ``run`` returns ``code``.

    Every namespace ``run`` receives is appended to ``seen``.
    """

    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("path")
        parser.add_argument("--loud", action="store_true")

    def run(args: argparse.Namespace) -> int:
        if seen is not None:
            seen.append(args)
        return code

    return registry.Command(
        name=name, summary=f"The fake tool {name}.", configure=configure, run=run
    )


class RegistryTestCase(unittest.TestCase):
    """Base class: restores the registry after each test."""

    def setUp(self) -> None:
        # Load the real tools first: a snapshot taken before them would make tearDown drop
        # them when this file runs alone, and a later _load_tools would not bring them back
        # (each module runs once).
        cli._load_tools()
        self._saved = dict(registry._REGISTRY)

    def tearDown(self) -> None:
        registry._REGISTRY.clear()
        registry._REGISTRY.update(self._saved)


class RegisterTest(RegistryTestCase):
    """``register`` and ``commands``."""

    def test_register_returns_the_command(self) -> None:
        command = _fake("zz-fake")
        self.assertIs(registry.register(command), command)
        self.assertIn(command, registry.commands())

    def test_registering_the_same_object_again_is_a_no_op(self) -> None:
        command = _fake("zz-fake")
        registry.register(command)
        before = registry.commands()
        self.assertIs(registry.register(command), command)
        self.assertEqual(registry.commands(), before)
        self.assertEqual([c.name for c in registry.commands()].count("zz-fake"), 1)

    def test_a_different_command_with_the_same_name_raises(self) -> None:
        first = _fake("zz-fake")
        registry.register(first)
        with self.assertRaises(RuntimeError):
            registry.register(_fake("zz-fake"))
        self.assertIs(next(c for c in registry.commands() if c.name == "zz-fake"), first)

    def test_commands_are_sorted_by_name(self) -> None:
        for name in ("zz-c", "zz-a", "zz-b"):
            registry.register(_fake(name))
        names = [c.name for c in registry.commands()]
        self.assertEqual(names, sorted(names))

    def test_command_is_frozen(self) -> None:
        with self.assertRaises(dataclasses.FrozenInstanceError):
            _fake("zz-fake").name = "other"  # type: ignore[misc]

    def test_prog(self) -> None:
        self.assertEqual(registry.PROG, "python3 -m textkit")


class MainWithToolsTest(RegistryTestCase):
    """``_main`` with registered tools."""

    def test_registered_command_is_listed_and_runs(self) -> None:
        seen: list = []
        registry.register(_fake("zz-fake", code=7, seen=seen))
        code, out, err = _main_captured(["--help"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn(("zz-fake", "The fake tool zz-fake."), _help_block(out, "tools:") or [])
        # The tool's exit code comes back as is, with the whole namespace passed to run.
        self.assertEqual(_main_captured(["zz-fake", "a.txt", "--loud"]), (7, "", ""))
        (args,) = seen
        self.assertEqual((args.command, args.path, args.loud), ("zz-fake", "a.txt", True))

    def test_exit_code_zero_and_nonzero_pass_through(self) -> None:
        for code in (0, 1, 2, 5):
            with self.subTest(code=code):
                registry.register(_fake(f"zz-code-{code}", code=code))
                self.assertEqual(_main_captured([f"zz-code-{code}", "x"])[0], code)

    def test_tools_block_follows_commands_after_a_blank_line(self) -> None:
        registry.register(_fake("zz-fake"))
        _, out, _ = _main_captured(["--help"])
        lines = out.splitlines()
        commands_rows = _help_block(out, "commands:")
        self.assertTrue(commands_rows)
        last_command = lines.index("commands:") + len(commands_rows or [])
        self.assertEqual(lines[last_command + 1 : last_command + 3], ["", "tools:"])
        self.assertNotIn("zz-fake", [name for name, _ in commands_rows or []])

    def test_no_tools_block_when_none_is_registered(self) -> None:
        registry._REGISTRY.clear()
        with mock.patch.object(cli, "_load_tools"):
            code, out, _ = _main_captured(["--help"])
        self.assertEqual(code, 0)
        self.assertIsNone(_help_block(out, "tools:"))
        self.assertTrue(_help_block(out, "commands:"))

    def test_tool_help_shows_its_summary_and_arguments(self) -> None:
        registry.register(_fake("zz-fake"))
        code, out, _ = _main_captured(["zz-fake", "--help"])
        self.assertEqual(code, 0)
        self.assertIn("The fake tool zz-fake.", out)
        self.assertIn("--loud", out)

    def test_tool_usage_error_exits_2(self) -> None:
        registry.register(_fake("zz-fake"))
        code, out, err = _main_captured(["zz-fake"])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("usage:", err)

    def test_value_error_from_a_tool_is_not_caught(self) -> None:
        # _main catches ValueError around function commands only; a tool handles its own.
        def run(args: argparse.Namespace) -> int:
            raise ValueError("tool bug")

        registry.register(registry.Command("zz-raises", "Raises.", lambda parser: None, run))
        with self.assertRaises(ValueError):
            _main_captured(["zz-raises"])

    def test_tool_named_like_a_function_command_raises_on_every_run(self) -> None:
        registry.register(_fake("slugify"))  # register itself does not know the functions
        for argv in (["--help"], ["--version"], ["slugify", "x"], ["word_count", "a b"]):
            with self.subTest(argv=argv):
                with self.assertRaises(RuntimeError):
                    _main_captured(argv)


class LoadToolsTest(RegistryTestCase):
    """``_load_tools``: discovery of the tool modules."""

    def test_load_tools_is_idempotent(self) -> None:
        before = registry.commands()
        cli._load_tools()
        cli._load_tools()
        self.assertEqual(registry.commands(), before)

    def test_every_tool_module_is_registered(self) -> None:
        self.assertEqual({c.name for c in registry.commands()}, _tool_module_names())

    def test_importing_main_loads_no_tool(self) -> None:
        # In a fresh interpreter, importing textkit.cli.main imports no module of
        # textkit/cli/ but the command line's own: tools are loaded by _main.
        code = (
            "import sys, textkit.cli.main\n"
            "print(' '.join(sorted(m for m in sys.modules if m.startswith('textkit.cli.'))))\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            env=dict(os.environ, PYTHONIOENCODING="utf-8"),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        loaded = set(proc.stdout.split())
        self.assertEqual(loaded, {f"textkit.cli.{name}" for name in _INFRASTRUCTURE})


class ToolsSurviveTest(unittest.TestCase):
    """After a registry test, ``--help`` still lists every tool module under ``textkit/cli/``."""

    def test_tools_survive_a_registry_test(self) -> None:
        # Run a test that registers a fake command, in this process, then look at --help.
        result = unittest.TestResult()
        MainWithToolsTest("test_registered_command_is_listed_and_runs").run(result)
        self.assertTrue(result.wasSuccessful(), result.failures + result.errors)
        code, out, _ = _main_captured(["--help"])
        self.assertEqual(code, 0)
        listed = {name for name, _ in _help_block(out, "tools:") or []}
        self.assertEqual(listed, _tool_module_names())
        self.assertNotIn("zz-fake", listed)


if __name__ == "__main__":
    unittest.main()
