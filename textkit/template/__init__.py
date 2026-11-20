"""Template engine of textkit (plan task T3.4): ``render(template, context) -> str``.

The package is split by stage: ``lexer`` finds the tags, ``parser`` builds a tree and finds
every syntax error, ``renderer`` fills the tree with the context, and ``filters`` holds the
fixed filter table. The syntax, the filters and the errors are documented in
``docs/template.md``; what a name missing from the context does is decided in the ADR
"template missing names" (docs/decisions/*-template-missing-names.md).

``__all__`` lists the public functions only (phase 3 rule "Packages"); the exception
classes are importable from here (``from textkit.template import TemplateSyntaxError``)
but are not in it.
"""

from textkit.template.errors import TemplateError, TemplateSyntaxError
from textkit.template.renderer import render

__all__ = ["render"]
