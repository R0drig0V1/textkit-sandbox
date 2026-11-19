<!-- ADR 0004: the sentence rule behind sentence_count (T2.2): terminators, abbreviations, ellipses. -->
# 0004. Where a sentence ends

Status: accepted (plan task T2.2).

## Context

`sentence_count(text)` (T2.2) needs a definition of "sentence end". Splitting at every `.`,
`!` and `?` is wrong for ordinary prose: abbreviations (`"Dr. Smith"`, `"e.g. this"`),
ellipses (`"Wait... what?"`), stacked terminators (`"Really?!"`), decimals (`"3.14"`) and
quotes after the full stop (`'He said "Hi." Then'`) all break it. A full solution needs a
language model or per-language abbreviation lists; this package is standard library only,
so the rule has to be small, predictable and documented, with its limits written down.

## Decision

The text is first split into **paragraphs** at a blank line (a line break, any whitespace,
another line break) or at U+2029 PARAGRAPH SEPARATOR. A paragraph end always ends a
sentence. A single line break does not: hard-wrapped prose is one sentence across lines.

Inside a paragraph, a **candidate end** is a maximal run of one or more **terminators**,
followed by any number of **closers**:

| Kind | Characters |
|------|------------|
| terminator | `.` `!` `?`, `…` U+2026, `‼` U+203C, `‽` U+203D, `⁇` U+2047, `⁈` U+2048, `⁉` U+2049, `؟` U+061F (Arabic), `।` U+0964 and `॥` U+0965 (Devanagari danda), `。` U+3002, `！` U+FF01, `？` U+FF1F (CJK) |
| closer | `"` `'` `)` `]` `}`, `»` `›` `”` `’`, `」` `』` `】` `）` |

A candidate end is a **sentence end** unless one of these holds, checked in order:

1. **Something other than whitespace follows it** (whitespace is `str.isspace()`), and the
   run has no CJK terminator (`。！？`). This keeps decimals, versions and addresses whole
   (`"3.14"`, `"v1.2.3"`, `"example.com"`, `"wait...what"`). CJK terminators are exempt
   because Chinese and Japanese put no space between sentences.
2. **The run is a single `.` right after a known abbreviation.** The abbreviation is the
   run of non-whitespace before the `.`, without leading punctuation (`"(e.g"` is `e.g`),
   compared in lower case against: `mr`, `mrs`, `ms`, `dr`, `prof` (titles, always followed
   by a name) and `e.g`, `i.e`, `cf`, `vs` (which introduce what follows).
3. **The next letter or digit after it is lower case** (`str.islower()`). The sentence goes
   on: `"Wait... what?"`, `'"Stop!" she said.'`, `"pens, etc. and paper"`.

A **sentence** is the text between two consecutive sentence ends (or a paragraph start or
end). It counts only if it contains a letter or digit, which is where a word of ADR 0001
can start, so runs of punctuation alone are not sentences. Text after the last terminator
is a sentence like any other. `sentence_count(text)` is how many sentences there are; it
raises `TypeError` for anything that is not a `str`.

What this means for the cases the plan asks about:

- **Abbreviations.** Only the nine listed above never end a sentence. Any other
  abbreviation ends one when an upper-case word follows (`"etc. Then"` is two sentences)
  and does not when a lower-case word follows (`"etc. and"`). `etc` is deliberately not in
  the list because it often ends a sentence; the titles are, because they never do.
- **Ellipses.** `...`, `..` and `…` are terminator runs like `.`: they end the sentence
  when an upper-case word follows (`"I wonder... Maybe."` is two) and not when a
  lower-case one does (`"Wait... what?"` is one). With no space after, they do not end it.
- **`?!` and other stacks.** A run of terminators is one candidate, so `"?!"`, `"!!!"`,
  `"?!?"` and `"!.."` end one sentence.
- **Decimals.** A `.` between digits has no whitespace after it, so `"3.14"` and
  `"$5.50"` never end a sentence; `"Pi is 3.14. Next"` ends one after `"3.14."`.
