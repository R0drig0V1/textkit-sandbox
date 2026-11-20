"""Inline syntax of the Markdown subset: raw text in, a list of inline nodes out (T3.5).

The constructs are ``**strong**``, ``*em*``, code spans (`` `code` ``), links
(``[text](url)``) and a backslash before ``\\``, ``*``, `` ` ``, ``[`` or ``]``, which prints
that character as is. Anything unmatched is text. Nodes hold raw text: escaping for HTML
and checking link schemes is ``textkit.markdown.html``'s job.

How it parses: one pass from left to right, then one emphasis pass, also from left to right
(a simplified form of CommonMark's delimiter algorithm). Neither backtracks, and both take
time linear in the length of the text (up to a logarithmic factor for the ``_Index``
lookups), because ``to_html`` takes text from anyone:

1. A backslash escape is checked first, so ``\\*`` and ``\\``` are text, never markers. A
   backslash before any other character, or at the end, is a backslash.
2. A run of N backticks opens a code span that closes at the next run of exactly N
   backticks; the content is kept as is (a backslash in it is a backslash). With no such
   run, the backticks are text.
3. ``[`` starts a link when an unescaped ``]`` follows with no unescaped ``[`` before it
   (code spans are skipped while looking), then ``(`` right after it and a ``)`` later.
   The URL is everything up to the first ``)``, stripped of spaces and tabs; the link text
   is parsed on its own, so emphasis never crosses a link's edge. Otherwise ``[`` is text.
4. A run of ``*`` is a delimiter. It can open when the character after it is not
   whitespace, and close when the character before it is not whitespace (the start and
   the end of the text count as whitespace). The emphasis pass then takes each closer from
   left to right and pairs it with the nearest opener before it: when both runs have two
   or more ``*`` left the pair is strong, otherwise emphasis; what remains of the runs is
   paired again or printed as ``*``. Overlapping markers therefore nest by that rule, not
   by CommonMark's: ``**a *b** c*`` gives emphasis inside emphasis, never ``<strong>``.

Every name here is private to the package (phase 3 rule "Packages").
"""

import re
from bisect import bisect_left
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

# The characters a backslash escapes (the plan's list). Others keep their backslash.
ESCAPABLE = "\\*`[]"


@dataclass(frozen=True)
class Text:
    """Plain text, unescaped."""

    text: str


@dataclass(frozen=True)
class Code:
    """A code span's content, exactly as written between its backtick runs."""

    text: str


@dataclass(frozen=True)
class Emphasis:
    """``*children*``."""

    children: Tuple["Inline", ...]


@dataclass(frozen=True)
class Strong:
    """``**children**``."""

    children: Tuple["Inline", ...]


@dataclass(frozen=True)
class Link:
    """``[children](url)``; ``url`` is raw: the renderer decides whether it is safe."""

    children: Tuple["Inline", ...]
    url: str


Inline = Union[Text, Code, Emphasis, Strong, Link]


class _Delimiter:
    """A run of ``*`` while the emphasis pass runs; ``count`` shrinks as pairs use it."""

    def __init__(self, count: int, can_open: bool, can_close: bool) -> None:
        self.count = count
        self.can_open = can_open
        self.can_close = can_close


_Node = Union[Inline, _Delimiter]


def _run_length(text: str, start: int, char: str) -> int:
    end = start
    while end < len(text) and text[end] == char:
        end += 1
    return end - start


class _Index:
    """Where the backtick runs and the ``)`` of one text are, found once.

    Looking them up with ``bisect`` instead of rescanning the text keeps parsing linear (up
    to the logarithmic lookup): with a rescan, many unmatched backtick runs or many ``[x](`` with no ``)`` would
    make it quadratic in the length of the text, which ``to_html`` takes from anyone.
    """

    def __init__(self, text: str) -> None:
        self.text = text
        # Maximal runs only: a code span closes at a run of exactly its opener's length.
        self.runs: Dict[int, List[int]] = {}
        for match in re.finditer(r"`+", text):
            self.runs.setdefault(len(match.group()), []).append(match.start())
        self.parens = [i for i, char in enumerate(text) if char == ")"]

    def closing_backticks(self, start: int, length: int) -> int:
        """Index of the first run of exactly ``length`` backticks at or after ``start``, or -1.

        ``start`` is always just past a maximal run, so every run found is maximal too.
        """
        starts = self.runs.get(length, [])
        k = bisect_left(starts, start)
        return starts[k] if k < len(starts) else -1

    def closing_paren(self, start: int) -> int:
        """Index of the first ``)`` at or after ``start``, or -1."""
        k = bisect_left(self.parens, start)
        return self.parens[k] if k < len(self.parens) else -1


