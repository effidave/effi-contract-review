"""
Core revision (track changes) extraction and manipulation for effilocal MCP server.

This module provides:
1. Revision extraction from Word documents (w:ins, w:del elements)
2. Accept individual revisions (make changes permanent)
3. Reject individual revisions (undo changes)
4. Accept/reject all revisions in bulk
5. Para_id association for UI linking

Word Track Changes XML Structure:
- <w:ins> wraps inserted text runs containing <w:t>
- <w:del> wraps deleted text runs containing <w:delText>
- Both have w:id, w:author, w:date attributes
"""

from typing import Dict, List, Optional, Any, Tuple
from docx import Document
from docx.document import Document as DocumentType
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
from lxml import etree

from effilocal.mcp_server.utils.document_utils import iter_document_paragraphs


# Namespace constants
W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W14_NS = 'http://schemas.microsoft.com/office/word/2010/wordml'

# For lxml xpath (used with raw etree elements)
LXML_NSMAP = {
    'w': W_NS,
    'w14': W14_NS,
}


# ============================================================================
# Revision Extraction
# ============================================================================

def extract_all_revisions(doc: DocumentType) -> List[Dict[str, Any]]:
    """
    Extract all tracked changes (revisions) from a Word document.
    
    Parses:
    - <w:ins> elements (insertions) - text that was added
    - <w:del> elements (deletions) - text that was removed
    
    Args:
        doc: The Document object to extract revisions from
        
    Returns:
        List of revision dictionaries with keys:
        - id: Unique revision ID (from w:id attribute)
        - type: 'insert' or 'delete'
        - text: The inserted or deleted text
        - author: Author who made the change
        - date: Date/time of the change
        - paragraph_index: Index of the paragraph containing this revision
        - para_id: The w14:paraId of the containing paragraph (for UI linking)
    """
    revisions = []
    
    # Iterate through all paragraphs in the document
    for para_index, para in enumerate(iter_document_paragraphs(doc)):
        p_element = para._element
        
        # Get para_id for UI linking
        para_id = p_element.get(qn('w14:paraId')) or ''
        
        # Find all insertions in this paragraph
        # python-docx OxmlElement.xpath doesn't use namespaces= keyword
        insertions = p_element.xpath('.//w:ins')
        for ins in insertions:
            revision = _extract_revision_data(ins, 'insert', para_index, para_id)
            if revision:
                revisions.append(revision)
        
        # Find all deletions in this paragraph
        deletions = p_element.xpath('.//w:del')
        for dele in deletions:
            revision = _extract_revision_data(dele, 'delete', para_index, para_id)
            if revision:
                revisions.append(revision)
    
    return revisions


def _extract_revision_data(
    element: etree._Element, 
    revision_type: str, 
    paragraph_index: int,
    para_id: str
) -> Optional[Dict[str, Any]]:
    """
    Extract data from a single revision element (w:ins or w:del).
    
    Args:
        element: The w:ins or w:del XML element
        revision_type: 'insert' or 'delete'
        paragraph_index: Index of the containing paragraph
        para_id: The para_id of the containing paragraph
        
    Returns:
        Dictionary with revision data, or None if extraction fails
    """
    try:
        # Get revision attributes using qn() for namespace handling
        rev_id = element.get(qn('w:id')) or ''
        author = element.get(qn('w:author')) or ''
        date = element.get(qn('w:date')) or ''
        
        # Extract text content using iter() instead of xpath
        # (xpath on sub-elements may not have namespace context)
        if revision_type == 'insert':
            # Insertions contain w:t elements
            text_elements = list(element.iter(qn('w:t')))
            text = ''.join(t.text or '' for t in text_elements)
        else:
            # Deletions contain w:delText elements
            text_elements = list(element.iter(qn('w:delText')))
            text = ''.join(t.text or '' for t in text_elements)
        
        # Skip empty revisions (formatting-only changes)
        if not text.strip() and not text:
            # Still include if it has any content (including whitespace)
            if not text:
                return None
        
        return {
            'id': rev_id,
            'type': revision_type,
            'text': text,
            'author': author,
            'date': date,
            'paragraph_index': paragraph_index,
            'para_id': para_id,
        }
        
    except Exception as e:
        return None


# ============================================================================
# Accept Revision
# ============================================================================

def accept_revision(doc: DocumentType, revision_id: str) -> bool:
    """
    Accept a specific revision, making the change permanent.
    
    For insertions: Keep the text, remove the w:ins wrapper
    For deletions: Remove the w:del element entirely (text is already "deleted")
    
    Args:
        doc: The Document object
        revision_id: The w:id attribute of the revision to accept
        
    Returns:
        True if successfully accepted, False if revision not found
    """
    # Find the revision element
    element, revision_type = _find_revision_element(doc, revision_id)
    
    if element is None:
        return False
    
    try:
        parent = element.getparent()
        if parent is None:
            return False
        
        if revision_type == 'insert':
            # Accept insertion: unwrap the w:ins but keep its children (the text runs)
            _unwrap_element(element)
        else:
            # Accept deletion: remove the w:del element entirely
            parent.remove(element)
        
        return True
        
    except Exception as e:
        return False


def _unwrap_element(element: etree._Element) -> None:
    """
    Remove an element but keep its children in place.
    
    This is used when accepting an insertion - we want to keep the text
    but remove the w:ins wrapper.
    """
    parent = element.getparent()
    if parent is None:
        return
    
    # Get the index where this element is
    index = list(parent).index(element)
    
    # Move all children to the parent at the same position
    for i, child in enumerate(list(element)):
        parent.insert(index + i, child)
    
    # Remove the now-empty wrapper element
    parent.remove(element)


