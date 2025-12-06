#!/usr/bin/env python3
"""
save_blocks.py - Save edited blocks back to a Word document

Sprint 2: WYSIWYG Editor save functionality

This script takes edited blocks from the webview editor and applies
the changes to the original .docx document using native w14:paraId
to identify which paragraphs to update.

Usage:
    python save_blocks.py <document_path> <blocks_json_path>

Input JSON format (text-based model):
    [
        {
            "id": "block-uuid",
            "para_id": "05C9333F",
            "text": "Updated paragraph text",
            "runs": [
                {"text": "Updated ", "formats": ["bold"]},
                {"text": "paragraph text", "formats": []}
            ]
        },
        ...
    ]

Note: Delete runs (with 'delete' in formats) are skipped during save
since they represent deleted content that shouldn't appear in the document.

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
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

from effilocal.doc.uuid_embedding import (
    extract_block_uuids, 
    find_paragraph_by_para_id,
    generate_para_id,
    set_paragraph_para_id,
    collect_all_para_ids,
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


def insert_new_paragraph(doc, block, after_para_id: str, existing_ids: set[str], use_para_id: str = None) -> tuple[str, bool]:
    """
    Insert a new paragraph into the document after the specified paragraph.
    
    Args:
        doc: Document object
        block: Block dict with text and runs
        after_para_id: The para_id of the paragraph to insert after
        existing_ids: Set of existing paraIds for collision checking
        use_para_id: Optional pre-generated para_id to use (from client-side generation)
        
    Returns:
        Tuple of (new_para_id, success)
    """
    # Find the paragraph to insert after
    after_para = find_paragraph_by_para_id(doc, after_para_id)
    if not after_para:
        return (None, False)
    
    # Create new paragraph element
    new_p = OxmlElement('w:p')
    
    # Use provided para_id or generate new one
    if use_para_id and use_para_id.upper() not in existing_ids:
        new_para_id = use_para_id.upper()
    else:
        new_para_id = generate_para_id(existing_ids)
    set_paragraph_para_id(new_p, new_para_id)
    existing_ids.add(new_para_id)
    
    # Copy style from the paragraph we're inserting after
    after_elem = after_para._element
    after_pPr = after_elem.find(qn('w:pPr'))
    if after_pPr is not None:
        # Clone the paragraph properties (excluding numPr to avoid numbering issues)
        new_pPr = OxmlElement('w:pPr')
        for child in after_pPr:
            if child.tag != qn('w:numPr'):  # Don't copy numbering
                # Create a copy of the element
                new_child = OxmlElement(child.tag.split('}')[-1] if '}' in child.tag else child.tag)
                for key, value in child.attrib.items():
                    new_child.set(key, value)
                new_pPr.append(new_child)
        if len(new_pPr) > 0:
            new_p.insert(0, new_pPr)
    
    # Add runs with text and formatting
    runs_data = block.get('runs', [])
    text = block.get('text', '')
    
    if not runs_data:
        runs_data = [{'text': text, 'formats': []}]
    
    for run_data in runs_data:
        formats = run_data.get('formats', [])
        
        # Skip delete runs
        if 'delete' in formats:
            continue
        
        run_text = run_data.get('text', '')
        if not run_text:
            continue
        
        r = OxmlElement('w:r')
        
        # Add run properties for formatting
        if formats:
            rPr = OxmlElement('w:rPr')
            if 'bold' in formats:
                b = OxmlElement('w:b')
                rPr.append(b)
            if 'italic' in formats:
                i = OxmlElement('w:i')
                rPr.append(i)
            if 'underline' in formats:
                u = OxmlElement('w:u')
                u.set(qn('w:val'), 'single')
                rPr.append(u)
            if len(rPr) > 0:
                r.append(rPr)
        
        t = OxmlElement('w:t')
        # Preserve spaces
        if run_text.startswith(' ') or run_text.endswith(' '):
            t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        t.text = run_text
        r.append(t)
        new_p.append(r)
    
    # Insert after the target paragraph
    parent = after_elem.getparent()
    target_position = list(parent).index(after_elem)
    parent.insert(target_position + 1, new_p)
    
    return (new_para_id, True)


def update_paragraph_content(paragraph, block):
    """
    Update a paragraph's content based on block data.
    
    Replaces all runs in the paragraph with new runs based on the
    block's text and runs formatting structure.
    
    Supports both text-based runs (new model) and position-based runs (legacy):
    - Text-based: run has 'text' or 'deleted_text' field
    - Position-based: run has 'start' and 'end' fields
    """
    text = block.get('text', '')
    runs_data = block.get('runs', [])
    
    # If no runs data, treat the whole text as unformatted
    if not runs_data:
        runs_data = [{'text': text, 'formats': []}]
    
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
        formats = run_data.get('formats', [])
        
        # Skip delete runs - they represent deleted content, not visible text
        if 'delete' in formats:
            continue
        
        # Get run text - support both text-based (new) and position-based (legacy) models
        if 'text' in run_data:
            # Text-based model (new)
            run_text = run_data['text']
        elif 'start' in run_data and 'end' in run_data:
            # Position-based model (legacy/editor operations)
            start = run_data.get('start', 0)
            end = run_data.get('end', len(text))
            run_text = text[start:end]
        else:
            # No text content
            run_text = ''
        
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
        
        # Collect all existing paraIds for collision checking when inserting new blocks
        existing_ids = collect_all_para_ids(doc)
        
        if not para_id_map:
            return {
                "success": False,
                "error": "No paragraph IDs found in document."
            }
        
        # Track updates and insertions
        updated_count = 0
        inserted_count = 0
        not_found = []
        
        # Separate blocks into existing (para_id found in document) and new (para_idx=-1 or para_id not in doc)
        existing_blocks = []
        new_blocks = []
        
        for block in blocks:
            para_id = block.get('para_id', '')
            para_idx = block.get('para_idx', 0)
            
            # New blocks have para_idx=-1 (set by editor on split)
            # OR have a para_id that doesn't exist in the document yet
            if para_idx == -1:
                new_blocks.append(block)
            elif para_id and para_id.upper() not in existing_ids:
                # para_id was client-generated but not yet in document
                new_blocks.append(block)
            elif para_id:
                existing_blocks.append(block)
            else:
                # No para_id and non-negative para_idx - shouldn't happen but treat as update attempt
                existing_blocks.append(block)

        # First pass: Update existing paragraphs - find by para_id (w14:paraId)
        for block in existing_blocks:
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
                not_found.append(f"{block_id} (para_id={para_id} not in document)")
        
        # Second pass: Insert new paragraphs (blocks without para_id)
        # These come from editor split operations
        for i, block in enumerate(new_blocks):
            block_id = block.get('id', '')
            
            # Find where to insert: look at previous block in the original blocks list
            block_index = next((j for j, b in enumerate(blocks) if b.get('id') == block_id), -1)
            
            if block_index <= 0:
                # Can't determine insertion point - insert at end
                not_found.append(f"{block_id} (new block, can't determine insertion point)")
                continue
            
            # Get the previous block's para_id
            prev_block = blocks[block_index - 1]
            prev_para_id = prev_block.get('para_id', '')
            
            if not prev_para_id:
                # Previous block also doesn't have para_id - skip for now
                not_found.append(f"{block_id} (new block, previous block also new)")
                continue
            
            # Insert after the previous paragraph, using client-generated para_id if available
            client_para_id = block.get('para_id', '')
            new_para_id, success = insert_new_paragraph(doc, block, prev_para_id, existing_ids, use_para_id=client_para_id)
            
            if success:
                inserted_count += 1
                # Update the block's para_id for future reference
                block['para_id'] = new_para_id
            else:
                not_found.append(f"{block_id} (failed to insert after {prev_para_id})")
        
        # Save document
        doc.save(doc_path)
        
        # Also update blocks.jsonl so the UI stays in sync
        # The temp blocks file is in the analysis directory
        temp_blocks_dir = Path(blocks_path).parent
        update_blocks_jsonl(temp_blocks_dir, blocks)
        
        total_count = updated_count + inserted_count
        message_parts = []
        if updated_count > 0:
            message_parts.append(f"updated {updated_count}")
        if inserted_count > 0:
            message_parts.append(f"inserted {inserted_count}")
        
        result = {
            "success": True,
            "block_count": total_count,
            "updated_count": updated_count,
            "inserted_count": inserted_count,
            "message": f"Saved {total_count} block(s) to document ({', '.join(message_parts)})" if message_parts else "No changes made"
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
