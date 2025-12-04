"""
Core comment extraction functionality for effilocal MCP server.

This module extends word_document_server.core.comments with:
1. Comment status extraction from commentsExtended.xml (active/resolved)
2. Enhanced comment data with para_id linkage
3. Status merging functionality

Override Pattern:
- Import all upstream functions
- Override functions that need status support
- Add new status-related functions
"""

import datetime
from typing import Dict, List, Optional, Any
from docx import Document
from docx.document import Document as DocumentType
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

from effilocal.mcp_server.utils.document_utils import iter_document_paragraphs

# Import upstream functions that we don't override (pass-through)
from word_document_server.core.comments import (
    extract_comments_from_paragraphs,
    filter_comments_by_author,
    get_comments_for_paragraph,
)

# Alias for API consistency
get_comments_by_author = filter_comments_by_author


# ============================================================================
# OVERRIDDEN Functions (extended with status support)
# ============================================================================

def extract_all_comments(doc: DocumentType) -> List[Dict[str, Any]]:
    """
    Extract all comments from a Word document, including status information from commentsExtended.xml.
    
    EXTENDED from upstream with:
    - Status extraction from commentsExtended.xml part
    - para_id linkage between comments.xml and commentsExtended.xml
    - Active/resolved status tracking
    - Paragraph index mapping by scanning document body
    - Reference text extraction (the text the comment is anchored to)
    
    Args:
        doc: The Document object to extract comments from
        
    Returns:
        List of dictionaries containing comment information including status
    """
    comments_map = {}
    
    try:
        # Access comments through document part
        comments_part = None
        for rel_id, rel in doc.part.rels.items():
            reltype = rel.reltype
            if 'comments' in reltype and 'Extended' not in reltype:
                comments_part = rel.target_part
                break
        
        if comments_part:
            # Parse comments.xml for comment elements
            comment_elements = comments_part.element.xpath('.//w:comment')
            
            for idx, comment_el in enumerate(comment_elements):
                comment_data = extract_comment_data(comment_el, idx)
                if comment_data:
                    # Use comment_id as key for mapping
                    cid = comment_data['comment_id']
                    comments_map[cid] = comment_data
        
        # Scan paragraphs to map comments to locations
        # This populates 'paragraph_index' for comments found in the body
        # Use iter_document_paragraphs to include SDT-wrapped paragraphs
        for i, p in enumerate(iter_document_paragraphs(doc)):
            p_element = p._element
            # Find comment references
            refs = p_element.xpath('.//w:commentReference')
            for ref in refs:
                cid = ref.get(qn('w:id'))
                if cid in comments_map:
                    comments_map[cid]['paragraph_index'] = i
                    
        # Also scan tables? (Optional, but good for completeness)
        # For now, let's stick to main body paragraphs as that's what manage_notes.py needs
        
        comments = list(comments_map.values())
        
        if not comments:
            # Fallback: scan paragraphs for comment references (upstream method)
            # Note: upstream method doesn't extract text well, but it's a fallback
            comments = extract_comments_from_paragraphs(doc)
        
        # Extract comment status information from commentsExtended.xml
        status_map = extract_comment_status_map(doc)
        
        # Merge status information into comments
        if status_map:
            comments = merge_comment_status(comments, status_map)
        
        # Extract reference text for all comments (the text they're anchored to)
        reference_texts = get_all_reference_texts(doc)
        for comment in comments:
            cid = comment.get('comment_id')
            if cid and cid in reference_texts:
                comment['reference_text'] = reference_texts[cid]
    
    except Exception as e:
        # If direct access fails, try alternative approach
        comments = extract_comments_from_paragraphs(doc)
    
    return comments


