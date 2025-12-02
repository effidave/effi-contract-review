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
        
        # Extract para_id (used to link to commentsExtended.xml status information)
        para_id = comment_element.get('{http://schemas.microsoft.com/office/word/2010/wordml}paraId', '')
        
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
    status_map = {}
    
    try:
        # Find the comments extended part through relationships
        document_part = doc.part
        comments_extended_part = None
        
        for rel_id, rel in document_part.rels.items():
            reltype = rel.reltype
            # Look for commentsExtended relationship (office 2012+ Word namespace)
            if 'commentsExtended' in reltype or 'w15' in reltype:
                comments_extended_part = rel.target_part
                break
        
        if comments_extended_part:
            # Parse commentsExtended.xml for w15:commentEx elements
            # Namespace: http://schemas.microsoft.com/office/word/2012/wordml
            comment_ex_elements = comments_extended_part.element.xpath('.//w15:commentEx')
            
            for comment_ex in comment_ex_elements:
                para_id = comment_ex.get(
                    '{http://schemas.microsoft.com/office/word/2012/wordml}paraId'
                )
                done_flag = comment_ex.get(
                    '{http://schemas.microsoft.com/office/word/2012/wordml}done',
                    '0'
                )
                
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
]
