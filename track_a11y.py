#!/usr/bin/env python3
"""
Accessibility issue tracker.

Builds a spreadsheet of accessibility-labeled GitHub issues:
  * every open one across all public repos, ranked by repo popularity
  * every one in your own repos, open and closed
  * a per-repo rollup of your own repos

Auth is optional. GitHub's search API answers unauthenticated requests, so a
plain `python3 track_a11y.py --owner someone` works with no sign-in at all.
If a token is available (GH_TOKEN, or a signed-in `gh`), the tool uses it for
higher rate limits, private repos, and the far cheaper GraphQL path.

Usage:
    python3 track_a11y.py --owner your-name
    python3 track_a11y.py --owner your-name --global-limit 500
    python3 track_a11y.py --owner your-name --no-global      # skip the public scan
    python3 track_a11y.py --owner your-name,your-org
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

API = "https://api.github.com"

# Label spellings that all mean "accessibility". GitHub treats a comma-separated
# label qualifier as OR, so these go into one query rather than one query each.
DEFAULT_LABELS = ["accessibility", "a11y", "accessibility-issue", "accessibility issue"]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(SCRIPT_DIR, "accessibility-issues.xlsx")

# Without a token the core API allows 60 requests an hour, so the number of
# repos we look up stars for has to stay small.
ANON_STAR_LOOKUPS = 40


# --------------------------------------------------------------------------
# Auth: entirely optional
# --------------------------------------------------------------------------

def resolve_token():
    """A token if one is lying around, otherwise None. Never prompts."""
    for var in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(var):
            return os.environ[var]
    try:
        proc = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


TOKEN = None  # set in main()


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

def request(url, data=None, retries=3):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "a11y-tracker",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers)

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as err:
            # Search is limited to 10 requests a minute without a token, and
            # GitHub answers a burst with 403 rather than a 429.
            if err.code in (403, 429) and attempt < retries - 1:
                wait = int(err.headers.get("Retry-After") or (20 * (attempt + 1)))
                print(f"  rate limited, waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            if err.code == 404:
                return None
            detail = err.read().decode(errors="replace")[:200]
            if err.code in (403, 429):
                hint = ("\nHint: set GH_TOKEN or run 'gh auth login' for a much higher limit."
                        if not TOKEN else "")
                sys.exit(f"GitHub rate limit hit.{hint}\n{detail}")
            sys.exit(f"GitHub API error {err.code} for {url}\n{detail}")
        except urllib.error.URLError as err:
            if attempt < retries - 1:
                time.sleep(3)
                continue
            sys.exit(f"Could not reach github.com: {err.reason}")
    return None


def graphql(query, variables):
    payload = request(f"{API}/graphql", data={"query": query, "variables": variables})
    if payload and payload.get("errors"):
        sys.exit("GitHub GraphQL error: " + json.dumps(payload["errors"])[:300])
    return (payload or {}).get("data")


def label_query(labels):
    """Quote multi-word labels, join with commas so GitHub reads it as OR."""
    return "label:" + ",".join(f'"{l}"' if " " in l else l for l in labels)


# --------------------------------------------------------------------------
# Searches
# --------------------------------------------------------------------------

def search_rest(query, limit, sort=None):
    """Paged REST issue search. GitHub caps any single search at 1000 results."""
    items, page = [], 1
    while len(items) < min(limit, 1000):
        params = {"q": query, "per_page": 100, "page": page}
        if sort:
            params["sort"], params["order"] = sort, "desc"
        data = request(f"{API}/search/issues?" + urllib.parse.urlencode(params))
        batch = (data or {}).get("items", [])
        items.extend(batch)
        if len(batch) < 100 or page >= 10:
            break
        page += 1
    return items[:limit]


GRAPHQL_SEARCH = """
query($q: String!, $after: String) {
  search(query: $q, type: ISSUE, first: 100, after: $after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on Issue {
        number title url createdAt updatedAt state
        comments { totalCount }
        labels(first: 20) { nodes { name } }
        repository { nameWithOwner stargazerCount primaryLanguage { name } }
      }
    }
  }
}
"""


def search_global(labels, limit):
    """Open accessibility issues across all public repos, with repo star counts.

    With a token this is GraphQL, which returns stars inline: 100 issues per
    call. Without one it falls back to REST plus a capped set of star lookups,
    because the anonymous core limit is 60 requests an hour.
    """
    base = f"{label_query(labels)} is:issue is:open is:public"

    if TOKEN:
        rows, cursor = [], None
        # Most-commented first: a sample of 300 out of ~17k should favour issues
        # people actually care about rather than whatever sorts first by default.
        while len(rows) < limit:
            data = graphql(GRAPHQL_SEARCH, {"q": base + " sort:comments-desc", "after": cursor})
            if not data:
                break
            block = data["search"]
            for n in block["nodes"]:
                if not n or not n.get("repository"):
                    continue
                rows.append({
                    "repo": n["repository"]["nameWithOwner"],
                    "stars": n["repository"]["stargazerCount"],
                    "language": (n["repository"].get("primaryLanguage") or {}).get("name") or "-",
                    "number": n["number"],
                    "title": n["title"],
                    "url": n["url"],
                    "labels": [l["name"] for l in n["labels"]["nodes"]],
                    "comments": n["comments"]["totalCount"],
                    "createdAt": n["createdAt"],
                    "updatedAt": n["updatedAt"],
                })
            if not block["pageInfo"]["hasNextPage"]:
                break
            cursor = block["pageInfo"]["endCursor"]
        rows = rows[:limit]
        capped = False
    else:
        raw = search_rest(base, limit, sort="comments")
        rows = [{
            "repo": "/".join(i["repository_url"].split("/")[-2:]),
            "stars": None,
            "language": "-",
            "number": i["number"],
            "title": i["title"],
            "url": i["html_url"],
            "labels": [l["name"] for l in i.get("labels", [])],
            "comments": i.get("comments", 0),
            "createdAt": i["created_at"],
            "updatedAt": i["updated_at"],
        } for i in raw]

        # Star counts cost one call each, so only the repos with the most hits
        # get looked up. The rest sort to the bottom with a blank star cell.
        by_hits = {}
        for r in rows:
            by_hits[r["repo"]] = by_hits.get(r["repo"], 0) + 1
        top = sorted(by_hits, key=lambda k: -by_hits[k])[:ANON_STAR_LOOKUPS]
        stars = {}
        with ThreadPoolExecutor(max_workers=4) as pool:
            for repo, info in zip(top, pool.map(lambda r: request(f"{API}/repos/{r}"), top)):
                if info:
                    stars[repo] = info.get("stargazers_count", 0)
        for r in rows:
            r["stars"] = stars.get(r["repo"])
        capped = len(by_hits) > ANON_STAR_LOOKUPS

    rows.sort(key=lambda r: (-(r["stars"] if r["stars"] is not None else -1), -r["comments"]))
    return rows, capped


def search_owner_issues(owners, labels):
    """Every accessibility issue in the owners' repos, open and closed."""
    merged = {}
    for owner in owners:
        query = f"{label_query(labels)} is:issue user:{owner}"
        for item in search_rest(query, 1000, sort="updated"):
            repo = "/".join(item["repository_url"].split("/")[-2:])
            merged[(repo, item["number"])] = {
                "repo": repo,
                "number": item["number"],
                "title": item["title"],
                "state": item["state"],
                "url": item["html_url"],
                "labels": [l["name"] for l in item.get("labels", [])],
                "assignee": ", ".join(a["login"] for a in item.get("assignees") or []) or "-",
                "comments": item.get("comments", 0),
                "createdAt": item["created_at"],
                "updatedAt": item["updated_at"],
            }
    return list(merged.values())


