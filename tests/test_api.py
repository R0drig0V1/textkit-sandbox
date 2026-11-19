"""API contract test: every public textkit function has a docstring and full type hints.

Plan task T2.5. The contract, and the choices behind it:

* **Which modules.** The package itself (``textkit/__init__.py``, its public namespace) and
  the modules ``pkgutil.iter_modules`` finds in it, so a module added later is covered with
  no list to maintain. A single-underscore module is private and out of the contract:
  ``textkit/_tokens.py`` (T1.10's shared tokenizer) has no README row, and its names may
  change with the helpers that use it. Dunder modules (``__init__``, ``__main__``) are in.
  This is the rule ``scripts/check.sh`` applies to ``textkit/*.py``, so the two never
  disagree about what is public. Subpackages are skipped, as ``check.sh`` only reads
  ``textkit/*.py``.
* **``textkit/__main__.py`` (T2.6, the command line) is covered**, like every dunder module
  in ``check.sh``: its functions are ``_``-prefixed today, but a public one added later must
  honour the contract. Importing it must not run the command line. Its ``if __name__ ==
  "__main__"`` guard ensures that, and the test guards it too: every module is imported with
  a dummy ``sys.argv`` and with standard output and error captured. A ``SystemExit`` or any
  output during the import fails the test with a clear message, instead of the run dying
  half-way. Discovery itself imports nothing.
* **Which functions.** "Public function" means what ``scripts/check.sh`` means: a
  top-level ``def`` (or ``async def``) in the module's own source whose name has no leading
  ``_``. The names are read from the module's syntax tree, not from its namespace, so
  names a module imports (``slugify`` imported into another module, ``typing.List``, ...)
  are never mistaken for its own functions.
* **Type hints.** Every parameter needs one: positional-only, ordinary, ``*args``,
  keyword-only and ``**kwargs``; and so does the return value (a function that returns
  nothing says ``-> None``). The hints are read with ``typing.get_type_hints``, so string
  annotations (``from __future__ import annotations``) are evaluated: an annotation that
  does not resolve, such as a typo in a type name, fails the test instead of passing as an
  opaque string.
* **Docstring.** Non-empty after ``strip()``. Whether it describes the behaviour and the
  failure modes is for review, not for a test.
* **No vacuous pass.** The checker is run on small fake functions defined here, each
  breaking one rule, and must report each of them; discovery is run on a fake module that
  imports a textkit function and must not report it; and the real run must find more than
  ten public functions, so a discovery that silently finds nothing fails.
"""

from __future__ import annotations

import ast
import contextlib
import importlib
import importlib.util
import inspect
import io
import pathlib
import pkgutil
import subprocess
import sys
import tempfile
import typing
import unittest
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Tuple

import textkit

# Fewer than this many public functions means discovery broke (14 when T2.5 was written).
MIN_PUBLIC_FUNCTIONS = 10


def is_private_module(name: str) -> bool:
    """True for a single-underscore module name (``_tokens``), false for ``__main__``.

    The same rule as ``scripts/check.sh``: a leading ``_`` makes a module private, but a
    dunder name (``__init__``, ``__main__``) does not.
    """
    return name.startswith("_") and not name.startswith("__")


def public_module_names() -> List[str]:
    """The dotted names of the package and its public modules, found without importing them.

    ``textkit`` itself comes first; then every module of the package except private
    (single-underscore) ones and subpackages; see the module docstring for why.
    """
    return [textkit.__name__] + sorted(
        f"{textkit.__name__}.{info.name}"
        for info in pkgutil.iter_modules(textkit.__path__)
        if not is_private_module(info.name) and not info.ispkg
    )


def import_quietly(name: str) -> Tuple[Optional[ModuleType], str]:
    """Import module ``name`` with a dummy ``sys.argv`` and output captured.

    Returns ``(module, "")`` when the import is silent, or ``(None, problem)`` when it
    raised ``SystemExit`` or wrote to standard output or error, as a command line run at
    import time would (``textkit.__main__`` without its ``__name__`` guard). Other
    exceptions propagate: a module that cannot be imported is a plain error.
    """
    out, err = io.StringIO(), io.StringIO()
    saved_argv = sys.argv
    sys.argv = ["textkit-api-contract-test"]
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            module = importlib.import_module(name)
    except SystemExit as exc:
        return None, f"importing it raised SystemExit({exc.code!r}): it ran at import time"
    finally:
        sys.argv = saved_argv
    if out.getvalue() or err.getvalue():
        return None, "importing it printed output: it ran at import time"
    return module, ""


