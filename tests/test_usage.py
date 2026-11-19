"""Usage guide test: every example in ``docs/usage.md`` runs, and every public function has one.

Plan task T2.8. The design, and the choices behind it:

* **Example format.** Python examples are fenced ``pycon`` blocks holding a doctest session
  (``>>>`` lines and their exact output). Each block is parsed with
  ``doctest.DocTestParser`` and run with ``doctest.DocTestRunner`` with no option flags, so
  the output must match exactly. Running the blocks one by one, instead of
  ``doctest.testfile`` over the whole page, keeps the Markdown clean (``testfile`` would
  read a closing fence right after an output line as part of that output) and lets the
  test know which block belongs to which function. Each block runs in fresh globals, so it
  imports what it uses and a block cannot pass thanks to an earlier one.
* **Command line examples** are fenced ``console`` blocks: ``$ python3 -m textkit ...``
  lines, each followed by its exact standard output. The command is split with ``shlex``
  and run with ``sys.executable`` (never a shell) from the repository root; it must exit 0
  and print exactly the lines shown. A ``$`` line that is anything else (another program,
  a pipe, a redirection) is reported, not skipped.
* **Nothing untested.** A fenced block of any other language, or with none, is reported:
  every example on the page is one the test runs.
* **Completeness.** Each function has a ``###`` heading holding its qualified name in
  backticks (``textkit.strings.squeeze``); its section runs to the next heading of level 3
  or less, and must hold a ``pycon`` block that calls the function (``name(``). The set of
  qualified names must equal the public functions, found with the discovery helpers of
  ``tests/test_api.py`` (``public_module_names``, ``import_quietly``, ``public_functions``),
  which apply the rule of ``scripts/check.sh``: single-underscore modules such as
  ``_tokens`` are private, a public function is a top-level ``def`` without a leading
  ``_``. So the three never disagree. A public function with no section, a heading for a
  function that does not exist (or sits in another module), a duplicate heading, a
  section with no example and a backticked ``###`` heading that is not a qualified textkit
  name are all reported.
* **No vacuous pass.** The checkers are run on small fake usage texts: a wrong output, a
  missing function, an unknown function, a section without an example, an untested block
  and a wrong command line output must each be reported. The real run must find more
  than ten public functions and run at least one example for each.
* **Determinism.** The examples avoid anything machine-dependent; ``char_freq``'s dict is in
  insertion order, so its repr is stable.
"""

from __future__ import annotations

import doctest
import io
import os
import pathlib
import re
import shlex
import subprocess
import sys
import unittest
from typing import Dict, List, NamedTuple, Set

from tests.test_api import import_quietly, public_functions, public_module_names

ROOT = pathlib.Path(__file__).resolve().parent.parent
USAGE = ROOT / "docs" / "usage.md"

# Fewer than this many public functions means discovery broke (14 when T2.8 was written).
MIN_PUBLIC_FUNCTIONS = 10

FENCE = re.compile(r"^```(.*)$")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
# A function entry: a level-3 heading that is one backticked name.
ENTRY = re.compile(r"^`([^`]+)`$")
QUALIFIED = re.compile(r"^textkit(\.[A-Za-z_]\w*)+$")
CLI_PREFIX = ["python3", "-m", "textkit"]


class Block(NamedTuple):
    """A fenced block: its language, the 1-based line of its opening fence, its text."""

    lang: str
    line: int
    text: str


class Entry(NamedTuple):
    """A function section: the heading's name, its line, and the blocks under it."""

    name: str
    line: int
    blocks: List[Block]


class Usage(NamedTuple):
    """A parsed usage page: every fenced block, the function sections, parse problems."""

    blocks: List[Block]
    entries: List[Entry]
    problems: List[str]


def parse_usage(text: str) -> Usage:
    """Split a usage page into fenced blocks and ``###`` function sections.

    Headings inside a fenced block are ignored. An unclosed fence is reported in
    ``problems`` (its block is dropped), as is a backticked ``###`` heading that is not a
    qualified textkit name.
    """
    blocks: List[Block] = []
    entries: List[Entry] = []
    problems: List[str] = []
    current = None  # the Entry whose section we are in, if any
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        fence = FENCE.match(lines[i])
        if fence:
            start = i
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                i += 1
            if i == len(lines):
                problems.append(f"line {start + 1}: unclosed fenced block")
                break
            block = Block(fence.group(1).strip(), start + 1, "\n".join(lines[start + 1:i]) + "\n")
            blocks.append(block)
            if current is not None:
                current.blocks.append(block)
        else:
            heading = HEADING.match(lines[i])
            if heading and len(heading.group(1)) <= 3:
                current = None
                entry = ENTRY.match(heading.group(2))
                if len(heading.group(1)) == 3 and entry:
                    name = entry.group(1)
                    if QUALIFIED.match(name):
                        current = Entry(name, i + 1, [])
                        entries.append(current)
                    else:
                        problems.append(
                            f"line {i + 1}: heading `{name}` is not a qualified name "
                            "(textkit.<module>.<function>)"
                        )
        i += 1
    return Usage(blocks, entries, problems)


