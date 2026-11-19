"""English noun plurals. Every public function is listed in the README's function table.

The rules ``pluralize`` covers (the ``-s``/``-es``/``-ies`` suffixes, the table of irregular
nouns) and how it handles letter case are decided in docs/decisions/0007-pluralize-rules.md,
which ends with the case table that ``tests/test_plural.py`` tests row by row.
"""

# Nouns whose plural no suffix rule produces, keyed by the lower-case singular. The ADR
# explains each group. Kept short on purpose: every entry is a promise, and a word missing
# from it still gets a regular plural instead of an error.
_IRREGULAR = {
    # Vowel change or old -en plurals.
    "child": "children",
    "foot": "feet",
    "goose": "geese",
    "man": "men",
    "mouse": "mice",
    "ox": "oxen",
    "person": "people",
    "tooth": "teeth",
    "woman": "women",
    # Same form in the singular and the plural.
    "deer": "deer",
    "fish": "fish",
    "moose": "moose",
    "series": "series",
    "sheep": "sheep",
    "species": "species",
    # -f / -fe -> -ves. Not a general rule: "roof", "chief" and "belief" take -s.
    "calf": "calves",
    "elf": "elves",
    "half": "halves",
    "knife": "knives",
    "leaf": "leaves",
    "life": "lives",
    "loaf": "loaves",
    "self": "selves",
    "shelf": "shelves",
    "thief": "thieves",
    "wife": "wives",
    "wolf": "wolves",
    # -o -> -oes. The default for -o is -s ("photo", "piano", "video"), so these are listed.
    "echo": "echoes",
    "hero": "heroes",
    "potato": "potatoes",
    "tomato": "tomatoes",
    "torpedo": "torpedoes",
    "veto": "vetoes",
    # A single final z after a vowel is doubled before -es.
    "fez": "fezzes",
    "quiz": "quizzes",
    "whiz": "whizzes",
}

# Endings (of the lower-cased word) that take -es: the plural adds a syllable after them.
_SIBILANT_ENDINGS = ("s", "x", "z", "ch", "sh")
_VOWELS = "aeiou"


def _common_prefix_length(a: str, b: str) -> int:
    """Return how many leading characters ``a`` and ``b`` share."""
    length = 0
    for x, y in zip(a, b):
        if x != y:
            break
        length += 1
    return length


def pluralize(word: str) -> str:
    """Return the English plural of the singular noun ``word``.

    The first rule that applies wins:

    1. ``""`` gives ``""``.
    2. A word in the irregular table, compared lower-cased as a whole, gets its listed
       plural: ``"child"`` -> ``"children"``, ``"knife"`` -> ``"knives"``, ``"potato"`` ->
       ``"potatoes"``, ``"quiz"`` -> ``"quizzes"``, ``"sheep"`` -> ``"sheep"``.
    3. A word ending in ``s``, ``x``, ``z``, ``ch`` or ``sh`` gets ``es``
       (``"bus"`` -> ``"buses"``, ``"church"`` -> ``"churches"``).
    4. A word ending in ``y`` after a letter that is not a vowel (``a e i o u``) ends in
       ``ies`` instead (``"city"`` -> ``"cities"``); after a vowel it gets ``s``
       (``"day"`` -> ``"days"``).
    5. Any other word gets ``s`` (``"cat"`` -> ``"cats"``, ``"photo"`` -> ``"photos"``).

    Case: the characters of ``word`` are kept as written. The added letters are upper case
    when ``word.isupper()`` and lower case otherwise (``"CITY"`` -> ``"CITIES"``,
    ``"City"`` -> ``"Cities"``). For an irregular word, the leading letters it shares with
    its plural are kept as written and the rest follows the same rule (``"Child"`` ->
    ``"Children"``, ``"CHILD"`` -> ``"CHILDREN"``, ``"Man"`` -> ``"Men"``).

    ``word`` is assumed to be one singular noun: an existing plural gets a second suffix
    (``"cats"`` -> ``"catses"``), and only the end of a phrase is looked at, so the irregular
    table never matches inside one (``"my child"`` -> ``"my childs"``). Never raises for a
    ``str`` argument; a non-``str`` raises ``TypeError``.
    """
    if not isinstance(word, str):
        raise TypeError(f"pluralize() expects a str, got {type(word).__name__}")
    if not word:
        return ""
    upper = word.isupper()
    lower = word.lower()

    plural = _IRREGULAR.get(lower)
    if plural is not None:
        # The key is ASCII, so ``lower`` has one character per character of ``word`` and
        # the shared prefix can be cut from ``word`` itself, keeping its case.
        keep = _common_prefix_length(lower, plural)
        rest = plural[keep:]
        return word[:keep] + (rest.upper() if upper else rest)

    if lower.endswith(_SIBILANT_ENDINGS):
        suffix, stem = "es", word
    elif (
        len(word) >= 2
        and word[-1] in "yY"
        and word[-2].isalpha()
        and word[-2].lower() not in _VOWELS
    ):
        suffix, stem = "ies", word[:-1]
    else:
        suffix, stem = "s", word
    return stem + (suffix.upper() if upper else suffix)
