"""Debug the attachment insertion to see what's happening."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from effilocal.doc import direct_docx

fixture_path = Path(__file__).parent / "fixtures" / "real_world" / "schedules.docx"

if fixture_path.exists():
    blocks = list(direct_docx.iter_blocks(fixture_path))
    
    # Find Schedule 1
    target_attachment_id = None
    for block in blocks:
        attachment = block.get("attachment")
        if isinstance(attachment, dict) and attachment.get("ordinal") == "1":
            target_attachment_id = attachment["attachment_id"]
            print(f"Found Schedule 1 with attachment_id: {target_attachment_id}")
            break
    
    if target_attachment_id:
        # Find all blocks with this attachment_id
        attachment_blocks = []
        for i, block in enumerate(blocks):
            if block.get("attachment_id") == target_attachment_id:
                attachment_blocks.append({
                    'idx': i,
                    'para_idx': block.get('para_idx'),
                    'text': block.get('text', '')[:80],
                    'attachment': block.get('attachment')
                })
        
        print(f"\nFound {len(attachment_blocks)} blocks for Schedule 1:")
        for ab in attachment_blocks:
            print(f"Block {ab['idx']}, Para {ab['para_idx']}: {ab['text']}")
            if ab['attachment']:
                print(f"  ^ This is the attachment header")
        
        if attachment_blocks:
            last = attachment_blocks[-1]
            print(f"\nLast block: idx={last['idx']}, para_idx={last['para_idx']}")
            print(f"Text: {last['text']}")
else:
    print(f"Fixture not found: {fixture_path}")
