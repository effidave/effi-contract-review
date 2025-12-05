#!/usr/bin/env python3
"""
AmendedParagraph - Wrapper for paragraphs with track changes support.

Option A Data Model:
- amended_text: Contains only VISIBLE text (normal runs + insertions, NO deletions)
- amended_runs: All runs including deletions
  - Normal/insert runs: start/end map to positions in amended_text
  - Delete runs: zero-width (start == end), with deleted_text field

This solves the python-docx limitation where paragraph.text excludes text inside w:ins elements.
"""

from typing import Iterator, List, Dict, Any, Optional
from docx.document import Document
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

# XML namespaces
NAMESPACE_W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NAMESPACE_W14 = 'http://schemas.microsoft.com/office/word/2010/wordml'


class AmendedParagraph:
    """
    Wraps a python-docx Paragraph to provide amended_text and amended_runs.
    
    The standard paragraph.text property excludes text inside w:ins elements.
    This wrapper iterates the underlying XML to build the complete visible text,
    plus a runs list with proper positions and deletion metadata.
    """
    
    def __init__(self, paragraph: Paragraph):
        """
        Initialize with a python-docx Paragraph object.
        
        Args:
            paragraph: A docx.text.paragraph.Paragraph object
        """
        self._paragraph = paragraph
        self._amended_text: Optional[str] = None
        self._amended_runs: Optional[List[Dict[str, Any]]] = None
    
    @property
    def amended_text(self) -> str:
        """
        Get the visible text of the paragraph (includes insertions, excludes deletions).
        
        This iterates the paragraph's XML to find all w:t elements (normal and inside w:ins),
        but excludes w:delText elements inside w:del.
        
        Returns:
            str: The visible text with insertions included, deletions excluded
        """
        if self._amended_text is None:
            self._build_amended_content()
        return self._amended_text
    
    @property
    def amended_runs(self) -> List[Dict[str, Any]]:
        """
        Get runs with positions relative to amended_text.
        
        Returns a list of run dictionaries with:
        - start: Start position in amended_text
        - end: End position in amended_text (== start for deletions)
        - formats: List of format strings ('bold', 'italic', 'insert', 'delete', etc.)
        - author: (optional) Author name for insertions/deletions
        - date: (optional) Date string for insertions/deletions
        - deleted_text: (only for delete runs) The deleted text content
        
        Returns:
            List of run dictionaries
        """
        if self._amended_runs is None:
            self._build_amended_content()
        return self._amended_runs
    
    def _build_amended_content(self) -> None:
        """
        Build amended_text and amended_runs by iterating paragraph XML.
        
        Iterates through all child elements of the paragraph looking for:
        - w:r (run) with w:t (text) - normal text
        - w:ins > w:r > w:t - inserted text (included in amended_text)
        - w:del > w:r > w:delText - deleted text (NOT in amended_text, stored in deleted_text)
        """
        p_elem = self._paragraph._p
        
        text_parts: List[str] = []
        runs: List[Dict[str, Any]] = []
        current_pos = 0
        
        # Iterate through all children of the paragraph
        for child in p_elem:
            tag = child.tag
            local_name = tag.split('}')[-1] if '}' in tag else tag
            
            if local_name == 'r':
                # Normal run - extract text from w:t elements
                run_text, run_formats = self._extract_run_content(child)
                if run_text:
                    runs.append({
                        'start': current_pos,
                        'end': current_pos + len(run_text),
                        'formats': run_formats,
                    })
                    text_parts.append(run_text)
                    current_pos += len(run_text)
            
            elif local_name == 'ins':
                # Insertion - extract author/date, then process contained runs
                author = child.get(qn('w:author'))
                date = child.get(qn('w:date'))
                
                for r_elem in child.iter(qn('w:r')):
                    run_text, run_formats = self._extract_run_content(r_elem)
                    if run_text:
                        run_dict = {
                            'start': current_pos,
                            'end': current_pos + len(run_text),
                            'formats': run_formats + ['insert'],
                        }
                        if author:
                            run_dict['author'] = author
                        if date:
                            run_dict['date'] = date
                        runs.append(run_dict)
                        text_parts.append(run_text)
                        current_pos += len(run_text)
            
            elif local_name == 'del':
                # Deletion - extract author/date and deleted text, but DON'T add to amended_text
                author = child.get(qn('w:author'))
                date = child.get(qn('w:date'))
                
                for r_elem in child.iter(qn('w:r')):
                    del_text = self._extract_deleted_text(r_elem)
                    if del_text:
                        run_dict = {
                            'start': current_pos,  # Zero-width: position but no width
                            'end': current_pos,    # Same as start
                            'formats': ['delete'],
                            'deleted_text': del_text,
                        }
                        if author:
                            run_dict['author'] = author
                        if date:
                            run_dict['date'] = date
                        runs.append(run_dict)
                        # Note: current_pos does NOT advance - deletion has zero width in amended_text
        
        self._amended_text = ''.join(text_parts)
        self._amended_runs = runs
    
    def _extract_run_content(self, r_elem) -> tuple:
        """
        Extract text and formatting from a w:r element.
        
        Args:
            r_elem: XML element (w:r)
            
        Returns:
            Tuple of (text_content, format_list)
        """
        text_parts = []
        formats = []
        
        # Get text from w:t elements
        for t_elem in r_elem.iter(qn('w:t')):
            if t_elem.text:
                text_parts.append(t_elem.text)
        
        # Get formatting from w:rPr
        rPr = r_elem.find(qn('w:rPr'))
        if rPr is not None:
            if rPr.find(qn('w:b')) is not None:
                formats.append('bold')
            if rPr.find(qn('w:i')) is not None:
                formats.append('italic')
            if rPr.find(qn('w:u')) is not None:
                formats.append('underline')
            if rPr.find(qn('w:strike')) is not None:
                formats.append('strikethrough')
        
        return ''.join(text_parts), formats
    
    def _extract_deleted_text(self, r_elem) -> str:
        """
        Extract deleted text from a w:r element inside w:del.
        
        Args:
            r_elem: XML element (w:r inside w:del)
            
        Returns:
            str: The deleted text content
        """
        text_parts = []
        for del_text_elem in r_elem.iter(qn('w:delText')):
            if del_text_elem.text:
                text_parts.append(del_text_elem.text)
        return ''.join(text_parts)


def iter_amended_paragraphs(doc: Document) -> Iterator[AmendedParagraph]:
    """
    Iterate over all paragraphs in a document as AmendedParagraph objects.
    
    Args:
        doc: A python-docx Document object
        
    Yields:
        AmendedParagraph objects for each paragraph in document order
    """
    for para in doc.paragraphs:
        yield AmendedParagraph(para)


def iter_amended_elements(doc: Document) -> Iterator[AmendedParagraph]:
    """
    Iterate over all paragraphs in a document including those in tables.
    
    This extends iter_amended_paragraphs to also include paragraphs inside
    table cells, in document order.
    
    Args:
        doc: A python-docx Document object
        
    Yields:
        AmendedParagraph objects for each paragraph (body and tables) in document order
    """
    body = doc.element.body
    
    for child in body:
        tag = child.tag
        local_name = tag.split('}')[-1] if '}' in tag else tag
        
        if local_name == 'p':
            # Regular paragraph
            para = Paragraph(child, doc)
            yield AmendedParagraph(para)
        
        elif local_name == 'tbl':
            # Table - iterate rows and cells
            for row in child.iter(qn('w:tr')):
                for cell in row.iter(qn('w:tc')):
                    for p_elem in cell.iter(qn('w:p')):
                        para = Paragraph(p_elem, doc)
                        yield AmendedParagraph(para)
