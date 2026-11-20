"""textkit.template: a small, safe text template engine (plan task T3.4).

``render(template, context)`` fills ``{{ name }}``, ``{% if %}``, ``{% for %}`` and
``{# comment #}`` tags from a dict; see ``docs/template.md`` for the syntax, the filters and
every error, and ADR 0007 for names missing from the context.

The package has three stages, one module each: ``lexer`` (text and tag tokens with their
positions), ``parser`` (a tree of nodes; every syntax error is raised here) and ``renderer``
(walks the tree with the context). ``filters`` holds the fixed filter table and
``exceptions`` the error classes.

``__all__`` lists functions only (phase 3 rule "Packages"): ``TemplateError`` and
``TemplateSyntaxError`` are importable from here but are not in it.
"""

from textkit.template.exceptions import TemplateError, TemplateSyntaxError
from textkit.template.renderer import render

__all__ = ["render"]
