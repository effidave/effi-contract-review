"""
Document tools for effilocal MCP server.

This module extends word_document_server.tools.document_tools with:
1. Markdown export functionality (save_document_as_markdown)

Override Pattern:
- Import all upstream functions
- Add new functions
"""

import os
import json
from typing import Dict, List, Optional, Any

# Import all upstream functions (pass-through)
from word_document_server.tools.document_tools import (
    create_document,
    get_document_info,
    get_document_text,
    get_document_outline,
    list_available_documents,
    create_document_copy,
)

from word_document_server.utils.file_utils import ensure_docx_extension


# ============================================================================
# NEW Functions (effilocal-specific)
# ============================================================================

async def save_document_as_markdown(filename: str) -> str:
    """Extract all text from a Word document and save as a Markdown (.md) file with the same base name.
    
    NEW function - exports Word document to Markdown format.
    
    This tool:
    - Extracts document outline (headings, tables)
    - Converts headings to Markdown format (# ## ###)
    - Exports tables as Markdown tables
    - Saves with automatic naming (appends suffix if file exists)
    
    Args:
        filename: Path to the Word document
        
    Returns:
        Success message with markdown file path
    """
    filename = ensure_docx_extension(filename)
    
    if not os.path.exists(filename):
        return f"Document {filename} does not exist"
    
    base_name = os.path.splitext(os.path.basename(filename))[0]
    doc_dir = os.path.dirname(os.path.abspath(filename))
    md_filename = os.path.join(doc_dir, base_name + ".md")
    
    # If file exists, append a numeric suffix
    if os.path.exists(md_filename):
        suffix = 1
        while True:
            alt_md_filename = os.path.join(doc_dir, f"{base_name}_{suffix}.md")
            if not os.path.exists(alt_md_filename):
                md_filename = alt_md_filename
                break
            suffix += 1
    
    try:
        # Get outline for headings/tables
        outline_json = await get_document_outline(filename)
        outline = json.loads(outline_json) if isinstance(outline_json, str) else outline_json
        
        # Get full text content
        text_content = await get_document_text(filename)
        
        md_lines = []
        
        # Add headings from outline
        for para in outline.get("paragraphs", []):
            style = para.get("style", "Normal")
            text = para.get("text", "")
            
            if style.startswith("Heading"):
                try:
                    level = int(style.split(" ")[-1])
                except Exception:
                    level = 1
                md_lines.append("#" * level + " " + text)
            elif style == "Title":
                md_lines.append(f"# {text}")
            elif style == "Subtitle":
                md_lines.append(f"## {text}")
        
        # Add main text content
        md_lines.append(text_content)
        
        # Add tables as Markdown
        for table in outline.get("tables", []):
            rows = table.get("rows", 0)
            cols = table.get("columns", 0)
            preview = table.get("preview", [])
            
            if preview:
                header = preview[0] if len(preview) > 0 else ["Header"] * cols
                md_lines.append("| " + " | ".join(header) + " |")
                md_lines.append("| " + " | ".join(["---"] * len(header)) + " |")
                
                for row in preview[1:]:
                    md_lines.append("| " + " | ".join(row) + " |")
        
        md_text = "\n".join(md_lines)
        
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(md_text)
        
        return f"Saved document text to {md_filename}"
    
    except Exception as e:
        return f"Failed to save markdown: {str(e)}"


# ============================================================================
# Re-export all functions for compatibility
# ============================================================================

__all__ = [
    # Pass-through functions (unchanged from upstream)
    'create_document',
    'get_document_info',
    'get_document_text',
    'get_document_outline',
    'list_available_documents',
    'create_document_copy',
    
    # New functions (effilocal-specific)
    'save_document_as_markdown',
]
