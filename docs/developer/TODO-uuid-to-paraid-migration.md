# UUID to w14:paraId Migration Task

## ✅ COMPLETED - December 2, 2025

All documentation and code comments have been updated to reflect the migration from custom UUID embedding to using Word's native `w14:paraId` attributes.

**Summary of changes:**
- Updated 11 documentation files to use para_id terminology
- Updated 2 schema files with corrected descriptions
- Renamed `_check_uuid_uniqueness` to `_check_id_uniqueness` in validate.py
- Clarified that `attachment_tools.py` uses w:tag for NEW paragraph tracking (separate purpose)
- All 162 tests passing

---

## Background

The codebase originally embedded custom UUIDs into Word documents using `<w:tag w:val="effi:block:UUID"/>` inside `<w:pPr>` elements. This approach was **abandoned** because:

1. **Schema violation**: `w:tag` inside `w:pPr` violates the OOXML schema (only valid in `w:sdtPr`)
2. **Word rejection**: Word refused to open documents with malformed XML
3. **Unnecessary**: Word already provides a native `w14:paraId` attribute on every paragraph (8-char hex, e.g., "05C9333F")

## New Approach (Already Implemented in Core)

The core logic has been refactored to use native `w14:paraId`:
- `effilocal/doc/uuid_embedding.py` - Now reads native para_ids, no embedding
- `effilocal/doc/content_hash.py` - Uses `para_id_map` parameter, `matched_by_para_id` stats
- `effilocal/flows/analyze_doc.py` - Uses `para_id_map` variable names
- `extension/src/extension.ts` - Dead code removed, messages updated

**What's NOT needed anymore:**
- Embedding custom UUIDs into documents
- The `embed_uuids.py` script (now a no-op)
- Error handling for "No embedded UUIDs"

## Task: Update Remaining Documentation & Comments

The following files contain **outdated references** to UUID embedding that need updating to reflect the new w14:paraId approach. Many are in documentation, schemas, and code comments.

---

## Priority 1: Documentation Files (High Impact)

### 1. `docs/synopsis.md`
**Lines 35, 109, 218** - Core project description still mentions w:tag UUID embedding

**Current (outdated):**
```markdown
* **Persistent UUID-based identities embedded in the `.docx` using paragraph tags (`w:pPr/w:tag`)**
```

**Should become:**
```markdown
* **Persistent block identities using Word's native `w14:paraId` attribute**
```

Similarly for line 109 and 218 which mention `<w:tag w:val="effi:block:<uuid>"/>`.

### 2. `docs/ARTIFACT_GUIDE.md`
**Lines 59, 480, 488, 605-630** - Example JSON uses placeholder UUIDs like "uuid-1", "uuid-3"

These are fine for example purposes (block IDs are still UUIDs), but comments could clarify:
- Line 59: Comment says "Unique block ID (UUID)" - keep as-is (block IDs are still UUIDs)
- Lines 605-630: Placeholder examples in artifact diff section - keep as-is

### 3. `docs/sprint_plans/SPRINT_01_FOUNDATION.md`
**Lines 10, 19, 25, 69-89, 148, 170-181** - Extensively describes the old w:tag embedding approach

Update "US1.1: UUID Embedding" section to describe the actual implementation using w14:paraId.

### 4. `docs/sprint_plans/SPRINT_ROADMAP.md`
**Lines 38, 50, 103-104, 150, 167** - References UUID embedding strategy

**Current:**
```markdown
│  - UUID management (embedded + hash fallback)                    │
```

**Should become:**
```markdown
│  - Block ID management (para_id + hash fallback)                 │
```

### 5. `docs/sprint_plans/SPRINT_02_WYSIWYG_EDITOR.md`
**Line 327, 471** - References "embedded UUID" for save targeting

### 6. `docs/developer/webview-architecture.md`
**Lines 199, 415** - References UUID embedding in architecture description

---

## Priority 2: Schema Files (Medium Impact)

### 7. `schemas/block.schema.json`
**Line 18** - Description mentions "embedded in .docx"

