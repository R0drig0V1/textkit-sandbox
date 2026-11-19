#!/usr/bin/env bash
# All the checks that define "green" for textkit: the unit tests, the README function table,
# the changelog and the ADR numbering. Usage: scripts/check.sh (exit 0 = green).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

python3 -m unittest discover -s tests -t . -q

python3 - <<'PY'
import ast, pathlib, re, sys
# Private modules (textkit/_tokens.py, ...) are not public API, whatever their names.
funcs = sorted(n.name for p in pathlib.Path("textkit").glob("*.py")
               if not p.name.startswith("_")
               for n in ast.parse(p.read_text()).body
               if isinstance(n, ast.FunctionDef) and not n.name.startswith("_"))
errors = []
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
