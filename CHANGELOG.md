# Changelog

## Unreleased

- Added `slugify`: turns text into a lower-case ASCII slug.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `truncate`: shortens text to a width, ending with a suffix when cut; raises `ValueError` when the width is smaller than the suffix.
- Added `wrap`: splits text into lines of at most `width` characters at spaces; existing newlines are reflowed (ADR 0001).