- **Quotes and brackets after the terminator** belong to the sentence they close:
  `'He said "Hi." Then'` is `'He said "Hi."'` and `"Then"`. A quote or bracket before the
  terminator needs no rule (`'"Hi". Then'` ends at `.` as usual).
- **No final terminator.** The rest of the text is still a sentence: `"Hello world"` is 1.
  A line break alone does not end it; a blank line does (`"Title\n\nBody."` is 2).
- **Empty or whitespace-only text** is 0, and so is text with no letter or digit
  (`"...!?"`).
- **Non-ASCII terminators** are supported as listed in the table. Inverted `¿` and `¡`
  are ordinary punctuation, and the Greek question mark `;` (U+037E) is not a terminator.

### Examples

Each row is checked by `tests/test_counts.py`, which reads this table: the first column is
a Python string literal, the second the list of sentences (as the private `_sentences`
returns them, stripped of surrounding whitespace), the third the count.

| Text | Sentences | Count | Why |
|------|-----------|-------|-----|
| `""` | `[]` | 0 | empty |
| `" \t\n "` | `[]` | 0 | whitespace only |
| `"...!?"` | `[]` | 0 | no letter or digit |
| `"Hello world"` | `["Hello world"]` | 1 | no final terminator |
| `"Hello world."` | `["Hello world."]` | 1 | one terminator |
| `"One. Two! Three?"` | `["One.", "Two!", "Three?"]` | 3 | the three ASCII terminators |
| `"First. Second"` | `["First.", "Second"]` | 2 | text after the last terminator |
| `"Hard-wrapped\nline. Next"` | `["Hard-wrapped\nline.", "Next"]` | 2 | a single line break does not end a sentence |
| `"Title\n\nBody text."` | `["Title", "Body text."]` | 2 | a blank line does |
| `"One\r\n \r\nTwo"` | `["One", "Two"]` | 2 | blank line with CRLF and spaces |
| `"One Two"` | `["One", "Two"]` | 2 | paragraph separator |
| `"!!! Hi."` | `["Hi."]` | 1 | a piece without letters is not a sentence |
| `"Hi. ..."` | `["Hi."]` | 1 | trailing dots alone are not a sentence |
| `"Really?! Yes."` | `["Really?!", "Yes."]` | 2 | `?!` is one end |
| `"What?!? No!!! Fine.."` | `["What?!?", "No!!!", "Fine.."]` | 3 | any stack is one end |
| `"Really‽ Yes‼ OK⁉"` | `["Really‽", "Yes‼", "OK⁉"]` | 3 | Unicode stacked marks |
| `"Dr. Smith arrived."` | `["Dr. Smith arrived."]` | 1 | title abbreviation |
| `"Mr. and Mrs. Smith left. They waved."` | `["Mr. and Mrs. Smith left.", "They waved."]` | 2 | titles, then a real end |
| `"Ask PROF. Lee."` | `["Ask PROF. Lee."]` | 1 | abbreviations match in any case |
| `"Use a tool (e.g. Pliers)."` | `["Use a tool (e.g. Pliers)."]` | 1 | `e.g` after a bracket |
| `"Cats, i.e. Felines, purr."` | `["Cats, i.e. Felines, purr."]` | 1 | `i.e` |
| `"See cf. Smith. Then go."` | `["See cf. Smith.", "Then go."]` | 2 | `cf` |
| `"Cats vs. Dogs is old."` | `["Cats vs. Dogs is old."]` | 1 | `vs` |
| `"Pens, paper, etc. Then sit."` | `["Pens, paper, etc.", "Then sit."]` | 2 | `etc` is not in the list |
| `"Pens, etc. and paper."` | `["Pens, etc. and paper."]` | 1 | lower case follows |
| `"Wait... what?"` | `["Wait... what?"]` | 1 | ellipsis, lower case follows |
| `"Wait… what?"` | `["Wait… what?"]` | 1 | U+2026, lower case follows |
| `"I wonder... Maybe not."` | `["I wonder...", "Maybe not."]` | 2 | ellipsis, upper case follows |
| `"wait...what"` | `["wait...what"]` | 1 | no space after the ellipsis |
| `"To be continued..."` | `["To be continued..."]` | 1 | ellipsis at the end |
| `"...and then it rained."` | `["...and then it rained."]` | 1 | leading ellipsis |
| `"Pi is 3.14. It is irrational."` | `["Pi is 3.14.", "It is irrational."]` | 2 | decimal, then a real end |
| `"It costs $5.50 today."` | `["It costs $5.50 today."]` | 1 | decimal |
| `"Version 1.2.3 is out."` | `["Version 1.2.3 is out."]` | 1 | version number |
| `"Mail me@example.com now."` | `["Mail me@example.com now."]` | 1 | address |
| `"See item 5. 6 apples left."` | `["See item 5.", "6 apples left."]` | 2 | a digit is not lower case |
| `'He said "Hi." Then he left.'` | `['He said "Hi."', 'Then he left.']` | 2 | closing quote after the terminator |
| `'He said "Hi". Then he left.'` | `['He said "Hi".', 'Then he left.']` | 2 | quote before the terminator |
| `'"Stop!" she said.'` | `['"Stop!" she said.']` | 1 | lower case after the quote |
| `"(See above.) Then go."` | `["(See above.)", "Then go."]` | 2 | closing bracket |
| `"Il a dit « Oui. » Puis"` | `["Il a dit « Oui.", "» Puis"]` | 2 | spaced French closer goes to the next sentence (known limit) |
| `"He said “Yes.” Then"` | `["He said “Yes.”", "Then"]` | 2 | typographic quote |
| `"Hello. world"` | `["Hello. world"]` | 1 | lower-case start joins (known limit) |
| `"I saw the Dr. Then I left."` | `["I saw the Dr. Then I left."]` | 1 | title at a real end (known limit) |
| `"The U.S. Army won."` | `["The U.S.", "Army won."]` | 2 | unlisted abbreviation (known limit) |
| `"¿Qué tal? Bien."` | `["¿Qué tal?", "Bien."]` | 2 | Spanish |
| `"Привет. Как дела?"` | `["Привет.", "Как дела?"]` | 2 | Cyrillic |
| `"你好。世界。"` | `["你好。", "世界。"]` | 2 | CJK full stop, no space needed |
| `"これはペンです！本当？"` | `["これはペンです！", "本当？"]` | 2 | full-width `！` and `？` |
| `"كيف حالك؟ أنا بخير."` | `["كيف حالك؟", "أنا بخير."]` | 2 | Arabic question mark |
| `"यह एक वाक्य है। यह दूसरा है।"` | `["यह एक वाक्य है।", "यह दूसरा है।"]` | 2 | Devanagari danda |
| `"3.14"` | `["3.14"]` | 1 | a number alone is a sentence |

## Consequences

- `sentence_count` gives the expected count for ordinary English prose, including
  abbreviations of names and Latin, ellipses, decimals and quoted speech, and for the
  scripts whose terminators are listed above.
- The rule is local: each candidate end looks only at the characters around it, so the
  function is linear in the length of the text and easy to predict from this page.
- Known limits, accepted for now: a sentence that starts with a lower-case letter is
  joined to the previous one (`"Hello. world"`); a listed title at a real sentence end
  does not end it (`"I saw the Dr. Then"`); unlisted abbreviations followed by a capital
  split (`"U.S. Army"`, `"Fig. 3"`, `"No. 5"`); initials split (`"J. R. R. Tolkien"`); a
  closer separated from the terminator by a space (French `"« Oui. »"`) starts the next
  sentence; an ASCII `?` or `.` between CJK characters with no space does
  not end a sentence; a single line break never ends one, so a list of unterminated lines
  is one sentence. Changing any of these changes `sentence_count` and needs a new ADR.