**Current:**
```json
"description": "Runtime UUID for the block. When Sprint 5 writes carriers, this value is embedded in the .docx."
```

**Should become:**
```json
"description": "Unique block ID. Matched to document paragraphs via native w14:paraId attribute."
```

### 8. `schemas/manifest.schema.json`
**Lines 32, 44** - References UUID persistence location and SDT markers

**Line 32 current:**
```json
"description": "Where block UUIDs are persisted in the .docx"
```

**Should become:**
```json
"description": "DEPRECATED - No longer used. Block IDs matched via native w14:paraId."
```

### 9. `schemas/edit_plan.schema.json`
**Lines 20, 30-31, 43, 56, 78, 89, 101-102, 118, 140, 152, 166, 180** - Uses `uuid` as definition name

These are internal schema references and can stay as-is since block IDs are still UUIDs. However, line 118 mentions "UUID SDTs" which should be updated.

---

## Priority 3: Python Code Comments (Low-Medium Impact)

### 10. `effilocal/flows/save_doc.py`
**Lines 1-4, 64, 71, 89, 93, 107, 111, 157, 159, 163** - Module docstring and function comments mention embedding

**Module docstring (lines 1-4):**
```python
"""Document save flow with UUID embedding and git integration.

This module handles:
1. Embedding block UUIDs as content controls
```

**Should become:**
```python
"""Document save flow with git integration.

Note: UUID embedding is no longer performed. We use native w14:paraId
for block matching. The embedding functions are kept as no-ops for
backward compatibility.
```

### 11. `effilocal/flows/analyze_doc.py`
**Lines 4, 272-278** - References "Extracts embedded UUIDs" and embedding

**Line 4:**
```python
- Extracts embedded UUIDs from content controls in .docx
```

**Should become:**
```python
- Uses native w14:paraId for block matching (no embedding needed)
```

### 12. `effilocal/mcp_server/utils/document_utils.py`
**Lines 55, 74** - Comments about not creating SDT wrappers

These are transitional comments that are now outdated. Should be simplified.

### 13. `effilocal/mcp_server/tools/attachment_tools.py`
**Lines 3, 21, 28, 30-31** - Uses uuid module and mentions w:tag for UUIDs

This code adds custom w:tag for attachment tracking - needs review if it's using the old approach.

### 14. `effilocal/util/validate.py`
**Lines 57, 70, 103, 107-108** - Function `_check_uuid_uniqueness` and error messages

These are for checking block ID uniqueness, which is still valid. Could rename to `_check_id_uniqueness` for clarity.

### 15. `effilocal/doc/models.py`
**Lines 14, 77, 79, 81, 87, 90, 92** - `uuid` field in TagRange and `make_block_range` function

These are for tag ranges (separate feature from paragraph identification). May still be valid.

### 16. `effilocal/artifact_loader.py`
**Lines 212, 232, 265, 317, 328, 347** - Docstring parameter descriptions say "UUID"

These refer to section/block/attachment IDs which are still UUIDs - the terminology is correct.

---

## Priority 4: Extension/Webview Code (Medium Impact)

### 17. `extension/src/webview/editor.js`
**Lines 22, 756** - JSDoc and function comment about "Block UUID" and "Generate a new UUID"

Line 22 is fine (block IDs are still UUIDs).
Line 756: If this is for generating new block IDs, it's still valid.

### 18. `extension/README.md`
**Line 104** - CLI example with `--doc-id <uuid>`

This is fine - doc-id is still a UUID, just not embedded into paragraphs.

---

## Priority 5: Test Files (Low Priority - Intentional Backward Compat)

### 19. `tests/test_uuid_embedding.py`
The entire file tests backward compatibility aliases. Function names like `test_embed_block_uuids_is_noop` are intentional to verify the deprecated functions still work.

**NO CHANGES NEEDED** - These test the backward compatibility layer.

### 20. `tests/test_content_hash.py`
**Lines 117, 143** - Imports from uuid_embedding module

These are valid - the module still exports the types.

---

## Priority 6: Other References (No Changes Needed)

