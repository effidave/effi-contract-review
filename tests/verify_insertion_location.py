"""Verify the insertion is truly AFTER the attachment, not part of it."""
import asyncio
import sys
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from effilocal.mcp_server.tools.attachment_tools import add_paragraph_after_attachment
from effilocal.doc import direct_docx

async def verify_insertion():
    temp = Path(__file__).parent / "temp_verify.docx"
    shutil.copy2(Path(__file__).parent / "fixtures" / "real_world" / "schedules.docx", temp)
    
    # Insert paragraph
    result = await add_paragraph_after_attachment(
        filename=str(temp),
        attachment_identifier="Schedule 1",
        text="NEW CONTENT AFTER SCHEDULE 1",
        inherit_numbering=False
    )
    
    print(f"Insertion result: {result}\n")
    
    # Analyze the modified document
    blocks = list(direct_docx.iter_blocks(temp))
    
    # Find Schedule 1 attachment_id
    schedule_1_att_id = None
    for b in blocks:
        att = b.get("attachment")
        if att and att.get("ordinal") == "1":
            schedule_1_att_id = att.get("attachment_id")
            break
    
    print(f"Schedule 1 attachment_id: {schedule_1_att_id}\n")
    
    # Show blocks around Schedule 1
    print("Blocks with Schedule 1 content:")
    for i, b in enumerate(blocks):
        if b.get("attachment_id") == schedule_1_att_id:
            print(f"  Block {i}: {b.get('text', '')[:60]}")
    
    print("\nBlock immediately AFTER Schedule 1:")
    found_schedule = False
    for i, b in enumerate(blocks):
        if b.get("attachment_id") == schedule_1_att_id:
            found_schedule = True
        elif found_schedule and b.get("attachment_id") != schedule_1_att_id:
            # This is the first block AFTER Schedule 1
            print(f"  Block {i}: {b.get('text', '')[:60]}")
            print(f"  attachment_id: {b.get('attachment_id')}")
            
            # Check if it's our inserted text
            if "NEW CONTENT" in b.get('text', ''):
                print("  [OK] This is our inserted paragraph!")
                print("  [OK] It is NOT part of Schedule 1 (different attachment_id)")
            else:
                print("  ✗ This is NOT our inserted paragraph")
                print(f"  ✗ Looking for 'NEW CONTENT', found: {b.get('text', '')[:60]}")
            break
    
    # Also check Schedule 2
    print("\n" + "="*60)
    print("Schedule 2 check:")
    schedule_2_att_id = None
    for b in blocks:
        att = b.get("attachment")
        if att and att.get("ordinal") == "2":
            schedule_2_att_id = att.get("attachment_id")
            break
    
    if schedule_2_att_id:
        print(f"Schedule 2 attachment_id: {schedule_2_att_id}")
        for i, b in enumerate(blocks):
            if b.get("attachment_id") == schedule_2_att_id:
                print(f"  Block {i}: {b.get('text', '')[:60]}")

if __name__ == "__main__":
    asyncio.run(verify_insertion())
