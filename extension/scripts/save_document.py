#!/usr/bin/env python
"""Script to save document with UUID embedding and optional git commit.

Usage:
    save_document.py <docx_path> <analysis_dir> [--no-commit] [--message <msg>]
    save_document.py checkpoint <docx_path> <analysis_dir> [--note <note>]

Outputs JSON result to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from effilocal.flows.save_doc import save_with_uuids, create_checkpoint


def main():
    parser = argparse.ArgumentParser(description="Save document with UUIDs")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Save command
    save_parser = subparsers.add_parser("save", help="Save document with UUIDs")
    save_parser.add_argument("docx_path", type=Path, help="Path to .docx file")
    save_parser.add_argument("analysis_dir", type=Path, help="Path to analysis directory")
    save_parser.add_argument("--no-commit", action="store_true", help="Skip git commit")
    save_parser.add_argument("--message", "-m", type=str, help="Custom commit message")

    # Checkpoint command
    checkpoint_parser = subparsers.add_parser("checkpoint", help="Create checkpoint commit")
    checkpoint_parser.add_argument("docx_path", type=Path, help="Path to .docx file")
    checkpoint_parser.add_argument("analysis_dir", type=Path, help="Path to analysis directory")
    checkpoint_parser.add_argument("--note", "-n", type=str, default="", help="Checkpoint note")

    args = parser.parse_args()

    if args.command == "checkpoint":
        result = create_checkpoint(
            args.docx_path,
            analysis_dir=args.analysis_dir,
            note=args.note,
        )
    else:
        # Default to save
        result = save_with_uuids(
            args.docx_path if hasattr(args, 'docx_path') else Path(sys.argv[1]),
            analysis_dir=args.analysis_dir if hasattr(args, 'analysis_dir') else Path(sys.argv[2]),
            auto_git=not getattr(args, 'no_commit', False),
            commit_message=getattr(args, 'message', None),
        )

    output = result.to_dict()
    print(json.dumps(output))


if __name__ == "__main__":
    main()
