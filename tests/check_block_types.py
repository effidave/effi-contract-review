"""Check block types."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from effilocal.doc import direct_docx

fixture_path = Path(__file__).parent / "fixtures" / "real_world" / "schedules.docx"
blocks = list(direct_docx.iter_blocks(fixture_path))

print("Blocks around Schedule 1:")
for i, b in enumerate(blocks[20:28]):
    block_type = b.get("type")
    para_idx = b.get("para_idx")
    text = b.get("text", "")[:50]
    print(f"{i+20}: type={block_type}, para_idx={para_idx}, text={text}")