def completeness_problems(usage: Usage, public: Set[str]) -> List[str]:
    """How ``usage`` fails to give one example per function of ``public``; empty if none.

    ``public`` holds qualified names (``textkit.strings.squeeze``). Reports every public
    function without a section, every section for a name not in ``public``, duplicate
    sections, and sections with no ``pycon`` block calling the function.
    """
    problems = list(usage.problems)
    seen: Dict[str, int] = {}
    for entry in usage.entries:
        if entry.name in seen:
            problems.append(
                f"line {entry.line}: `{entry.name}` already has a section (line {seen[entry.name]})"
            )
            continue
        seen[entry.name] = entry.line
        if entry.name not in public:
            problems.append(f"line {entry.line}: `{entry.name}` is not a public textkit function")
            continue
        short = entry.name.rsplit(".", 1)[1]
        calls = re.compile(rf"\b{re.escape(short)}\(")
        if not any(b.lang == "pycon" and calls.search(b.text) for b in entry.blocks):
            problems.append(f"line {entry.line}: `{entry.name}` has no pycon example calling it")
    problems.extend(
        f"`{name}` has no section in the usage guide" for name in sorted(public - set(seen))
    )
    for block in usage.blocks:
        if block.lang not in ("pycon", "console"):
            problems.append(
                f"line {block.line}: fenced block of language {block.lang!r} is not run by the "
                "test (use pycon or console)"
            )
    return problems


def run_pycon(blocks: List[Block], filename: str) -> List[str]:
    """Run every ``pycon`` block of ``blocks`` as a doctest; one message per failing block.

    A block with no ``>>>`` example is reported too. Each block gets fresh globals and its
    failures are reported with line numbers of ``filename``.
    """
    parser = doctest.DocTestParser()
    problems = []
    for block in blocks:
        if block.lang != "pycon":
            continue
        test = parser.get_doctest(
            block.text, {"__name__": "usage_example"}, f"block at line {block.line}",
            filename, block.line,
        )
        if not test.examples:
            problems.append(f"line {block.line}: pycon block has no >>> example")
            continue
        out = io.StringIO()
        result = doctest.DocTestRunner(verbose=False, optionflags=0).run(test, out=out.write)
        if result.failed:
            problems.append(out.getvalue())
    return problems


def run_console(blocks: List[Block]) -> List[str]:
    """Run every command of the ``console`` blocks of ``blocks``; one message per failure.

    Each ``$`` line must be ``python3 -m textkit ...``; it is run with ``sys.executable``
    from the repository root and must exit 0 with exactly the output lines below it.
    """
    problems = []
    for block in blocks:
        if block.lang != "console":
            continue
        lines = block.text.splitlines()
        if not lines or not lines[0].startswith("$ "):
            problems.append(f"line {block.line}: console block must start with a $ command")
            continue
        for offset, line in enumerate(lines):
            if not line.startswith("$ "):
                continue
            where = f"line {block.line + 1 + offset}"
            expected = []
            for later in lines[offset + 1:]:
                if later.startswith("$ "):
                    break
                expected.append(later)
            try:
                argv = shlex.split(line[2:])
            except ValueError as exc:
                problems.append(f"{where}: cannot parse {line!r}: {exc}")
                continue
            if argv[:3] != CLI_PREFIX or any(a in ("|", ">", "<", ";", "&&") for a in argv):
                problems.append(f"{where}: only `python3 -m textkit ...` commands run: {line!r}")
                continue
            result = subprocess.run(
                [sys.executable] + argv[1:], cwd=ROOT, capture_output=True, text=True,
                timeout=60, env=dict(os.environ, PYTHONIOENCODING="utf-8"),
            )
            got = result.stdout.splitlines()
            if result.returncode != 0 or got != expected:
                problems.append(
                    f"{where}: {line!r}\n  expected (exit 0): {expected!r}\n"
                    f"  got (exit {result.returncode}): {got!r}\n  stderr: {result.stderr!r}"
                )
    return problems


def all_problems(text: str, public: Set[str], filename: str = "usage.md") -> List[str]:
    """Every completeness problem and failing example of the usage page ``text``."""
    usage = parse_usage(text)
    return (
        completeness_problems(usage, public)
        + run_pycon(usage.blocks, filename)
        + run_console(usage.blocks)
    )


