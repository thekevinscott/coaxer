# Changelog

## Unreleased

### Added
- Multi-field labeling TUI with cell cursor (spreadsheet-style editing)
- Pre-population: agents can fill first-pass labels, humans correct in TUI
- Unified `fields` array format with per-field `table`/`detail` visibility
- Searchable filter for label sets with >9 options
- Clickable URLs in table columns (OSC 8 hyperlinks)
- CJK-aware column truncation
- `Shift+U` to clear entire row
- curtaincall e2e tests (real PTY)
- Auto-release on push to main (patch-release workflow)
- PyPI publishing via trusted publishing
- Skillet evals for TUI label file generation (8 scenarios, 16 evals)
- pyskillet as dev dependency

### Fixed
- `DataTable.CursorMoved` -> `RowHighlighted` (Textual 8.x)
- `u` key now clears cell under cursor, not always first field
- Resume crash on non-dict/invalid JSON output files
- Duplicate force-include causing PyPI wheel rejection
- Surface SDK error messages (e.g. usage limits) instead of generic exit code 1

### Changed
- Promoted `tui.py` to `tui/` package with external `.tcss` stylesheet
- SKILL.md updated with comprehensive TUI documentation and unified format
- Old subprocess e2e tests replaced with curtaincall
