"""English noun plurals. The rules and the case handling are decided in
docs/decisions/0001-pluralize-rules.md; every public function is listed in the README's
function table."""

# All the tables are keyed by the lower-cased singular. They are deliberately short: a
# rule-based pluralizer cannot be complete, and the ADR names exactly what is covered.

# Nouns whose plural is the singular itself, returned exactly as typed.
_UNCHANGED = frozenset({"deer", "fish", "series", "sheep", "species"})

# Whole-word irregular plurals; the result is re-cased to follow the input (see _recase).
_IRREGULAR = {
    "child": "children",
    "foot": "feet",
    "goose": "geese",
    "man": "men",
    "mouse": "mice",
    "ox": "oxen",
    "person": "people",
    "tooth": "teeth",
    "woman": "women",
}

# Nouns ending in -f or -fe that take -ves. A list, not a rule: "roof", "chief" and
# "belief" end the same way and take a plain -s.
_F_TO_VES = frozenset(
    {"calf", "half", "knife", "leaf", "life", "loaf", "self", "shelf", "thief", "wife", "wolf"}
)

# Nouns ending in -o that take -es. A list, not a rule: most -o nouns ("photo", "piano",
# "radio") take a plain -s, and no spelling rule tells the two groups apart.
_O_TO_OES = frozenset({"echo", "hero", "potato", "tomato", "torpedo", "veto"})

# Nouns ending in a single -z that double it before -es ("quiz" -> "quizzes").
_Z_DOUBLING = frozenset({"fez", "quiz", "whiz"})

# Endings after which -es is added instead of -s.
_SIBILANT_ENDINGS = ("s", "x", "z", "ch", "sh")

_VOWELS = "aeiou"


def _recase(plural: str, word: str) -> str:
    """Give a table plural (lower case) the case pattern of the singular ``word``."""
    if word.isupper():
        return plural.upper()
    if word[0].isupper():
        return plural[0].upper() + plural[1:]
    return plural


def pluralize(word: str) -> str:
    """Return the English plural of the singular noun ``word``.

    Rules, first match wins (``docs/decisions/0001-pluralize-rules.md`` has the full list and
    a table of cases):

    1. ``""`` gives ``""``.
    2. Unchanged nouns (``sheep``, ``fish``, ...) are returned exactly as typed.
    3. Irregular nouns (``child`` -> ``children``, ...) are replaced from a table and
       re-cased like the input: ``"CHILD"`` -> ``"CHILDREN"``, ``"Child"`` -> ``"Children"``.
    4. Listed ``-f``/``-fe`` nouns take ``-ves`` (``knife`` -> ``knives``).
    5. Listed ``-z`` nouns double it before ``-es`` (``quiz`` -> ``quizzes``).
    6. Listed ``-o`` nouns take ``-es`` (``potato`` -> ``potatoes``); other ``-o`` nouns
       take ``-s`` (``photo`` -> ``photos``).
    7. Nouns ending in ``s``, ``x``, ``z``, ``ch`` or ``sh`` take ``-es``.
    8. A consonant followed by ``y`` becomes ``-ies`` (``city`` -> ``cities``); a vowel
       followed by ``y`` takes ``-s`` (``day`` -> ``days``).
    9. Everything else takes ``-s``.

    Tables and endings are matched case-insensitively. Rules 4 to 9 keep the typed stem and
    add the ending in upper case when ``word.isupper()``, else in lower case
    (``"BOX"`` -> ``"BOXES"``, ``"Box"`` -> ``"Boxes"``).

    ``word`` is taken to be one singular noun: it is not split, stripped or checked, so an
    already plural noun is pluralized again (``"cats"`` -> ``"catses"``). Any ``str`` gives
    a result; a non-``str`` raises ``TypeError``.
    """
    if not isinstance(word, str):
        raise TypeError(f"pluralize() expects a str, got {type(word).__name__}")
    if word == "":
        return ""
    lower = word.lower()
    if lower in _UNCHANGED:
        return word
    if lower in _IRREGULAR:
        return _recase(_IRREGULAR[lower], word)

    def ending(suffix: str) -> str:
        # The added letters follow the input only when it is shouted; a capitalized or
        # mixed-case word keeps its stem and gets a lower-case ending.
        return suffix.upper() if word.isupper() else suffix

    if lower in _F_TO_VES:
        stem = word[:-2] if lower.endswith("fe") else word[:-1]
        return stem + ending("ves")
    if lower in _Z_DOUBLING:
        return word + ending("zes")
    if lower in _O_TO_OES:
        return word + ending("es")
    if lower.endswith(_SIBILANT_ENDINGS):
        return word + ending("es")
    if len(lower) >= 2 and lower[-1] == "y" and lower[-2].isalpha() and lower[-2] not in _VOWELS:
        return word[:-1] + ending("ies")
    return word + ending("s")
