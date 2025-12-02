#!/usr/bin/env python3
"""
embed_uuids.py - Embed block UUIDs into a Word document

This script reads blocks.jsonl and embeds the UUIDs as paragraph tags
(w:pPr/w:tag) in the corresponding .docx document. This enables the 
save flow to identify which paragraphs to update.

Usage:
    python embed_uuids.py <document_path> <blocks_jsonl_path>

Output JSON format:
    {
        "success": true,
        "embedded_count": 45,
        "message": "Embedded 45 UUIDs into document"
    }
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from docx import Document
from effilocal.doc.uuid_embedding import embed_block_uuids


def load_blocks_jsonl(blocks_path: str) -> list[dict]:
    """Load blocks from JSONL file."""
    blocks = []
    with open(blocks_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                blocks.append(json.loads(line))
    return blocks


def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            "success": False,
            "error": "Usage: embed_uuids.py <document_path> <blocks_jsonl_path>"
        }))
        sys.exit(1)
    
    doc_path = sys.argv[1]
    blocks_path = sys.argv[2]
    
    try:
        # Load blocks
        blocks = load_blocks_jsonl(blocks_path)
        
        if not blocks:
            print(json.dumps({
                "success": False,
                "error": "No blocks found in blocks.jsonl"
            }))
            sys.exit(1)
        
        # Embed UUIDs
        result = embed_block_uuids(doc_path, blocks)
        
        print(json.dumps({
            "success": True,
            "embedded_count": len(result),
            "message": f"Embedded {len(result)} UUIDs into document"
        }))
        sys.exit(0)
        
    except FileNotFoundError as e:
        print(json.dumps({"success": False, "error": f"File not found: {e}"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == '__main__':
    main()
