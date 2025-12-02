# Sprint 1: UUID Persistence & Git Integration

**Completed:** December 2025
**Status:** ✅ All tests passing

---

## Overview

Sprint 1 established stable document identity that survives external edits and re-analysis, plus integrated git version control.

## Features Implemented

### 1. UUID Embedding in .docx Documents

**Location:** `effilocal/doc/uuid_embedding.py`

Block UUIDs are embedded directly into .docx documents using Word's Structured Document Tag (SDT) content controls. This allows the system to track which paragraph is which, even after the document is edited in Microsoft Word.

**Key Functions:**

```python
# Wrap paragraphs in SDT content controls with UUID tags
embed_block_uuids(doc: Document, blocks: List[dict]) -> dict[str, str]

# Extract UUID → BlockKey mapping from document
extract_block_uuids(doc: Document) -> Dict[str, BlockKey]

# Remove all effi SDTs while preserving content
remove_all_uuid_controls(doc: Document) -> int

# Legacy: Extract UUID → paragraph index (paragraphs only)
extract_block_uuids_legacy(doc: Document) -> Dict[str, int]
```

**Block Key Types:**
```python
@dataclass(frozen=True)
class ParaKey:
    """Key for a top-level paragraph block."""
    para_idx: int

@dataclass(frozen=True)
class TableCellKey:
    """Key for a table cell block."""
    table_idx: int
    row: int
    col: int

BlockKey = ParaKey | TableCellKey
```

**Content Control Structure:**
```xml
<w:sdt>
  <w:sdtPr>
    <w:tag w:val="effi:block:uuid-here"/>
    <w:id w:val="12345"/>
  </w:sdtPr>
  <w:sdtContent>
    <w:p><!-- paragraph content --></w:p>
  </w:sdtContent>
</w:sdt>
```

**Key Behaviors:**
- UUIDs survive Word save/close/reopen cycles
- UUIDs survive copy/paste within same document
- Tag format: `effi:block:<uuid>`
- **Supported locations:**
  - Top-level body paragraphs (matched by `para_idx`)
  - Paragraphs inside SDT content controls
  - Paragraphs inside table cells (matched by `table: {table_id, row, col}`)
- **Not currently supported:** headers, footers, text boxes

**Block Matching:**
Blocks are matched to document positions using:
- `ParaKey(para_idx)` for top-level paragraphs - uses `para_idx` field
- `TableCellKey(table_idx, row, col)` for table cells - uses `table: {table_id: "tbl_N", row: int, col: int}` field

### 2. Content Hash Fallback

**Location:** `effilocal/doc/content_hash.py`

When UUIDs are lost (e.g., content control stripped by Word or another editor), the system falls back to matching blocks by content hash.

**Key Functions:**

```python
# Compute SHA-256 of normalized text
compute_block_hash(text: str) -> str

# Three-phase matching: UUID → hash → position
match_blocks_by_hash(old_blocks: List[dict], new_blocks: List[dict], 
                     embedded_uuids: Dict[str, BlockKey] = None) -> MatchResult
```

**Matching Strategy (in priority order):**
1. **UUID match** - Extracted from embedded content controls (paragraphs and table cells)
2. **Hash match** - SHA-256 of normalized text (lowercase, collapsed whitespace)
3. **Position match** - Proximity heuristics when hash matches multiple candidates

**MatchResult Structure:**
```python
@dataclass
class MatchResult:
    matches: List[BlockMatch]       # Matched pairs with method and confidence
    unmatched_old: List[str]        # Deleted blocks
    unmatched_new: List[str]        # New blocks
```### 3. Git Integration

**Location:** `effilocal/util/git_ops.py`

Automatic version control with meaningful commit messages.

**Key Functions:**

```python
# Stage and commit if changes exist
auto_commit(repo: Repo, message: str, files: List[Path]) -> Optional[str]

# Generate formatted commit message
generate_commit_message(action: str, details: dict) -> str

# Retrieve commit history for a file
get_file_history(repo: Repo, file: Path, max_count: int = 50) -> List[CommitInfo]
```

**Commit Message Format:**
```
[effi] <action>: <summary>
```

Examples:
- `[effi] edit: Modified clause 3.2.1`
- `[effi] analyze: Initial analysis of Agreement.docx`
- `[effi] checkpoint: Before major restructure`

**Extension Commands:**
- **Save & Commit** - Saves document with auto-commit
- **Save Checkpoint** - Creates explicit checkpoint with custom note

### 4. Re-Analysis with UUID Preservation

**Location:** `effilocal/flows/analyze_doc.py`

When re-analyzing a document after external edits, existing block UUIDs are preserved where content matches.

**Enhanced Analysis Flow:**
1. Extract embedded UUIDs from .docx
2. Load previous `blocks.jsonl` if exists
3. Parse document into new blocks
4. Match new blocks to old by: UUID > hash > position
5. Assign matched UUIDs; generate new UUIDs for unmatched
6. Emit `analysis_delta.json` with change summary

