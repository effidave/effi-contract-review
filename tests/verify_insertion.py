"""Verify the attachment insertion worked correctly."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from effilocal.doc import direct_docx

temp_file = Path(__file__).parent / "temp_test_attachment.docx"

if temp_file.exists():
    blocks = list(direct_docx.iter_blocks(temp_file))
    
    # Find blocks around Schedule 1
    schedule1_idx = None
    for i, b in enumerate(blocks):
        attachment = b.get('attachment')
        if isinstance(attachment, dict) and attachment.get('ordinal') == '1':
            schedule1_idx = i
            break
    
    if schedule1_idx:
        print(f"Schedule 1 found at block index {schedule1_idx}")
        print(f"\nBlocks around Schedule 1:")
        for i in range(max(0, schedule1_idx - 1), min(len(blocks), schedule1_idx + 5)):
            b = blocks[i]
            text = b.get('text', '')[:80]
            attachment = b.get('attachment')
            attachment_id = b.get('attachment_id')
            print(f"{i}: {text}")
            if attachment:
                print(f"   Attachment: {attachment}")
            elif attachment_id:
                print(f"   Part of attachment: {attachment_id}")
            print()
    else:
        print("Schedule 1 not found")
else:
    print(f"Temp file not found: {temp_file}")
