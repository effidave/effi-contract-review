"""Test the para_id based attachment insertion."""
import asyncio
import sys
from pathlib import Path
import shutil
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from effilocal.mcp_server.tools.attachment_tools import add_paragraph_after_attachment
from effilocal.doc import direct_docx

@pytest.mark.asyncio
async def test_insertion():
    temp = Path(__file__).parent / "temp_test_attach.docx"
    shutil.copy2(Path(__file__).parent / "fixtures/real_world/schedules.docx", temp)
    
    try:
        result = await add_paragraph_after_attachment(
            filename=str(temp),
            attachment_identifier="Schedule 1",
            text="TEST PARAGRAPH INSERTED HERE",
            inherit_numbering=False
        )
        
        print(f"Result: {result}")
        print()
        
        # Check where it was inserted
        blocks = list(direct_docx.iter_blocks(temp))
        print("Looking for TEST PARAGRAPH:")
        for i, b in enumerate(blocks):
            if "TEST PARAGRAPH" in b.get("text", ""):
                print(f"  Block {i}: {b.get('text', '')[:80]}")
                print(f"  Attachment ID: {b.get('attachment_id')}")
                print()
        
        # Show Schedule 1 blocks
        print("Schedule 1 blocks:")
        for i, b in enumerate(blocks):
            att = b.get("attachment")
            if att and att.get("ordinal") == "1":
                print(f"  Block {i}: {b.get('text', '')[:80]}")
        
        # Show blocks after Schedule 1
        schedule_1_att_id = None
        for b in blocks:
            att = b.get("attachment")
            if att and att.get("ordinal") == "1":
                schedule_1_att_id = att.get("attachment_id")
                break
        
        if schedule_1_att_id:
            print(f"\nBlocks with Schedule 1 attachment_id ({schedule_1_att_id}):")
            for i, b in enumerate(blocks):
                if b.get("attachment_id") == schedule_1_att_id:
                    print(f"  Block {i}: {b.get('text', '')[:80]}")
            
            print("\nBlock immediately after Schedule 1:")
            found_last = False
            for i, b in enumerate(blocks):
                if found_last:
                    print(f"  Block {i}: {b.get('text', '')[:80]}")
                    print(f"  Attachment ID: {b.get('attachment_id')}")
                    break
                if b.get("attachment_id") == schedule_1_att_id:
                    found_last = True
    finally:
        # Cleanup
        if temp.exists():
            temp.unlink()

if __name__ == "__main__":
    asyncio.run(test_insertion())
