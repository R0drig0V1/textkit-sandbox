# Changelog

## Unreleased

- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (`"Ñandú"` -> `"Nandu"`).
- Added `truncate`: cuts text to an exact width, suffix included; raises `ValueError` when the width is smaller than the suffix.
