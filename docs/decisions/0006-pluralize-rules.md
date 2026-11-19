<!-- 0006-pluralize-rules: which English plural rules textkit.plural.pluralize covers, its irregular table and its case handling. -->
# 0006. Which plural rules `pluralize` covers, and how it handles case

## Context

`textkit.plural.pluralize(word)` (plan task T3.6) returns the plural of an English noun.
English plurals follow a few spelling rules (`-s`, `-es` after a hissing sound, `-y` ->
`-ies`) and many exceptions: vowel changes (`man` -> `men`), old `-en` plurals (`child` ->
`children`), unchanged plurals (`sheep`), `-f` -> `-ves` for some words only (`knife` ->
`knives` but `roof` -> `roofs`), `-o` -> `-oes` for some words only (`potato` -> `potatoes`
but `photo` -> `photos`). A complete answer needs a dictionary, which the standard-library-only
rule of `textkit` rules out, and inflection libraries that try still get many words wrong.
Readers will also ask what happens to `"Child"` and `"CHILD"`, to words that are already
plural, and to phrases. So the rules have to be few, ordered, and stated without reference
to the implementation. Every case below is a test.

## Decision

The first rule that applies wins.

1. **Empty.** `""` gives `""`.
2. **Irregular table.** The word, lower-cased with `str.lower()` and compared as a whole, is
   looked up in a fixed table, and a listed word gets its listed plural:
   - vowel change or `-en`: `child` -> `children`, `foot` -> `feet`, `goose` -> `geese`,
     `man` -> `men`, `mouse` -> `mice`, `ox` -> `oxen`, `person` -> `people`, `tooth` ->
     `teeth`, `woman` -> `women`;
   - unchanged: `deer`, `fish`, `moose`, `series`, `sheep`, `species`;
   - `-f`/`-fe` -> `-ves`: `calf`, `elf`, `half`, `knife`, `leaf`, `life`, `loaf`, `self`,
     `shelf`, `thief`, `wife`, `wolf`;
   - `-o` -> `-oes`: `echo`, `hero`, `potato`, `tomato`, `torpedo`, `veto`;
   - doubled `z`: `fez` -> `fezzes`, `quiz` -> `quizzes`, `whiz` -> `whizzes`.
3. **Sibilants.** A word whose lower-cased form ends in `s`, `x`, `z`, `ch` or `sh` gets
   `es`: `bus` -> `buses`, `box` -> `boxes`, `buzz` -> `buzzes`, `church` -> `churches`,
   `dish` -> `dishes`.
4. **Consonant + `y`.** A word of two or more characters ending in `y` or `Y` whose previous
   character is a letter (`str.isalpha()`) other than `a e i o u` (in either case) drops the
   `y` and gets `ies`: `city` -> `cities`. After a vowel, or when `y` is the whole word, the
   word falls through to rule 5: `day` -> `days`, `y` -> `ys`.
5. **Default.** Any other word gets `s`: `cat` -> `cats`, `photo` -> `photos`, `roof` ->
   `roofs`.

**Case.** The characters of the input are kept as written; only the added letters get a
case. They are upper case when `word.isupper()` is true (the word has a cased character and
no lower-case one) and lower case otherwise: `CITY` -> `CITIES`, `City` -> `Cities`, `iPhone`
-> `iPhones`. An irregular plural is built the same way: the leading characters the
lower-cased word shares with its listed plural are kept from the input, and the rest of the
plural is added with that case: `Child` -> `Child` + `ren`, `CHILD` -> `CHILD` + `REN`,
`Man` -> `M` + `en`, `Person` -> `Pe` + `ople`, `Sheep` -> `Sheep`. So the three casings the
plan asks about (`child`, `Child`, `CHILD`) need no separate rule, and a mixed-case input is
never rewritten.

**Input.** The argument is assumed to be one singular noun. Nothing is trimmed or
normalized. A non-`str` raises `TypeError`; no `str` raises, so the CLI of plan task T2.6
can call it with any text.

Why listed exceptions rather than more rules: `-f` -> `-ves`, `-o` -> `-oes` and the `z`
doubling each have about as many words that break them as words that follow them (`roof`,
`chief`, `belief`; `photo`, `piano`, `video`, `zoo`; `waltz`, `topaz`). As rules they would
turn a correct regular plural into a wrong one for every word they miss; as table entries a
missed word only falls back to the regular plural, which is right more often. Why the shared
prefix for case rather than "title-case the result when the input is title case": the prefix
keeps every input character as written, so it works for all-caps, capitalized and mixed-case
input with one rule, and agrees with the suffix rules, which also keep the input as written.

