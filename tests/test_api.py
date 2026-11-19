"""API contract test for textkit (plan task T2.5, docs/phases/phase-2-tools.md).

Every public function of every ``textkit`` module must have a docstring and type hints for
all its parameters and its return value, and the set of public functions must equal the
README function table. Nothing is hard-coded: modules are discovered with
``pkgutil.iter_modules(textkit.__path__)`` and functions with ``inspect.getmembers``, so a
correct function added by any later task passes without editing this file.

"Public function" is the definition in docs/phases/phase-1-core-helpers.md ("Rules for every
task"): a top-level ``def`` whose name does not start with ``_``, in a module of ``textkit/``
whose name does not start with ``_``. ``scripts/check.sh`` applies the same definition to the
source with ``ast``; this test applies it to the imported modules.

Hints are read with ``typing.get_type_hints``, which evaluates every annotation, so an
annotation that does not evaluate on the running Python (``str | None`` on 3.9, for example)
fails here instead of at the first caller that introspects it.
"""

import importlib
import inspect
import pathlib
import pkgutil
import re
import types
import typing
import unittest

import textkit

README = pathlib.Path(__file__).resolve().parents[1] / "README.md"

# A row of the README function table: | `name` | `textkit.module` | description |
_ROW = re.compile(r"^\| `(\w+)` \| `([\w.]+)` \|", re.M)


def public_modules() -> list[types.ModuleType]:
    """Import and return every module of ``textkit`` whose name does not start with ``_``."""
    return [
        importlib.import_module(f"{textkit.__name__}.{info.name}")
        for info in pkgutil.iter_modules(textkit.__path__)
        if not info.name.startswith("_")
    ]


def public_functions(module: types.ModuleType) -> dict[str, typing.Callable[..., object]]:
    """Return the public functions defined in ``module``, by name.

    Imported functions are excluded by ``f.__module__ == module.__name__`` (``counts``
    imports ``words`` from ``_tokens``). ``f.__name__ == name`` keeps only the name the
    ``def`` gave, so a module-level alias (``other = some_function``) is not counted twice:
    the definition is about ``def`` statements, as in ``scripts/check.sh``.
    """
    return {
        name: func
        for name, func in inspect.getmembers(module, inspect.isfunction)
        if not name.startswith("_")
        and func.__module__ == module.__name__
        and func.__name__ == name
    }


def contract_problems(func: typing.Callable[..., object]) -> list[str]:
    """Return what ``func`` lacks under the API contract; an empty list means it complies.

    Checked: a non-blank docstring, annotations that evaluate with ``typing.get_type_hints``,
    a hint for every parameter (``*args`` and ``**kwargs`` included) and a return hint
    (``-> None`` counts: ``get_type_hints`` maps it to ``NoneType``).
    """
    problems = []
    if not (func.__doc__ or "").strip():
        problems.append("no docstring")
    try:
        hints = typing.get_type_hints(func)
    except Exception as exc:  # NameError, TypeError, ...: whatever evaluation raises.
        problems.append(f"annotations do not evaluate: {type(exc).__name__}: {exc}")
        return problems
    for param in inspect.signature(func).parameters:
        if param not in hints:
            problems.append(f"no type hint for parameter {param!r}")
    if "return" not in hints:
        problems.append("no return type hint")
    return problems


def readme_rows() -> list[tuple[str, str]]:
    """Return the ``(function, module)`` rows of the README function table, in order.

    Only the "## Functions" section is read, so a table elsewhere in the README is ignored.
    """
    text = README.read_text(encoding="utf-8")
    match = re.search(r"^## Functions\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if match is None:
        raise AssertionError(f"no '## Functions' section in {README}")
    return _ROW.findall(match.group(1))


class ApiContractTest(unittest.TestCase):
    """The contract applied to the real package."""

    def setUp(self) -> None:
        self.functions = {
            (name, module.__name__): func
            for module in public_modules()
            for name, func in public_functions(module).items()
        }

    def test_discovers_functions(self) -> None:
        # Guards against discovery silently finding nothing, which would pass every check.
        self.assertTrue(self.functions, "no public function discovered in textkit")

    def test_every_public_function_has_docstring_and_type_hints(self) -> None:
        for (name, module), func in sorted(self.functions.items()):
            with self.subTest(function=f"{module}.{name}"):
                self.assertEqual(contract_problems(func), [])

    def test_discovered_set_equals_readme_table(self) -> None:
        rows = readme_rows()
        names = [name for name, _ in rows]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        self.assertEqual(duplicates, [], "functions listed more than once in the README")
        self.assertEqual(
            {name for name, _ in self.functions}, set(names),
            "README function table out of sync with the public functions",
        )

    def test_readme_module_column_matches(self) -> None:
        # Two functions of the same name in different modules would collide in the README
        # name column, so the pairs are compared too.
        self.assertEqual(set(self.functions), set(readme_rows()))


class ContractProblemsTest(unittest.TestCase):
    """The checker itself catches each gap, so a green ApiContractTest means something."""

    @staticmethod
    def _define(source: str) -> typing.Callable[..., object]:
        namespace: dict[str, object] = {"typing": typing}
        exec(source, namespace)  # noqa: S102 - fixed test sources, no user input.
        func = namespace["f"]
        assert callable(func)
        return func

    def test_compliant_function_has_no_problems(self) -> None:
        func = self._define(
            'def f(a: int, *args: str, b: "typing.Optional[str]" = None, **kw: int) -> None:\n'
            '    """Doc."""\n'
        )
        self.assertEqual(contract_problems(func), [])

    def test_missing_docstring(self) -> None:
        func = self._define("def f(a: int) -> int:\n    return a\n")
        self.assertEqual(contract_problems(func), ["no docstring"])

    def test_blank_docstring(self) -> None:
        func = self._define('def f(a: int) -> int:\n    """  """\n')
        self.assertEqual(contract_problems(func), ["no docstring"])

    def test_missing_parameter_hints(self) -> None:
        func = self._define('def f(a, *args, **kwargs) -> int:\n    """Doc."""\n')
        self.assertEqual(
            contract_problems(func),
            [
                "no type hint for parameter 'a'",
                "no type hint for parameter 'args'",
                "no type hint for parameter 'kwargs'",
            ],
        )

    def test_missing_return_hint(self) -> None:
        func = self._define('def f(a: int):\n    """Doc."""\n')
        self.assertEqual(contract_problems(func), ["no return type hint"])

    def test_annotation_that_does_not_evaluate(self) -> None:
        func = self._define('def f(a: "Undefined") -> int:\n    """Doc."""\n')
        problems = contract_problems(func)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("annotations do not evaluate: NameError"))

    def test_imported_and_private_functions_are_not_public(self) -> None:
        module = types.ModuleType("fake_module")
        exec(  # noqa: S102 - fixed test source.
            "from textkit.strings import slugify\n"
            "def _helper() -> None: pass\n"
            "def public() -> None: pass\n"
            "alias = public\n",
            module.__dict__,
        )
        self.assertEqual(sorted(public_functions(module)), ["public"])


if __name__ == "__main__":
    unittest.main()
