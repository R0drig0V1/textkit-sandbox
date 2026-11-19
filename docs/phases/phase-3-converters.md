<!-- Phase 3 of textkit: independent converters, one new module each. Each task is one pull
     request. Built for width: no task depends on another, so many can run at once. -->
# Phase 3: converters

Same rules as phase 1 (its "Rules for every task" section). Every task creates its own new
module `textkit/<module>.py` and its test file `tests/test_<module>.py`, adds its README row
and CHANGELOG line, and depends on nothing: all of them can start at once, alongside phases 1
and 2.

- [ ] **T3.1 `levenshtein`** in `textkit/distance.py`: `levenshtein(a, b) -> int`, the edit
      distance with insertions, deletions and substitutions of cost 1. `levenshtein("", "")`
      is 0; `levenshtein("kitten", "sitting")` is 3.
- [ ] **T3.2 `rot13`** in `textkit/ciphers.py`: `rot13(text) -> str`; ASCII letters rotate
      by 13 keeping their case, every other character is unchanged; `rot13(rot13(s)) == s`.
- [ ] **T3.3 `to_roman`** in `textkit/roman.py`: `to_roman(n) -> str` for `1 <= n <= 3999`
      in standard subtractive form (`1994` -> `"MCMXCIV"`); any other `n`, or a non-`int`
      (a `bool` included), raises `ValueError`.
- [ ] **T3.4 `number_to_words`** in `textkit/numbers.py`: `number_to_words(n) -> str` in
      English for `0 <= n <= 999`, lower case, hyphenated tens (`42` -> `"forty-two"`,
      `105` -> `"one hundred five"`, `0` -> `"zero"`); outside the range raises `ValueError`.
- [ ] **T3.5 `is_email`** in `textkit/emails.py`: `is_email(text) -> bool`. Write an ADR on
      what is accepted (one `@`, the local part and domain characters, dots, the length
      limits) and implement what it decides; no network and no DNS.
- [ ] **T3.6 `pluralize`** in `textkit/plural.py`: `pluralize(word) -> str` for English
      nouns. Write an ADR on the rules it covers (`-s`, `-es`, consonant `-y` -> `-ies`, a
      short table of irregulars such as `child` -> `children`) and on case handling, and
      implement what it decides.
- [ ] **T3.7 `soundex`** in `textkit/phonetic.py`: `soundex(name) -> str`, the American
      Soundex code (`"Robert"` -> `"R163"`, `"Tymczak"` -> `"T522"`); letters only, case
      ignored; a name with no ASCII letter raises `ValueError`.
- [ ] **T3.8 `initials`** in `textkit/names.py`: `initials(name) -> str`, the upper-case
      first letter of each space- or hyphen-separated part, no separators
      (`"jean-luc picard"` -> `"JLP"`); `""` returns `""`.
- [ ] **T3.9 `ordinal`** in `textkit/ordinals.py`: `ordinal(n) -> str` for `int` `n >= 0`
      (`1` -> `"1st"`, `2` -> `"2nd"`, `11` -> `"11th"`, `112` -> `"112th"`, `0` -> `"0th"`);
      a negative `n` or a non-`int` (a `bool` included) raises `ValueError`.
- [ ] **T3.10 `human_bytes`** in `textkit/sizes.py`: `human_bytes(n) -> str` in binary units
      with one decimal from KiB up (`0` -> `"0 B"`, `1023` -> `"1023 B"`, `1536` ->
      `"1.5 KiB"`, up to `TiB`); a negative `n` raises `ValueError`.
- [ ] **T3.11 `parse_duration`** in `textkit/durations.py`: `parse_duration(text) -> int`,
      seconds from `h`, `m` and `s` parts in that order, each optional but at least one
      (`"1h30m"` -> `5400`, `"45s"` -> `45`, `"2h5s"` -> `7205`); spaces and anything else
      raise `ValueError`.
- [ ] **T3.12 `render`** in `textkit/templates.py`: `render(template, values) -> str`
      replaces `{name}` placeholders with `str(values[name])`; `{{` and `}}` are literal
      braces; a missing name raises `KeyError`; no attribute or index access (`{a.b}` and
      `{a[0]}` raise `ValueError`).
