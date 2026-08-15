# a11y-tracker

A spreadsheet of accessibility issues on GitHub: the ones worth contributing to across
all public repos, and the ones sitting in your own.

**No sign-in, no API key, no install steps.** One command:

```bash
python3 track_a11y.py --owner your-username
```

That works because GitHub's search API answers anonymous requests. Signing in is
supported and adds private repos, but it is never required.

## What you get

`accessibility-issues.xlsx`, four sheets:

| Sheet | Contents |
| --- | --- |
| **All public repos** | Open accessibility issues in independent open source projects, most-starred first. Big-company repos are filtered out, and there is a "good first issue" column. |
| **My repos** | Accessibility issues in your own repos, open and closed. Open items sort first, amber for open, green for closed. |
| **My repo rollup** | Every repo you own with its open and closed counts, so the quiet ones are visible too. |
| **Run info** | When it ran, what was searched, and what the numbers do and do not cover. |

## Three ways to use it

### 1. As a skill for your AI assistant

This repo *is* a Claude Code skill. Clone it straight into your skills folder:

```bash
git clone <this-repo> ~/.claude/skills/a11y-tracker
```

Then ask your assistant something like "find accessibility issues in my repos" and it
handles the rest. `SKILL.md` tells it what to run and what the flags mean.

### 2. As a one-off command

Clone anywhere and run it. The only requirement beyond Python 3.9+ is `openpyxl`:

```bash
python3 -m pip install --user openpyxl
python3 track_a11y.py --owner your-username
```

### 3. On a weekly schedule (macOS)

```bash
./install.sh
```

It asks for a username, a day of the week, and a time, then sets up a background job and
runs once so you see results immediately. `./uninstall.sh` removes it.

The folder must not live in `~/Documents`, `~/Desktop`, or `~/Downloads`: macOS blocks
background jobs from those. The installer checks and tells you.

On Linux, add this to `crontab -e` instead (last field is the day, 0 for Sunday):

```
30 14 * * 5 /path/to/a11y-tracker/run.sh --owner your-username
```

## Options

```
--owner NAME[,NAME]   user or org to scan (several are merged into one workbook)
--global-limit N      how many public issues to pull, max 1000, default 300
--no-global           skip the public sheet, only scan your repos
--per-repo N          max issues per repo on the public sheet, default 3, 0 for no cap
--exclude-big-tech    leave big-company issues out of the file entirely
--exclude-owners a,b  leave out more owners
--any-license         include repos with no recognizable open source license
--min-stars N         ignore public repos below this star count
--labels A,B,C        label spellings to match
--out PATH            where to write the .xlsx
```

## Big tech is a filter, not a decision

Column A on the public sheet says `independent` or `big company`, and the file opens with
the filter already set to `independent`. Microsoft, Google, Meta, Apple, Amazon, Adobe,
Oracle and about 110 other owners are in the file, just hidden and shaded grey.

To bring them back, clear the filter on column A (in Excel: click the arrow on column A,
tick `big company`, or Data > Clear). To make it permanent, pass `--exclude-big-tech` and
they never get written at all.

The owner list lives at the top of `track_a11y.py` under `BIG_TECH_OWNERS` and is meant
to be edited. `--exclude-owners a,b` adds more for a single run.

The other three rules do drop rows, because they are not judgment calls:
- **Repos with no recognizable open source license.** Source-available and unlicensed
  code is not the same as open source. Pass `--any-license` to keep them.
- **Archived repos and forks.** Nothing to contribute to.
- **Extra issues from a repo already listed.** Three per repo by default, so one busy
  backlog cannot fill the sheet. A 300-row pull typically covers around 200 projects.

Run info records how many rows each rule removed.

## Signing in (optional)

Anonymous mode has exactly two limits:

- private repos are invisible
- star counts are looked up for the top 25 repos only, because the anonymous rate limit
  is 60 requests an hour. Missing counts leave the cell blank rather than failing the run.

If either matters, run `gh auth login --web` (it opens github.com with a one-time code,
nothing to copy by hand) or export a `GH_TOKEN`. The script finds a token on its own and
says which mode it used in the Run info sheet.

## Honest limits

- **"Most downloads" does not exist for GitHub repos.** Stars are the popularity metric,
  and the sheet says so in Run info.
- **The public sheet is a sample.** There are roughly 17,000 open accessibility issues on
  GitHub. The default pull is the 300 most-commented, then sorted by stars. Raise it with
  `--global-limit`, up to GitHub's hard cap of 1000 per search.
- **Labels matched:** `accessibility`, `a11y`, `accessibility-issue`, `accessibility
  issue`. Anything else needs `--labels`.
