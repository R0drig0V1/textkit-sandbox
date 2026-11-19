<!-- Phase 3 of textkit: independent converters, one new module each. Each task is one pull
     request. Built for width: no task depends on another, so many can run at once. -->
# Phase 3: converters

Same rules as phase 1 (its "Rules for every task" section). Every task creates its own new
module `textkit/<module>.py` and its test file `tests/test_<module>.py`, adds its README row
and CHANGELOG line, and depends on nothing: all of them can start at once, alongside phases 1
and 2.

## Rules for phase 3 (in addition to phase 1's)

- **No CLI edits.** No phase-3 PR edits `textkit/__main__.py` or `tests/test_cli.py`: T2.6's
  generic rules (argument conversion for `int` parameters, exit 1 on `ValueError`, `KeyError`
  or `TypeError`) cover every phase-3 function. So every phase-3 function with one required
  parameter raises only `ValueError`, `KeyError` or `TypeError` for any `str` argument (any
  `int` for an `int` parameter), and its own test file calls it with `"a"` (or `1`). When
  `tests/test_cli.py` fails in a phase-3 PR, the PR fixes its function; only a failure that a
  stub function reproduces in `test_cli.py` is a T2.6 bug, reported to the integrator.
- **`int` parameters** reject a non-`int` and a `bool` with `ValueError`
  (`isinstance(n, bool) or not isinstance(n, int)`), checked before the range.
- **Docs**: no `docs/` page other than the task's ADR (the module docstring and the README row
  are the documentation). An ADR is cited only by its full stem or a link to
  `docs/decisions/NNNN-<slug>.md`, never as a bare "ADR NNNN": the integrator's merge script
  renumbers a colliding ADR to the next free number and rewrites stems, links, the heading and
  index rows, but not bare numbers elsewhere.
- **ADR case tables**: a task that writes an ADR ends it with a table of cases
  (input -> output) containing at least the rows listed in the task; its test file tests every
  row.
- **Python 3.9**, beyond phase 1's rule: no `itertools.pairwise`, `zip(..., strict=...)`,
  `int.bit_count` or `X | Y` in `isinstance`.
- **README conflicts**: when two PRs only add different rows to the README function table, the
  integrator may resolve it at merge as a union of rows in alphabetical order; the author
  still keeps rows alphabetical on rebase.

## Tasks

- [ ] **T3.1 `levenshtein`** in `textkit/distance.py`: `levenshtein(a, b) -> int`, the edit
      distance with insertions, deletions and substitutions of cost 1. `levenshtein("", "")`
      is 0; `levenshtein("kitten", "sitting")` is 3.
- [ ] **T3.2 `rot13`** in `textkit/ciphers.py`: `rot13(text) -> str`; ASCII letters rotate
      by 13 keeping their case, every other character is unchanged; `rot13(rot13(s)) == s`.
- [x] **T3.3 `to_roman`** in `textkit/roman.py`: `to_roman(n) -> str` for `1 <= n <= 3999`
      in standard subtractive form (`1994` -> `"MCMXCIV"`); any other `n`, or a non-`int`
      (a `bool` included), raises `ValueError`.
