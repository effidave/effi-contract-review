"""
Numbering analysis tools for Word Document Server.

These tools use effilocal's NumberingInspector to provide detailed
numbering analysis of Word documents, including list structure,
counters, formats, and rendered numbers.
"""
import os
from pathlib import Path
from typing import Optional

from word_document_server.utils.file_utils import ensure_docx_extension

try:
    from effilocal.doc.numbering_inspector import NumberingInspector
    EFFILOCAL_AVAILABLE = True
except ImportError:
    EFFILOCAL_AVAILABLE = False


async def analyze_document_numbering(
    filename: str,
    debug: bool = False,
    include_non_numbered: bool = False,
) -> str:
    """
    Analyze the numbering structure of a Word document.
    
    Uses effilocal's NumberingInspector to produce a detailed analysis of:
    - Numbered paragraphs (lists, outlines, etc.)
    - Numbering formats (decimal, roman, bullets, etc.)
    - Counter values and rendered numbers
    - Numbering hierarchy and levels
    
    Args:
        filename: Path to the Word document
        debug: If True, include additional debug information
        include_non_numbered: If True, include paragraphs without numbering
    
    Returns:
        Formatted string with numbering analysis results
    """
    if not EFFILOCAL_AVAILABLE:
        return (
            "effilocal package not available. Please install it to use numbering analysis.\n"
            "The effilocal package should be in the same workspace."
        )
    
    filename = ensure_docx_extension(filename)
    
    if not os.path.exists(filename):
        return f"Document {filename} does not exist"
    
    try:
        # Create inspector from document
        docx_path = Path(filename)
        inspector = NumberingInspector.from_docx(docx_path)
        
        # Analyze all paragraphs
        rows, debug_rows = inspector.analyze(debug=debug)
        
        if not rows:
            return f"No paragraphs found in {filename}"
        
        # Filter to numbered paragraphs unless include_non_numbered is True
        if not include_non_numbered:
            numbered_rows = [row for row in rows if row.get("rendered_number")]
        else:
            numbered_rows = rows
        
        if not numbered_rows:
            return f"No numbered paragraphs found in {filename}"
        
        # Format the results
        result = f"Numbering Analysis for {filename}\n"
        result += "=" * 80 + "\n\n"
        result += f"Total paragraphs: {len(rows)}\n"
        result += f"Numbered paragraphs: {len([r for r in rows if r.get('rendered_number')])}\n\n"
        
        # Display each numbered paragraph
        for i, row in enumerate(numbered_rows, 1):
            rendered = row.get("rendered_number", "")
            text = row.get("text", "")[:100]  # Truncate long text
            if len(row.get("text", "")) > 100:
                text += "..."
            
            level = row.get("ilvl", 0)
            num_id = row.get("numId", "N/A")
            abstract_num_id = row.get("abstractNumId", "N/A")
            num_fmt = row.get("numFmt", "N/A")
            
            result += f"Paragraph {i}:\n"
            result += f"  Rendered: {rendered}\n"
            result += f"  Level: {level}\n"
            result += f"  Format: {num_fmt}\n"
            result += f"  NumID: {num_id}, AbstractNumID: {abstract_num_id}\n"
            result += f"  Text: {text}\n"
            
            # Add debug info if requested
            if debug and debug_rows and i - 1 < len(debug_rows):
                debug_row = debug_rows[i - 1]
                if debug_row:
                    result += f"  Debug Info:\n"
                    for key, value in debug_row.items():
                        if key not in ["text"]:  # Skip text since we already show it
                            result += f"    {key}: {value}\n"
            
            result += "\n"
        
        return result
    
    except Exception as e:
        return f"Failed to analyze numbering: {str(e)}"


