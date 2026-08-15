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
the top 40 only, leaving the rest blank and sorted last. The cap exists because of the
60 requests per hour anonymous core limit, and Run info says when it applied.

**Own-repo sheet.** Plain REST search with `user:<owner>`, which needs no token for
public repos. Repo listing prefers `/user/repos?affiliation=owner` when the token owns
the account (so private repos appear), otherwise `/users/{o}/repos` then `/orgs/{o}/repos`.

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

## Verified behavior

- Signed in: 42 repos including private, 200 public issues, about 14 seconds
- Anonymous (gh off PATH): 29 public repos, 100 public issues, stars for 40 repos, 8 seconds
- Top of the public sheet: `microsoft/vscode` at 188,689 stars
- Weekly launchd run: exit 0
