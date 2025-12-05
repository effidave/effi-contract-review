"""
Run extraction with revision formatting support.

This module provides functions to extract runs from Word paragraphs,
including track changes (insertions and deletions) as formatting info.

Option A Data Model:
- Positions are relative to VISIBLE text only (no deleted text)
- Insert runs: normal start/end positions in visible text
- Delete runs: zero-width (start == end), with deleted_text field

Each run is extracted with:
- start: Character position start in visible text (0-based)
- end: Character position end in visible text
- formats: List of format strings ('bold', 'italic', 'underline', 'insert', 'delete')
- author: Author of revision (for insert/delete runs)
- date: Date of revision (for insert/delete runs)
- deleted_text: (delete runs only) The deleted text content
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
from lxml import etree


# Namespace constants
W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def extract_paragraph_runs(paragraph: Paragraph) -> List[Dict[str, Any]]:
    """
    Extract runs from a paragraph with formatting and revision info.
    
    Uses Option A model: positions relative to visible text only.
    Delete runs have zero width with deleted_text field.
    
    Args:
        paragraph: A python-docx Paragraph object
        
    Returns:
        List of run dictionaries with keys:
        - start: int - character position start in visible text
        - end: int - character position end in visible text
        - formats: List[str] - format names ('bold', 'italic', 'underline', 'insert', 'delete')
        - author: Optional[str] - revision author (for insert/delete)
        - date: Optional[str] - revision date (for insert/delete)
        - deleted_text: Optional[str] - deleted content (for delete runs only)
    """
    runs = []
    position = 0  # Position in VISIBLE text only
    p_elem = paragraph._p
    
    # Process all elements in paragraph
    for child in p_elem:
        child_runs, new_position = _process_element_option_a(child, position)
        runs.extend(child_runs)
        position = new_position
    
    return runs


def _process_element_option_a(
    element: etree._Element, 
    start_pos: int
) -> tuple[List[Dict[str, Any]], int]:
    """
    Process an XML element and extract runs using Option A model.
    
    Returns tuple of (runs_list, new_position).
    For deletions, position doesn't advance (zero-width).
    """
    runs = []
    tag = etree.QName(element.tag).localname if hasattr(element.tag, 'localname') or '}' in str(element.tag) else element.tag
    position = start_pos
    
    if tag == 'ins':
        # Insertion element - process contained runs with 'insert' format
        author = element.get(qn('w:author'))
        date = element.get(qn('w:date'))
        
        for child in element:
            child_tag = etree.QName(child.tag).localname if '}' in str(child.tag) else child.tag
            if child_tag == 'r':
                run = _extract_run(child, position, extra_formats=['insert'], author=author, date=date)
                if run and run['end'] > run['start']:
                    runs.append(run)
                    position = run['end']
    
    elif tag == 'del':
        # Deletion element - zero-width position with deleted_text
        author = element.get(qn('w:author'))
        date = element.get(qn('w:date'))
        
        for child in element:
            child_tag = etree.QName(child.tag).localname if '}' in str(child.tag) else child.tag
            if child_tag == 'r':
                run = _extract_deleted_run_option_a(child, position, author=author, date=date)
                if run:
                    runs.append(run)
                    # Position does NOT advance - deletion is zero-width in visible text
    
    elif tag == 'r':
        # Normal run
        run = _extract_run(element, position)
        if run:
            runs.append(run)
            position = run['end']
    
    return runs, position


def _process_element(element: etree._Element, start_pos: int) -> List[Dict[str, Any]]:
    """
    Process an XML element and extract runs (legacy - full text positions).
    
    Handles:
    - w:r (normal runs)
    - w:ins (insertions)
    - w:del (deletions)
    """
    runs = []
    tag = etree.QName(element.tag).localname if hasattr(element.tag, 'localname') or '}' in str(element.tag) else element.tag
    
    # Handle different element types
    if tag == 'ins':
        # Insertion element - process contained runs with 'insert' format
        author = element.get(qn('w:author'))
        date = element.get(qn('w:date'))
        
        position = start_pos
        for child in element:
            child_tag = etree.QName(child.tag).localname if '}' in str(child.tag) else child.tag
            if child_tag == 'r':
                run = _extract_run(child, position, extra_formats=['insert'], author=author, date=date)
                if run and run['end'] > run['start']:
                    runs.append(run)
                    position = run['end']
    
    elif tag == 'del':
        # Deletion element - process contained runs with 'delete' format
        author = element.get(qn('w:author'))
        date = element.get(qn('w:date'))
        
        position = start_pos
        for child in element:
            child_tag = etree.QName(child.tag).localname if '}' in str(child.tag) else child.tag
            if child_tag == 'r':
                run = _extract_deleted_run(child, position, author=author, date=date)
                if run and run['end'] > run['start']:
                    runs.append(run)
                    position = run['end']
    
    elif tag == 'r':
        # Normal run
        run = _extract_run(element, start_pos)
        if run:
            runs.append(run)
    
    return runs


def _extract_run(
    r_elem: etree._Element, 
    start_pos: int, 
    extra_formats: Optional[List[str]] = None,
    author: Optional[str] = None,
    date: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Extract a single run from a w:r element.
    """
    text = ''
    
    # Get text from w:t elements
    for t_elem in r_elem.iter(qn('w:t')):
        if t_elem.text:
            text += t_elem.text
    
    if not text:
        return None
    
    # Extract formatting
    formats = []
    rPr = r_elem.find(qn('w:rPr'))
    if rPr is not None:
        # Bold
        if rPr.find(qn('w:b')) is not None:
            b_elem = rPr.find(qn('w:b'))
            val = b_elem.get(qn('w:val'))
            if val not in ('0', 'false'):
                formats.append('bold')
        
        # Italic
        if rPr.find(qn('w:i')) is not None:
            i_elem = rPr.find(qn('w:i'))
            val = i_elem.get(qn('w:val'))
            if val not in ('0', 'false'):
                formats.append('italic')
        
        # Underline
        u_elem = rPr.find(qn('w:u'))
        if u_elem is not None:
            val = u_elem.get(qn('w:val'))
            if val and val != 'none':
                formats.append('underline')
    
    # Add extra formats (insert/delete)
    if extra_formats:
        formats.extend(extra_formats)
    
    run: Dict[str, Any] = {
        'start': start_pos,
        'end': start_pos + len(text),
        'formats': formats,
        'author': author,  # Always include, may be None
        'date': date,      # Always include, may be None
    }
    
    return run


