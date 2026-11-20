"""Block structure of the Markdown subset: lines in, a list of blocks out (plan task T3.5).

This module knows nothing about inline syntax or HTML: the text a block holds (a heading's
title, a paragraph, a list item, a quoted paragraph) is kept raw, with its lines already
joined by one space, for ``textkit.markdown.inlines`` to parse. Code block lines are kept
exactly as written, minus their line endings.

The rules, decided in docs/decisions/0009-markdown-subset-raw-html-and-link-schemes.md:

- a line ends at ``"\\n"``, ``"\\r\\n"`` or a lone ``"\\r"``; the ending is dropped;
- a *blank* line is empty or holds spaces and tabs only;
- every block marker (``#``, ``-``, ``*``, digits, ``>``, three backticks, ``---``) must be
  at the start of the line: an indented marker is ordinary text;
- a heading, a list item, an opening fence, a quote line and ``---`` interrupt a
  paragraph; a blank line ends a list or a quote; any line that does not continue a list
  (an item of the same kind or a line indented by two spaces or more) ends it, and any line
  that does not start with ``>`` ends a quote.

Every name here is private to the package (phase 3 rule "Packages"): only
``textkit.markdown.__all__`` is public API.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

# Every line ending of the plan: "\r\n" is tried first so that it counts as one ending.
_LINE_END = re.compile(r"\r\n|\r|\n")
# "#" to "######" and one space; seven "#" do not match (the space must follow the sixth).
_HEADING = re.compile(r"(#{1,6}) (.*)")
_BULLET = re.compile(r"[-*] (.*)")
# ASCII digits only: "\d" would accept other scripts' digits as list numbers.
_ORDERED = re.compile(r"[0-9]+\. (.*)")
# An opening fence has no backtick after the first three, so "````" and "```a`b" are text.
_FENCE_OPEN = re.compile(r"```([^`]*)")
_FENCE_CLOSE = re.compile(r"```[ \t]*")
_RULE = re.compile(r"---[ \t]*")
# Spaces and tabs only: other whitespace ("\x0c", " ") is text in this subset.
_SPACE = " \t"


@dataclass(frozen=True)
class Heading:
    """An ATX heading: ``level`` from 1 to 6 and its raw inline ``text``."""

    level: int
    text: str


@dataclass(frozen=True)
class Paragraph:
    """A paragraph: its lines, stripped of spaces and tabs, joined by one space."""

    text: str


@dataclass(frozen=True)
class ListBlock:
    """A one-level list, ordered (``1.``) or not (``-``, ``*``); ``items`` holds raw text."""

    ordered: bool
    items: Tuple[str, ...]


@dataclass(frozen=True)
class CodeBlock:
    """A fenced code block: its ``language`` (``None`` when absent) and its raw ``lines``."""

    language: Optional[str]
    lines: Tuple[str, ...]


@dataclass(frozen=True)
class Quote:
    """A block quote; it holds paragraphs only, each as raw inline text."""

    paragraphs: Tuple[str, ...]


@dataclass(frozen=True)
class Rule:
    """A horizontal rule, ``---`` alone on a line."""


Block = Union[Heading, Paragraph, ListBlock, CodeBlock, Quote, Rule]


def split_lines(text: str) -> List[str]:
    """Split ``text`` into lines at ``"\\n"``, ``"\\r\\n"`` or a lone ``"\\r"``.

    The endings are dropped. A final line ending ends the last line rather than starting an
    empty one, so ``"a\\n"`` is ``["a"]`` (and an unclosed fence does not gain an empty last
    line); ``""`` is ``[]``.
    """
    lines = _LINE_END.split(text)
    if lines[-1] == "":
        lines.pop()
    return lines


def _is_blank(line: str) -> bool:
    return line.strip(_SPACE) == ""


def _interrupts_paragraph(line: str) -> bool:
    """Whether ``line`` starts a block that ends the paragraph before it."""
    return bool(
        _HEADING.fullmatch(line)
        or _BULLET.fullmatch(line)
        or _ORDERED.fullmatch(line)
        or _FENCE_OPEN.fullmatch(line)
        or line.startswith(">")
        or _RULE.fullmatch(line)
    )


def _join(parts: List[str]) -> str:
    # Empty parts (an item whose first line is "- ") would leave a stray space.
    return " ".join(part for part in parts if part)


def parse_blocks(text: str) -> List[Block]:
    """Group the lines of ``text`` into blocks, in order.

    See the module docstring for the rules. An unclosed fence runs to the end of the text.
    Never raises for any ``str``; ``""`` and blank text give ``[]``.
    """
    lines = split_lines(text)
    blocks: List[Block] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if _is_blank(line):
            i += 1
            continue

        fence = _FENCE_OPEN.fullmatch(line)
        if fence:
            # The language is the first word of the info string; the rest is ignored.
            info = fence.group(1).strip(_SPACE)
            language = re.split(r"[ \t]+", info)[0] if info else None
            body = []
            i += 1
            while i < n and not _FENCE_CLOSE.fullmatch(lines[i]):
                body.append(lines[i])
                i += 1
            i += 1  # the closing fence, or past the end when there is none
            blocks.append(CodeBlock(language, tuple(body)))
            continue

        heading = _HEADING.fullmatch(line)
        if heading:
            blocks.append(Heading(len(heading.group(1)), heading.group(2).strip(_SPACE)))
            i += 1
            continue

        if _RULE.fullmatch(line):
            blocks.append(Rule())
            i += 1
            continue

        if line.startswith(">"):
            # Only paragraphs: the text after ">" is never parsed as another block. A ">"
            # line with nothing after it separates two paragraphs of the same quote.
            paragraphs: List[str] = []
            current: List[str] = []
            while i < n and lines[i].startswith(">"):
                rest = lines[i][1:].strip(_SPACE)
                if rest:
                    current.append(rest)
                elif current:
                    paragraphs.append(_join(current))
                    current = []
                i += 1
            if current:
                paragraphs.append(_join(current))
            blocks.append(Quote(tuple(paragraphs)))
            continue

        ordered = _ORDERED.fullmatch(line)
        first = ordered or _BULLET.fullmatch(line)
        if first:
            is_ordered = ordered is not None
            # An item of the other kind ends the list: "1." after "-" starts a new one.
            item_marker = _ORDERED if is_ordered else _BULLET
            items = [[first.group(1).strip(_SPACE)]]
            i += 1
            while i < n and not _is_blank(lines[i]):
                line = lines[i]
                # Continuation first, so an indented "- x" belongs to the item (one level).
                if line.startswith("  "):
                    items[-1].append(line.strip(_SPACE))
                else:
                    item = item_marker.fullmatch(line)
                    if not item:
                        break
                    items.append([item.group(1).strip(_SPACE)])
                i += 1
            blocks.append(ListBlock(is_ordered, tuple(_join(parts) for parts in items)))
            continue

        parts = [line.strip(_SPACE)]
        i += 1
        while i < n and not _is_blank(lines[i]) and not _interrupts_paragraph(lines[i]):
            parts.append(lines[i].strip(_SPACE))
            i += 1
        blocks.append(Paragraph(_join(parts)))
    return blocks
