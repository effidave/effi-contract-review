#!/usr/bin/env python3
"""
embed_uuids.py - DEPRECATED: No longer needed

Block identification now uses Word's native w14:paraId attribute, which is 
already present on every paragraph. No embedding is required.

This script is kept for backward compatibility but is effectively a no-op.
It reads blocks.jsonl and reports success without modifying the document.

Usage:
    python embed_uuids.py <document_path> <blocks_jsonl_path>

Output JSON format:
    {
        "success": true,
        "embedded_count": 45,
        "message": "Using native w14:paraId - no embedding required (45 blocks)"
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
        
        # No embedding needed - we use native w14:paraId
        # Just report the number of blocks with para_ids
        blocks_with_para_id = sum(1 for b in blocks if b.get("para_id"))
        
        print(json.dumps({
            "success": True,
            "embedded_count": blocks_with_para_id,
            "message": f"Using native w14:paraId - no embedding required ({blocks_with_para_id} blocks)"
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