def public_qualified_names() -> Set[str]:
    """The qualified names of textkit's public functions, by ``tests/test_api.py``'s rule."""
    names = set()
    for module_name in public_module_names():
        module, problem = import_quietly(module_name)
        if module is None:
            raise AssertionError(f"{module_name}: {problem}")
        names.update(f"{module_name}.{name}" for name, _ in public_functions(module))
    return names


# A small fake page for the checker's own tests; the fake "public" set below matches it.
GOOD_PAGE = """\
# Fake

### `textkit.strings.squeeze`

```pycon
>>> from textkit.strings import squeeze
>>> squeeze("a   b")
'a b'
```

## Command line

```console
$ python3 -m textkit slugify "Hello, World!"
hello-world
```
"""
FAKE_PUBLIC = {"textkit.strings.squeeze"}


class CheckerTest(unittest.TestCase):
    """The checkers report each kind of problem, so the real test cannot pass vacuously."""

    def assertReports(self, page: str, needle: str, public: Set[str] = FAKE_PUBLIC) -> None:
        problems = all_problems(page, public)
        self.assertTrue(any(needle in p for p in problems), f"{needle!r} not in {problems!r}")

    def test_accepts_a_good_page(self) -> None:
        self.assertEqual(all_problems(GOOD_PAGE, FAKE_PUBLIC), [])

    def test_reports_a_wrong_output(self) -> None:
        self.assertReports(GOOD_PAGE.replace("'a b'", "'a  b'"), "Failed example")

    def test_reports_a_missing_function(self) -> None:
        self.assertReports(
            GOOD_PAGE, "`textkit.strings.slugify` has no section",
            FAKE_PUBLIC | {"textkit.strings.slugify"},
        )

    def test_reports_an_unknown_function(self) -> None:
        page = GOOD_PAGE.replace("textkit.strings.squeeze`", "textkit.strings.squash`")
        self.assertReports(page, "`textkit.strings.squash` is not a public textkit function")
        # The other side of the same mistake: the real function is now missing.
        self.assertReports(page, "`textkit.strings.squeeze` has no section")

    def test_reports_a_function_under_the_wrong_module(self) -> None:
        page = GOOD_PAGE.replace("### `textkit.strings.", "### `textkit.cases.")
        self.assertReports(page, "`textkit.cases.squeeze` is not a public textkit function")

    def test_reports_an_unqualified_heading(self) -> None:
        self.assertReports(
            GOOD_PAGE.replace("### `textkit.strings.squeeze`", "### `squeeze`"),
            "is not a qualified name",
        )

    def test_reports_a_duplicate_section(self) -> None:
        section = GOOD_PAGE.split("## Command line")[0].split("# Fake\n")[1]
        self.assertReports(GOOD_PAGE + section, "already has a section")

    def test_reports_a_section_without_an_example(self) -> None:
        page = GOOD_PAGE.replace('>>> squeeze("a   b")\n\'a b\'\n', "")
        self.assertReports(page, "has no pycon example calling it")

    def test_reports_an_untested_block(self) -> None:
        self.assertReports(GOOD_PAGE + "\n```python\nsqueeze('x')\n```\n", "not run by the test")

    def test_reports_an_unclosed_fence(self) -> None:
        self.assertReports(GOOD_PAGE + "\n```pycon\n>>> 1\n1\n", "unclosed fenced block")

    def test_reports_a_wrong_command_line_output(self) -> None:
        self.assertReports(GOOD_PAGE.replace("hello-world", "hello_world"), "expected (exit 0)")

    def test_reports_a_command_line_failure(self) -> None:
        self.assertReports(
            GOOD_PAGE.replace("slugify", "no_such_function"), "got (exit 2)"
        )

    def test_reports_a_command_it_cannot_run(self) -> None:
        page = GOOD_PAGE.replace('$ python3 -m textkit slugify "Hello, World!"',
                                 '$ echo "Hello, World!" | python3 -m textkit slugify -')
        self.assertReports(page, "only `python3 -m textkit ...` commands run")


class UsageGuideTest(unittest.TestCase):
    """docs/usage.md gives a passing example for every public function."""

    def test_every_public_function_has_a_passing_example(self) -> None:
        public = public_qualified_names()
        self.assertGreater(len(public), MIN_PUBLIC_FUNCTIONS, "discovery found too few functions")
        text = USAGE.read_text(encoding="utf-8")
        usage = parse_usage(text)
        # Every section holds at least one example, so this is one or more per function.
        self.assertGreaterEqual(sum(b.lang == "pycon" for b in usage.blocks), len(public))
        problems = all_problems(text, public, str(USAGE))
        self.assertEqual(problems, [], "\n" + "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
