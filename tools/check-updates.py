#!/usr/bin/env python3
"""List third-party skills and agents from sources.json that changed upstream.

Usage: python3 tools/check-updates.py
Needs the GitHub CLI (`gh auth login`). It only reads and reports; it changes nothing.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def latest_commit(repo, path):
    query = f"repos/{repo}/commits?per_page=1" + (f"&path={path}" if path else "")
    out = subprocess.run(["gh", "api", query, "-q", ".[0].sha"], capture_output=True, text=True)
    return out.stdout.strip() or None


def is_newer(repo, pinned, latest):
    """True if `latest` is ahead of `pinned`. The latest commit touching a path is often older
    than the pinned repo HEAD, and that does not count as an update."""
    out = subprocess.run(["gh", "api", f"repos/{repo}/compare/{pinned}...{latest}", "-q", ".status"],
                         capture_output=True, text=True)
    return out.stdout.strip() in ("ahead", "diverged")


def main():
    items = json.loads((ROOT / "sources.json").read_text())["items"]
    outdated = 0
    for item in items:
        latest = latest_commit(item["repo"], item["path"])
        pinned = item["commit"]
        if latest is None:
            status = "ERROR  could not read upstream"
        elif pinned is None:
            status = f"UNPINNED  latest {latest[:7]}"
        elif latest == pinned or not is_newer(item["repo"], pinned, latest):
            status = "ok"
        else:
            outdated += 1
            status = (f"UPDATE  {pinned[:7]} -> {latest[:7]}  "
                      f"https://github.com/{item['repo']}/compare/{pinned[:12]}...{latest[:12]}")
        print(f"{item['name']:<28} {status}")
    print(f"\n{outdated} with upstream changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
