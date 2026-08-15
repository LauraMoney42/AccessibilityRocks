# AccessibilityRocks

**[Browse the dashboard](https://lauramoney42.github.io/AccessibilityRocks/)** · accessibility issues in open source that need help.

[![issues](https://img.shields.io/endpoint?url=https://lauramoney42.github.io/AccessibilityRocks/badge-issues.json)](https://lauramoney42.github.io/AccessibilityRocks/)
[![good first issues](https://img.shields.io/endpoint?url=https://lauramoney42.github.io/AccessibilityRocks/badge-gfi.json)](https://lauramoney42.github.io/AccessibilityRocks/)
[![fixes merged](https://img.shields.io/endpoint?url=https://lauramoney42.github.io/AccessibilityRocks/badge-fixes.json)](https://lauramoney42.github.io/AccessibilityRocks/)

A spreadsheet and dashboard of accessibility issues on GitHub: the ones worth contributing
to across all public repos, and the ones sitting in your own.

The badges above are live. They read three small JSON files that regenerate every Monday,
so nothing is hardcoded and there is no badge service to sign up for. Copy the markdown
from this file to put them anywhere.

**No sign-in, no API key, no install steps.** One command:

```bash
python3 track_a11y.py --owner your-username
```

That works because GitHub's search API answers anonymous requests. Signing in is
supported and adds private repos, but it is never required.

## What you get

`accessibility-issues.xlsx`, five sheets:

| Sheet | Contents |
| --- | --- |
| **All public repos** | Open accessibility issues, most-starred first. Every column sorts and filters: real dates, numeric stars, comments, age, and idle days. |
| **By specialty** | The index: how many open issues and projects sit in each area, how many are good first issues, and the most-starred project in that area. Start here, then filter column A on the sheet before it. |
| **My repos** | Accessibility issues in your own repos, open and closed. Open items sort first, amber for open, green for closed. |
| **My repo rollup** | Every repo you own with its open and closed counts, so the quiet ones are visible too. |
| **Run info** | When it ran, what was searched, and what the numbers do and do not cover. |

## The dashboard

**Live at [lauramoney42.github.io/AccessibilityRocks/](https://lauramoney42.github.io/AccessibilityRocks/)**

`docs/index.html` is a browsable version for people who want to *find* work rather than
audit their own repos: search, filter by specialty and language, sort by stars or by how
long an issue has sat untouched, and keep a personal list.

To host it free on GitHub Pages from your own repo:

1. Push this repo to GitHub.
2. Settings > Pages > Source: "Deploy from a branch", branch `main`, folder `/docs`.
3. Actions tab > "Refresh accessibility data" > Run workflow, to fill in the first data file.

It then refreshes itself every Monday. The workflow uses the built-in Actions token, so
there is no secret to create, and `docs/data.json` only ever contains public issues.

## Is the dashboard itself accessible?

It would be a bad look otherwise. What was checked and fixed:

| Check | Result |
| --- | --- |
| Landmarks | `header`, `main`, `footer`, and a search region |
| Skip link | Skips the filter bar straight to the results, which take focus |
| Keyboard | Every control reachable, all named, focus ring 3px at 5.6:1 (light) and 7.3:1 (dark) |
| Live regions | Result counts and list changes announce instead of changing silently |
| Contrast | All text at least 4.5:1 in both themes; control borders raised to 4.4:1 for WCAG 1.4.11 |
| List semantics | `role="list"` where `list-style: none` would otherwise strip it in VoiceOver |
| Volume | Results page at 100, cutting roughly 900 tab stops to about 300 |
| Scoreboard | Top ten in a plain grid. A side-scroller was tried and dropped: it needs its own focusable region and accessible name to stay keyboard-usable, and ten rows fit without any of that |
| Motion | No animation, so nothing to reduce |

Two things were genuinely broken and are now fixed: control borders sat at 1.2:1 against
the background, which fails 1.4.11 since inputs share the page background and the border
*is* the control boundary; and the milestone chips used `opacity: .38`, which drags text
under the contrast floor. Dashed borders replaced the opacity.

**Not yet done:** no test with a real screen reader. The checks above are structural,
keyboard, and contrast, run in a browser. VoiceOver and NVDA passes are the obvious next
step, and if you find something, [open an issue](../../issues).

## The scoreboard

The dashboard ranks people who actually merged accessibility fixes in the last 90 days.
That number is verifiable: a merged pull request carrying an accessibility label is a fact
the GitHub API will confirm, which is why the board uses it instead of anything
self-reported.

Three rules keep the ordering honest, and each one exists because the version before it
was gamed by accident:

1. **Fixes to your own repos do not count.** The board is about helping someone else's
   users.
2. **Each owner counts at most three times.** Not each repo: splitting a backlog across
   two repos under one account was the loophole that produced a bogus number one.
3. **Repos under 50 stars are left out.** A brand new repo with a crowd of contributors
   merging into it is a hackathon, not the open source commons.

Before those rules the entire top of the board was one account's two new repos, at 1 and
22 stars. After them it is Mozilla, WebKit, indico, scaleway, Orange-OpenSource and
headlamp. `--scoreboard-min-stars` changes the floor, which needs a token to apply since
it costs a star lookup per repo.

Everyone who merges a fix also lands on [CONTRIBUTORS.md](CONTRIBUTORS.md), the
contributors wall, regenerated every Monday. That is a real page in a real repo: linkable,
indexed, and worth more than a counter only this site recognizes. Two merged pull requests
also earns GitHub's own Pull Shark achievement, which lands on the contributor's profile.

**Make a Post** sits under the scoreboard. It asks for a GitHub username, checks the API
for merged pull requests carrying an accessibility label, and drafts a LinkedIn post from
the real numbers: "Contribute to AccessibilityRocks with me", what they fixed, and a link
to the issue list. No merged fixes means no post, since the text quotes counts that have
to be true.

The draft is copied to the clipboard rather than passed in the share URL, because LinkedIn
strips prefilled text from share links.

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

## Sorting and filtering

Every column is real data, not text that looks like data:

- **Opened** and **Last activity** are Excel dates, so sorting them is chronological.
  Text dates sort alphabetically, which is why they are stored properly here.
- **Stars**, **Comments**, **Age (days)**, **Idle (days)**, and **#** are numbers.
- **Area**, **Also covers**, **Owner**, **License**, **Language**, **Found via**, and
  **Good first issue** are consistent values, so their filter dropdowns are short lists
  rather than hundreds of one-off strings.

Useful combinations: sort by **Idle (days)** descending to find abandoned issues, or by
**Opened** ascending for the oldest unfixed problems. Filter **Good first issue** to
`yes` and sort by **Stars** for high-visibility starter work.

## Finding your area

Every issue is read and given our own labels, from nine specialties:

Screen reader & ARIA, Keyboard & focus, Color & contrast, Captions & media, Motion &
seizure safety, Text & zoom, Forms & error messages, Touch & mobile, Cognitive & plain
language. Anything that cannot be placed lands in **General / unclassified** rather than
being guessed at.

Issues usually touch more than one area: a modal dialog bug is both focus and screen
reader work. **Area** is the primary one, used for grouping, and **Also covers** lists
the rest, so filtering on either finds the issue. About a quarter of rows carry more than
one area.

Open the **By specialty** sheet, find your row, then filter the public sheet to that area.
The index counts primary and secondary separately, so it matches what filtering returns.

## Work nobody labeled

The `accessibility` label only helps once a maintainer applies it, so everything filed
before it existed is still sitting under `bug` or `enhancement`. A second pass searches
issue **titles** for `screen reader`, `keyboard navigation`, `color contrast`, `alt text`,
`WCAG`, and `aria-label`, excluding anything already labeled. Those rows say
`text match: "<phrase>"` in the Found via column, and a recent run turned up 136 of them:
Chart.js keyboard navigation, scikit-learn alt text, Telegram screen reader support.

Title matching is deliberate. Searching bodies pulled in issue templates and game
compatibility reports that merely mentioned the words. `--no-untagged` skips the pass.

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
