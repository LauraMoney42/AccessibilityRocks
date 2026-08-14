# a11y-tracker

Polls the GitHub API once a day for every issue in LauraMoney42's repos that carries an
accessibility-style label, and writes them to an Excel workbook.

## Why it lives at `~/a11y-tracker`

macOS TCC blocks launchd background agents from reading or writing `~/Documents` unless
Full Disk Access is granted manually. The real files sit in the home folder (unprotected)
and `~/Documents/GIT/a11y-tracker` is a symlink pointing at them, so the project is still
findable where the rest of the work lives.

## Files

| File | Purpose |
| --- | --- |
| `track_a11y.py` | The whole tracker: queries GitHub, builds the workbook |
| `run.sh` | launchd wrapper (fixes PATH, appends to `a11y-tracker.log`) |
| `accessibility-issues.xlsx` | The output, overwritten on every run |
| `a11y-tracker.log` | One line per run |
| `~/Library/LaunchAgents/com.kindcode.a11y-tracker.plist` | Daily 09:00 schedule |

## How it works

1. `gh search issues --owner LauraMoney42 --label <variant>` runs once per label spelling
   in `LABEL_VARIANTS` (`accessibility`, `a11y`, `accessibility-issue`,
   `accessibility issue`). Results merge on repo + issue number so duplicates collapse.
2. `gh repo list` pulls all 42 repos, then a thread pool of 8 checks each repo's label
   list so the workbook can show which repos have the label defined but no issues yet.
3. openpyxl writes three sheets: **Issues**, **Repos**, **Run info**.

Auth comes from the `gh` CLI's existing token in the macOS keyring, so there is no API
key stored in this project.

## Sheets

- **Issues**: one row per accessibility item. Open items sort to the top, amber fill for
  open, green for closed. Includes age in days and a clickable link.
- **Repos**: all 42 repos with open/closed counts and whether an accessibility label
  exists. Repos with open items sort first and are highlighted.
- **Run info**: timestamp, label variants searched, totals.

## Running it manually

```
python3 ~/a11y-tracker/track_a11y.py
```

Options: `--owner <user>`, `--out <path>`, `--no-label-audit` (skips the per-repo label
check, roughly 42 fewer API calls).

## Rate limits

A full run costs about 46 REST calls against a 5000/hour limit, so the daily schedule
uses well under 1% of the budget.

## Changing the schedule

Edit `StartCalendarInterval` in the plist, then:

```
launchctl bootout gui/501/com.kindcode.a11y-tracker
launchctl bootstrap gui/501 ~/Library/LaunchAgents/com.kindcode.a11y-tracker.plist
```

To stop it permanently, run the `bootout` line and delete the plist.
