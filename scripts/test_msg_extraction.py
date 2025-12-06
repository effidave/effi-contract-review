#!/usr/bin/env python3
"""Test script to verify MSG attachment extraction works."""

import olefile
from pathlib import Path


def get_attachments_from_msg(msg_path: str) -> list[dict]:
    """Extract attachments from MSG file using olefile directly.
    
    This bypasses extract_msg's attachment parsing which fails on some MSG files.
    """
    ole = olefile.OleFileIO(msg_path)
    attachments = []
    
    # Find all attachment directories
    attach_dirs = set()
    for stream in ole.listdir():
        stream_path = '/'.join(stream)
        if stream_path.startswith('__attach_version1.0_'):
            parts = stream_path.split('/')
            if len(parts) >= 1:
                attach_dirs.add(parts[0])
    
    for attach_dir in sorted(attach_dirs):
        attachment = {'dir': attach_dir}
        
        # Get filename (3707001F = long filename, 3704001F = short filename)
        try:
            data = ole.openstream(f'{attach_dir}/__substg1.0_3707001F').read()
            attachment['filename'] = data.decode('utf-16-le').rstrip('\x00')
        except Exception:
            try:
                data = ole.openstream(f'{attach_dir}/__substg1.0_3704001F').read()
                attachment['filename'] = data.decode('utf-16-le').rstrip('\x00')
            except Exception:
                attachment['filename'] = None
        
        # Get data (37010102 = binary data)
        try:
            attachment['data'] = ole.openstream(f'{attach_dir}/__substg1.0_37010102').read()
        except Exception:
            attachment['data'] = None
            
        if attachment['filename']:
            attachments.append(attachment)
    
    ole.close()
    return attachments


if __name__ == "__main__":
    import sys
    from io import BytesIO
    from docx import Document
    
    # Add project root to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from effilocal.mcp_server.core.comments import extract_all_comments
    
    base_dir = Path(r'C:\Users\DavidSant\effi-contract-review\EL_Precedents\analysis\quick_contract_review')
    
    print("=== Instructions Email ===")
    atts = get_attachments_from_msg(base_dir / 'email_instructions.msg')
    for a in atts:
        is_docx = a['filename'].lower().endswith('.docx')
        print(f"  Filename: {a['filename']}")
        print(f"    Data size: {len(a['data']) if a['data'] else 0} bytes")
        print(f"    Is .docx: {is_docx}")
    
    print("\n=== Advice Email ===")
    atts = get_attachments_from_msg(base_dir / 'email_advice.msg')
    docx_count = 0
    edited_doc_data = None
    for a in atts:
        is_docx = a['filename'].lower().endswith('.docx')
        if is_docx:
            docx_count += 1
            edited_doc_data = a['data']
        print(f"  Filename: {a['filename']}")
        print(f"    Data size: {len(a['data']) if a['data'] else 0} bytes")
        print(f"    Is .docx: {is_docx}")
    print(f"\nTotal .docx files in advice email: {docx_count}")
    
    # Test comment extraction
    if edited_doc_data:
        print("\n=== Comments in Edited Document ===")
        doc = Document(BytesIO(edited_doc_data))
        comments = extract_all_comments(doc)
        print(f"Found {len(comments)} comments")
        
        # Group by prefix
        for_didimo = [c for c in comments if c['text'].startswith('For Didimo')]
        for_nbc = [c for c in comments if c['text'].startswith('For NBC')]
        other = [c for c in comments if not c['text'].startswith('For Didimo') and not c['text'].startswith('For NBC')]
        
        print(f"  For Didimo: {len(for_didimo)}")
        print(f"  For NBC: {len(for_nbc)}")
        print(f"  Other: {len(other)}")
        
        # Show first few
        print("\nSample comments:")
        for c in comments[:3]:
            text_preview = c['text'][:100].replace('\n', ' ')
            print(f"  [{c['author']}] {text_preview}...")