def public_functions(module: ModuleType) -> List[Tuple[str, Any]]:
    """The ``(name, object)`` pairs of the public functions ``module`` defines itself.

    The names are the top-level ``def`` and ``async def`` statements of the module's source
    file without a leading ``_``, as in ``scripts/check.sh``; imported names never appear in
    that list. Raises ``OSError`` if the source file cannot be read.
    """
    source = pathlib.Path(module.__file__).read_text(encoding="utf-8")
    names = [
        node.name
        for node in ast.parse(source).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    ]
    return [(name, getattr(module, name)) for name in names]


def contract_violations(func: Callable[..., Any]) -> List[str]:
    """The ways ``func`` breaks the API contract, as readable messages; empty if none.

    Checks a non-empty docstring, a resolvable type hint for every parameter (``*args``,
    ``**kwargs`` and keyword-only ones included) and a return annotation. An annotation that
    ``typing.get_type_hints`` cannot evaluate is reported, not raised.
    """
    problems = []
    if not (func.__doc__ or "").strip():
        problems.append("no docstring")
    try:
        hints: Dict[str, Any] = typing.get_type_hints(func)
    except Exception as exc:  # NameError for a typo, TypeError for a non-type, ...
        problems.append(f"annotations do not resolve: {type(exc).__name__}: {exc}")
        return problems
    for name, param in inspect.signature(func).parameters.items():
        if name not in hints:
            prefix = {param.VAR_POSITIONAL: "*", param.VAR_KEYWORD: "**"}.get(param.kind, "")
            problems.append(f"parameter {prefix}{name} has no type hint")
    if "return" not in hints:
        problems.append("no return annotation")
    return problems


# Fake functions for the checker's own tests. Their annotations are strings (the
# ``__future__`` import above), so the checker must evaluate them to accept them.


def _good(a: int, /, b: str, *args: int, c: bool = True, **kwargs: str) -> List[str]:
    """Every kind of parameter, all annotated."""
    return []


def _good_returns_none(text: str) -> None:
    """Returns nothing, and says so."""


def _no_docstring(text: str) -> str:
    return text


def _blank_docstring(text: str) -> str:
    """   """
    return text


def _missing_param_hint(text: str, width) -> str:  # noqa: ANN001 (deliberate)
    """Lacks a hint for width."""
    return text


def _missing_args_hint(text: str, *args) -> str:  # noqa: ANN002 (deliberate)
    """Lacks a hint for *args."""
    return text


def _missing_kwargs_hint(text: str, **kwargs) -> str:  # noqa: ANN003 (deliberate)
    """Lacks a hint for **kwargs."""
    return text


def _missing_kwonly_hint(text: str, *, strict=False) -> str:  # noqa: ANN001 (deliberate)
    """Lacks a hint for the keyword-only strict."""
    return text


def _missing_return(text: str):  # noqa: ANN202 (deliberate)
    """Lacks a return annotation."""
    return text


def _typo_in_annotation(text: Strr) -> str:  # noqa: F821 (deliberate typo)
    """Annotated with a name that does not exist."""
    return text


class ContractCheckerTest(unittest.TestCase):
    """The checker reports each broken rule, so the contract test cannot pass vacuously."""

    def test_accepts_fully_annotated_functions(self) -> None:
        self.assertEqual(contract_violations(_good), [])
        self.assertEqual(contract_violations(_good_returns_none), [])

    def test_reports_each_broken_rule(self) -> None:
        cases = {
            _no_docstring: "no docstring",
            _blank_docstring: "no docstring",
            _missing_param_hint: "parameter width has no type hint",
            _missing_args_hint: "parameter *args has no type hint",
            _missing_kwargs_hint: "parameter **kwargs has no type hint",
            _missing_kwonly_hint: "parameter strict has no type hint",
            _missing_return: "no return annotation",
        }
        for func, expected in cases.items():
            with self.subTest(func=func.__name__):
                self.assertEqual(contract_violations(func), [expected])

    def test_reports_an_annotation_that_does_not_resolve(self) -> None:
        problems = contract_violations(_typo_in_annotation)
        self.assertEqual(len(problems), 1)
        self.assertIn("annotations do not resolve: NameError", problems[0])
        self.assertIn("Strr", problems[0])