**New Artifact:** `analysis_delta.json`
```json
{
  "timestamp": "2025-12-02T10:30:00Z",
  "matched_by_uuid": 45,
  "matched_by_hash": 3,
  "matched_by_position": 1,
  "new_blocks": ["uuid1", "uuid2"],
  "deleted_blocks": ["uuid3"],
  "modified_blocks": ["uuid4", "uuid5"]
}
```

### 5. Save Flow with UUID Embedding

**Location:** `effilocal/flows/save_doc.py`

**Key Functions:**

```python
# Embed UUIDs and optionally git commit
save_with_uuids(docx_path: Path, blocks_path: Path, auto_commit: bool = True) -> dict

# Create named checkpoint commit
create_checkpoint(docx_path: Path, note: str = "") -> dict
```

---

## Extension Integration

### New Commands in `extension.ts`

| Command | Description |
|---------|-------------|
| `effi.saveDocument` | Save with UUIDs embedded + auto-commit |
| `effi.saveCheckpoint` | Create checkpoint with custom note |
| `effi.showVersionHistory` | Quick pick to browse git history |

### Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `effiContractViewer.autoCommit` | `true` | Auto-commit on save |

### Python Scripts

| Script | Purpose |
|--------|---------|
| `extension/scripts/save_document.py` | Save with UUID embedding |
| `extension/scripts/get_history.py` | Retrieve git commit history |

---

## File Structure

```
effilocal/
├── doc/
│   ├── uuid_embedding.py   # Content control manipulation
│   └── content_hash.py     # Hash-based matching
├── util/
│   └── git_ops.py          # Git commit/history operations
└── flows/
    ├── analyze_doc.py      # Enhanced with UUID preservation
    └── save_doc.py         # Save with embedded UUIDs

extension/scripts/
├── save_document.py        # CLI wrapper for save flow
└── get_history.py          # CLI wrapper for git history
```

---

## Test Coverage

All tests in `tests/` directory:

| Test File | Coverage |
|-----------|----------|
| `test_uuid_embedding.py` | UUID wrap/extract/remove, save/reload cycles |
| `test_content_hash.py` | Hash computation, matching strategies |
| `test_git_ops.py` | Commit, history retrieval, checkpoint |

**Key Test Cases:**
- UUIDs survive document save/reload
- Hash fallback matches 90%+ blocks when UUIDs stripped
- Position heuristics resolve ambiguous hash matches
- Git commits only when changes exist

---

## Usage Examples

### Embedding UUIDs Programmatically

```python
from docx import Document
from effilocal.doc.uuid_embedding import embed_block_uuids, extract_block_uuids, ParaKey, TableCellKey

# Load document and blocks (paragraphs and table cells)
doc = Document("contract.docx")
blocks = [
    {"id": "uuid1", "para_idx": 0},  # Top-level paragraph
    {"id": "uuid2", "para_idx": 1},
    {"id": "cell-uuid", "table": {"table_id": "tbl_0", "row": 0, "col": 0}},  # Table cell
]

# Embed UUIDs
result = embed_block_uuids(doc, blocks)
doc.save("contract.docx")

# Later, extract them back
uuid_map = extract_block_uuids(doc)
# {
#   "uuid1": ParaKey(para_idx=0),
#   "uuid2": ParaKey(para_idx=1),
#   "cell-uuid": TableCellKey(table_idx=0, row=0, col=0)
# }
```

### Matching Blocks After External Edit

```python
from effilocal.doc.content_hash import match_blocks_by_hash
from effilocal.doc.uuid_embedding import ParaKey, TableCellKey

old_blocks = [{"id": "a", "text": "Original clause"}, ...]
new_blocks = [{"id": "temp1", "text": "Original clause"}, ...]

# With embedded UUIDs (paragraphs and table cells)
embedded = {"a": ParaKey(0), "cell-a": TableCellKey(0, 1, 2)}
result = match_blocks_by_hash(old_blocks, new_blocks, embedded_uuids=embedded)
# result.matches contains BlockMatch objects with old_id, new_id, method, confidence
```

### Auto-Commit on Save

```python
from effilocal.util.git_ops import auto_commit, generate_commit_message
from git import Repo

repo = Repo(".")
message = generate_commit_message("edit", {"blocks": 3})
commit_hash = auto_commit(repo, message, ["contract.docx", "analysis/"])
```

---

## Known Limitations

1. **Nested Content Controls**: Word may strip nested SDTs; use flat structure
2. **Hash Collisions**: Very similar clauses may match incorrectly; position heuristics help
3. **Headers/Footers**: Content in headers and footers is not tracked
4. **Multi-Paragraph Table Cells**: When a table cell contains multiple paragraphs, they are combined into a single block in `blocks.jsonl`. The UUID content control is wrapped around the first paragraph only.

---

## Future Enhancements

- "Repair UUIDs" command for recovery scenarios
- Use `w14:paraId` as additional matching signal
- Conflict resolution UI when hash matches multiple blocks
