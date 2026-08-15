# a11y-tracker

Polls the GitHub API weekly for every issue in one or more owners' repos that
carries an accessibility-style label, and writes them to an Excel workbook.

Built for personal use first, then generalized so any repo owner can clone it, run
`./install.sh`, and get the same thing for their own account. `README.md` is the
front door for those users; this file is the internal design note.

## Why it lives at `~/a11y-tracker`

macOS TCC blocks launchd background agents from reading or writing `~/Documents` unless
Full Disk Access is granted manually. The real files sit in the home folder (unprotected)
and `~/Documents/GIT/a11y-tracker` is a symlink pointing at them, so the project is still
findable where the rest of the work lives. `install.sh` checks for this and refuses to
install into a protected folder rather than failing quietly at run time.

## Files

| File | Purpose |
| --- | --- |
| `track_a11y.py` | The whole tracker: queries GitHub, builds the workbook |
| `install.sh` | Interactive setup: deps, username, day, time, launchd job, test run |
| `uninstall.sh` | Removes the launchd job, leaves data alone |
| `run.sh` | launchd wrapper (fixes PATH, appends to `a11y-tracker.log`) |
| `README.md` | Public-facing docs for anyone who clones this |
| `accessibility-issues.xlsx` | The output, overwritten on every run |
| `~/Library/LaunchAgents/com.a11ytracker.weekly.plist` | The schedule |

## How it works

1. `gh search issues --owner <owner> --label <variant>` runs once per owner and label
   spelling. Results merge on repo + issue number so duplicates collapse.
2. `gh repo list` pulls the owner's repos, then a thread pool of 8 checks each repo's
   label list so the workbook can show repos that have the label defined but no issues.
3. openpyxl writes three sheets: **Issues**, **Repos**, **Run info**.

Auth comes from the `gh` CLI's existing token, so no API key is stored in this project
and private repos the user can see are covered automatically.

## Design decisions worth remembering

- **No `--state` flag on `gh search issues`.** It only accepts `open|closed`; omitting it
  returns both, which is what the closed-item history needs.
- **`preflight()` runs before anything else.** A shared tool fails on missing `gh` or
  missing openpyxl, so each one exits with the exact fix command.
- **Sign-in is offered, not instructed.** `ensure_auth()` and the installer both hand off
  to `gh auth login --web`, which opens github.com with a one-time code, rather than
  telling the user to go read gh's docs. Guarded by `sys.stdin.isatty()`: under launchd
  there is no terminal to type a code into, so the scheduled run exits with a message in
  the log instead of hanging on stdin forever.
- **`--clipboard` only on macOS.** It needs a clipboard tool that Linux may not have.
- **Owner defaults to `gh api user --jq .login`.** Zero-argument runs work for whoever
  cloned it. `--owner a,b` supports people who own both a user and an org.
- **The label audit is optional.** It costs one API call per repo, which matters on a
  500-repo org and not at all on a personal account.

## Verified behavior

- Personal account, 42 repos: about 4 seconds
- `mui` org, 20 repos, 679 accessibility items: about 14 seconds
- Unknown username: warns, then exits 1 with a clear message
- Scheduled run under launchd: exit 0, the keychain token is readable headlessly

## Rate limits

A full personal run costs about 46 REST calls against a 5000/hour limit, well under 1%
of the budget, and the weekly schedule uses it once every seven days.
