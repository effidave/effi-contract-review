#!/usr/bin/env python3
"""
save_blocks.py - Save edited blocks back to a Word document

Sprint 2: WYSIWYG Editor save functionality

This script takes edited blocks from the webview editor and applies
the changes to the original .docx document using native w14:paraId
to identify which paragraphs to update.

Usage:
    python save_blocks.py <document_path> <blocks_json_path>

Input JSON format:
    [
        {
            "id": "block-uuid",
            "text": "Updated paragraph text",
            "runs": [
                {"start": 0, "end": 5, "formats": ["bold"]},
                {"start": 5, "end": 10, "formats": []}
            ]
        },
        ...
    ]

Output JSON format:
    {
        "success": true,
        "block_count": 3,
        "message": "Saved 3 blocks to document"
    }
    or
    {
        "success": false,
        "error": "Error message"
    }
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

from effilocal.doc.uuid_embedding import (
    extract_block_uuids, 
    find_paragraph_by_para_id,
    ParaKey, 
    TableCellKey,
)


def get_paragraph_by_para_id(doc, para_id: str):
    """
    Get a paragraph element from the document by its w14:paraId.
    
    This uses Word's native paragraph IDs which are preserved across
    save/close/reopen cycles.
    
    Args:
        doc: Document object
        para_id: The 8-character hex paraId to find
        
    Returns:
        Paragraph object or None if not found
    """
    return find_paragraph_by_para_id(doc, para_id)


def get_paragraph_by_key(doc, key):
    """
    Get a paragraph element from the document by its BlockKey.
    
    This is a fallback for when UUID lookup fails.
    
    Args:
        doc: Document object
        key: ParaKey or TableCellKey
    
    Returns:
        Paragraph object or None if not found
    """
    if isinstance(key, ParaKey):
        if 0 <= key.para_idx < len(doc.paragraphs):
            return doc.paragraphs[key.para_idx]
    elif isinstance(key, TableCellKey):
        if 0 <= key.table_idx < len(doc.tables):
            table = doc.tables[key.table_idx]
            try:
                cell = table.cell(key.row, key.col)
                if cell.paragraphs:
                    return cell.paragraphs[0]
            except IndexError:
                pass
    return None


def apply_formatting(run, formats):
    """Apply formatting to a run based on format list."""
    run.bold = 'bold' in formats
    run.italic = 'italic' in formats
    run.underline = 'underline' in formats


def update_paragraph_content(paragraph, block):
    """
    Update a paragraph's content based on block data.
    
    Replaces all runs in the paragraph with new runs based on the
    block's text and runs formatting structure.
    """
    text = block.get('text', '')
    runs_data = block.get('runs', [])
    
    # If no runs data, treat the whole text as unformatted
    if not runs_data:
        runs_data = [{'start': 0, 'end': len(text), 'formats': []}]
    
    # Clear existing runs (but preserve paragraph properties)
    for run in paragraph.runs:
        run.text = ''
    
    # Remove empty runs
    p = paragraph._p
    for r in list(p.findall(qn('w:r'))):
        t_elements = r.findall(qn('w:t'))
        if not t_elements or all(not (t.text or '') for t in t_elements):
            # Keep at least one run for formatting
            pass
    
    # Clear all run text first
    paragraph.clear()
    
    # Add new runs with formatting
    for run_data in runs_data:
        start = run_data.get('start', 0)
        end = run_data.get('end', len(text))
        formats = run_data.get('formats', [])
        
        run_text = text[start:end]
        if run_text:  # Only add non-empty runs
            run = paragraph.add_run(run_text)
            apply_formatting(run, formats)


def update_blocks_jsonl(analysis_dir: Path, edited_blocks: list):
    """
    Update blocks.jsonl with edited block content.
    
    Reads the existing blocks.jsonl, updates matching blocks with new text/runs,
    and writes back.
    
    Args:
        analysis_dir: Path to analysis directory containing blocks.jsonl
        edited_blocks: List of edited block dicts with id, text, runs
    """
    blocks_path = analysis_dir / 'blocks.jsonl'
    if not blocks_path.exists():
        return
    
    # Create id -> edited block mapping
    edited_by_id = {b['id']: b for b in edited_blocks}
    
    # Read existing blocks
    existing_blocks = []
    with open(blocks_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                existing_blocks.append(json.loads(line))
    
    # Update matching blocks
    for block in existing_blocks:
        if block.get('id') in edited_by_id:
            edited = edited_by_id[block['id']]
            block['text'] = edited.get('text', block.get('text', ''))
            if 'runs' in edited:
                block['runs'] = edited['runs']
    
    # Write back
    with open(blocks_path, 'w', encoding='utf-8') as f:
        for block in existing_blocks:
            f.write(json.dumps(block, ensure_ascii=False) + '\n')


def save_blocks_to_document(doc_path: str, blocks_path: str):
    """
    Save edited blocks to a Word document.
    
    Args:
        doc_path: Path to the .docx document
        blocks_path: Path to JSON file containing edited blocks
    
    Returns:
        dict with success status and details
    """
    import sys
    
    try:
        # Load blocks
        with open(blocks_path, 'r', encoding='utf-8') as f:
            blocks = json.load(f)
        
        # Debug: log what we received
        print(f"DEBUG: Received {len(blocks)} blocks to save", file=sys.stderr)
        if blocks:
            print(f"DEBUG: First block id: {blocks[0].get('id', 'NO ID')}", file=sys.stderr)
            print(f"DEBUG: First block para_id: {blocks[0].get('para_id', 'NO PARA_ID')}", file=sys.stderr)
            print(f"DEBUG: First block text (first 50 chars): {blocks[0].get('text', '')[:50]}", file=sys.stderr)
        
        if not blocks:
            return {"success": True, "block_count": 0, "message": "No blocks to save"}
        
        # Load document
        doc = Document(doc_path)
        
        # Extract para_id -> paragraph mapping (uses native Word w14:paraId)
        para_id_map = extract_block_uuids(doc)
        
        if not para_id_map:
            return {
                "success": False,
                "error": "No paragraph IDs found in document."
            }
        
        # Track updates
        updated_count = 0
        not_found = []

        # Update paragraphs - find by para_id (w14:paraId)
        for block in blocks:
            block_id = block.get('id', '')
            para_id = block.get('para_id', '')

            # Primary: look up by native Word para_id (8-char hex)
            paragraph = None
            if para_id:
                paragraph = get_paragraph_by_para_id(doc, para_id)

            if paragraph:
                update_paragraph_content(paragraph, block)
                updated_count += 1
            elif para_id and para_id in para_id_map:
                # Fall back to key-based lookup using position
                key = para_id_map[para_id]
                paragraph = get_paragraph_by_key(doc, key)
                if paragraph:
                    update_paragraph_content(paragraph, block)
                    updated_count += 1
                else:
                    not_found.append(f"{block_id} (para_id={para_id}, key={key})")
            else:
                not_found.append(f"{block_id} (no para_id)")
        
        # Save document
        doc.save(doc_path)
        
        # Also update blocks.jsonl so the UI stays in sync
        # The temp blocks file is in the analysis directory
        temp_blocks_dir = Path(blocks_path).parent
        update_blocks_jsonl(temp_blocks_dir, blocks)
        
        result = {
            "success": True,
            "block_count": updated_count,
            "message": f"Saved {updated_count} block(s) to document"
        }
        
        if not_found:
            result["warnings"] = f"Could not find paragraphs for: {', '.join(not_found[:5])}"
            if len(not_found) > 5:
                result["warnings"] += f" and {len(not_found) - 5} more"
        
        return result
        
    except FileNotFoundError as e:
        return {"success": False, "error": f"File not found: {e}"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            "success": False,
            "error": "Usage: save_blocks.py <document_path> <blocks_json_path>"
        }))
        sys.exit(1)
    
    doc_path = sys.argv[1]
    blocks_path = sys.argv[2]
    
    result = save_blocks_to_document(doc_path, blocks_path)
    print(json.dumps(result))
    
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
