"""Block structure of ``textkit.markdown``: lines in, a list of blocks out.

``split_lines(text)`` cuts the text into lines and ``parse_blocks(text)`` groups them into
blocks. The text of a block is kept raw (its inline Markdown is not parsed here; that is
``inlines.render_inlines``'s job), so this module knows nothing about HTML.

Lines end at ``"\\n"``, ``"\\r\\n"`` or a lone ``"\\r"``, and the ending is dropped. Block
markers are recognized only at the start of a line (an indented ``- x`` is text, not a list
item). "Blank" and "whitespace" below mean spaces and tabs only.

- **Heading**: ``#`` to ``######``, a space, the text (``Heading``).
- **Rule**: ``---`` alone on the line, trailing spaces allowed (``Rule``).
- **Fenced code**: a line starting with three backticks, then an optional language (the
  first word after them); the content runs to a line that is three backticks alone, or to
  the end of the text. Content lines are kept exactly (``CodeBlock``).
- **Quote**: consecutive lines starting with ``>``; the text after ``>`` is never parsed
  as another block. A ``>`` line with no text separates its paragraphs (``Quote``).
- **List**: consecutive items of one kind, unordered (``-`` or ``*`` and a space, the two
  markers mixing in one list) or ordered (digits, ``.`` and a space; the numbers are not
  checked). An item is its line plus the following lines indented by two spaces or more,
  joined by one space. A blank line, or any other line, ends the list (``ListBlock``).
- **Paragraph**: consecutive lines that start no other block, joined by one space. A
  heading, a rule, a fence, a quote or a list item interrupts it (``Paragraph``).

Every line of text that is joined (paragraphs, items, quote paragraphs) is stripped of
spaces and tabs at both ends first; the text inside a line is kept as is.
"""

import re
from dataclasses import dataclass
from typing import Optional, Union

# A line ending: "\r\n" first, so it is one ending and not two.
_LINE_END = re.compile(r"\r\n|\r|\n")
_HEADING = re.compile(r"(#{1,6}) (.*)")
_RULE = re.compile(r"---[ \t]*")
_FENCE = re.compile(r"```(.*)")
_CLOSING_FENCE = re.compile(r"```[ \t]*")
_UNORDERED_ITEM = re.compile(r"[-*] (.*)")
# ASCII digits only: "\d" would also take digits of other scripts ("٣. x").
_ORDERED_ITEM = re.compile(r"[0-9]+\. (.*)")
_BLANK = " \t"
# Lines indented this much continue the list item above them.
_CONTINUATION_INDENT = "  "


@dataclass(frozen=True)
class Heading:
    """``# text``: ``level`` from 1 to 6, ``text`` raw inline Markdown."""

    level: int
    text: str


@dataclass(frozen=True)
class Paragraph:
    """Consecutive lines of text, joined by one space."""

    text: str


@dataclass(frozen=True)
class ListBlock:
    """A one-level list: ``ordered`` for ``1.`` items, ``items`` the raw text of each."""

    ordered: bool
    items: tuple[str, ...]


@dataclass(frozen=True)
class CodeBlock:
    """A fenced code block: ``language`` (``None`` when absent) and the content lines."""

    language: Optional[str]
    lines: tuple[str, ...]


@dataclass(frozen=True)
class Quote:
    """A block quote: the raw text of each of its paragraphs (possibly none)."""

    paragraphs: tuple[str, ...]


@dataclass(frozen=True)
class Rule:
    """A horizontal rule, ``---``."""


Block = Union[Heading, Paragraph, ListBlock, CodeBlock, Quote, Rule]


def split_lines(text: str) -> list[str]:
    """Split ``text`` at ``"\\n"``, ``"\\r\\n"`` and lone ``"\\r"``, dropping the endings.

    A final line ending ends the last line rather than starting an empty one, so
    ``"a\\n"`` and ``"a"`` both give ``["a"]``; ``""`` gives ``[]``. Unlike
    ``str.splitlines``, nothing else (``"\\x0c"``, ``"\\x85"``, ``"\\u2028"``) ends a line.
    """
    if not text:
        return []
    lines = _LINE_END.split(text)
    if lines[-1] == "":
        lines.pop()
    return lines


