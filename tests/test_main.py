"""Tests for textkit.__main__, the command line (plan task T2.6).

Most tests run ``_main(argv)`` in process with stdout, stderr (and stdin, for ``-``)
replaced by ``io.StringIO``. The output formats and error paths that no real command
reaches yet (list, float, ``ValueError``) use small fake commands passed through the
``commands`` argument, and command discovery is tested on fake modules registered in
``sys.modules``. Subprocess runs of ``python3 -m textkit --help`` and ``--version`` prove
that the entry point itself works. ``VersionTest`` covers ``--version`` and
``textkit.__version__`` (plan task T2.7).
"""

import contextlib
import io
import re
import subprocess
import sys
import types
import unittest
from pathlib import Path
from typing import List, Optional

import textkit
from textkit.__main__ import _discover, _main

ROOT = Path(__file__).resolve().parent.parent

# The canonical form of a PEP 440 version (the regex of PEP 440, Appendix B).
PEP440_CANONICAL = re.compile(
    r"^([1-9][0-9]*!)?(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))*((a|b|rc)(0|[1-9][0-9]*))?"
    r"(\.post(0|[1-9][0-9]*))?(\.dev(0|[1-9][0-9]*))?$"
)


def run(argv: List[str], commands=None, stdin: Optional[str] = None):
    """Run ``_main(argv)`` in process; return (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    old_stdin = sys.stdin
    if stdin is not None:
        sys.stdin = io.StringIO(stdin)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = _main(argv, commands)
    finally:
        sys.stdin = old_stdin
    return code, out.getvalue(), err.getvalue()


# Fake commands for the output types and error paths no real command produces yet.
def fake_bool(text: str) -> bool:
    """Is the text "yes"."""
    return text == "yes"


def fake_list(text: str) -> List[str]:
    """Split on whitespace."""
    return text.split()


def fake_float(text: str) -> float:
    """Half the length."""
    return len(text) / 2


def fake_value_error(text: str) -> str:
    """Always rejects the text."""
    raise ValueError(f"bad text {text!r}")


def fake_type_error(text: str) -> str:
    """Always raises TypeError."""
    raise TypeError("wrong type")


FAKES = {
    "fake_bool": fake_bool,
    "fake_list": fake_list,
    "fake_float": fake_float,
    "fake_value_error": fake_value_error,
    "fake_type_error": fake_type_error,
}


class RealCommandsTest(unittest.TestCase):
    def test_str_printed_as_is(self):
        self.assertEqual(run(["squeeze", "  a   b  "]), (0, "a b\n", ""))
        self.assertEqual(run(["slugify", "Hello, World!"]), (0, "hello-world\n", ""))

    def test_int(self):
        self.assertEqual(run(["word_count", "well-known words here"]), (0, "3\n", ""))

    def test_bool(self):
        self.assertEqual(run(["is_palindrome", "Was it a car"]), (0, "false\n", ""))
        self.assertEqual(run(["is_palindrome", "Never odd or even"]), (0, "true\n", ""))

    def test_dict_key_tab_value_in_order(self):
        self.assertEqual(run(["char_freq", "baab"]), (0, "b\t2\na\t2\n", ""))

    def test_empty_dict_prints_nothing(self):
        self.assertEqual(run(["char_freq", "   "]), (0, "", ""))

    def test_text_with_spaces_is_one_argument(self):
        self.assertEqual(run(["to_snake_case", "parse URL now"]), (0, "parse_url_now\n", ""))

    def test_text_starting_with_dash_after_double_dash(self):
        self.assertEqual(run(["squeeze", "--", "-x  y"]), (0, "-x y\n", ""))

    def test_stdin_with_dash(self):
        self.assertEqual(run(["squeeze", "-"], stdin="a   b\n"), (0, "a b\n", ""))

    def test_stdin_drops_only_one_trailing_line_break(self):
        # strip_accents keeps whitespace, so the remaining "\n" shows in the output.
        self.assertEqual(run(["strip_accents", "-"], stdin="Ñandú\n\n"), (0, "Nandu\n\n", ""))
        self.assertEqual(run(["strip_accents", "-"], stdin="é\r\n"), (0, "e\n", ""))
        self.assertEqual(run(["strip_accents", "-"], stdin="é"), (0, "e\n", ""))


class FakeOutputTypesTest(unittest.TestCase):
    def test_bool(self):
        self.assertEqual(run(["fake_bool", "yes"], FAKES), (0, "true\n", ""))
        self.assertEqual(run(["fake_bool", "no"], FAKES), (0, "false\n", ""))

    def test_list_one_item_per_line(self):
        self.assertEqual(run(["fake_list", "a b c"], FAKES), (0, "a\nb\nc\n", ""))
        self.assertEqual(run(["fake_list", " "], FAKES), (0, "", ""))

    def test_float(self):
        self.assertEqual(run(["fake_float", "abc"], FAKES), (0, "1.5\n", ""))


class ErrorPathsTest(unittest.TestCase):
    def assertUsageError(self, argv, fragment):
        code, out, err = run(argv)
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn(fragment, err)
        self.assertNotIn("Traceback", err)

    def test_unknown_function(self):
        self.assertUsageError(["nope", "x"], "invalid choice: 'nope'")

    def test_function_that_is_not_a_command(self):
        # truncate needs a width, so it is not offered.
        self.assertUsageError(["truncate", "x"], "invalid choice: 'truncate'")

    def test_no_function(self):
        self.assertUsageError([], "required")

    def test_missing_text(self):
        self.assertUsageError(["squeeze"], "required: text")

    def test_extra_words_are_not_joined(self):
        self.assertUsageError(["squeeze", "a", "b"], "unrecognized arguments: b")

    def test_value_error(self):
        code, out, err = run(["fake_value_error", "x"], FAKES)
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(err, "textkit: fake_value_error: bad text 'x'\n")

    def test_type_error(self):
        code, out, err = run(["fake_type_error", "x"], FAKES)
        self.assertEqual((code, out, err), (1, "", "textkit: fake_type_error: wrong type\n"))

    def test_undecodable_stdin(self):
        stdin = io.TextIOWrapper(io.BytesIO(b"\xff\xfe"), encoding="utf-8")
        old_stdin, sys.stdin = sys.stdin, stdin
        try:
            err = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                code = _main(["squeeze", "-"])
        finally:
            sys.stdin = old_stdin
        self.assertEqual(code, 1)
        self.assertTrue(err.getvalue().startswith("textkit: squeeze: "))

    def test_help_returns_zero(self):
        code, out, err = run(["--help"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("char_freq", out)

    def test_function_help_shows_docstring(self):
        code, out, _ = run(["slugify", "--help"])
        self.assertEqual(code, 0)
        self.assertIn("Failure modes", out)


def fake_module(name: str, source: str) -> str:
    """Register a module built from ``source`` under ``name``; return the name."""
    module = types.ModuleType(name)
    exec(compile(source, name, "exec"), module.__dict__)
    sys.modules[name] = module
    return name


class DiscoveryTest(unittest.TestCase):
    def tearDown(self):
        for name in [n for n in sys.modules if n.startswith("fake_textkit_")]:
            del sys.modules[name]

    def test_real_commands(self):
        commands = _discover()
        for name in ("squeeze", "slugify", "word_count", "char_freq", "strip_accents",
                     "to_snake_case", "to_camel_case"):
            self.assertIn(name, commands)
        # A second required parameter excludes a function.
        for name in ("truncate", "wrap", "slug_title"):
            self.assertNotIn(name, commands)
        self.assertFalse([n for n in commands if n.startswith("_")])
        self.assertEqual(list(commands), sorted(commands))

    def test_selection_rules(self):
        source = '''
from typing import List
from textwrap import dedent
def one(text: str) -> str: return text
def defaults(text: str, width: int = 3, *rest: str, **opts: str) -> str: return text
def two(text: str, width: int) -> str: return text
def none() -> str: return ""
def not_text(n: int) -> int: return n
def untyped(text): return text
def keyword_only(*, text: str) -> str: return text
def _private(text: str) -> str: return text
'''
        commands = _discover([fake_module("fake_textkit_a", source)])
        # dedent is a one-text function too, but imported, so it is not offered.
        self.assertEqual(list(commands), ["defaults", "one"])

    def test_future_annotations_are_accepted(self):
        source = "from __future__ import annotations\ndef late(text: str) -> str: return text\n"
        self.assertEqual(list(_discover([fake_module("fake_textkit_b", source)])), ["late"])

    def test_name_clash_fails_loudly(self):
        a = fake_module("fake_textkit_c", "def same(text: str) -> str: return 'c'\n")
        b = fake_module("fake_textkit_d", "def same(text: str) -> str: return 'd'\n")
        with self.assertRaises(RuntimeError) as ctx:
            _discover([a, b])
        self.assertIn("fake_textkit_c", str(ctx.exception))
        self.assertIn("fake_textkit_d", str(ctx.exception))


class VersionTest(unittest.TestCase):
    def test_version_is_pep440_str(self):
        self.assertIsInstance(textkit.__version__, str)
        self.assertRegex(textkit.__version__, PEP440_CANONICAL)

    def test_version_option(self):
        self.assertEqual(run(["--version"]), (0, f"textkit {textkit.__version__}\n", ""))

    def test_version_needs_no_function(self):
        # The function is required, but argparse runs --version before that check, also
        # when no command exists at all.
        self.assertEqual(run(["--version"], {}), (0, f"textkit {textkit.__version__}\n", ""))

    def test_version_wins_over_a_following_function(self):
        self.assertEqual(run(["--version", "squeeze"])[:2], (0, f"textkit {textkit.__version__}\n"))

    def test_version_after_the_function_is_a_usage_error(self):
        code, out, err = run(["squeeze", "x", "--version"])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("unrecognized arguments: --version", err)

    def test_single_source(self):
        # __main__ must read textkit.__version__, never repeat the literal.
        source = (ROOT / "textkit" / "__main__.py").read_text(encoding="utf-8")
        self.assertNotIn(textkit.__version__, source)


class EntryPointTest(unittest.TestCase):
    def test_python_m_textkit_help(self):
        proc = subprocess.run(
            [sys.executable, "-m", "textkit", "--help"],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("usage: python3 -m textkit", proc.stdout)
        self.assertIn("squeeze", proc.stdout)

    def test_python_m_textkit_version(self):
        proc = subprocess.run(
            [sys.executable, "-m", "textkit", "--version"],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, f"textkit {textkit.__version__}\n")
        self.assertEqual(proc.stderr, "")


if __name__ == "__main__":
    unittest.main()
