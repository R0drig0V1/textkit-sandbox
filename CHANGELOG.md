# Changelog

## Unreleased

- Added `slugify`: turns text into a lower-case ASCII slug.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `to_snake_case`: converts camelCase, PascalCase and kebab-case identifiers to snake_case ([ADR](docs/decisions/0002-snake-case-capital-runs.md)).
- Added `wrap`: splits text into lines of at most `width` characters at spaces; existing newlines are reflowed (ADR 0001).