def _is_blank(line: str) -> bool:
    return not line.strip(_BLANK)


def _join(parts: list[str]) -> str:
    """Strip each part and join the non-empty ones with one space."""
    return " ".join(stripped for stripped in (p.strip(_BLANK) for p in parts) if stripped)


def _list_item(line: str) -> Optional[tuple[bool, str]]:
    """``(ordered, text)`` if ``line`` is a list item, else ``None``."""
    match = _UNORDERED_ITEM.fullmatch(line)
    if match:
        return False, match.group(1)
    match = _ORDERED_ITEM.fullmatch(line)
    if match:
        return True, match.group(1)
    return None


def _starts_block(line: str) -> bool:
    """Whether ``line`` starts a block that interrupts a paragraph."""
    return bool(
        _HEADING.fullmatch(line)
        or _RULE.fullmatch(line)
        or _FENCE.fullmatch(line)
        or line.startswith(">")
        or _list_item(line)
    )


def _parse_fence(lines: list[str], i: int) -> tuple[CodeBlock, int]:
    info = lines[i][3:].strip(_BLANK)
    language = re.split(r"[ \t]", info, 1)[0] if info else None
    content = []
    i += 1
    while i < len(lines) and not _CLOSING_FENCE.fullmatch(lines[i]):
        content.append(lines[i])
        i += 1
    # Past the closing fence; an unclosed fence has consumed every line.
    return CodeBlock(language, tuple(content)), i + 1


def _parse_quote(lines: list[str], i: int) -> tuple[Quote, int]:
    paragraphs: list[str] = []
    current: list[str] = []
    while i < len(lines) and lines[i].startswith(">"):
        text = lines[i][1:]
        if _is_blank(text):
            if current:
                paragraphs.append(_join(current))
                current = []
        else:
            current.append(text)
        i += 1
    if current:
        paragraphs.append(_join(current))
    return Quote(tuple(paragraphs)), i


def _parse_list(lines: list[str], i: int, ordered: bool) -> tuple[ListBlock, int]:
    items: list[list[str]] = []
    while i < len(lines):
        line = lines[i]
        item = _list_item(line)
        if item is not None and item[0] == ordered:
            items.append([item[1]])
        elif items and line.startswith(_CONTINUATION_INDENT) and not _is_blank(line):
            items[-1].append(line)
        else:
            break
        i += 1
    return ListBlock(ordered, tuple(_join(parts) for parts in items)), i


def _parse_paragraph(lines: list[str], i: int) -> tuple[Paragraph, int]:
    parts = [lines[i]]
    i += 1
    while i < len(lines) and not _is_blank(lines[i]) and not _starts_block(lines[i]):
        parts.append(lines[i])
        i += 1
    return Paragraph(_join(parts)), i


def parse_blocks(text: str) -> list[Block]:
    """Parse ``text`` into its blocks, in order (see the module docstring for the rules).

    Blank lines separate blocks and produce none; ``""`` and blank text give ``[]``. Never
    raises for a ``str``: a line that matches no block marker is paragraph text.
    """
    lines = split_lines(text)
    blocks: list[Block] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        block: Block
        if _is_blank(line):
            i += 1
            continue
        heading = _HEADING.fullmatch(line)
        item = _list_item(line)
        if _FENCE.fullmatch(line):
            block, i = _parse_fence(lines, i)
        elif heading:
            block, i = Heading(len(heading.group(1)), heading.group(2).strip(_BLANK)), i + 1
        elif _RULE.fullmatch(line):
            block, i = Rule(), i + 1
        elif line.startswith(">"):
            block, i = _parse_quote(lines, i)
        elif item is not None:
            block, i = _parse_list(lines, i, ordered=item[0])
        else:
            block, i = _parse_paragraph(lines, i)
        blocks.append(block)
    return blocks
