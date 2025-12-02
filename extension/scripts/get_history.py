#!/usr/bin/env python
"""Script to get git version history for a document.

Usage:
    get_history.py <docx_path> [--max <count>]

Outputs JSON list of commits to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from effilocal.util.git_ops import (
    get_file_history,
    get_effi_commits,
    get_repo_root,
    is_git_repo,
)


def main():
    parser = argparse.ArgumentParser(description="Get document version history")
    parser.add_argument("docx_path", type=Path, help="Path to .docx file")
    parser.add_argument("--max", type=int, default=50, help="Maximum commits to return")
    parser.add_argument("--effi-only", action="store_true", help="Only show effi commits")

    args = parser.parse_args()

    docx_path = Path(args.docx_path)

    if not docx_path.exists():
        print(json.dumps({"success": False, "error": f"File not found: {docx_path}"}))
        return

    repo_root = get_repo_root(docx_path.parent)
    if not repo_root:
        print(json.dumps({"success": False, "error": "Not in a git repository"}))
        return

    if args.effi_only:
        commits = get_effi_commits(repo_root, max_commits=args.max)
    else:
        commits = get_file_history(repo_root, docx_path, max_commits=args.max)

    output = {
        "success": True,
        "repo_root": str(repo_root),
        "file": str(docx_path),
        "commits": [c.to_dict() for c in commits],
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
