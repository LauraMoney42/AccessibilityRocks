# Changelog

## 2026-08-14 20:49
- Dates are now real Excel dates with a `yyyy-mm-dd` format instead of strings, so sorting
  by date is chronological. Counts are numbers and blanks are `None`.
- Added **Last activity** and **Idle (days)** so abandoned issues can be sorted to the top
- Every issue is now read and labeled, not just the vague ones: `refine_areas()` fetches
  all 405 bodies (cap 600, `--classify-cap`) in about 35 seconds
- Added **Also covers**: issues get every area they touch, not just one, since a modal
  dialog bug is both focus and screen reader work. 102 of 405 rows carry more than one.
- **By specialty** now splits primary from secondary counts so the index matches what
  filtering actually returns
- Fixed silently wrong classification: keyword matching was substring-based, so `form`
  fired on "information", "platform", and "performance". That put 87 unrelated issues in
  Forms & error messages. Matching is now anchored with `\b`, and Forms dropped from 124
  to 31 with the difference returning to General / unclassified.
- Files affected: `track_a11y.py`, `README.md`, `SKILL.md`, `PROJECT_OVERVIEW.md`

## 2026-08-14 20:39
- Added a specialty column and a **By specialty** index sheet, so a contributor can find
  the accessibility area they actually work in. Nine areas, ordered keyword matching,
  with an honest `General / unclassified` bucket for titles that place nowhere.
- Added a second search pass for accessibility work nobody labeled: six phrases matched
  against issue titles, excluding anything already carrying an accessibility label. The
  last run found 136, including Chart.js keyboard navigation and scikit-learn alt text.
- The untagged pass matches `in:title` only. Matching bodies returned Proton game
  compatibility reports and a Prettier tabs debate, because templates mention the words.
- Added `refine_areas()`: a capped second pass that reads issue bodies to place vague
  titles, moving 64 of 100 unclassified rows into a real specialty
- Dropped `bodyText` from the bulk GraphQL query. 100 nodes with bodies returns
  RESOURCE_LIMITS_EXCEEDED, and 50 nodes returns a 502: issue bodies are unbounded.
- Added a "Found via" column showing `labeled` or `text match: "<phrase>"`
- Added `--no-untagged` and `--no-deep-classify`
- Files affected: `track_a11y.py`, `README.md`, `SKILL.md`, `PROJECT_OVERVIEW.md`

## 2026-08-14 20:19
- Big tech is now a spreadsheet filter instead of a fetch-time decision. Column A tags
  every public row `independent` or `big company`; the file opens filtered to
  `independent` with those rows hidden and shaded grey, so including them is one click.
- `--include-big-tech` replaced by `--exclude-big-tech`, which keeps them out of the file
  entirely for anyone who never wants to see them
- The row budget counts independent rows only, so hidden rows do not eat the limit:
  a 250 request returned 250 independent plus 19 big company
- Both `row_dimensions.hidden` and an `auto_filter` criterion are set, since Excel honours
  the filter and other readers only honour hidden rows
- Files affected: `track_a11y.py`, `README.md`, `SKILL.md`, `PROJECT_OVERVIEW.md`

## 2026-08-14 19:48
- Public sheet now lists independent open source projects only. Four filters run by
  default: ~110 big-company owners excluded, a recognized open source license required,
  no archived repos or forks, and at most 3 issues per repo.
- Added `--include-big-tech`, `--exclude-owners`, `--any-license`, `--min-stars`,
  and `--per-repo`; `BIG_TECH_OWNERS` is an editable set at the top of the file
- Added a License column, and Run info now reports how many rows each filter removed
- Star lookups now fail soft: hitting the anonymous rate limit blanks the cell instead of
  killing the run. Found by exhausting the 60/hour anonymous budget during testing.
- Lowered the anonymous star lookup cap from 40 to 25 to leave headroom in that budget
- Filtered rows are replaced rather than subtracted, so a 300-row request still returns
  300 rows: currently 196 distinct projects, 45 tagged good first issue
- Files affected: `track_a11y.py`, `README.md`, `SKILL.md`, `PROJECT_OVERVIEW.md`

## 2026-08-14 19:28
- Sign-in is no longer required. Rewrote the transport layer onto urllib against the
  GitHub REST and GraphQL APIs, with `gh` demoted to one of three optional token sources
  (`GH_TOKEN`, `GITHUB_TOKEN`, `gh auth token`, or nothing at all).
- Added an "All public repos" sheet: open accessibility issues across GitHub, ranked by
  repo stars, with language, comment count, and a good-first-issue column
- Renamed the personal sheets to "My repos" and "My repo rollup", added stars to the rollup
- Added `SKILL.md` so the repo can be cloned into `~/.claude/skills/` and driven by an
  AI assistant with no setup
- Collapsed the four per-label searches into one query using GitHub's comma-OR label
  syntax
- `install.sh` now treats signing in as optional and defaults to no
- Popularity is measured in stars, since GitHub exposes no download count for repos, and
  the Run info sheet states that plus the public-sample rule
- Tested both paths: signed in (42 repos, private included) and fully anonymous with gh
  removed from PATH (29 public repos, stars capped at 40 with a note in the sheet)
- Files affected: `track_a11y.py`, `install.sh`, `SKILL.md`, `README.md`,
  `PROJECT_OVERVIEW.md`

## 2026-08-14 19:07
- Browser sign-in: when no GitHub session exists, the installer and the script now offer
  to open github.com through `gh auth login --web` instead of printing a command to run
- One-time code is copied to the clipboard on macOS via `--clipboard`
- Sign-in is gated on `sys.stdin.isatty()`, so the weekly launchd job logs
  "GitHub sign-in has expired" and exits rather than hanging on a prompt no one can see
- Added a heads-up line about gh's own two setup questions before handing off
- Tested with a sandboxed `GH_CONFIG_DIR` and a real pty: decline path, non-tty path, and
  the handoff to gh (killed before the browser opened). Real credentials untouched.
- Files affected: `track_a11y.py`, `install.sh`, `README.md`, `PROJECT_OVERVIEW.md`

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
