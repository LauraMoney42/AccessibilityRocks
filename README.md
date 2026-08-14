# a11y-tracker

Every accessibility issue across your GitHub repos, in one spreadsheet, updated daily.

Point it at a username or an org. It searches every repo you own for issues labeled
`accessibility`, `a11y`, `accessibility-issue`, or `accessibility issue`, and writes them
to an Excel workbook with open items sorted to the top.

## Quickstart

```bash
git clone <this-repo> ~/a11y-tracker
cd ~/a11y-tracker
./install.sh
```

The installer asks for a GitHub username (it offers your own as the default) and an hour
to run, then sets up a daily background job and does one test run so you see results
immediately.

To run it once without scheduling anything:

```bash
python3 track_a11y.py --owner your-username
```

## Requirements

- [GitHub CLI](https://cli.github.com): `brew install gh`, then `gh auth login`
- Python 3.9+ with `openpyxl` (the installer adds it if missing)

There is no API key to create. The tool reuses the token `gh` already holds, which also
means private repos you can see are included.

## What you get

`accessibility-issues.xlsx`, three sheets:

| Sheet | Contents |
| --- | --- |
| **Issues** | One row per accessibility item: repo, number, title, state, labels, assignee, comment count, age in days, clickable link. Open items sort first and are shaded amber, closed ones green. |
| **Repos** | Every repo with its open/closed accessibility counts, plus whether an accessibility label exists there at all. Repos with open work sort to the top. |
| **Run info** | When it last ran, which owners and labels were searched, and the totals. |

## Options

```
--owner NAME[,NAME]   user or org to scan (default: your gh login)
--labels A,B,C        label spellings to search (default: the four above)
--out PATH            where to write the .xlsx
--no-label-audit      skip the per-repo label check, one fewer API call per repo
```

Scanning several owners at once puts them in a single sheet:

```bash
python3 track_a11y.py --owner your-name,your-org
```

## Scheduling

`install.sh` writes a launchd agent at
`~/Library/LaunchAgents/com.a11ytracker.daily.plist`. To change the time, re-run
`./install.sh`. To stop it, run `./uninstall.sh`.

On Linux, skip the installer and add this to `crontab -e`:

```
0 9 * * * /path/to/a11y-tracker/run.sh --owner your-username
```

## macOS gotcha

Background jobs on macOS cannot read `~/Documents`, `~/Desktop`, or `~/Downloads` without
Full Disk Access. Keep the folder somewhere like `~/a11y-tracker`. `install.sh` checks for
this and stops with an explanation rather than failing silently at 9am. Running the script
by hand from anywhere works fine.

## Cost

One run is about one API call per label spelling, plus one per repo for the label audit.
A 42-repo account uses roughly 46 of the 5000 requests per hour that GitHub allows. Large
orgs are fine too: a 20-repo org with 679 accessibility issues takes about 14 seconds.

## Logs

- `a11y-tracker.log`: one line per run
- `launchd.err.log`: only written when the scheduled job itself fails to start