# ============================================================================
# Reject Revision
# ============================================================================

def reject_revision(doc: DocumentType, revision_id: str) -> bool:
    """
    Reject a specific revision, undoing the change.
    
    For insertions: Remove the w:ins element entirely (discard the inserted text)
    For deletions: Convert w:delText back to w:t, unwrap the w:del (restore the text)
    
    Args:
        doc: The Document object
        revision_id: The w:id attribute of the revision to reject
        
    Returns:
        True if successfully rejected, False if revision not found
    """
    element, revision_type = _find_revision_element(doc, revision_id)
    
    if element is None:
        return False
    
    try:
        parent = element.getparent()
        if parent is None:
            return False
        
        if revision_type == 'insert':
            # Reject insertion: remove the entire w:ins element (including its text)
            parent.remove(element)
        else:
            # Reject deletion: convert w:delText to w:t and unwrap
            _convert_del_to_normal_text(element)
            _unwrap_element(element)
        
        return True
        
    except Exception as e:
        return False


def _convert_del_to_normal_text(del_element: etree._Element) -> None:
    """
    Convert w:delText elements inside a w:del to normal w:t elements.
    
    This is used when rejecting a deletion - we want to restore the deleted text
    as normal text.
    """
    # Find all w:delText elements
    del_texts = list(del_element.iter(qn('w:delText')))
    
    for del_text in del_texts:
        # Create a new w:t element with the same text
        new_t = etree.Element(qn('w:t'))
        new_t.text = del_text.text
        
        # Preserve xml:space attribute if present
        space_attr = del_text.get('{http://www.w3.org/XML/1998/namespace}space')
        if space_attr:
            new_t.set('{http://www.w3.org/XML/1998/namespace}space', space_attr)
        
        # Replace delText with t
        parent = del_text.getparent()
        if parent is not None:
            index = list(parent).index(del_text)
            parent.remove(del_text)
            parent.insert(index, new_t)


# ============================================================================
# Find Revision Element
# ============================================================================

def _find_revision_element(
    doc: DocumentType, 
    revision_id: str
) -> Tuple[Optional[etree._Element], Optional[str]]:
    """
    Find a revision element by its ID.
    
    Args:
        doc: The Document object
        revision_id: The w:id attribute to search for
        
    Returns:
        Tuple of (element, type) where type is 'insert' or 'delete',
        or (None, None) if not found
    """
    # Search in document body
    body = doc.element.body
    
    # Search for insertion - iterate through all paragraphs
    for para in body.iterchildren():
        # Search recursively for w:ins with matching id
        for ins in para.iter(qn('w:ins')):
            if ins.get(qn('w:id')) == revision_id:
                return ins, 'insert'
        
        # Search for w:del with matching id
        for dele in para.iter(qn('w:del')):
            if dele.get(qn('w:id')) == revision_id:
                return dele, 'delete'
    
    return None, None


# ============================================================================
# Bulk Operations
# ============================================================================

def accept_all_revisions(doc: DocumentType) -> Dict[str, Any]:
    """
    Accept all tracked changes in the document.
    
    Args:
        doc: The Document object
        
    Returns:
        Dictionary with:
        - success: True if completed
        - accepted_count: Number of revisions accepted
        - errors: List of any errors encountered
    """
    revisions = extract_all_revisions(doc)
    accepted_count = 0
    errors = []
    
    # Process in reverse order to avoid index shifting issues
    for rev in reversed(revisions):
        try:
            if accept_revision(doc, rev['id']):
                accepted_count += 1
            else:
                errors.append(f"Failed to accept revision {rev['id']}")
        except Exception as e:
            errors.append(f"Error accepting revision {rev['id']}: {str(e)}")
    
    return {
        'success': len(errors) == 0 or accepted_count > 0,
        'accepted_count': accepted_count,
        'errors': errors if errors else None,
    }


def reject_all_revisions(doc: DocumentType) -> Dict[str, Any]:
    """
    Reject all tracked changes in the document.
    
    Args:
        doc: The Document object
        
    Returns:
        Dictionary with:
        - success: True if completed
        - rejected_count: Number of revisions rejected
        - errors: List of any errors encountered
    """
    revisions = extract_all_revisions(doc)
    rejected_count = 0
    errors = []
    
    # Process in reverse order to avoid index shifting issues
    for rev in reversed(revisions):
        try:
            if reject_revision(doc, rev['id']):
                rejected_count += 1
            else:
                errors.append(f"Failed to reject revision {rev['id']}")
        except Exception as e:
            errors.append(f"Error rejecting revision {rev['id']}: {str(e)}")
    
    return {
        'success': len(errors) == 0 or rejected_count > 0,
        'rejected_count': rejected_count,
        'errors': errors if errors else None,
    }


# ============================================================================
# Utility Functions
# ============================================================================

def get_revision_summary(doc: DocumentType) -> Dict[str, Any]:
    """
    Get a summary of revisions in the document.
    
    Returns:
        Dictionary with:
        - total: Total number of revisions
        - insertions: Number of insertions
        - deletions: Number of deletions
        - authors: List of unique authors
    """
    revisions = extract_all_revisions(doc)
    
    insertions = [r for r in revisions if r['type'] == 'insert']
    deletions = [r for r in revisions if r['type'] == 'delete']
    authors = list(set(r['author'] for r in revisions if r.get('author')))
    
    return {
        'total': len(revisions),
        'insertions': len(insertions),
        'deletions': len(deletions),
        'authors': authors,
    }
