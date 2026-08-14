# Changelog

## 2026-08-14 18:53
- Created the accessibility issue tracker: daily GitHub API poll to an Excel workbook
- Added `track_a11y.py` (searches 4 label spellings, audits all 42 repos, 3-sheet xlsx)
- Added `run.sh` launchd wrapper with an explicit PATH for Homebrew `gh` and `python3`
- Installed `com.kindcode.a11y-tracker` launchd agent, daily at 09:00 local
- Moved the project from `Documents/GIT/a11y-tracker` to `~/a11y-tracker` and symlinked
  it back: macOS TCC denies launchd agents access to `~/Documents` (job exited 127)
- Dropped the `--state all` flag from the gh search: gh only accepts `open|closed`, and
  omitting the flag returns both
- Files affected: `track_a11y.py`, `run.sh`, `PROJECT_OVERVIEW.md`,
  `~/Library/LaunchAgents/com.kindcode.a11y-tracker.plist`