def fetch_owner_repos(owners):
    """Public repos always. Private ones too when the token owns them."""
    me = None
    if TOKEN:
        who = request(f"{API}/user")
        me = (who or {}).get("login")

    repos = []
    for owner in owners:
        if me and owner.lower() == me.lower():
            paths = ["/user/repos?affiliation=owner&per_page=100"]
        else:
            paths = [f"/users/{owner}/repos?per_page=100&type=owner",
                     f"/orgs/{owner}/repos?per_page=100&type=sources"]
        got = None
        for path in paths:
            page, collected = 1, []
            while True:
                data = request(f"{API}{path}&page={page}")
                if data is None:
                    break
                collected.extend(data)
                if len(data) < 100:
                    break
                page += 1
            if collected:
                got = collected
                break
        if not got:
            print(f"  warning: no repos found for '{owner}' (typo, or all private)",
                  file=sys.stderr)
            continue
        repos.extend(got)
    return repos


# --------------------------------------------------------------------------
# Workbook
# --------------------------------------------------------------------------

def parse_ts(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def build_workbook(global_rows, capped, mine, repos, owners, labels, out_path):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    header_fill = PatternFill("solid", fgColor="1F3864")
    header_font = Font(color="FFFFFF", bold=True)
    open_fill = PatternFill("solid", fgColor="FFF2CC")    # amber: needs attention
    closed_fill = PatternFill("solid", fgColor="E2EFDA")  # green: done
    link_font = Font(color="0563C1", underline="single")

    def style(ws, widths):
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(vertical="center")
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    def link_cell(ws, row, col, url):
        c = ws.cell(row=row, column=col)
        c.hyperlink = url
        c.value = "open"
        c.font = link_font

    now = datetime.now(timezone.utc)
    wb = Workbook()

    # --- Sheet 1: all public repos, most popular first ---------------------
    ws = wb.active
    ws.title = "All public repos"
    ws.append(["Repo", "Stars", "Language", "#", "Title", "Labels", "Comments",
               "Good first issue", "Created", "Updated", "Age (days)", "Link"])
    for r in global_rows:
        created = parse_ts(r["createdAt"])
        gfi = any("good first issue" in l.lower() or "good-first-issue" in l.lower()
                  or "help wanted" in l.lower() for l in r["labels"])
        ws.append([
            r["repo"],
            r["stars"] if r["stars"] is not None else "",
            r["language"],
            r["number"],
            r["title"],
            ", ".join(r["labels"]),
            r["comments"],
            "yes" if gfi else "",
            created.strftime("%Y-%m-%d") if created else "",
            parse_ts(r["updatedAt"]).strftime("%Y-%m-%d") if r["updatedAt"] else "",
            (now - created).days if created else "",
            r["url"],
        ])
        link_cell(ws, ws.max_row, 12, r["url"])
    style(ws, [34, 8, 12, 7, 58, 30, 10, 16, 12, 12, 11, 8])

    # --- Sheet 2: your own repos ------------------------------------------
    ws2 = wb.create_sheet("My repos")
    ws2.append(["Repo", "#", "Title", "State", "Labels", "Assignee", "Comments",
                "Created", "Updated", "Age (days)", "Link"])
    # Open first, then most recently updated: the top of the sheet is the work.
    mine.sort(key=lambda i: (i["state"] != "open", -parse_ts(i["updatedAt"]).timestamp()))
    for i in mine:
        created = parse_ts(i["createdAt"])
        ws2.append([
            i["repo"], i["number"], i["title"], i["state"],
            ", ".join(i["labels"]), i["assignee"], i["comments"],
            created.strftime("%Y-%m-%d") if created else "",
            parse_ts(i["updatedAt"]).strftime("%Y-%m-%d") if i["updatedAt"] else "",
            (now - created).days if created else "",
            i["url"],
        ])
        row = ws2.max_row
        fill = open_fill if i["state"] == "open" else closed_fill
        for c in range(1, 12):
            ws2.cell(row=row, column=c).fill = fill
        link_cell(ws2, row, 11, i["url"])
    style(ws2, [30, 6, 58, 8, 32, 16, 10, 12, 12, 11, 8])

    # --- Sheet 3: your repo rollup ----------------------------------------
    ws3 = wb.create_sheet("My repo rollup")
    ws3.append(["Repo", "Stars", "Open a11y", "Closed a11y", "Total",
                "Private", "Archived", "Repo updated", "Link"])
    counts = {}
    for i in mine:
        b = counts.setdefault(i["repo"], {"open": 0, "closed": 0})
        b["open" if i["state"] == "open" else "closed"] += 1
    for repo in sorted(repos, key=lambda r: (
            -counts.get(r["full_name"], {"open": 0})["open"],
            -r.get("stargazers_count", 0),
            r["full_name"].lower())):
        c = counts.get(repo["full_name"], {"open": 0, "closed": 0})
        updated = parse_ts(repo.get("updated_at"))
        ws3.append([
            repo["full_name"], repo.get("stargazers_count", 0),
            c["open"], c["closed"], c["open"] + c["closed"],
            "yes" if repo.get("private") else "no",
            "yes" if repo.get("archived") else "no",
            updated.strftime("%Y-%m-%d") if updated else "",
            repo["html_url"],
        ])
        if c["open"]:
            for col in range(1, 10):
                ws3.cell(row=ws3.max_row, column=col).fill = open_fill
        link_cell(ws3, ws3.max_row, 9, repo["html_url"])
    style(ws3, [34, 8, 11, 12, 8, 9, 10, 14, 8])

    # --- Sheet 4: run metadata --------------------------------------------
    ws4 = wb.create_sheet("Run info")
    open_mine = sum(1 for i in mine if i["state"] == "open")
    notes = [
        ("Last run (UTC)", now.strftime("%Y-%m-%d %H:%M")),
        ("Owners scanned", ", ".join(owners)),
        ("Labels matched", ", ".join(labels)),
        ("Signed in", "yes (private repos included)" if TOKEN else "no (public data only)"),
        ("Public issues listed", len(global_rows)),
        ("Public sample", "most-commented open accessibility issues, then sorted by stars"),
        ("Popularity metric", "repo stars (GitHub does not expose download counts)"),
        ("Your repos scanned", len(repos)),
        ("Your issues found", f"{len(mine)} ({open_mine} open)"),
    ]
    if capped:
        notes.append(("Note", f"star counts fetched for the top {ANON_STAR_LOOKUPS} repos "
                              f"only; sign in to rank them all"))
    for k, v in notes:
        ws4.append([k, v])
    for cell in ws4["A"]:
        cell.font = Font(bold=True)
    ws4.column_dimensions["A"].width = 22
    ws4.column_dimensions["B"].width = 70

    wb.save(out_path)
    return open_mine


# --------------------------------------------------------------------------

def main():
    global TOKEN

    ap = argparse.ArgumentParser(
        description="Track accessibility-labeled GitHub issues in a spreadsheet.")
    ap.add_argument("--owner", default=None,
                    help="GitHub user or org (comma-separated for several)")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output .xlsx path")
    ap.add_argument("--labels", default=",".join(DEFAULT_LABELS),
                    help="comma-separated label spellings to match")
    ap.add_argument("--global-limit", type=int, default=300,
                    help="how many public issues to pull (max 1000, default 300)")
    ap.add_argument("--no-global", action="store_true",
                    help="skip the all-public-repos sheet")
    args = ap.parse_args()

    try:
        import openpyxl  # noqa: F401
    except ImportError:
        sys.exit("Missing dependency. Install it with:\n  python3 -m pip install --user openpyxl")

    TOKEN = resolve_token()

    owner_arg = args.owner or os.environ.get("A11Y_OWNER")
    if not owner_arg and TOKEN:
        who = request(f"{API}/user")
        owner_arg = (who or {}).get("login")
    if not owner_arg:
        sys.exit("Which GitHub account should I scan? Pass --owner <username>.")
    owners = [o.strip() for o in owner_arg.split(",") if o.strip()]
    labels = [l.strip() for l in args.labels.split(",") if l.strip()]
    out_path = os.path.expanduser(args.out)

    print(f"Scanning {', '.join(owners)}" + ("" if TOKEN else " (not signed in, public data only)"))

    global_rows, capped = ([], False)
    if not args.no_global:
        global_rows, capped = search_global(labels, min(args.global_limit, 1000))
        print(f"  {len(global_rows)} open accessibility issues across public GitHub")

    mine = search_owner_issues(owners, labels)
    repos = fetch_owner_repos(owners)
    open_mine = build_workbook(global_rows, capped, mine, repos, owners, labels, out_path)

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[{stamp}] your repos: {len(mine)} items ({open_mine} open) across "
          f"{len(repos)} repos -> {out_path}")


if __name__ == "__main__":
    main()
