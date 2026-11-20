"""Tests for ``textkit/cli/markdown.py``, the ``python3 -m textkit markdown <file>`` tool (T3.5).

Every test runs the real command line in a subprocess (phase 3 rule "The command line"),
through ``_run`` and ``_run_bytes`` of ``tests/test_cli.py`` (cwd the repository root,
``PYTHONIOENCODING=utf-8``), with input files written to a ``tempfile`` directory and passed
as absolute paths, since the checks run in parallel. ``_run`` decodes in text mode, which
turns ``"\\r"`` into ``"\\n"``, so the ``"\\r\\n"`` test uses ``_run_bytes``. The exit codes
are 0 (converted) and 2 (a file that cannot be read, or a usage error); there is no 1,
because ``to_html`` accepts every text.
"""

import os
import pathlib
import tempfile
import unittest

from tests.test_cli import _run, _run_bytes
from textkit.cli.registry import PROG
from textkit.markdown import to_html


class MarkdownCommandTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = pathlib.Path(tmp.name).resolve()

    def _write(self, name: str, data: bytes) -> str:
        path = self.dir / name
        path.write_bytes(data)
        return str(path)

    def test_converts_a_file(self):
        text = "# Title\n\nSome *text* & <b>.\n"
        path = self._write("a.md", text.encode("utf-8"))
        proc = _run("markdown", path)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.stdout, to_html(text))
        self.assertEqual(
            proc.stdout, "<h1>Title</h1>\n<p>Some <em>text</em> &amp; &lt;b&gt;.</p>\n"
        )

    def test_crlf_file_gives_lf_only_html(self):
        text = "# T\r\n\r\n```py\r\nx = 1\r\n```\r\n"
        path = self._write("crlf.md", text.encode("utf-8"))
        proc = _run_bytes("markdown", path)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            proc.stdout,
            '<h1>T</h1>\n<pre><code class="language-py">x = 1\n</code></pre>\n'.encode("utf-8"),
        )

    def test_non_ascii_text_round_trips_as_utf8(self):
        path = self._write("u.md", "- ñandú 😀\n".encode("utf-8"))
        proc = _run_bytes("markdown", path)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "<ul>\n<li>ñandú 😀</li>\n</ul>\n".encode("utf-8"))

    def test_empty_file_writes_nothing(self):
        proc = _run_bytes("markdown", self._write("empty.md", b""))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, b"")
        self.assertEqual(proc.stderr, b"")

    def test_missing_file_exits_2(self):
        path = str(self.dir / "missing.md")
        proc = _run("markdown", path)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertEqual(
            proc.stderr, f"{PROG} markdown: error: {path}: No such file or directory\n"
        )

    def test_directory_exits_2(self):
        proc = _run("markdown", str(self.dir))
        self.assertEqual(proc.returncode, 2)
        self.assertTrue(proc.stderr.startswith(f"{PROG} markdown: error: {self.dir}: "))
        self.assertNotIn("Traceback", proc.stderr)

    def test_invalid_utf8_exits_2(self):
        path = self._write("latin1.md", "# año".encode("latin-1"))
        proc = _run("markdown", path)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertEqual(proc.stderr, f"{PROG} markdown: error: {path}: not valid UTF-8\n")

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root reads any file")
    def test_unreadable_file_exits_2(self):
        path = self._write("secret.md", b"# x")
        os.chmod(path, 0)
        self.addCleanup(os.chmod, path, 0o600)
        proc = _run("markdown", path)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(
            proc.stderr, f"{PROG} markdown: error: {path}: Permission denied\n"
        )

    def test_missing_argument_is_a_usage_error(self):
        proc = _run("markdown")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("usage:", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_help_lists_the_tool(self):
        proc = _run("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        tools = proc.stdout.split("\ntools:\n", 1)[1]
        self.assertRegex(tools, r"(?m)^  markdown +Convert a Markdown file to HTML")


if __name__ == "__main__":
    unittest.main()
