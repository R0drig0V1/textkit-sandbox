#!/usr/bin/env bash
# All the checks that define "green" for textkit: the unit tests, the README function table,
# the changelog and the ADR numbering. Usage: scripts/check.sh (exit 0 = green).
#
# The wait: before anything runs, the script sleeps TEXTKIT_CHECK_SECONDS (75 by default). It
# stands for the build and test suite of a real project, which take minutes where these take
# a second, so that every check holds one of the machine's heavy slots for a while and a red
# check costs the wait too. It is skipped in CI. Do not shorten or skip it in a task.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

if [[ -z "${CI:-}" ]]; then
    sleep "${TEXTKIT_CHECK_SECONDS:-75}"
fi

python3 -m unittest discover -s tests -t . -q

python3 - <<'PY'
import ast, pathlib, re, sys
# Public function: a top-level def not starting with "_", in a module not starting with "_"
# (phase 1 "Rules for every task"), so private modules such as _tokens.py are skipped.
funcs = [n.name for p in pathlib.Path("textkit").glob("*.py")
         if not p.name.startswith("_")
         for n in ast.parse(p.read_text()).body
         if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]
# A package (phase 3 "Rules added for phase 3"): the names in the literal __all__ of its
# __init__.py; a package without __all__ has no public functions.
errors = []
for init in sorted(pathlib.Path("textkit").glob("[!_]*/__init__.py")):
    for node in ast.parse(init.read_text()).body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "__all__"):
            try:
                funcs += [str(name) for name in ast.literal_eval(node.value)]
            except ValueError:
                errors.append(f"{init}: __all__ must be a literal list of strings")
funcs = sorted(funcs)
# Every public function is in the README table, once, and the table names nothing else.
rows = re.findall(r"^\| `(\w+)` \|", pathlib.Path("README.md").read_text(), re.M)
bad = sorted({f for f in funcs if rows.count(f) != 1} | {r for r in rows if r not in funcs})
if bad:
    errors.append(f"README function table out of sync: {bad}")
# Every public function is named in CHANGELOG.md.
changelog = pathlib.Path("CHANGELOG.md").read_text()
missing = [f for f in funcs if f"`{f}`" not in changelog]
if missing:
    errors.append(f"functions missing from CHANGELOG.md: {missing}")
# ADR numbers are unique and contiguous from 0001, and each is in the index.
d = pathlib.Path("docs/decisions")
nums = sorted(int(m.group(1)) for p in d.glob("*.md") if (m := re.match(r"(\d{4})-", p.name)))
if nums != list(range(1, len(nums) + 1)):
    errors.append(f"ADR numbers must be unique and contiguous from 0001: {nums}")
index = (d / "README.md").read_text()
gone = [n for n in nums if f"{n:04d}" not in index]
if gone:
    errors.append(f"ADRs missing from docs/decisions/README.md: {gone}")
if errors:
    sys.exit("\n".join(errors))
PY
echo "check: green"
