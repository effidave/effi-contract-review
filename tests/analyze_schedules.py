"""Quick script to analyze schedules.docx for attachments."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from effilocal.doc import direct_docx

fixture_path = Path(__file__).parent / "fixtures" / "real_world" / "schedules.docx"

if fixture_path.exists():
    blocks = list(direct_docx.iter_blocks(fixture_path))
    attachments = [
        {
            'idx': i,
            'text': b.get('text', '')[:80],
            'attachment': b.get('attachment')
        }
        for i, b in enumerate(blocks)
        if b.get('attachment')
    ]
    
    print(f"Found {len(attachments)} blocks with attachments:")
    for a in attachments[:10]:
        print(f"{a['idx']}: {a['text']}")
        print(f"  Attachment: {a['attachment']}")
        print()
else:
    print(f"Fixture not found: {fixture_path}")