def extract_comment_data(comment_element, index: int) -> Optional[Dict[str, Any]]:
    """
    Extract data from a single comment element.
    
    EXTENDED from upstream with:
    - para_id extraction for linking to commentsExtended.xml
    - status and is_resolved fields (defaults)
    
    Args:
        comment_element: XML element representing the comment
        index: Comment index
        
    Returns:
        Dictionary with comment data or None if extraction fails
    """
    try:
        # Extract comment attributes
        comment_id = comment_element.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id', '')
        author = comment_element.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author', '')
        initials = comment_element.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}initials', '')
        date_str = comment_element.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}date', '')
        
        # Extract para_id from the first paragraph INSIDE the comment
        # The para_id (w14:paraId) is on the w:p element, not the w:comment element
        para_id = ''
        para_elements = comment_element.xpath('.//w:p')
        if para_elements:
            para_id = para_elements[0].get('{http://schemas.microsoft.com/office/word/2010/wordml}paraId', '')
        
        # Parse date if available
        date = None
        if date_str:
            try:
                date = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                date = date.isoformat()
            except:
                date = date_str
        
        # Extract comment text content
        text = ''
        for text_el in comment_element.xpath('.//w:t'):
            text += text_el.text or ''
        
        return {
            'id': f'comment_{index + 1}',
            'comment_id': comment_id,
            'para_id': para_id,
            'author': author,
            'initials': initials,
            'date': date,
            'text': text.strip(),
            'paragraph_index': None,  # Will be filled if we can determine it
            'in_table': False,
            'reference_text': '',
            'status': 'active',  # Will be updated with actual status if commentsExtended exists
            'is_resolved': False,
            'done_flag': 0  # 0=active, 1=resolved
        }
    
    except Exception as e:
        return None


# ============================================================================
# NEW Functions (status extraction from commentsExtended.xml)
# ============================================================================

def extract_comment_status_map(doc: DocumentType) -> Dict[str, Dict[str, Any]]:
    """
    Extract comment status information from commentsExtended.xml.
    
    NEW function - extracts status from Office 2012+ commentsExtended part.
    
    The commentsExtended.xml part contains w15:commentEx elements with:
    - w15:paraId: Links to the w14:paraId in comments.xml
    - w15:done: Status flag (0=active/unresolved, 1=resolved)
    
    Args:
        doc: The Document object
        
    Returns:
        Dictionary mapping paraId to status info: {'paraId': {'status': 'active|resolved', 'done': 0|1, 'is_resolved': bool}}
    """
    from lxml import etree
    
    status_map = {}
    
    try:
        # Find the comments extended part through relationships
        document_part = doc.part
        comments_extended_part = None
        
        for rel_id, rel in document_part.rels.items():
            reltype = rel.reltype
            # Look for commentsExtended relationship (office 2012+ Word namespace)
            if 'commentsExtended' in reltype:
                comments_extended_part = rel.target_part
                break
        
        if comments_extended_part:
            # Parse commentsExtended.xml from blob (generic Part doesn't have .element)
            root = etree.fromstring(comments_extended_part.blob)
            
            # Namespace: http://schemas.microsoft.com/office/word/2012/wordml
            W15_NS = 'http://schemas.microsoft.com/office/word/2012/wordml'
            nsmap = {'w15': W15_NS}
            
            comment_ex_elements = root.xpath('.//w15:commentEx', namespaces=nsmap)
            
            for comment_ex in comment_ex_elements:
                para_id = comment_ex.get(f'{{{W15_NS}}}paraId')
                done_flag = comment_ex.get(f'{{{W15_NS}}}done', '0')
                
                if para_id:
                    # Convert done flag to boolean and status string
                    is_resolved = done_flag == '1'
                    status = 'resolved' if is_resolved else 'active'
                    
                    status_map[para_id] = {
                        'status': status,
                        'done': int(done_flag),
                        'is_resolved': is_resolved
                    }
    except Exception as e:
        # If commentsExtended doesn't exist or can't be parsed, return empty map
        # This is normal for older Word documents without comment status tracking
        pass
    
    return status_map


