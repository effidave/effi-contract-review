"""
Run extraction with revision formatting support.

This module provides functions to extract runs from Word paragraphs,
including track changes (insertions and deletions) as formatting info.

Text-Based Run Model:
- Normal/insert runs have 'text' field with their content
- Delete runs have 'deleted_text' field with deleted content
- No position-based fields (start/end) - each run carries its own text

Each run is extracted with:
- text: (normal/insert runs) The text content of the run
- deleted_text: (delete runs only) The deleted text content
- formats: List of format strings ('bold', 'italic', 'underline', 'insert', 'delete')
- author: Author of revision (for insert/delete runs)
- date: Date of revision (for insert/delete runs)
"""

from __future__ import annotations

from typing import Any, Dict
from docx.text.paragraph import Paragraph


def add_runs_to_block(block: Dict[str, Any], paragraph: Paragraph) -> None:
    """
    Add runs information to a block dictionary using text-based model.
    
    Uses AmendedParagraph for correct text content extraction.
    Normal/insert runs have 'text' field, delete runs have 'deleted_text' field.
    
    Args:
        block: Block dictionary to update (modified in place)
        paragraph: Paragraph to extract runs from
    """
    from effilocal.doc.amended_paragraph import AmendedParagraph
    
    amended = AmendedParagraph(paragraph)
    runs = amended.amended_runs
    
    # If no runs found but block has text, create a default run
    if not runs and block.get('text'):
        runs = [{'text': block['text'], 'formats': []}]
    
    block['runs'] = runs
