# Changelog

## 2026-08-14 19:01
- Switched the schedule from daily to weekly: the installer now asks for a day of the
  week and an `HH:MM` time, and writes a `Weekday` key into the launchd plist
- Day input accepts a name, a three-letter abbreviation, or a number (Sunday = 0)
- Renamed the job to `com.a11ytracker.weekly` and reinstalled it as Monday 09:00
- Fixed the installer's verification step: it waited on the log file, which already
  exists on a re-install, so it read the exit code before the run finished and reported
  "(never exited)". It now polls launchd until the job reports a numeric exit code.
- Files affected: `install.sh`, `uninstall.sh`, `README.md`, `PROJECT_OVERVIEW.md`

## 2026-08-14 18:58
- Made the tracker shareable: any repo owner can clone it and run `./install.sh`
- `--owner` now accepts a comma-separated list and defaults to the current `gh` login,
  so a zero-argument run works for whoever cloned the project
- Added `--labels` for custom label spellings and a `preflight()` check that exits with
  the exact fix command for missing gh, missing login, or missing openpyxl
- Added `install.sh` (prompts for username and hour, writes the launchd job, verifies
  with a live test run) and `uninstall.sh`
- `install.sh` refuses to install into `~/Documents`, `~/Desktop`, or `~/Downloads`
  because macOS TCC blocks background jobs there
- Added a Comments column to the Issues sheet
- Added `README.md`, `requirements.txt`, `.gitignore`; initialized a local git repo
- Renamed the launchd job to `com.a11ytracker.daily` and reinstalled it
- Tested against `mui` (20 repos, 679 items, 14s) and an invalid username
- Files affected: `track_a11y.py`, `run.sh`, `install.sh`, `uninstall.sh`, `README.md`,
  `PROJECT_OVERVIEW.md`, `requirements.txt`, `.gitignore`

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
