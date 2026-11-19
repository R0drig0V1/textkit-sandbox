<!-- ADR: which English plural rules pluralize covers and how it handles letter case. -->
# 0004. Rules and case handling of `pluralize`

## Context

`pluralize(word)` in `textkit/plural.py` (plan task T3.6) returns the plural of an English
noun. English plurals are not fully rule-based: `-o`, `-f` and `-z` nouns split into groups
that no spelling rule tells apart, and some nouns are irregular or invariable. Callers also
pass capitalized and upper-case words (`"Child"`, `"CHILD"`), and the CLI (T2.6) passes any
string, so the function needs a defined answer for every `str`.

## Decision

The input is one singular noun. It is not split into words, stripped or validated. The rules
are tried in this order and the first match wins; tables and endings are matched against the
lower-cased word.

1. **Empty**: `""` gives `""`.
2. **Unchanged**: `deer`, `fish`, `series`, `sheep`, `species` are returned exactly as typed.
3. **Irregular** (whole-word table): `child` -> `children`, `foot` -> `feet`, `goose` ->
   `geese`, `man` -> `men`, `mouse` -> `mice`, `ox` -> `oxen`, `person` -> `people`,
   `tooth` -> `teeth`, `woman` -> `women`.
4. **`-f`/`-fe` -> `-ves`**, listed nouns only: `calf`, `half`, `knife`, `leaf`, `life`,
   `loaf`, `self`, `shelf`, `thief`, `wife`, `wolf`. Other `-f` nouns (`roof`, `chief`)
   fall through to `-s`.
5. **`-z` doubling**, listed nouns only: `fez`, `quiz`, `whiz` take `-zes`. Other `-z`
   nouns (`buzz`, `waltz`) take `-es` by rule 7.
6. **`-o` -> `-oes`**, listed nouns only: `echo`, `hero`, `potato`, `tomato`, `torpedo`,
   `veto`. Every other `-o` noun (`photo`, `piano`) takes `-s` by rule 9, the more common
   case for modern words.
7. **Sibilants**: a word ending in `s`, `x`, `z`, `ch` or `sh` takes `-es` (`bus` ->
   `buses`, not `busses`).
8. **`-y`**: an ASCII consonant letter followed by `y` becomes `-ies` (`city` -> `cities`);
   a vowel (`a e i o u`) followed by `y` takes `-s` (`day` -> `days`). A non-ASCII letter
   before `y` is not a consonant for this rule, so `"ñy"` takes `-s` by rule 9.
9. **Default**: `-s`.

Words are compared to the lists exactly (after lower-casing), not by suffix, so compounds
(`pocketknife`, `superhero`) get the regular rules.

**Case handling.**

- Unchanged nouns keep the input as typed (`"SHEEP"` -> `"SHEEP"`).
- Irregular plurals come from a lower-case table and are re-cased: if `word.isupper()` the
  whole plural is upper-cased (`"CHILD"` -> `"CHILDREN"`); else if the first character is
  upper case it is capitalized (`"Child"` -> `"Children"`, also `"ChIlD"` -> `"Children"`);
  otherwise it is returned lower case.
- Rules 4 to 9 keep the stem exactly as typed and add the ending in upper case when
  `word.isupper()`, otherwise in lower case (`"BOX"` -> `"BOXES"`, `"Box"` -> `"Boxes"`,
  `"iPhone"` -> `"iPhones"`).

**Failure modes.** Every `str` gives a result; nothing raises for a string, which keeps the
T2.6 CLI rules trivially satisfied. A non-`str` raises `TypeError`.

## Consequences

- The function is predictable and small, but incomplete: nouns outside the lists get the
  regular rules (`cactus` -> `cactuses`, `criterion` -> `criterions`, `roof` -> `roofs`).
  Adding a noun is a one-line table change plus a row below.
- An already plural word is pluralized again (`"cats"` -> `"catses"`); detecting plurals is
  out of scope.
- Multi-word input is treated as one word: only its end matters for rules 7 to 9, and the
  tables never match (`"baby child"` -> `"baby childs"`).

## Cases

`tests/test_plural.py` tests every row.

| Input | Output | Rule |
|-------|--------|------|
| `"cat"` | `"cats"` | 9 |
| `"bus"` | `"buses"` | 7 |
| `"box"` | `"boxes"` | 7 |
| `"buzz"` | `"buzzes"` | 7 |
| `"quiz"` | `"quizzes"` | 5 |
| `"church"` | `"churches"` | 7 |
| `"dish"` | `"dishes"` | 7 |
| `"city"` | `"cities"` | 8 |
| `"day"` | `"days"` | 8 |
| `"potato"` | `"potatoes"` | 6 |
| `"photo"` | `"photos"` | 9 |
| `"knife"` | `"knives"` | 4 |
| `"leaf"` | `"leaves"` | 4 |
| `"roof"` | `"roofs"` | 9 |
| `"child"` | `"children"` | 3 |
| `"Child"` | `"Children"` | 3 |
| `"CHILD"` | `"CHILDREN"` | 3 |
| `"person"` | `"people"` | 3 |
| `"sheep"` | `"sheep"` | 2 |
| `"SHEEP"` | `"SHEEP"` | 2 |
| `"Box"` | `"Boxes"` | 7 |
| `"CITY"` | `"CITIES"` | 8 |
| `"Knife"` | `"Knives"` | 4 |
| `"iPhone"` | `"iPhones"` | 9 |
| `"ñy"` | `"ñys"` | 9 |
| `"y"` | `"ys"` | 9 |
| `"a"` | `"as"` | 9 |
| `""` | `""` | 1 |
