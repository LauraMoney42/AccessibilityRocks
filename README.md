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
| **All public repos** | Open accessibility issues across GitHub, most-starred repos first. Includes a "good first issue" column, so contribution targets are one filter away. |
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
--labels A,B,C        label spellings to match
--out PATH            where to write the .xlsx
```

## Signing in (optional)

Anonymous mode has exactly two limits:

- private repos are invisible
- star counts are looked up for the top 40 repos only, because the anonymous rate limit
  is 60 requests an hour

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
