# Sprint 1: Block Identity & Git Integration

**Completed:** December 2025
**Status:** ✅ All tests passing (162 tests)

---

## Overview

Sprint 1 established stable document identity that survives external edits and re-analysis, plus integrated git version control.

## Features Implemented

### 1. Block Identification via Native w14:paraId

**Location:** `effilocal/doc/uuid_embedding.py`

Block identification uses the native `w14:paraId` attribute that Word provides on every paragraph. This is an 8-character hexadecimal value (e.g., "05C9333F") that Word maintains automatically.

**Why w14:paraId (not custom embedding):**
- `w:tag` elements inside `w:pPr` violate OOXML schema (only valid in `w:sdtPr`)
- Custom tags caused Word to refuse to open documents
- Native `w14:paraId` is always present, stable, and 100% schema-compliant
- No embedding needed - Word maintains these IDs automatically

**Key Functions:**

```python
# Read native w14:paraId from paragraph element
get_paragraph_para_id(para_elem: Element) -> str | None

# Find paragraph in document by its para_id
find_paragraph_by_para_id(doc: Document, para_id: str) -> Element | None

# Extract para_id → BlockKey mapping from document
extract_block_uuids(doc: Document | Path) -> dict[str, BlockKey]

# Assign block IDs using matching strategies
assign_block_ids(blocks: list[dict], para_id_map: dict[str, BlockKey], 
                 old_blocks: list[dict] | None = None) -> dict[str, str]
```

**Deprecated Functions (no-ops for backward compatibility):**
```python
embed_block_uuids(doc, blocks)      # Returns empty dict - no embedding needed
remove_all_uuid_tags(doc)           # Returns 0 - nothing to remove
set_paragraph_uuid(para_elem, uuid) # Returns True - no-op
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

**Native Paragraph ID Structure:**
```xml
<w:p w14:paraId="05C9333F" w14:textId="77777777">
  <w:pPr>
    <!-- paragraph properties -->
  </w:pPr>
  <!-- paragraph content -->
</w:p>
```

**Key Behaviors:**
- `w14:paraId` is present on every paragraph automatically
- Survives Word save/close/reopen cycles
- Survives copy/paste within same document
- 100% OOXML schema compliant
- **Supported locations:**
  - Top-level body paragraphs (matched by `para_idx`)
  - Paragraphs inside table cells (matched by `table: {table_id, row, col}`)
- **Not currently tracked:** headers, footers, text boxes

**ID Assignment Priority:**
When assigning block IDs during analysis:
1. **Para_id match** - Match to previous block at same para_id location
2. **Hash match** - Match by content hash (SHA-256 of normalized text)
3. **Position match** - Proximity heuristics for remaining blocks
4. **Generate new** - Create ID from para_id (e.g., "blk_05C9333F")

### 2. Content Hash Fallback

**Location:** `effilocal/doc/content_hash.py`

When para_ids don't match (e.g., document structure changed significantly), the system falls back to matching blocks by content hash.

**Key Functions:**

```python
# Compute SHA-256 of normalized text
compute_block_hash(text: str) -> str

# Three-phase matching: para_id → hash → position
match_blocks_by_hash(old_blocks: List[dict], new_blocks: List[dict], 
                     embedded_uuids: Dict[str, BlockKey] = None) -> MatchResult
```

**Matching Strategy (in priority order):**
1. **Para_id match** - Match by document's native w14:paraId attributes
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

### 4. Re-Analysis with Para_id Matching

**Location:** `effilocal/flows/analyze_doc.py`

When re-analyzing a document after external edits, existing block IDs are preserved where content matches.

**Enhanced Analysis Flow:**
1. Extract native `w14:paraId` attributes from .docx
2. Load previous `blocks.jsonl` if exists
3. Parse document into new blocks
4. Match new blocks to old by: para_id > hash > position
5. Assign matched IDs; generate new IDs for unmatched
6. Emit `analysis_delta.json` with change summary

**New Artifact:** `analysis_delta.json`
```json
{
  "timestamp": "2025-12-02T10:30:00Z",
  "matched_from_para_id": 45,
  "matched_from_hash": 3,
  "matched_from_position": 1,
  "new_blocks": ["uuid1", "uuid2"],
  "deleted_blocks": ["uuid3"],
  "modified_blocks": ["uuid4", "uuid5"]
}
```

### 5. Save Flow

**Location:** `effilocal/flows/save_doc.py`

**Key Functions:**

```python
# Save edited blocks back to document
save_blocks(docx_path: Path, blocks_path: Path) -> dict

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
| `extension/scripts/save_blocks.py` | Save edited blocks back to document |
| `extension/scripts/get_history.py` | Retrieve git commit history |
| `extension/scripts/embed_uuids.py` | DEPRECATED - no longer needed |

