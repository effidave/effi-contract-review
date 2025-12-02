# Sprint 1: Foundation & UUID Persistence

**Duration:** 2 weeks  
**Goal:** Establish stable document identity that survives external edits and re-analysis, plus hybrid git integration.

---

## Objectives

1. **Embed UUIDs in .docx** - Block IDs persist inside the Word document
2. **Hash-based fallback** - Recover identity when UUIDs are lost
3. **Hybrid git commits** - Auto-commit on save with meaningful messages
4. **Re-analysis stability** - Preserve UUIDs when document is re-analyzed

---

## User Stories

### US1.1: UUID Embedding
**As a** lawyer editing a contract in Word,  
**I want** the system to remember which clause is which after I save,  
**So that** my notes and LLM context remain attached to the right clauses.

**Acceptance Criteria:**
- [ ] Each block gets a UUID embedded as a content control tag
- [ ] UUID survives save/close/reopen cycle in Word
- [ ] UUID survives copy/paste within same document
- [ ] Test: Create doc → add content controls → save → reopen → verify UUIDs intact

### US1.2: Hash Fallback Recovery
**As a** lawyer who edited a contract in Word and accidentally removed formatting,  
**I want** the system to match paragraphs by content when UUIDs are lost,  
**So that** I don't lose my annotation history.

**Acceptance Criteria:**
- [ ] Each block stores a `content_hash` (SHA-256 of normalized text)
- [ ] Re-analysis first tries UUID match, then hash match
- [ ] Position heuristics used when hash matches multiple candidates
- [ ] Test: Remove content controls → re-analyze → verify 90%+ blocks matched

### US1.3: Hybrid Git Integration
**As a** lawyer saving my work,  
**I want** changes automatically committed with a useful message,  
**So that** I have a complete audit trail without manual git commands.

**Acceptance Criteria:**
- [ ] Save triggers git commit of .docx + analysis artifacts
- [ ] Commit message format: `[effi] <action>: <summary>`
- [ ] "Major save" option for explicit checkpoints
- [ ] Commits only when there are actual changes
- [ ] Test: Edit → Save → verify commit appears with correct message

### US1.4: Re-Analysis UUID Preservation
**As a** system re-analyzing a document after external edits,  
**I want** to preserve existing block UUIDs where content matches,  
**So that** references in notes/history remain valid.

**Acceptance Criteria:**
- [ ] Re-analysis loads previous `blocks.jsonl` for UUID matching
- [ ] Matched blocks keep their UUID; new blocks get new UUIDs
- [ ] Deleted blocks noted in `analysis_delta.json`
- [ ] Test: Edit doc externally → re-analyze → verify UUID continuity

---

## Technical Tasks

### T1.1: Content Control Implementation (3 days)
**File:** `effilocal/doc/uuid_embedding.py` (new)

```python
# Core functions needed:
def embed_block_uuids(doc: Document, blocks: List[dict]) -> None:
    """Insert content controls with UUID tags into document."""
    
def extract_block_uuids(doc: Document) -> Dict[str, str]:
    """Extract UUID → paragraph mapping from content controls."""
    
def remove_all_uuid_controls(doc: Document) -> int:
    """Remove all effi content controls (for testing/reset)."""
```

**Implementation Notes:**
- Use `python-docx` OxmlElement for content control manipulation
- Content control structure:
  ```xml
  <w:sdt>
    <w:sdtPr>
      <w:tag w:val="effi:block:uuid-here"/>
      <w:id w:val="12345"/>
    </w:sdtPr>
    <w:sdtContent>
      <w:p>...</w:p>
    </w:sdtContent>
  </w:sdt>
  ```
- Handle edge cases: tables, nested structures

### T1.2: Content Hash Implementation (1 day)
**File:** `effilocal/doc/content_hash.py` (new)

