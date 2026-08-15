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

## The dashboard

`docs/index.html` is one self-contained file: no build, no dependencies, no framework. It
fetches `docs/data.json` (about 170 KB for 405 issues) and does all filtering in memory.
GitHub Pages serves `/docs` from `main`, and `.github/workflows/refresh.yml` regenerates
the JSON weekly using the built-in `GITHUB_TOKEN`.

`write_json()` publishes public issues only. The owner's own repos are deliberately
excluded: the file is designed to be committed to a public repo, and a private repo's
issue titles must never ride along with it.

Recognition is self-reported and says so. A static page cannot verify a merged PR, so it
tracks picks in `localStorage` and the milestone labels describe exactly that. The
LinkedIn button drafts the post and copies it to the clipboard rather than passing text in
the URL, because LinkedIn strips prefilled share text.

## Accessibility of the dashboard itself

Audited with a scripted structural pass in the browser, a real keyboard tab through the
focus order, and contrast maths over the palette. Findings that were real bugs:

- **Control borders at 1.2:1.** Inputs sit on a background nearly identical to their own,
  so the border is the entire visual boundary and WCAG 1.4.11 wants 3:1. Added
  `--control-line` at 4.4:1 light and 5.9:1 dark.
- **`opacity: .38` on unearned milestones.** Opacity blends text toward the background and
  quietly fails contrast. Replaced with a dashed border and muted colour.
- **300 toggle buttons with no state.** Added `aria-pressed`.
- **Silent filtering.** Result counts now live in a `role="status"` region.
- **900 tab stops.** Results page at 100, and "Show more" moves focus to the first new card.

`:focus-visible` had to be verified with an actual Tab keypress: programmatic `.focus()`
does not match it in Chrome, so a scripted check reports no outline even when the ring
works.

## Spreadsheet mechanics

Dates are written as `datetime` values with a `yyyy-mm-dd` number format, not strings.
A string date sorts alphabetically, which looks right for ISO dates until a filter or a
chart touches it, and it can never be compared or subtracted. Counts are ints for the
same reason. Missing values are `None`, not `""`, so they sort as blanks instead of
before every number.

## Specialty classification

`AREAS` is an ordered list of (area, keywords), compiled into `AREA_PATTERNS` with a
leading `\b`. Matching is anchored to word starts because plain substring matching was
quietly broken: `form` fired on "information", "platform", and "performance", inflating
Forms & error messages to 124 issues. With boundaries it sits at 31, and the difference
went back to `General / unclassified` where it belongs.

`classify_all()` returns every area an issue touches, in AREAS order. The first is the
primary area used for grouping and the rest fill the "Also covers" column, since a modal
dialog bug is genuinely both focus and screen reader work. About a quarter of rows carry
more than one.

The body is the awkward one. GraphQL cannot carry it in bulk: 100 issue nodes with
`bodyText` returns `RESOURCE_LIMITS_EXCEEDED`, and dropping to 50 nodes traded that for a
502 timeout. Issue bodies are unbounded, so there is no page size that makes this safe.
The bulk search therefore classifies on title and labels only, and `refine_areas()` then
reads every issue individually: one REST call each, capped at 600, eight in flight, soft
so a failure costs a row rather than the run. 405 issues take about 35 seconds of the
minute-long run.

## The unlabeled pass

The new default label only helps going forward, so `search_untagged()` looks for the work
that predates it: six phrases, `in:title`, excluding anything already carrying an
accessibility label.

`in:title` is not an optimization, it is the difference between usable and useless.
Searching bodies returned `ValveSoftware/Proton` game compatibility reports and a Prettier
tabs-vs-spaces debate, because those issues mention the words somewhere in a template.
Title matching returned Chart.js keyboard navigation and scikit-learn alt text.

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
- Full run with both extra passes: about 50 seconds, 250 labeled + 136 unlabeled rows
- Specialty spread on that run: 134 screen reader, 100 unclassified, 56 keyboard,
  40 contrast, 36 forms, 9 text and zoom, 3 captions, 2 motion, 1 cognitive
