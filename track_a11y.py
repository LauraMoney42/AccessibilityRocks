#!/usr/bin/env python3
"""
Accessibility issue tracker.

Polls the GitHub API (through the authenticated `gh` CLI) for every issue in one or
more owners' repos that carries an accessibility-style label, and writes the results
to a formatted Excel workbook.

Why `gh` instead of raw requests: `gh` already holds a valid OAuth token, so there is
no separate secret for a user of this tool to create, store, or rotate.

Usage:
    python3 track_a11y.py                        # uses your own gh login
    python3 track_a11y.py --owner someuser
    python3 track_a11y.py --owner me,my-org      # several owners in one sheet
    python3 track_a11y.py --out ~/Desktop/a11y.xlsx
    python3 track_a11y.py --labels accessibility,a11y,ux-a11y
    python3 track_a11y.py --no-label-audit       # skip the per-repo label check
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

# Label spellings that all mean "accessibility". GitHub label search is
# case-insensitive but not fuzzy, so each variant needs its own query.
DEFAULT_LABELS = [
    "accessibility",
    "a11y",
    "accessibility-issue",
    "accessibility issue",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(SCRIPT_DIR, "accessibility-issues.xlsx")


# --------------------------------------------------------------------------
# Preflight
# --------------------------------------------------------------------------

def preflight():
    """Fail with an actionable message instead of a stack trace."""
    if shutil.which("gh") is None:
        sys.exit(
            "GitHub CLI not found.\n"
            "  macOS:  brew install gh\n"
            "  Linux:  https://github.com/cli/cli#installation\n"
            "Then run: gh auth login"
        )

    status = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if status.returncode != 0:
        sys.exit("Not logged in to GitHub. Run: gh auth login")

    try:
        import openpyxl  # noqa: F401
    except ImportError:
        sys.exit(
            "Missing dependency openpyxl. Install it with:\n"
            "  python3 -m pip install --user openpyxl"
        )


def current_login():
    """The logged-in gh user, used when --owner is not supplied."""
    proc = subprocess.run(["gh", "api", "user", "--jq", ".login"],
                          capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else None


# --------------------------------------------------------------------------
# GitHub queries
# --------------------------------------------------------------------------

def gh(args, allow_fail=False):
    """Run a gh command and return parsed JSON (or None when allow_fail and it errors)."""
    proc = subprocess.run(["gh"] + args, capture_output=True, text=True)
    if proc.returncode != 0:
        if allow_fail:
            return None
        sys.exit(f"gh {' '.join(args)} failed:\n{proc.stderr.strip()}")
    out = proc.stdout.strip()
    return json.loads(out) if out else []


def fetch_issues(owners, labels):
    """Search every owner x label combination and merge on repo+number."""
    fields = ("number,repository,title,state,labels,createdAt,updatedAt,"
              "url,assignees,isPullRequest,commentsCount")
    merged = {}
    for owner in owners:
        for label in labels:
            # No --state flag: gh only accepts open|closed there, and omitting it
            # returns both, which is what we want for the closed-item history.
            rows = gh([
                "search", "issues",
                "--owner", owner,
                "--label", label,
                "--limit", "1000",
                "--json", fields,
            ], allow_fail=True) or []
            for row in rows:
                merged[(row["repository"]["nameWithOwner"], row["number"])] = row
    return list(merged.values())


def fetch_repos(owners, labels, label_audit=True):
    repos = []
    for owner in owners:
        found = gh([
            "repo", "list", owner,
            "--limit", "500",
            "--json", "name,nameWithOwner,url,updatedAt,isPrivate,isArchived",
        ], allow_fail=True)
        if found is None:
            print(f"  warning: could not list repos for '{owner}' (typo, or no access)",
                  file=sys.stderr)
            continue
        repos.extend(found)

    if not label_audit:
        for r in repos:
            r["a11yLabels"] = None
        return repos

    wanted = {l.lower().replace(" ", "-") for l in labels}

    def labels_for(repo):
        data = gh(["api", f"repos/{repo['nameWithOwner']}/labels", "--paginate"],
                  allow_fail=True) or []
        names = [lbl["name"] for lbl in data]
        repo["a11yLabels"] = [
            n for n in names
            if n.lower().replace("_", "-").replace(" ", "-") in wanted
            or "accessib" in n.lower()
            or n.lower() == "a11y"
        ]
        return repo

    # 8 workers keeps us well under the 5000 req/hr REST limit while staying quick.
    with ThreadPoolExecutor(max_workers=8) as pool:
        repos = list(pool.map(labels_for, repos))
    return repos


# --------------------------------------------------------------------------
# Workbook
# --------------------------------------------------------------------------

def parse_ts(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def build_workbook(issues, repos, owners, labels, out_path):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    header_fill = PatternFill("solid", fgColor="1F3864")
    header_font = Font(color="FFFFFF", bold=True)
    open_fill = PatternFill("solid", fgColor="FFF2CC")    # amber: needs attention
    closed_fill = PatternFill("solid", fgColor="E2EFDA")  # green: done
    link_font = Font(color="0563C1", underline="single")

    def style_sheet(ws, widths):
        for idx, width in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(idx)].width = width
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(vertical="center")
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    now = datetime.now(timezone.utc)
    wb = Workbook()

    # --- Sheet 1: every accessibility issue -------------------------------
    ws = wb.active
    ws.title = "Issues"
    ws.append(["Repo", "#", "Title", "State", "Type", "Labels", "Assignee",
               "Comments", "Created", "Updated", "Age (days)", "Link"])

    # Open items first, then most recently updated, so the top of the sheet is
    # always the actionable part.
    issues.sort(key=lambda i: (i["state"] != "open", -parse_ts(i["updatedAt"]).timestamp()))

    for issue in issues:
        created = parse_ts(issue["createdAt"])
        updated = parse_ts(issue["updatedAt"])
        ws.append([
            issue["repository"]["nameWithOwner"],
            issue["number"],
            issue["title"],
            issue["state"],
            "PR" if issue.get("isPullRequest") else "Issue",
            ", ".join(lbl["name"] for lbl in issue.get("labels") or []),
            ", ".join(a["login"] for a in issue.get("assignees") or []) or "-",
            issue.get("commentsCount", 0),
            created.strftime("%Y-%m-%d") if created else "",
            updated.strftime("%Y-%m-%d") if updated else "",
            (now - created).days if created else "",
            issue["url"],
        ])
        r = ws.max_row
        fill = open_fill if issue["state"] == "open" else closed_fill
        for c in range(1, 13):
            ws.cell(row=r, column=c).fill = fill
        link = ws.cell(row=r, column=12)
        link.hyperlink = issue["url"]
        link.value = "open"
        link.font = link_font

    style_sheet(ws, [30, 6, 60, 8, 8, 34, 16, 10, 12, 12, 11, 8])

    # --- Sheet 2: repo rollup ---------------------------------------------
    ws2 = wb.create_sheet("Repos")
    ws2.append(["Repo", "Open a11y", "Closed a11y", "Total",
                "a11y label defined", "Private", "Archived", "Repo updated", "Link"])

    counts = {}
    for issue in issues:
        name = issue["repository"]["nameWithOwner"]
        bucket = counts.setdefault(name, {"open": 0, "closed": 0})
        bucket["open" if issue["state"] == "open" else "closed"] += 1

    def sort_key(repo):
        c = counts.get(repo["nameWithOwner"], {"open": 0, "closed": 0})
        return (-c["open"], -c["closed"], repo["nameWithOwner"].lower())

    for repo in sorted(repos, key=sort_key):
        c = counts.get(repo["nameWithOwner"], {"open": 0, "closed": 0})
        repo_labels = repo.get("a11yLabels")
        updated = parse_ts(repo.get("updatedAt"))
        ws2.append([
            repo["nameWithOwner"],
            c["open"],
            c["closed"],
            c["open"] + c["closed"],
            ", ".join(repo_labels) if repo_labels
            else ("none" if repo_labels is not None else "not checked"),
            "yes" if repo.get("isPrivate") else "no",
            "yes" if repo.get("isArchived") else "no",
            updated.strftime("%Y-%m-%d") if updated else "",
            repo["url"],
        ])
        r = ws2.max_row
        if c["open"]:
            for col in range(1, 10):
                ws2.cell(row=r, column=col).fill = open_fill
        link = ws2.cell(row=r, column=9)
        link.hyperlink = repo["url"]
        link.value = "open"
        link.font = link_font

    style_sheet(ws2, [34, 11, 12, 8, 26, 9, 10, 14, 8])

    # --- Sheet 3: run metadata --------------------------------------------
    ws3 = wb.create_sheet("Run info")
    open_count = sum(1 for i in issues if i["state"] == "open")
    for k, v in [
        ("Last run (UTC)", now.strftime("%Y-%m-%d %H:%M")),
        ("Owners scanned", ", ".join(owners)),
        ("Label variants", ", ".join(labels)),
        ("Repos scanned", len(repos)),
        ("Issues found", len(issues)),
        ("Open", open_count),
        ("Closed", len(issues) - open_count),
    ]:
        ws3.append([k, v])
    for cell in ws3["A"]:
        cell.font = Font(bold=True)
    ws3.column_dimensions["A"].width = 22
    ws3.column_dimensions["B"].width = 60

    wb.save(out_path)
    return open_count


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Track accessibility-labeled GitHub issues in a spreadsheet.")
    ap.add_argument("--owner", default=None,
                    help="GitHub user or org (comma-separated for several). "
                         "Defaults to your gh login.")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output .xlsx path")
    ap.add_argument("--labels", default=",".join(DEFAULT_LABELS),
                    help="comma-separated label spellings to search")
    ap.add_argument("--no-label-audit", action="store_true",
                    help="skip the per-repo label listing (one fewer API call per repo)")
    args = ap.parse_args()

    preflight()

    owner_arg = args.owner or os.environ.get("A11Y_OWNER") or current_login()
    if not owner_arg:
        sys.exit("Could not determine a GitHub owner. Pass --owner <username>.")
    owners = [o.strip() for o in owner_arg.split(",") if o.strip()]
    labels = [l.strip() for l in args.labels.split(",") if l.strip()]

    out_path = os.path.expanduser(args.out)
    issues = fetch_issues(owners, labels)
    repos = fetch_repos(owners, labels, label_audit=not args.no_label_audit)
    if not repos:
        sys.exit(f"No repos found for: {', '.join(owners)}")

    open_count = build_workbook(issues, repos, owners, labels, out_path)

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[{stamp}] {len(issues)} accessibility items ({open_count} open) "
          f"across {len(repos)} repos -> {out_path}")


if __name__ == "__main__":
    main()