The following are **valid uses** of `uuid` that should NOT be changed:

### Python stdlib `from uuid import uuid4`
Used for generating unique IDs for:
- `definition_tracker.py` - Definition IDs
- `attachment_tracker.py` - Attachment/section IDs
- `pipeline.py` - Section IDs
- `sections.py` - Section IDs
- `paragraphs.py` - Section IDs
- Various test files - Test data generation

### Block IDs are still UUIDs
Block IDs (`block.id`) are still UUID strings - just not embedded into documents. References to "block UUID" in the context of the block's ID field are correct.

### `tools/dispatcher.py` - `_coerce_uuid` function
This validates UUID-format strings and is still needed.

---

## Files That Can Be Deleted (Optional)

### `EL_Projects/Wiseflow/drafts/current_drafts/find_uuid.py`
Appears to be a one-off script for finding uuid references. Can be deleted.

---

## Summary Checklist

### Must Update:
- [x] `docs/synopsis.md` - Lines 35, 109, 218
- [x] `docs/sprint_plans/SPRINT_01_FOUNDATION.md` - "US1.1: UUID Embedding" section
- [x] `docs/sprint_plans/SPRINT_ROADMAP.md` - Lines 38, 50, 103-104
- [x] `effilocal/flows/save_doc.py` - Module docstring and comments
- [x] `effilocal/flows/analyze_doc.py` - Line 4 comment
- [x] `schemas/block.schema.json` - Line 18 description
- [x] `schemas/manifest.schema.json` - Lines 32, 44

### Should Update:
- [x] `docs/sprint_plans/SPRINT_02_WYSIWYG_EDITOR.md` - Lines 327, 471
- [x] `docs/developer/webview-architecture.md` - Lines 199, 415
- [x] `effilocal/mcp_server/utils/document_utils.py` - Lines 55, 74
- [x] `effilocal/mcp_server/tools/attachment_tools.py` - Reviewed: uses w:tag for NEW paragraph tracking (separate from para_id matching), clarified docstrings

### Nice to Have:
- [x] `effilocal/util/validate.py` - Renamed `_check_uuid_uniqueness` to `_check_id_uniqueness`
- [x] `schemas/edit_plan.schema.json` - Removed SDT reference from tag_add description

### Do NOT Change:
- `tests/test_uuid_embedding.py` - Backward compat tests
- `tests/test_content_hash.py` - Valid imports
- Python stdlib `from uuid import uuid4` usages
- References to block.id being a UUID

---

## How to Verify Changes

After making updates:

1. **Run tests**: `pytest tests/ -v --tb=short`
   - Should still have 162+ tests passing
   
2. **Compile extension**: 
   ```powershell
   $env:PATH = 'C:\Users\DavidSant\node-v25.2.1-win-x64;' + $env:PATH
   cd extension
   npm run compile
   ```

3. **Grep for remaining issues**: 
   ```powershell
   grep -rn "embed.*[Uu][Uu][Ii][Dd]|w:tag.*uuid|UUID.*embed" --include="*.py" --include="*.md" --include="*.json"
   ```

---

## Key Terminology

| Old Term | New Term | Context |
|----------|----------|---------|
| "embedded UUID" | "native para_id" | How blocks are matched to paragraphs |
| "UUID embedding" | "para_id matching" | The process of linking blocks to document |
| "w:tag w:val='effi:block:...'" | "w14:paraId attribute" | The XML element used |
| "embed_block_uuids()" | No-op (kept for compat) | The function is deprecated |
| "extract embedded UUIDs" | "extract para_ids" | Reading IDs from document |

## Reference Files (Already Updated)

These files have already been updated and can serve as examples:
- `effilocal/doc/uuid_embedding.py` - Core implementation
- `effilocal/doc/content_hash.py` - Uses para_id terminology
- `.github/copilot-instructions.md` - Full documentation of new approach
- `docs/developer/sprint-1-uuid-persistence.md` - Updated developer guide
- `extension/src/extension.ts` - Dead code removed, messages updated