async def get_numbering_summary(filename: str) -> str:
    """
    Get a high-level summary of numbering styles used in a document.
    
    Args:
        filename: Path to the Word document
    
    Returns:
        Summary of numbering styles and their usage
    """
    if not EFFILOCAL_AVAILABLE:
        return (
            "effilocal package not available. Please install it to use numbering analysis.\n"
            "The effilocal package should be in the same workspace."
        )
    
    filename = ensure_docx_extension(filename)
    
    if not os.path.exists(filename):
        return f"Document {filename} does not exist"
    
    try:
        # Create inspector from document
        docx_path = Path(filename)
        inspector = NumberingInspector.from_docx(docx_path)
        
        # Analyze all paragraphs
        rows, _ = inspector.analyze(debug=False)
        
        if not rows:
            return f"No paragraphs found in {filename}"
        
        # Collect statistics
        numbered_count = 0
        formats_used = {}
        levels_used = {}
        num_ids_used = set()
        
        for row in rows:
            if row.get("rendered_number"):
                numbered_count += 1
                
                # Track format types
                num_fmt = row.get("numFmt", "unknown")
                formats_used[num_fmt] = formats_used.get(num_fmt, 0) + 1
                
                # Track levels
                level = row.get("ilvl", 0)
                levels_used[level] = levels_used.get(level, 0) + 1
                
                # Track num_ids
                num_id = row.get("numId")
                if num_id is not None:
                    num_ids_used.add(num_id)
        
        # Format the summary
        result = f"Numbering Summary for {filename}\n"
        result += "=" * 80 + "\n\n"
        result += f"Total paragraphs: {len(rows)}\n"
        result += f"Numbered paragraphs: {numbered_count}\n"
        result += f"Unique numbering styles: {len(num_ids_used)}\n\n"
        
        if formats_used:
            result += "Numbering Formats Used:\n"
            for fmt, count in sorted(formats_used.items(), key=lambda x: x[1], reverse=True):
                result += f"  {fmt}: {count} paragraph(s)\n"
            result += "\n"
        
        if levels_used:
            result += "Hierarchy Levels Used:\n"
            for level, count in sorted(levels_used.items()):
                result += f"  Level {level}: {count} paragraph(s)\n"
            result += "\n"
        
        return result
    
    except Exception as e:
        return f"Failed to generate numbering summary: {str(e)}"


async def extract_outline_structure(filename: str, max_level: Optional[int] = None) -> str:
    """
    Extract the document outline based on numbering structure.
    
    This creates a hierarchical view of numbered items, useful for
    understanding document structure and navigation.
    
    Args:
        filename: Path to the Word document
        max_level: Maximum level depth to include (None for all levels)
    
    Returns:
        Formatted outline structure
    """
    if not EFFILOCAL_AVAILABLE:
        return (
            "effilocal package not available. Please install it to use numbering analysis.\n"
            "The effilocal package should be in the same workspace."
        )
    
    filename = ensure_docx_extension(filename)
    
    if not os.path.exists(filename):
        return f"Document {filename} does not exist"
    
    try:
        # Create inspector from document
        docx_path = Path(filename)
        inspector = NumberingInspector.from_docx(docx_path)
        
        # Analyze all paragraphs
        rows, _ = inspector.analyze(debug=False)
        
        if not rows:
            return f"No paragraphs found in {filename}"
        
        # Filter to numbered paragraphs
        numbered_rows = [row for row in rows if row.get("rendered_number")]
        
        if not numbered_rows:
            return f"No numbered paragraphs found in {filename}"
        
        # Build outline
        result = f"Document Outline for {filename}\n"
        result += "=" * 80 + "\n\n"
        
        for row in numbered_rows:
            level = row.get("ilvl", 0)
            
            # Skip if beyond max_level
            if max_level is not None and level > max_level:
                continue
            
            rendered = row.get("rendered_number", "")
            text = row.get("text", "")[:80]  # Truncate for outline view
            if len(row.get("text", "")) > 80:
                text += "..."
            
            # Indent based on level
            indent = "  " * level
            result += f"{indent}{rendered} {text}\n"
        
        return result
    
    except Exception as e:
        return f"Failed to extract outline structure: {str(e)}"
