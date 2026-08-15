# Changelog

## 2026-08-14 21:41
- Reworked the scoreboard ranking after the top of the board turned out to be one
  account's two small repos (1 and 22 stars) with a crowd merging into them:
  - counts distinct **owners**, not repos. Splitting a backlog across two repos under one
    account was the loophole that produced the bogus number one.
  - caps each owner at 3 fixes toward the score, so breadth beats volume
  - ignores repos under 50 stars, added as `--scoreboard-min-stars`
- The board is now Orange-OpenSource, indico, WebKit, headlamp, scaleway, mozilla, SAP.
  Total counted fixes dropped from 246 to 81, which is the point: the missing 165 were
  farming.
- The star floor needs a token, since it costs a star lookup per repo. Without one the
  other two rules still apply and the run says the floor was skipped.
- Dashboard and CONTRIBUTORS.md now show orgs rather than repo counts, and both state the
  three rules
- Files affected: `track_a11y.py`, `docs/index.html`, `CONTRIBUTORS.md`, `README.md`

## 2026-08-14 21:45
- Removed the "On the wall? Bring someone with you" panel: markup, verification state,
  milestone chips, and the stored username. The contributors wall link moved onto the
  scoreboard so nothing was lost with it.
- Replaced it with a single **Make a Post** button under the scoreboard. It reveals one
  username field, checks GitHub for merged accessibility fixes, and drafts the post from
  real counts. Zero merged fixes means no post, since the text quotes numbers.
- Post wording trimmed to the four paragraphs and the link, with the Pull Shark line and
  the sign-off dropped
- Files affected: `docs/index.html`, `README.md`

## 2026-08-14 21:35
- Removed the "I'm on it" shortlist entirely: buttons, panel, localStorage, and the
  toggle code. It was a bookmark that looked like a claim, and recognition now comes from
  merged work instead.
- Added the contributors wall: `--contributors CONTRIBUTORS.md` writes a markdown table of
  everyone who merged an accessibility fix in the window (40 people, 246 fixes), with a
  "how to get on this list" section. The weekly workflow regenerates and commits it.
- Rewrote the LinkedIn draft as an invitation. It opens with "Contribute to
  AccessibilityRocks with me", names the person's real merged fixes and projects, links
  the issue list, mentions Pull Shark and the wall, and closes with "Who is in?"
- Post writer moved directly under the scoreboard and links to the wall
- Fixed hashtags being duplicated in the draft, and a draft written from a local copy
  linking to localhost instead of the live site
- Files affected: `track_a11y.py`, `docs/index.html`, `.github/workflows/refresh.yml`,
  `CONTRIBUTORS.md`, `README.md`, `SKILL.md`

## 2026-08-14 21:35
- The LinkedIn post writer now unlocks only for people on the scoreboard. Entering a
  GitHub username queries the API for merged accessibility PRs, so recognition follows a
  merge rather than a click. Milestone chips now count merged fixes.
- Verified against a real contributor (10 merged fixes, rank 6 on the board) and against
  an account with none, which stays locked
- Handled GitHub's 422 for unknown usernames separately: it is a spelling problem, not an
  outage, and the generic error message said the wrong thing
- Split the panels: "Your shortlist" states plainly that picks are a private bookmark
  which does not comment on the issue or tell the maintainer anything
- Scoreboard trimmed to a compact top ten. A side-scrolling version was built and dropped:
  it would need `tabindex="0"` and an accessible name to stay keyboard-scrollable, and ten
  rows fit in less space than the scroller did.
- Files affected: `docs/index.html`, `README.md`

## 2026-08-14 21:20
- Audited the dashboard's own accessibility and fixed everything found:
  - Added `main` landmark, a skip link, and a focusable results target
  - Added `aria-pressed` to the 300 pick buttons so toggle state is announced
  - Added live regions for the result count and list changes
  - Added a 3px `:focus-visible` ring, verified with a real keyboard tab
  - Added `role="list"` where `list-style: none` strips list semantics in VoiceOver
- Fixed two real contrast failures: control borders were 1.2:1 against the page, failing
  WCAG 1.4.11 because inputs share the page background and the border is the only
  boundary; and milestone chips used `opacity: .38`, dropping text below 4.5:1
- Results now page at 100 with a "Show more" button that moves focus to the first new
  card, cutting roughly 900 tab stops to about 300
- Known gap, stated in the README: no real screen reader test yet
- Files affected: `docs/index.html`, `README.md`

## 2026-08-14 21:09
- Published to https://github.com/LauraMoney42/AccessibilityRocks with Pages serving
  /docs, live at https://lauramoney42.github.io/AccessibilityRocks/
- Added a scoreboard of people who merged accessibility fixes in the last 90 days, built
  from merged PRs carrying an accessibility label. Verifiable, unlike self-reported counts.
- Scoring caps each project at five fixes. Raw counts let one repo's backlog own the board
  (one contributor had 25 fixes in a single project); pure breadth let two drive-by fixes
  outrank twenty-five real ones. Self-owned repos are excluded.
- Added three shields.io endpoint badges regenerated with the data: open issues, good
  first issues, fixes merged
- Fixed the Actions run failing with "Resource not accessible by integration": the code
  treated every 403 as a rate limit, but an Actions token returns 403 for endpoints
  outside its scope. Permission errors are now distinguished, and the optional identity
  lookup degrades instead of aborting.
- Files affected: `track_a11y.py`, `docs/index.html`, `docs/badge-*.json`, `README.md`

## 2026-08-14 20:56
- Added a dashboard at `docs/index.html`: search, filter by specialty, language, good
  first issue, and unlabeled; sort by stars, idle time, age, or discussion. One file, no
  dependencies, light and dark.
- Added `--json` to export dashboard data, and a personal picks list stored in the
  visitor's browser with milestone labels and a LinkedIn post drafter
- Added `.github/workflows/refresh.yml`: weekly refresh using the built-in Actions token,
  committing `docs/data.json`, so GitHub Pages can host the whole thing for free
- `write_json()` publishes public issues only. The owner's own repos are excluded so a
  private repo's issue titles can never end up in a file committed to a public repo.
- Fixed the empty-state buttons showing on an empty list: `display: flex` on `.actions`
  outranks the browser's `[hidden]` rule
- Verified in a browser: filters, claiming, milestones, sorting, and the post draft
- Files affected: `track_a11y.py`, `docs/index.html`, `docs/data.json`,
  `.github/workflows/refresh.yml`, `README.md`, `SKILL.md`, `PROJECT_OVERVIEW.md`

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