---

## File Structure

```
effilocal/
├── doc/
│   ├── uuid_embedding.py   # Para_id reading and block ID assignment
│   └── content_hash.py     # Hash-based matching
├── util/
│   └── git_ops.py          # Git commit/history operations
└── flows/
    ├── analyze_doc.py      # Enhanced with para_id matching
    └── save_doc.py         # Save blocks back to document

extension/scripts/
├── save_blocks.py          # CLI wrapper for save flow
├── get_history.py          # CLI wrapper for git history
└── embed_uuids.py          # DEPRECATED - no longer needed
```

---

## Test Coverage

All tests in `tests/` directory:

| Test File | Coverage |
|-----------|----------|
| `test_uuid_embedding.py` | Para_id extraction, block ID assignment (27 tests) |
| `test_content_hash.py` | Hash computation, matching strategies |
| `test_git_ops.py` | Commit, history retrieval, checkpoint |

**Key Test Cases:**
- Para_ids are correctly extracted from paragraphs
- Para_ids are case-insensitive for matching
- Hash fallback matches blocks when para_ids don't match
- Position heuristics resolve ambiguous hash matches
- Deprecated functions work as no-ops for backward compatibility
- Git commits only when changes exist

---

## Usage Examples

### Reading Para_ids Programmatically

```python
from docx import Document
from effilocal.doc.uuid_embedding import (
    get_paragraph_para_id, 
    find_paragraph_by_para_id,
    extract_block_uuids,
    ParaKey, 
    TableCellKey
)

# Load document
doc = Document("contract.docx")

# Read para_id from a specific paragraph
para = doc.paragraphs[0]._element
para_id = get_paragraph_para_id(para)  # e.g., "05C9333F"

# Find paragraph by para_id
found = find_paragraph_by_para_id(doc, "05C9333F")

# Extract all para_ids as mapping
para_id_map = extract_block_uuids(doc)
# {
#   "05C9333F": ParaKey(para_idx=0),
#   "1A2B3C4D": ParaKey(para_idx=1),
#   "DEADBEEF": TableCellKey(table_idx=0, row=0, col=0)
# }
```

### Matching Blocks After External Edit

```python
from effilocal.doc.content_hash import match_blocks_by_hash
from effilocal.doc.uuid_embedding import ParaKey, TableCellKey

old_blocks = [{"id": "a", "text": "Original clause"}, ...]
new_blocks = [{"id": "temp1", "text": "Original clause"}, ...]

# With para_id map from document
para_id_map = {"a": ParaKey(0), "cell-a": TableCellKey(0, 1, 2)}
result = match_blocks_by_hash(old_blocks, new_blocks, embedded_uuids=para_id_map)
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

1. **Para_id Uniqueness**: Word generates para_ids; duplicates are rare but possible after copy/paste
2. **Hash Collisions**: Very similar clauses may match incorrectly; position heuristics help
3. **Headers/Footers**: Content in headers and footers is not tracked
4. **Multi-Paragraph Table Cells**: When a table cell contains multiple paragraphs, they are combined into a single block in `blocks.jsonl`.

---

## Architecture Decision: Why w14:paraId

The original approach embedded custom UUIDs using `<w:tag w:val="effi:block:UUID"/>` inside `<w:pPr>`. This was abandoned because:

1. **OOXML Schema Violation**: `<w:tag>` is only valid inside `<w:sdtPr>` (Structured Document Tag Properties), not inside `<w:pPr>` (Paragraph Properties)
2. **Word Rejection**: Documents with invalid `w:tag` placement caused Word to refuse to open them
3. **Unnecessary Complexity**: Word already provides stable paragraph IDs via `w14:paraId`

The current approach reads the native `w14:paraId` attribute that Word automatically maintains on every `<w:p>` element. Benefits:
- 100% OOXML schema compliant
- No document corruption risk
- No embedding/extraction needed
- Survives all Word operations