- [x] **T3.4 `number_to_words`** in `textkit/numwords.py` (not `numbers.py`: it would shadow
      the standard library's `numbers` whenever `textkit/` is on `sys.path`):
      `number_to_words(n) -> str` in English for `0 <= n <= 999`, lower case, hyphenated tens,
      no "and" (`0` -> `"zero"`, `13` -> `"thirteen"`, `20` -> `"twenty"`, `42` ->
      `"forty-two"`, `100` -> `"one hundred"`, `105` -> `"one hundred five"`, `110` ->
      `"one hundred ten"`, `999` -> `"nine hundred ninety-nine"`); outside the range, or a
      non-`int` (a `bool` included), raises `ValueError`.
- [x] **T3.5 `is_email`** in `textkit/emails.py`: `is_email(text) -> bool`. Write an ADR on
      what is accepted (one `@`, the local part and domain characters, dots, the length
      limits) and implement what it decides; no network and no DNS. Minimum case-table rows,
      written as Python literals: `"a@b.co"`, `"a.b@c.co"`, `".a@b.co"`, `"a..b@c.co"`,
      `"a@b"`, `"a@b.co."`, `'"a b"@c.co'` (a quoted local part), `"a@[1.2.3.4]"`,
      `"ü@b.co"`, `"a@b@c.co"`, `" a@b.co"`, `""`; both sides of each length limit:
      `"a"*64 + "@b.co"` and `"a"*65 + "@b.co"`, and a 254- and a 255-character address built
      only from labels of at most 63 characters (e.g. `"a@" + ".".join(["b"*63]*3) + "." + "c"*k`),
      the ADR stating the construction next to each row.
- [x] **T3.6 `pluralize`** in `textkit/plural.py`: `pluralize(word) -> str` for English
      nouns. Write an ADR on the rules it covers (`-s`, `-es`, consonant `-y` -> `-ies`, a
      short table of irregulars such as `child` -> `children`) and on case handling, and
      implement what it decides. Minimum case-table rows: `cat`, `bus`, `box`, `buzz`,
      `quiz`, `church`, `dish`, `city`, `day`, `potato`, `photo`, `knife`, `child`, `Child`,
      `CHILD`, `sheep`, `""`.
- [x] **T3.7 `soundex`** in `textkit/phonetic.py`: `soundex(name) -> str`, the American
      Soundex code. Rules: every character that is not an ASCII letter is removed first (it
      is transparent, not a separator); case is ignored; the first letter is kept,
      upper-cased; B F P V -> 1, C G J K Q S X Z -> 2, D T -> 3, L -> 4, M N -> 5, R -> 6;
      A E I O U Y H W are not coded. Letters with the same code that are adjacent, or
      separated only by H or W, are coded once, the first letter included; the same code
      separated by a vowel (A E I O U Y) is coded twice. Pad with `0` or cut to 4
      characters. A name with no ASCII letter raises `ValueError`. Tests: `Robert` R163,
      `Rupert` R163, `Tymczak` T522, `Ashcraft` A261, `Pfister` P236, `Honeyman` H555, `Lee`
      L000, `O'Brien` O165, `José` J200; `""`, `"123"`, `"é"` raise `ValueError`.
- [x] **T3.8 `initials`** in `textkit/names.py`: `initials(name) -> str`, `c.upper()` of the
      first letter of each space- or hyphen-separated part (it may be several characters), no separators
      (`"jean-luc picard"` -> `"JLP"`); `""` returns `""`. Split with
      `re.split(r"[ -]+", name)` (only spaces and hyphens; runs count as one; empty parts are
      ignored; tabs are not separators). Each part contributes `c.upper()` for its first
      character `c` with `c.isalpha()`; a part with no letter contributes nothing. Tests:
      `"  jean--luc  picard "` -> `"JLP"`, `"o'brien"` -> `"O"`, `"élodie durand"` -> `"ÉD"`,
      `"3d printer"` -> `"DP"`, `"- -"` -> `""`, `"ßa"` -> `"SS"`. No Unicode normalization:
      NFD input gives the bare base letter (NFD `"élodie"` -> `"E"`); test both forms.
- [x] **T3.9 `ordinal`** in `textkit/ordinals.py`: `ordinal(n) -> str` for `int` `n >= 0`
      (`0` -> `"0th"`, `1` -> `"1st"`, `2` -> `"2nd"`, `11` -> `"11th"`, `101` -> `"101st"`,
      `111` -> `"111th"`, `112` -> `"112th"`, `113` -> `"113th"`, `1011` -> `"1011th"`,
      `1021` -> `"1021st"`); a negative `n` or a non-`int` (a `bool` included) raises
      `ValueError`.
- [x] **T3.10 `human_bytes`** in `textkit/sizes.py`: `human_bytes(n) -> str` in binary units.
      The unit is the largest of B, KiB, MiB, GiB, TiB with `n >= 1024**k`, chosen before
      rounding. Below 1024 the result is `f"{n} B"`; from KiB up it is
      `f"{n / 1024**k:.1f} <unit>"`. A negative `n`, or a non-`int` (a `bool` included),
      raises `ValueError`. Tests: `0` -> `"0 B"`, `1` -> `"1 B"`, `1023` -> `"1023 B"`, `1024`
      -> `"1.0 KiB"`, `1280` -> `"1.2 KiB"`, `1536` -> `"1.5 KiB"`, `1048575` ->
      `"1024.0 KiB"`, `1048576` -> `"1.0 MiB"`, `1024**4` -> `"1.0 TiB"`, `1024**5` ->
      `"1024.0 TiB"`; `-1`, `1.5`, `True` raise. An `n` for which `n / 1024**k` overflows a float
      raises `ValueError` (catch `OverflowError`); test `10**400`.
- [x] **T3.11 `parse_duration`** in `textkit/durations.py`: `parse_duration(text) -> int`,
      seconds from `h`, `m` and `s` parts in that order, each optional but at least one
      (`"1h30m"` -> `5400`, `"45s"` -> `45`, `"2h5s"` -> `7205`). The whole text must match
      `re.fullmatch(r"(?:([0-9]+)h)?(?:([0-9]+)m)?(?:([0-9]+)s)?", text)` with at least one
      group present: ASCII digits only (not `\d` or `str.isdigit`, which accept non-ASCII
      digits), `fullmatch` (not `match` with `$`, which accepts a trailing newline), lower-case
      units only. Values are not range-limited and zero is allowed (`"90m"` -> 5400, `"0s"` ->
      0, `"01h"` -> 3600). Everything else raises `ValueError`; tests: `""`, `"1H"`,
      `"1h 30m"`, `" 45s"`, `"30m1h"`, `"1h1h"`, `"1.5h"`, `"-1h"`, `"45"`, `"45s\n"`,
      `"١h"`.
- [x] **T3.12 `render`** in `textkit/templates.py`:
      `render(template: str, values: Mapping[str, object]) -> str` (`typing.Mapping`).
      Scanning left to right, `{{` and `}}` are literal braces. A placeholder is `{` + a name
      matching `[A-Za-z_][A-Za-z0-9_]*` + `}` and is replaced with `str(values[name])`. Any
      other brace content (empty, digits, spaces, `.`, `[`, `!`, `:`) and any unmatched `{` or
      `}` raise `ValueError`. The whole template is validated before any lookup, so `{a.b}`
      raises `ValueError` even when `a` is missing. A missing name raises `KeyError(name)`.
      Values go through `str()` only; format specs are never applied (do not use
      `str.format` or `format_map`). Tests: `("{{x}}", {})` -> `"{x}"`,
      `("{{{x}}}", {"x": 1})` -> `"{1}"`; `ValueError` for `"{}"`, `"{0}"`, `"{ x }"`,
      `"{x:>5}"`, `"{x!r}"`, `"a } b"`, `"a { b"`, `"{a.b}"`, `"{a[0]}"`;
      `("{y}", {"x": 1})` -> `KeyError`.
