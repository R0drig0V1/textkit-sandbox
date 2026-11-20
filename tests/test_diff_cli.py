"""Tests for textkit/cli/diff.py, ``python3 -m textkit diff <file-a> <file-b>`` (plan task T3.6).

Every test runs the real command line in a subprocess through ``_run`` and ``_run_bytes`` of
``tests/test_cli.py`` (cwd the repository root, UTF-8), with its input files in a fresh
``tempfile`` directory passed as absolute paths, so parallel runs never share a file.
"""

import os
import tempfile
import unittest

from tests.test_cli import _run, _run_bytes
from textkit.diff import unified_diff


class DiffCommandTest(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)

    def _file(self, name: str, content: bytes) -> str:
        """Write ``content`` to a new file in the temporary directory; return its absolute path."""
        path = os.path.join(self._dir.name, name)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def test_equal_files_exit_0_and_print_nothing(self):
        a = self._file("a.txt", b"same\ntext\n")
        b = self._file("b.txt", b"same\ntext\n")
        proc = _run("diff", a, b)
        self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, "", ""))

    def test_different_files_exit_1_and_print_the_diff(self):
        a = self._file("a.txt", "one\ntwo\nthree\n".encode("utf-8"))
        b = self._file("b.txt", "one\ndos\nthree\n".encode("utf-8"))
        proc = _run("diff", a, b)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.stdout, "--- a\n+++ b\n@@ -1,3 +1,3 @@\n one\n-two\n+dos\n three\n")

    def test_output_is_written_unchanged(self):
        # Non-ASCII text, no final newline: the marker and the UTF-8 bytes as the function
        # gives them, with nothing added.
        a = self._file("a.txt", "año\nnaïve".encode("utf-8"))
        b = self._file("b.txt", "año\nnaive".encode("utf-8"))
        proc = _run_bytes("diff", a, b)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, unified_diff("año\nnaïve", "año\nnaive").encode("utf-8"))

    def test_crlf_file_against_lf_file_exits_1(self):
        a = self._file("crlf.txt", b"one\r\ntwo\r\n")
        b = self._file("lf.txt", b"one\ntwo\n")
        proc = _run_bytes("diff", a, b)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        expected = "--- a\n+++ b\n@@ -1,2 +1,2 @@\n-one\r\n-two\r\n+one\n+two\n"
        self.assertEqual(proc.stdout, expected.encode("utf-8"))

    def test_missing_file_exits_2(self):
        a = self._file("a.txt", b"x\n")
        missing = os.path.join(self._dir.name, "missing.txt")
        for args in ((a, missing), (missing, a)):
            with self.subTest(args=args):
                proc = _run("diff", *args)
                self.assertEqual((proc.returncode, proc.stdout), (2, ""))
                self.assertTrue(
                    proc.stderr.startswith(f"python3 -m textkit diff: error: {missing}: "),
                    proc.stderr,
                )
                self.assertNotIn("Traceback", proc.stderr)

    def test_directory_and_invalid_utf8_exit_2(self):
        a = self._file("a.txt", b"x\n")
        latin1 = self._file("latin1.txt", "café\n".encode("latin-1"))
        for bad in (self._dir.name, latin1):
            with self.subTest(bad=bad):
                proc = _run("diff", a, bad)
                self.assertEqual((proc.returncode, proc.stdout), (2, ""))
                self.assertIn(f"python3 -m textkit diff: error: {bad}: ", proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("not valid UTF-8", _run("diff", a, latin1).stderr)

    def test_wrong_argument_count_exits_2(self):
        a = self._file("a.txt", b"x\n")
        proc = _run("diff", a)
        self.assertEqual((proc.returncode, proc.stdout), (2, ""))
        self.assertIn("usage:", proc.stderr)

    def test_listed_under_tools_in_help(self):
        proc = _run("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        tools = proc.stdout.split("tools:", 1)[1]
        self.assertIn("diff", tools.split())


if __name__ == "__main__":
    unittest.main()