def merge_comment_status(comments: List[Dict[str, Any]], status_map: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge comment status information into comment dictionaries.
    
    NEW function - links status from commentsExtended to comments.
    
    Args:
        comments: List of comment dictionaries extracted from comments.xml
        status_map: Status information map from commentsExtended.xml
        
    Returns:
        Comments list with status information merged in (status, is_resolved, done_flag fields updated)
    """
    for comment in comments:
        # Use para_id if available, otherwise fall back to comment_id
        para_id = comment.get('para_id')
        
        if para_id and para_id in status_map:
            status_info = status_map[para_id]
            comment['status'] = status_info['status']
            comment['is_resolved'] = status_info['is_resolved']
            comment['done_flag'] = status_info['done']
        else:
            # Default to 'active' if no status information available
            comment.setdefault('status', 'active')
            comment.setdefault('is_resolved', False)
            comment.setdefault('done_flag', 0)
    
    return comments


# ============================================================================
# NEW Functions (resolve/unresolve comments - Sprint 3 Phase 1)
# ============================================================================

def _get_comments_extended_part(doc: DocumentType):
    """
    Get the commentsExtended part from a document.
    
    Args:
        doc: The Document object
        
    Returns:
        Tuple of (comments_extended_part, rel_id) or (None, None) if not found
    """
    for rel_id, rel in doc.part.rels.items():
        reltype = rel.reltype
        if 'commentsExtended' in reltype:
            return rel.target_part, rel_id
    return None, None


def _get_comment_para_id(doc: DocumentType, comment_id: str) -> Optional[str]:
    """
    Get the para_id for a given comment_id by looking in comments.xml.
    
    Args:
        doc: The Document object
        comment_id: The w:id of the comment (as string)
        
    Returns:
        The para_id (w14:paraId) for the comment, or None if not found
    """
    try:
        comments_part = None
        for rel_id, rel in doc.part.rels.items():
            if 'comments' in rel.reltype and 'Extended' not in rel.reltype and 'Ids' not in rel.reltype and 'Extensible' not in rel.reltype:
                comments_part = rel.target_part
                break
        
        if comments_part and hasattr(comments_part, 'element'):
            # Use python-docx's CT_Comments element which has a comment_lst
            ct_comments = comments_part.element
            if hasattr(ct_comments, 'comment_lst'):
                for comment in ct_comments.comment_lst:
                    if str(comment.id) == str(comment_id):
                        # Find first paragraph inside the comment
                        W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
                        W14_NS = 'http://schemas.microsoft.com/office/word/2010/wordml'
                        paras = comment.findall(f'{{{W_NS}}}p')
                        if paras:
                            para_id = paras[0].get(f'{{{W14_NS}}}paraId')
                            return para_id
    except Exception:
        pass
    return None


def resolve_comment(doc: DocumentType, comment_id: str) -> bool:
    """
    Mark a comment as resolved by updating commentsExtended.xml.
    
    This sets the w15:done attribute to "1" for the comment's entry in 
    commentsExtended.xml, which Word interprets as "resolved".
    
    Args:
        doc: The Document object
        comment_id: The w:id attribute of the comment to resolve
        
    Returns:
        True if successfully resolved, False if comment not found or error
    """
    return _set_comment_done_flag(doc, comment_id, done=True)


def unresolve_comment(doc: DocumentType, comment_id: str) -> bool:
    """
    Mark a comment as active (unresolve it) by updating commentsExtended.xml.
    
    This sets the w15:done attribute to "0" for the comment's entry in 
    commentsExtended.xml, which Word interprets as "active".
    
    Args:
        doc: The Document object
        comment_id: The w:id attribute of the comment to unresolve
        
    Returns:
        True if successfully unresolved, False if comment not found or error
    """
    return _set_comment_done_flag(doc, comment_id, done=False)


def _set_comment_done_flag(doc: DocumentType, comment_id: str, done: bool) -> bool:
    """
    Set the done flag for a comment in commentsExtended.xml.
    
    Args:
        doc: The Document object
        comment_id: The w:id attribute of the comment
        done: True to mark as resolved (done="1"), False for active (done="0")
        
    Returns:
        True if successfully updated, False if comment not found or error
    """
    from lxml import etree
    
    try:
        # Get the para_id for this comment
        para_id = _get_comment_para_id(doc, comment_id)
        if not para_id:
            return False
        
        # Get commentsExtended part
        comments_extended_part, _ = _get_comments_extended_part(doc)
        if not comments_extended_part:
            return False
        
        # Parse the XML from blob
        root = etree.fromstring(comments_extended_part.blob)
        
        # Define namespaces
        W15_NS = 'http://schemas.microsoft.com/office/word/2012/wordml'
        nsmap = {'w15': W15_NS}
        
        # Find the commentEx element with matching paraId
        comment_ex_elements = root.xpath(
            f'.//w15:commentEx[@w15:paraId="{para_id}"]',
            namespaces=nsmap
        )
        
        if not comment_ex_elements:
            return False
        
        # Update the done attribute
        done_value = '1' if done else '0'
        comment_ex = comment_ex_elements[0]
        comment_ex.set(f'{{{W15_NS}}}done', done_value)
        
        # Write the modified XML back to the part's blob
        # We need to use the correct declaration and encoding
        new_xml = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone='yes')
        comments_extended_part._blob = new_xml
        
        return True
        
    except Exception as e:
        return False


def extract_reference_text(doc: DocumentType, comment_id: str) -> str:
    """
    Extract the text that a comment is anchored to.
    
    Word documents mark commented text with commentRangeStart and commentRangeEnd
    elements. This function finds the text between these markers for a given comment.
    
    Args:
        doc: The Document object
        comment_id: The w:id attribute of the comment
        
    Returns:
        The text that the comment is anchored to, or empty string if not found
    """
    try:
        reference_text = []
        in_range = False
        
        # Walk through all paragraphs looking for the comment range
        for para in iter_document_paragraphs(doc):
            p_element = para._element
            
            # Check for range start and end within this paragraph
            for child in p_element.iter():
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                
                # Check for commentRangeStart
                if tag == 'commentRangeStart':
                    cid = child.get(qn('w:id'))
                    if cid == comment_id:
                        in_range = True
                        continue
                
                # Check for commentRangeEnd
                if tag == 'commentRangeEnd':
                    cid = child.get(qn('w:id'))
                    if cid == comment_id:
                        in_range = False
                        # Return what we've collected
                        return ''.join(reference_text).strip()
                
                # Collect text while in range
                if in_range and tag == 't':
                    if child.text:
                        reference_text.append(child.text)
        
        return ''.join(reference_text).strip()
        
    except Exception as e:
        return ''


def get_all_reference_texts(doc: DocumentType) -> Dict[str, str]:
    """
    Extract reference text for all comments in a document.
    
    This is more efficient than calling extract_reference_text for each comment
    as it only iterates through the document once.
    
    Args:
        doc: The Document object
        
    Returns:
        Dictionary mapping comment_id to its reference text
    """
    reference_texts: Dict[str, str] = {}
    active_ranges: Dict[str, List[str]] = {}  # comment_id -> list of text fragments
    
    try:
        for para in iter_document_paragraphs(doc):
            p_element = para._element
            
            for child in p_element.iter():
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                
                # Handle commentRangeStart
                if tag == 'commentRangeStart':
                    cid = child.get(qn('w:id'))
                    if cid:
                        active_ranges[cid] = []
                
                # Handle commentRangeEnd
                elif tag == 'commentRangeEnd':
                    cid = child.get(qn('w:id'))
                    if cid and cid in active_ranges:
                        reference_texts[cid] = ''.join(active_ranges[cid]).strip()
                        del active_ranges[cid]
                
                # Collect text for all active ranges
                elif tag == 't' and child.text:
                    for cid in active_ranges:
                        active_ranges[cid].append(child.text)
    
    except Exception:
        pass
    
    return reference_texts


# ============================================================================
# Re-export all functions for compatibility
# ============================================================================

__all__ = [
    # Overridden functions (extended with status support)
    'extract_all_comments',
    'extract_comment_data',
    
    # Pass-through functions (unchanged from upstream)
    'extract_comments_from_paragraphs',
    'get_comments_by_author',
    'get_comments_for_paragraph',
    
    # New functions (status extraction)
    'extract_comment_status_map',
    'merge_comment_status',
    
    # New functions (resolve/unresolve - Sprint 3 Phase 1)
    'resolve_comment',
    'unresolve_comment',
    
    # New functions (reference text extraction)
    'extract_reference_text',
    'get_all_reference_texts',
]
