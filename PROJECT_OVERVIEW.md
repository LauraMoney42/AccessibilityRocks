# a11y-tracker

Builds a spreadsheet of accessibility-labeled GitHub issues: the open ones across all
public repos ranked by repo popularity, plus the ones in a given account's own repos.

Started as a personal weekly job, then generalized twice: once so any repo owner could
install it, and again so a friend could use it with no sign-in at all. `README.md` is the
front door for those users, `SKILL.md` is the front door for their AI assistants, and
this file is the internal design note.

## The auth decision, and why it changed

The first version shelled out to `gh` for every call, which made a GitHub login a hard
prerequisite. Setting that up was the single worst part of the experience: browser flow,
one-time code, plus gh's own git-credential questions.

GitHub's REST search API answers unauthenticated requests (10 per minute), and the core
API allows 60 requests an hour anonymously. That covers everything except private repos.
So `gh` was demoted from the transport layer to one of three optional token sources:

```
GH_TOKEN / GITHUB_TOKEN  ->  `gh auth token`  ->  none (anonymous)
```

Everything now goes through one `request()` helper over urllib. A token changes three
things and nothing else: private repos appear, GraphQL becomes available, and the rate
limit stops mattering.

## Why lives at `~/a11y-tracker`

macOS TCC blocks launchd background agents from reading or writing `~/Documents` unless
Full Disk Access is granted manually. The real files sit in the home folder and
`~/Documents/GIT/a11y-tracker` is a symlink. `install.sh` refuses to install into a
protected folder rather than failing quietly at run time.

## Files

| File | Purpose |
| --- | --- |
| `track_a11y.py` | The whole tracker: queries GitHub, builds the workbook |
| `SKILL.md` | Claude Code skill definition, so the repo can be cloned into `~/.claude/skills/` |
| `install.sh` | Optional weekly scheduling: username, day, time, launchd job, test run |
| `uninstall.sh` | Removes the launchd job, leaves data alone |
| `run.sh` | launchd wrapper (fixes PATH, appends to `a11y-tracker.log`) |
| `~/Library/LaunchAgents/com.a11ytracker.weekly.plist` | The schedule |

## How the two searches differ

**Public sheet.** With a token, GraphQL returns 100 issues per call with
`stargazerCount` inline, so ranking by popularity is free. Without one, REST search
returns no star data, so the tool counts which repos appear most and looks up stars for
the top 25 only, leaving the rest blank and sorted last. The cap exists because of the
60 requests per hour anonymous core limit, and Run info says when it applied.

**Own-repo sheet.** Plain REST search with `user:<owner>`, which needs no token for
public repos. Repo listing prefers `/user/repos?affiliation=owner` when the token owns
the account (so private repos appear), otherwise `/users/{o}/repos` then `/orgs/{o}/repos`.

## What the public sheet excludes, and why

The point of that sheet is finding projects that need volunteer help, so four rules run
by default:

| Rule | Reason |
| --- | --- |
| ~110 big-company owners hidden, not dropped | They have paid accessibility teams, but whether to help them anyway is the reader's call, so it belongs in the spreadsheet rather than in the fetch |
| Recognized open source license required | Source-available is not open source; `NOASSERTION` means GitHub could not identify it |
| No archived repos, no forks | Nothing to contribute to |
| At most 3 issues per repo | One busy backlog would otherwise fill the sheet; a 300-row pull covers ~200 projects |

Big-company rows are written with a grey fill, tagged `big company` in column A, and
hidden via `row_dimensions[i].hidden` plus an `auto_filter` criterion set to
`independent`. Both are needed: Excel honours the filter, and hiding the rows keeps the
view correct in readers that ignore stored filter definitions. `limit` counts independent
rows only, so tagged rows never eat the budget.

`BIG_TECH_OWNERS` sits at the top of the file as an editable set, with `--exclude-big-tech`
and `--exclude-owners` as the escape hatches. Run info reports how many rows each rule
removed, so the filtering is visible rather than silent.

Filtered rows are replaced rather than subtracted: the pull keeps going until it has the
requested count of keepers.

## Design decisions worth remembering

- **Comma-separated labels are OR in GitHub search.** `label:accessibility,a11y,"a b"`
  is one query instead of four, and multi-word labels need the quotes.
- **Sample honestly.** The public sheet pulls the most-commented open issues and then
  sorts by stars, because GitHub cannot sort issues by repo popularity and caps any
  search at 1000 results. Run info states the sample rule rather than implying the sheet
  is exhaustive.
- **Stars, not downloads.** GitHub exposes no download count for a repo. The column is
  labeled Stars and Run info explains the substitution.
- **Scheduling never prompts.** A launchd job has no terminal, so nothing in the run path
  asks a question. Auth is resolved silently or skipped.
- **403 means rate limit here, not forbidden.** Search answers a burst with 403, so
  `request()` retries with backoff before giving up, and the error names the fix.
- **Star lookups fail soft.** They are the one call that is nice-to-have, so they pass
  `soft=True`: a rate limit blanks the cell and sets a global flag to stop trying, rather
  than throwing away a spreadsheet that is otherwise complete. Found by exhausting the
  anonymous 60/hour budget during testing, which killed an entire run.

## Verified behavior

- Signed in: 42 repos including private, 300 public issues across 196 distinct projects,
  45 of them tagged good first issue, about 18 seconds
- Anonymous (gh off PATH): 29 public repos, public sheet complete with stars
- Anonymous with the core budget already exhausted: run completes, stars blank, note in
  Run info
- Top of the public sheet after filtering: electron, mui, storybook, svelte, mastodon,
  leaflet, NewPipe. Before filtering it was microsoft/vscode and react-native.
- Weekly launchd run: exit 0
