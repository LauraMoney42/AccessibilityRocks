---
name: a11y-tracker
description: Build a spreadsheet of accessibility-labeled GitHub issues, both across all public repos ranked by popularity and inside a specific user's or org's repos. Use when someone asks to find accessibility issues, a11y issues, accessibility work to contribute to, or wants their repos audited for accessibility-tagged issues.
---

# a11y-tracker

Produces `accessibility-issues.xlsx` with four sheets:

1. **All public repos** - open accessibility issues, most-starred first, with a "good first issue" column. Column A tags each row `independent` or `big company`, and the sheet opens filtered to `independent`. Big-company rows are present but hidden, so the reader can unhide them without re-running anything. Unlicensed repos, archived repos, and forks are left out.
2. **My repos** - accessibility issues in the person's own repos, open and closed
3. **My repo rollup** - per-repo counts, so empty repos are visible too
4. **Run info** - what was searched and when

## Running it

```bash
python3 track_a11y.py --owner <github-username>
```

`track_a11y.py` sits next to this file. Use its absolute path.

**No sign-in is required.** GitHub's search API answers anonymous requests, so this
works immediately for anyone. Do not ask the user to authenticate before trying.

## Steps

1. If the user has not said which GitHub account to scan, ask for the username or org.
   Only that one question is needed to start.
2. Run the command. It takes 10 to 30 seconds.
3. Report the headline numbers from the output, then open the file:
   `open accessibility-issues.xlsx` on macOS, `xdg-open` on Linux.

## Useful flags

| Flag | Effect |
| --- | --- |
| `--global-limit N` | how many public issues to pull, max 1000, default 300 |
| `--no-global` | skip the public sheet, only scan their repos |
| `--owner a,b` | scan several accounts into one workbook |
| `--labels x,y` | match different label spellings |
| `--per-repo N` | max issues per repo on the public sheet, default 3 |
| `--exclude-big-tech` | leave big-company issues out of the file entirely |
| `--exclude-owners a,b` | filter out more owners |
| `--min-stars N` | ignore repos below a star count |
| `--out PATH` | write somewhere else |

## When to suggest signing in

Anonymous mode has two limits worth naming only if they matter to the user:

- private repos are invisible
- star counts are fetched for the top 25 repos, so ranking below that is incomplete

If they want either, they can run `gh auth login --web` (opens github.com, no key to
copy) or set `GH_TOKEN`. The script picks up a token automatically. Never make this a
prerequisite.

## Scheduling

`./install.sh` sets up a weekly macOS job and asks for a day and time. Only bring this
up if the user asks for recurring updates. It must not live in `~/Documents`,
`~/Desktop`, or `~/Downloads`, since macOS blocks background jobs from those folders.

## Notes

- "Most downloads" is not a thing GitHub exposes for repos. Stars are used as the
  popularity ranking, and the sheet says so.
- Big-company repos are hidden behind a spreadsheet filter rather than dropped, on the
  reasoning that those companies have paid accessibility teams but the reader may still
  want the option. If they ask to see them, tell them to clear the filter on column A
  rather than re-running the script. The owner list is at the top of `track_a11y.py`.
- The public sample is the most-commented open accessibility issues, then sorted by
  stars. It is a sample of roughly 17,000 open issues, not the complete set.
- Requires Python 3.9+ and `openpyxl` (`python3 -m pip install --user openpyxl`).