def _extract_deleted_run(
    r_elem: etree._Element, 
    start_pos: int,
    author: Optional[str] = None,
    date: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Extract a deleted run from a w:r element inside w:del (legacy - full text).
    
    Deleted text uses w:delText instead of w:t.
    """
    text = ''
    
    # Get text from w:delText elements
    for del_text in r_elem.iter(qn('w:delText')):
        if del_text.text:
            text += del_text.text
    
    if not text:
        return None
    
    # Extract formatting
    formats = ['delete']
    rPr = r_elem.find(qn('w:rPr'))
    if rPr is not None:
        if rPr.find(qn('w:b')) is not None:
            b_elem = rPr.find(qn('w:b'))
            val = b_elem.get(qn('w:val'))
            if val not in ('0', 'false'):
                formats.append('bold')
        
        if rPr.find(qn('w:i')) is not None:
            i_elem = rPr.find(qn('w:i'))
            val = i_elem.get(qn('w:val'))
            if val not in ('0', 'false'):
                formats.append('italic')
        
        u_elem = rPr.find(qn('w:u'))
        if u_elem is not None:
            val = u_elem.get(qn('w:val'))
            if val and val != 'none':
                formats.append('underline')
    
    run: Dict[str, Any] = {
        'start': start_pos,
        'end': start_pos + len(text),
        'formats': formats,
        'author': author,  # Always include, may be None
        'date': date,      # Always include, may be None
    }
    
    return run


def _extract_deleted_run_option_a(
    r_elem: etree._Element, 
    start_pos: int,
    author: Optional[str] = None,
    date: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Extract a deleted run using Option A model (zero-width with deleted_text).
    
    The run has start == end (zero width in visible text) and stores
    the deleted content in the deleted_text field.
    """
    text = ''
    
    # Get text from w:delText elements
    for del_text in r_elem.iter(qn('w:delText')):
        if del_text.text:
            text += del_text.text
    
    if not text:
        return None
    
    # Extract formatting
    formats = ['delete']
    rPr = r_elem.find(qn('w:rPr'))
    if rPr is not None:
        if rPr.find(qn('w:b')) is not None:
            b_elem = rPr.find(qn('w:b'))
            val = b_elem.get(qn('w:val'))
            if val not in ('0', 'false'):
                formats.append('bold')
        
        if rPr.find(qn('w:i')) is not None:
            i_elem = rPr.find(qn('w:i'))
            val = i_elem.get(qn('w:val'))
            if val not in ('0', 'false'):
                formats.append('italic')
        
        u_elem = rPr.find(qn('w:u'))
        if u_elem is not None:
            val = u_elem.get(qn('w:val'))
            if val and val != 'none':
                formats.append('underline')
    
    run: Dict[str, Any] = {
        'start': start_pos,      # Zero-width: same as start
        'end': start_pos,        # Zero-width: same as start
        'formats': formats,
        'author': author,
        'date': date,
        'deleted_text': text,    # Store deleted content here
    }
    
    return run


def add_runs_to_block(block: Dict[str, Any], paragraph: Paragraph) -> None:
    """
    Add runs information to a block dictionary using Option A model.
    
    Uses AmendedParagraph for correct positioning relative to visible text.
    Delete runs will have zero width with deleted_text field.
    
    Args:
        block: Block dictionary to update (modified in place)
        paragraph: Paragraph to extract runs from
    """
    from effilocal.doc.amended_paragraph import AmendedParagraph
    
    amended = AmendedParagraph(paragraph)
    runs = amended.amended_runs
    
    # If no runs found but block has text, create a default run
    if not runs and block.get('text'):
        text_len = len(block['text'])
        runs = [{'start': 0, 'end': text_len, 'formats': []}]
    
    block['runs'] = runs


def add_runs_to_block_legacy(block: Dict[str, Any], paragraph: Paragraph) -> None:
    """
    Add runs information to a block dictionary (legacy - full text positions).
    
    This is the old implementation that uses positions relative to full text
    including deletions. Kept for backwards compatibility.
    
    Args:
        block: Block dictionary to update (modified in place)
        paragraph: Paragraph to extract runs from
    """
    runs = extract_paragraph_runs(paragraph)
    
    # If no runs found but block has text, create a default run
    if not runs and block.get('text'):
        text_len = len(block['text'])
        runs = [{'start': 0, 'end': text_len, 'formats': []}]
    
    block['runs'] = runs
