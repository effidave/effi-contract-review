"""Test custom paragraph IDs for tracking newly created paragraphs."""
import asyncio
import sys
from pathlib import Path
import shutil
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from effilocal.mcp_server.tools.attachment_tools import (
    add_new_attachment_after,
    find_paragraph_by_id
)
from docx import Document
from docx.oxml.ns import qn

@pytest.mark.asyncio
async def test_custom_para_ids():
    temp = Path(__file__).parent / "temp_custom_id_test.docx"
    shutil.copy2(Path(__file__).parent / "fixtures" / "real_world" / "schedules.docx", temp)
    
    try:
        print("=" * 80)
        print("TEST: Create Schedule 3 and track it with custom para ID")
        print("=" * 80)
        
        # Add new Schedule 3
        result = await add_new_attachment_after(
            filename=str(temp),
            after_attachment="Schedule 2",
            new_attachment_text="Schedule 3 - Test Attachment",
            content="This is the content of Schedule 3"
        )
        
        print(f"\nResult: {result}")
        
        # Extract the custom IDs from the result
        import re
        header_id_match = re.search(r'header_id=([0-9a-f\-]+)', result)
        content_id_match = re.search(r'content_id=([0-9a-f\-]+)', result)
        
        header_custom_id = header_id_match.group(1) if header_id_match else None
        content_custom_id = content_id_match.group(1) if content_id_match else None
        
        print(f"\nExtracted IDs:")
        print(f"  Header custom_id: {header_custom_id}")
        print(f"  Content custom_id: {content_custom_id}")
        
        # Reload the document and try to find the paragraphs
        print("\n" + "=" * 80)
        print("VERIFICATION: Finding paragraphs by custom ID")
        print("=" * 80)
        
        doc = Document(temp)
        
        # Find header by custom ID
        if header_custom_id:
            header_para = find_paragraph_by_id(doc, custom_id=header_custom_id)
            if header_para:
                print(f"\n✓ Found header paragraph by custom ID:")
                print(f"  Text: {header_para.text[:80]}")
                print(f"  Style: {header_para.style.style_id if header_para.style else None}")
                
                # Check the w:tag in XML
                pPr = header_para._element.find(qn('w:pPr'))
                if pPr is not None:
                    tag = pPr.find(qn('w:tag'))
                    if tag is not None:
                        print(f"  w:tag value: {tag.get(qn('w:val'))}")
            else:
                print(f"\n✗ Could not find header paragraph by custom ID")
        
        # Find content by custom ID
        if content_custom_id:
            content_para = find_paragraph_by_id(doc, custom_id=content_custom_id)
        if content_para:
            print(f"\n✓ Found content paragraph by custom ID:")
            print(f"  Text: {content_para.text[:80]}")
            
            # Check the w:tag in XML
            pPr = content_para._element.find(qn('w:pPr'))
            if pPr is not None:
                tag = pPr.find(qn('w:tag'))
                if tag is not None:
                    print(f"  w:tag value: {tag.get(qn('w:val'))}")
            else:
                print(f"\n✗ Could not find content paragraph by custom ID")
        
        # Test that we can perform operations on the found paragraph
        print("\n" + "=" * 80)
        print("TEST: Perform operations on found paragraph")
        print("=" * 80)
        
        if header_custom_id:
            header_para = find_paragraph_by_id(doc, custom_id=header_custom_id)
            if header_para:
                # Try to add a new paragraph after it
                target_p = header_para._p
                parent = target_p.getparent()
                target_position = list(parent).index(target_p)
                
                from docx.oxml import OxmlElement
                new_p = OxmlElement('w:p')
                r = OxmlElement('w:r')
                t = OxmlElement('w:t')
                t.text = "New paragraph inserted after Schedule 3 header using custom ID"
                r.append(t)
                new_p.append(r)
                
                parent.insert(target_position + 1, new_p)
                doc.save(temp)
                
                print("✓ Successfully added a new paragraph after Schedule 3 header")
                
                # Reload and verify
                doc2 = Document(temp)
                for para in doc2.paragraphs:
                    if "New paragraph inserted after Schedule 3" in para.text:
                        print(f"✓ Verified: Found the newly inserted paragraph")
                        break
        
        print("\n" + "=" * 80)
    finally:
        # Cleanup
        if temp.exists():
            temp.unlink()

if __name__ == "__main__":
    asyncio.run(test_custom_para_ids())