class DiscoveryTest(unittest.TestCase):
    """Discovery finds a module's own public defs and nothing it imports."""

    def test_skips_imported_and_private_names(self) -> None:
        source = (
            '"""A fake module."""\n'
            "from typing import List\n"
            "from textkit.strings import slugify\n"
            "def _helper() -> None:\n"
            '    """Private."""\n'
            "def own(text: str) -> List[str]:\n"
            '    """Public."""\n'
            "    return [slugify(text)]\n"
            "async def own_async() -> None:\n"
            '    """Public too."""\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "fake_textkit_module.py"
            path.write_text(source, encoding="utf-8")
            spec = importlib.util.spec_from_file_location("fake_textkit_module", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            found = [name for name, _ in public_functions(module)]
        self.assertEqual(found, ["own", "own_async"])

    def test_private_modules_are_out_and_dunder_modules_in(self) -> None:
        self.assertTrue(is_private_module("_tokens"))
        self.assertFalse(is_private_module("__main__"))
        self.assertFalse(is_private_module("strings"))
        before = set(sys.modules)
        names = public_module_names()
        self.assertEqual(set(sys.modules) - before, set(), "discovery must import nothing")
        self.assertEqual(names[0], "textkit")
        self.assertIn("textkit.strings", names)
        self.assertIn("textkit.__main__", names)
        self.assertNotIn("textkit._tokens", names)


class ImportGuardTest(unittest.TestCase):
    """A module that runs (exits or prints) when imported is reported, not fatal."""

    def _import_fake(self, body: str) -> Tuple[Optional[ModuleType], str]:
        with tempfile.TemporaryDirectory() as tmp:
            pathlib.Path(tmp, "fake_cli_module.py").write_text(body, encoding="utf-8")
            sys.path.insert(0, tmp)
            try:
                return import_quietly("fake_cli_module")
            finally:
                sys.path.remove(tmp)
                sys.modules.pop("fake_cli_module", None)

    def test_reports_a_module_that_exits_on_import(self) -> None:
        module, problem = self._import_fake("import sys\nsys.exit(2)\n")
        self.assertIsNone(module)
        self.assertIn("SystemExit(2)", problem)

    def test_reports_a_module_that_prints_on_import(self) -> None:
        module, problem = self._import_fake("print('usage: textkit ...')\n")
        self.assertIsNone(module)
        self.assertIn("printed output", problem)

    def test_accepts_a_guarded_module(self) -> None:
        module, problem = self._import_fake(
            "import sys\nif __name__ == '__main__':\n    sys.exit(2)\n"
        )
        self.assertIsNotNone(module)
        self.assertEqual(problem, "")

    def test_importing_textkit_main_does_not_run_the_cli(self) -> None:
        # A fresh interpreter, because another test may already have imported (and so
        # cached) textkit.__main__ in this one, which would make the import a no-op.
        root = pathlib.Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, "-c", "import textkit.__main__"],
            cwd=root, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr), (0, "", ""),
            "importing textkit.__main__ must not run the command line",
        )


class ApiContractTest(unittest.TestCase):
    """Every public function of every public textkit module honours the contract."""

    def test_every_public_function_has_docstring_and_type_hints(self) -> None:
        checked = 0
        violations = []
        for module_name in public_module_names():
            module, problem = import_quietly(module_name)
            if module is None:
                violations.append(f"{module_name}: {problem}")
                continue
            for name, obj in public_functions(module):
                checked += 1
                where = f"{module_name}.{name}"
                if not callable(obj):
                    violations.append(f"{where}: rebound to a non-callable {type(obj).__name__}")
                    continue
                violations.extend(f"{where}: {p}" for p in contract_violations(obj))
        self.assertGreater(checked, MIN_PUBLIC_FUNCTIONS, "discovery found too few functions")
        self.assertEqual(violations, [], "\n" + "\n".join(violations))


if __name__ == "__main__":
    unittest.main()