```python
def compute_block_hash(text: str) -> str:
    """Compute SHA-256 of normalized text."""
    # Normalize: lowercase, collapse whitespace, strip punctuation
    
def match_blocks_by_hash(
    old_blocks: List[dict], 
    new_blocks: List[dict]
) -> List[Tuple[str, str]]:  # (old_id, new_id) pairs
    """Match blocks using hash + position heuristics."""
```

### T1.3: Git Integration (2 days)
**File:** `effilocal/util/git_ops.py` (new)

```python
def auto_commit(
    repo_path: Path,
    message: str,
    files: List[Path]
) -> Optional[str]:  # commit hash or None if nothing to commit
    """Stage specified files and commit if there are changes."""
    
def generate_commit_message(
    action: str,  # 'edit', 'analyze', 'checkpoint'
    details: dict
) -> str:
    """Generate formatted commit message."""
```

**Extension Changes:**
- `extension.ts`: Call git commit after save operations
- Add setting: `effiContractViewer.autoCommit` (default: true)

### T1.4: Re-Analysis with UUID Matching (3 days)
**File:** `effilocal/flows/analyze_doc.py` (modify)

```python
def analyze(
    docx_path: Path,
    *,
    doc_id: str,
    out_dir: Path,
    preserve_uuids: bool = True,  # NEW
    # ...
) -> dict[str, Path]:
    """
    Enhanced analysis flow:
    1. Extract embedded UUIDs from docx
    2. Load previous blocks.jsonl if exists
    3. Parse document into new blocks
    4. Match new blocks to old by: UUID > hash > position
    5. Assign matched UUIDs, generate new for unmatched
    6. Emit analysis_delta.json with changes
    """
```

**New artifact:** `analysis_delta.json`
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

### T1.5: Save Flow with UUID Embedding (2 days)
**File:** `effilocal/flows/save_doc.py` (new)

```python
def save_document(
    blocks: List[dict],
    output_path: Path,
    original_docx: Path = None,
    preserve_formatting: bool = True
) -> None:
    """
    Save blocks back to .docx with embedded UUIDs.
    
    If original_docx provided, try to preserve non-block content
    (headers, footers, styles, etc.)
    """
```

### T1.6: Extension Integration (2 days)

**extension.ts changes:**
- Add "Save & Commit" command
- Add "Save Checkpoint" command (explicit major save)
- Show git commit status in status bar
- Handle save failures gracefully

**webview/main.js changes:**
- Add save button to toolbar
- Show "saved" / "unsaved changes" indicator
- Debounce frequent edits before marking unsaved

---

## Testing Plan

### Unit Tests
- `test_uuid_embedding.py`: Content control creation/extraction
- `test_content_hash.py`: Hash computation and matching
- `test_git_ops.py`: Commit generation (mock git)

### Integration Tests
- `test_analyze_with_uuid_preservation.py`:
  1. Analyze fresh document
  2. Modify document externally
  3. Re-analyze
  4. Verify UUID continuity

### Manual Tests
1. **Round-trip test:**
   - Create document in extension
   - Open in Word, make edits
   - Re-open in extension
   - Verify blocks matched correctly

2. **UUID loss recovery:**
   - Create document with UUIDs
   - Strip content controls (manual or tool)
   - Re-analyze
   - Verify hash fallback worked

---

## Definition of Done

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Manual round-trip test successful
- [ ] Documentation updated:
  - [ ] `copilot-instructions.md` updated with UUID details
  - [ ] `ARTIFACT_GUIDE.md` updated with `analysis_delta.json`
- [ ] No regressions in existing functionality
- [ ] Code reviewed and merged

---

## Dependencies

- **python-docx:** Content control XML manipulation
- **gitpython:** Git operations (or subprocess calls)

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Content controls break Word compatibility | Low | High | Test with multiple Word versions |
| Hash collisions on similar clauses | Medium | Medium | Add position weight to matching |
| Git conflicts with external tools | Low | Low | Document git workflow |

---

## Notes

- Content controls are the most robust embedding method, but fall back gracefully
- Consider adding a "repair UUIDs" command for recovery scenarios
- Future: Could use `w14:paraId` as additional matching signal (already available)
