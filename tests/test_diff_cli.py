"""Tests for textkit/cli/diff.py, the ``python3 -m textkit diff`` tool (plan task T3.6).

Run through ``subprocess`` with ``_run`` and ``_run_bytes`` from ``tests/test_cli.py`` (cwd
the repository root, ``PYTHONIOENCODING=utf-8``), every exit code at least once. Input files
are written to a fresh ``tempfile`` directory and passed as absolute paths, so parallel runs
of the checks never share a file (phase 3 rule "The command line").
"""

import os
import pathlib
import tempfile
import unittest

from tests.test_cli import _run, _run_bytes
from textkit.cli.registry import PROG
from textkit.diff import unified_diff


class DiffCommandTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = pathlib.Path(directory.name)

    def _file(self, name, data):
        """Write ``data`` (bytes, or text written as UTF-8 bytes) and return its absolute path."""
        path = self.dir / name
        path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        return str(path.resolve())

    def test_equal_files_exit_0_and_write_nothing(self):
        a = self._file("a.txt", "same\ntext\n")
        b = self._file("b.txt", "same\ntext\n")
        result = _run("diff", a, b)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def test_different_files_exit_1_with_the_unified_diff(self):
        old, new = "one\ntwo\nthree\n", "one\n2\nthree\nfour ñ\n"
        result = _run("diff", self._file("a.txt", old), self._file("b.txt", new))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, unified_diff(old, new))
        self.assertTrue(result.stdout.startswith("--- a\n+++ b\n@@ -1,3 +1,4 @@\n"))
        self.assertEqual(result.stderr, "")

    def test_crlf_against_lf_exits_1_and_keeps_the_carriage_returns(self):
        result = _run_bytes("diff", self._file("a.txt", b"x\r\ny\r\n"),
                            self._file("b.txt", b"x\ny\n"))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stdout,
            "--- a\n+++ b\n@@ -1,2 +1,2 @@\n-x\r\n-y\r\n+x\n+y\n".encode("utf-8"),
        )

    def test_missing_file_exits_2_without_traceback(self):
        a = self._file("a.txt", "x\n")
        missing = str((self.dir / "missing.txt").resolve())
        for args in ((a, missing), (missing, a)):
            with self.subTest(args=args):
                result = _run("diff", *args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith(f"{PROG} diff: error: {missing}: "))
                self.assertNotIn("Traceback", result.stderr)

    def test_invalid_utf8_and_directories_exit_2(self):
        a = self._file("a.txt", "x\n")
        bad = self._file("bad.txt", b"ok\n\xff\n")
        result = _run("diff", a, bad)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            result.stderr, f"{PROG} diff: error: {bad}: not valid UTF-8 (byte 0xff at offset 3)\n"
        )
        result = _run("diff", a, str(self.dir.resolve()))
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.startswith(f"{PROG} diff: error: {self.dir.resolve()}: "))
        self.assertNotIn("Traceback", result.stderr)

    def test_file_without_final_newline(self):
        result = _run_bytes("diff", self._file("a.txt", "end"), self._file("b.txt", "end\n"))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stdout,
            b"--- a\n+++ b\n@@ -1 +1 @@\n-end\n\\ No newline at end of file\n+end\n",
        )

    def test_wrong_argument_count_exits_2_and_help_lists_the_tool(self):
        result = _run("diff", self._file("a.txt", "x\n"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("file-b", result.stderr)
        listing = _run("--help").stdout.split("tools:", 1)[1]
        self.assertIn("  diff ", listing)


if __name__ == "__main__":
    unittest.main()