## Consequences

- Plurals not in the table come out regular and wrong: `stomach` -> `stomaches` (a `ch`
  said as `k`), `cactus` -> `cactuses` (no Latin plurals), `soliloquy` -> `soliloquys` (the
  `u` of `qu` counts as a vowel), `scarf` -> `scarfs`. Accepted. Adding a word is an
  additive change to this ADR's list, the table in `textkit/plural.py` and the tests.
- An already plural input gets a second suffix: `cats` -> `catses`. Telling singular from
  plural needs a dictionary.
- Only the end of a phrase is looked at, and the table matches the whole input, so
  `my child` -> `my childs` while `big box` -> `big boxes`. Compound nouns such as
  `mother-in-law` are out of scope.
- Proper nouns follow the rules: `Kennedy` -> `Kennedies`, not `Kennedys`.
- Whitespace and punctuation are kept as written and the suffix goes after them: `cat ` ->
  `cat s`. The caller trims.
- Non-ASCII words follow the same rules (`café` -> `cafés`): only the endings above and the
  vowels `a e i o u` are special, so an accented vowel before `y` counts as a consonant.
- Text with no cased character gets a lower-case suffix: `123` -> `123s`.

## Cases

Inputs and outputs are Python string literals. `tests/test_plural.py` tests every row and
checks that this table and its own case list stay identical.

| Input | Plural | Why |
|-------|--------|-----|
| `""` | `""` | rule 1: empty text |
| `"cat"` | `"cats"` | rule 5: the default `s` |
| `"bus"` | `"buses"` | rule 3: ends in `s` |
| `"box"` | `"boxes"` | rule 3: ends in `x` |
| `"buzz"` | `"buzzes"` | rule 3: ends in `z` |
| `"waltz"` | `"waltzes"` | rule 3: a `z` after a consonant is not doubled |
| `"quiz"` | `"quizzes"` | rule 2: doubled `z` |
| `"church"` | `"churches"` | rule 3: ends in `ch` |
| `"dish"` | `"dishes"` | rule 3: ends in `sh` |
| `"city"` | `"cities"` | rule 4: consonant + `y` |
| `"day"` | `"days"` | rule 5: vowel + `y` |
| `"toy"` | `"toys"` | rule 5: vowel + `y` |
| `"y"` | `"ys"` | rule 5: a lone `y` has no letter before it |
| `"potato"` | `"potatoes"` | rule 2: listed `-oes` plural |
| `"photo"` | `"photos"` | rule 5: `-o` takes `s` unless listed |
| `"knife"` | `"knives"` | rule 2: listed `-ves` plural |
| `"roof"` | `"roofs"` | rule 5: `-f` takes `s` unless listed |
| `"child"` | `"children"` | rule 2: `-en` plural |
| `"Child"` | `"Children"` | shared prefix kept as written, rest lower case |
| `"CHILD"` | `"CHILDREN"` | all caps: the added letters are upper case |
| `"Man"` | `"Men"` | only the shared prefix `M` is kept from the input |
| `"person"` | `"people"` | rule 2: a different word |
| `"mouse"` | `"mice"` | rule 2: vowel change |
| `"sheep"` | `"sheep"` | rule 2: unchanged plural |
| `"SHEEP"` | `"SHEEP"` | unchanged plural keeps its case |
| `"CITY"` | `"CITIES"` | all caps with rule 4 |
| `"City"` | `"Cities"` | capitalized input, lower-case suffix |
| `"BOX"` | `"BOXES"` | all caps with rule 3 |
| `"iPhone"` | `"iPhones"` | mixed case: input kept, lower-case suffix |
| `"a"` | `"as"` | any text gets a plural, no error |
| `"café"` | `"cafés"` | non-ASCII words follow the same rules |
| `"stomach"` | `"stomaches"` | known miss: `ch` said as `k` is not detected |
| `"cats"` | `"catses"` | the input is assumed singular |
| `"my child"` | `"my childs"` | the table matches the whole input only |
| `"123"` | `"123s"` | no cased character: lower-case suffix |