def _match_link(index: _Index, start: int) -> Optional[Tuple[str, str, int]]:
    """Match a link at ``text[start] == "["``: ``(label, url, end)`` or ``None``."""
    text = index.text
    i, n = start + 1, len(text)
    while i < n:
        char = text[i]
        if char == "\\" and i + 1 < n and text[i + 1] in ESCAPABLE:
            i += 2
        elif char == "`":
            run = _run_length(text, i, "`")
            close = index.closing_backticks(i + run, run)
            i = close + run if close != -1 else i + run
        elif char == "[":
            return None  # links do not nest: the outer "[" is text
        elif char == "]":
            break
        else:
            i += 1
    if i >= n or not text.startswith("(", i + 1):
        return None
    close = index.closing_paren(i + 2)
    if close == -1:
        return None
    return text[start + 1 : i], text[i + 2 : close].strip(" \t"), close + 1


def _tokenize(text: str) -> List[_Node]:
    """First pass: text, code spans, links and ``*`` delimiters, left to right."""
    index = _Index(text)
    nodes: List[_Node] = []
    buffer: List[str] = []

    def flush() -> None:
        if buffer:
            nodes.append(Text("".join(buffer)))
            buffer.clear()

    i, n = 0, len(text)
    while i < n:
        char = text[i]
        if char == "\\" and i + 1 < n and text[i + 1] in ESCAPABLE:
            buffer.append(text[i + 1])
            i += 2
        elif char == "`":
            run = _run_length(text, i, "`")
            close = index.closing_backticks(i + run, run)
            if close == -1:
                buffer.append("`" * run)
                i += run
            else:
                flush()
                nodes.append(Code(text[i + run : close]))
                i = close + run
        elif char == "[":
            link = _match_link(index, i)
            if link is None:
                buffer.append(char)
                i += 1
            else:
                label, url, i = link
                flush()
                nodes.append(Link(tuple(parse_inlines(label)), url))
        elif char == "*":
            run = _run_length(text, i, "*")
            before = text[i - 1] if i > 0 else " "
            after = text[i + run] if i + run < n else " "
            flush()
            nodes.append(_Delimiter(run, not after.isspace(), not before.isspace()))
            i += run
        else:
            buffer.append(char)
            i += 1
    flush()
    return nodes


def _merge_text(nodes: List[Inline]) -> List[Inline]:
    """Merge adjacent ``Text`` nodes and drop empty ones.

    The pieces of a run of text are joined once: adding them one by one would copy the
    growing string each time, which is quadratic on text such as ``"a* " * N``.
    """
    result: List[Inline] = []
    pieces: List[str] = []
    for node in nodes:
        if isinstance(node, Text):
            pieces.append(node.text)
            continue
        if pieces:
            joined = "".join(pieces)
            if joined:
                result.append(Text(joined))
            pieces = []
        result.append(node)
    joined = "".join(pieces)
    if joined:
        result.append(Text(joined))
    return result


class _Frame:
    """An opener still waiting for its closer, and the nodes that followed it so far."""

    def __init__(self, opener: _Delimiter) -> None:
        self.opener = opener
        self.children: List[Inline] = []


def _pair_emphasis(nodes: List[_Node]) -> List[Inline]:
    """Second pass: pair ``*`` delimiters into ``Strong`` and ``Emphasis``; return the nodes.

    One pass from left to right over a stack of frames, one per opener still unmatched,
    innermost last. The nearest opener before a closer is always the top frame (an opener
    after it would be above it), so pairing is O(1): the top frame's nodes become the
    children of the new node, which joins the frame below it, or stays in the same frame
    when the opener still has ``*`` left. Every node is moved once per pair that holds it,
    so the pass is linear in the number of nodes. A closer that finds no frame is text, or
    a new frame when it can also open; a delimiter that a pair encloses without matching it
    is already text in that pair, so nothing can pair across a pair's edge.
    """
    root: List[Inline] = []
    frames: List[_Frame] = []
    for node in nodes:
        target = frames[-1].children if frames else root
        if not isinstance(node, _Delimiter):
            target.append(node)
            continue
        if node.can_close:
            while node.count and frames:
                frame = frames[-1]
                opener = frame.opener
                use = 2 if opener.count >= 2 and node.count >= 2 else 1
                opener.count -= use
                node.count -= use
                children = tuple(_merge_text(frame.children))
                pair = Strong(children) if use == 2 else Emphasis(children)
                if opener.count:
                    # "*" left on the opener: the same closer pairs again ("***a***").
                    frame.children = [pair]
                else:
                    frames.pop()
                    (frames[-1].children if frames else root).append(pair)
        if node.count:
            if node.can_open:
                frames.append(_Frame(node))
            else:
                (frames[-1].children if frames else root).append(Text("*" * node.count))
    # Openers never closed are text. Each frame was opened after the content of the frame
    # below it, so writing them out bottom to top keeps the order (and stays linear).
    for frame in frames:
        root.append(Text("*" * frame.opener.count))
        root.extend(frame.children)
    return _merge_text(root)


def parse_inlines(text: str) -> List[Inline]:
    """Parse the raw inline ``text`` of a block into a list of inline nodes.

    See the module docstring for the rules. Adjacent text is merged into one ``Text`` node
    and ``""`` gives ``[]``. Never raises for any ``str``: an unmatched marker is text.
    Linear time in ``len(text)``, up to a logarithmic factor for the index lookups.
    """
    return _pair_emphasis(_tokenize(text))
