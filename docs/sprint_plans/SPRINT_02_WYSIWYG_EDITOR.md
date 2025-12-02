# Sprint 2: WYSIWYG Editor Core

**Duration:** 2 weeks  
**Goal:** Replace read-only document view with a fully editable WYSIWYG interface.

---

## Objectives

1. **ContentEditable Editor** - Edit document text directly in webview
2. **Basic Formatting** - Bold, Italic, Underline via toolbar
3. **Block Structure** - Maintain paragraph/heading/list hierarchy
4. **Save to .docx** - Persist edits back to Word format

---

## User Stories

### US2.1: Direct Text Editing
**As a** lawyer reviewing a contract,  
**I want** to click on any clause and edit it directly,  
**So that** I can make quick corrections without leaving VS Code.

**Acceptance Criteria:**
- [ ] Clicking on text places cursor for editing
- [ ] Typing inserts/replaces text
- [ ] Enter key creates new paragraph
- [ ] Backspace at start of paragraph merges with previous
- [ ] Undo/Redo works (Ctrl+Z, Ctrl+Y)
- [ ] Test: Edit text → save → reopen → verify changes

### US2.2: Formatting Toolbar
**As a** lawyer emphasizing important terms,  
**I want** to make text bold, italic, or underlined,  
**So that** the contract formatting is clear.

**Acceptance Criteria:**
- [ ] Toolbar with B, I, U buttons
- [ ] Select text → click button → format applied
- [ ] Keyboard shortcuts: Ctrl+B, Ctrl+I, Ctrl+U
- [ ] Toggle behavior (click again to remove)
- [ ] Formatting visible in editor
- [ ] Test: Apply bold → save → verify bold in .docx

### US2.3: Clause Structure Preservation
**As a** lawyer editing a numbered clause,  
**I want** the numbering and hierarchy to remain intact,  
**So that** I don't break the contract structure.

**Acceptance Criteria:**
- [ ] Heading styles visible (larger font, bold)
- [ ] Numbered clauses show ordinals
- [ ] Indentation reflects hierarchy
- [ ] Editing text doesn't affect numbering
- [ ] Test: Edit clause 3.2.1 text → verify numbering unchanged

### US2.4: Save Document
**As a** lawyer who made edits,  
**I want** to save my changes to the .docx file,  
**So that** I can share the updated contract.

**Acceptance Criteria:**
- [ ] Save button in toolbar
- [ ] Ctrl+S keyboard shortcut
- [ ] "Unsaved changes" indicator
- [ ] Success notification on save
- [ ] Re-analysis triggered after save
- [ ] Test: Edit → Save → Open in Word → verify changes

---

## Technical Design

### Editor Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Webview Editor                       │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────┐    │
│  │  Toolbar: [B] [I] [U] | [Save] [Undo] [Redo]│    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │  Editor Container (ContentEditable)          │    │
│  │  ┌─────────────────────────────────────────┐│    │
│  │  │ <div class="block" data-id="uuid1">     ││    │
│  │  │   <span class="ordinal">1.1</span>      ││    │
│  │  │   <span contenteditable="true">text</span│    │
│  │  │ </div>                                   ││    │
│  │  │ <div class="block" data-id="uuid2">...  ││    │
│  │  └─────────────────────────────────────────┘│    │
│  └─────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────┤
│  Block Model (in-memory)                            │
│  blocks = [{ id, text, formatting, ... }, ...]      │
└─────────────────────────────────────────────────────┘
```

### Library Decision: Custom vs. Framework

**Options Considered:**
1. **Custom ContentEditable** - Full control, minimal dependencies
2. **Lexical (Meta)** - Modern, React-based, good performance
3. **ProseMirror** - Powerful, complex, Vue/React agnostic
4. **Quill** - Simple, good UX, limited customization

**Recommendation: Custom ContentEditable with careful implementation**

Rationale:
- Our editing needs are simple (no tables, images, complex nesting)
- Blocks are our unit of structure, not characters
- Easier to integrate with existing block model
- Smaller bundle size

### Technical Tasks

### T2.1: Editable Block Component (3 days)
**File:** `extension/src/webview/editor.js` (new)

```javascript
class BlockEditor {
  constructor(container, blocks) {
    this.container = container;
    this.blocks = blocks; // Reference to block array
    this.undoStack = [];
    this.redoStack = [];
  }
  
  render() {
    // Render blocks as editable divs
  }
  
  handleInput(blockId, newText) {
    // Update block, push to undo stack
  }
  
  handleKeydown(event, blockId) {
    // Handle Enter, Backspace, Tab
  }
  
  applyFormat(format) {
    // Apply bold/italic/underline to selection
  }
  
  getSelection() {
    // Get current selection with block context
  }
  
  undo() { /* ... */ }
  redo() { /* ... */ }
}
```

### T2.2: Formatting Implementation (2 days)
**File:** `extension/src/webview/formatting.js` (new)

```javascript
// Formatting is stored at run level in block model
// Block structure:
{
  id: "uuid",
  text: "This is bold and normal text",
  runs: [
    { start: 0, end: 8, formats: ["bold"] },  // "This is "
    { start: 8, end: 12, formats: [] },        // "and "
    // ...
  ]
}

function applyFormatToSelection(blocks, selection, format) {
  // Find affected blocks
  // Split runs at selection boundaries
  // Toggle format on affected runs
  // Merge adjacent runs with same formats
}

function renderBlockWithFormatting(block) {
  // Convert runs to HTML spans with appropriate classes
}
```

### T2.3: Toolbar Component (1 day)
**File:** `extension/src/webview/toolbar.js` (new)

```javascript
class Toolbar {
  constructor(editor) {
    this.editor = editor;
  }
  
  render() {
    return `
      <div class="toolbar">
        <button id="bold-btn" title="Bold (Ctrl+B)">B</button>
        <button id="italic-btn" title="Italic (Ctrl+I)">I</button>
        <button id="underline-btn" title="Underline (Ctrl+U)">U</button>
        <div class="separator"></div>
        <button id="undo-btn" title="Undo (Ctrl+Z)">↶</button>
        <button id="redo-btn" title="Redo (Ctrl+Y)">↷</button>
        <div class="separator"></div>
        <button id="save-btn" title="Save (Ctrl+S)">💾 Save</button>
        <span id="save-status"></span>
      </div>
    `;
  }
  
  updateButtonStates(selection) {
    // Highlight active formats based on selection
  }
}
```

### T2.4: Keyboard Shortcuts (1 day)
**File:** `extension/src/webview/shortcuts.js` (new)

```javascript
const SHORTCUTS = {
  'ctrl+b': () => editor.applyFormat('bold'),
  'ctrl+i': () => editor.applyFormat('italic'),
  'ctrl+u': () => editor.applyFormat('underline'),
  'ctrl+z': () => editor.undo(),
  'ctrl+y': () => editor.redo(),
  'ctrl+s': () => saveDocument(),
};

function setupShortcuts(editor) {
  document.addEventListener('keydown', (e) => {
    const key = getShortcutKey(e);
    if (SHORTCUTS[key]) {
      e.preventDefault();
      SHORTCUTS[key]();
    }
  });
}
```

### T2.5: Save Flow - Webview to Extension (2 days)
**File:** `extension/src/webview/save.js` (new)

```javascript
async function saveDocument() {
  const dirtyBlocks = editor.getDirtyBlocks();
  
  if (dirtyBlocks.length === 0) {
    showStatus('No changes to save');
    return;
  }
  
  showStatus('Saving...');
  
  vscode.postMessage({
    command: 'saveBlocks',
    blocks: editor.getBlocks(),
    documentPath: currentDocumentPath
  });
}

// Handle save result
window.addEventListener('message', (event) => {
  if (event.data.command === 'saveResult') {
    if (event.data.success) {
      showStatus('Saved ✓');
      editor.markClean();
    } else {
      showStatus('Save failed: ' + event.data.error);
    }
  }
});
```

### T2.6: Save Flow - Extension to Python (2 days)
**File:** `extension/src/extension.ts` (modify)

```typescript
// Handle save message from webview
case 'saveBlocks':
  await saveBlocksToDocument(message.blocks, message.documentPath);
  break;

async function saveBlocksToDocument(blocks: any[], documentPath: string) {
  const workspaceRoot = /* ... */;
  const pythonCmd = getPythonPath(workspaceRoot);
  const scriptPath = path.join(__dirname, '..', 'scripts', 'save_document.py');
  
  // Write blocks to temp file
  const tempPath = path.join(os.tmpdir(), 'effi_blocks.json');
  fs.writeFileSync(tempPath, JSON.stringify(blocks));
  
  // Call Python save script
  const { stdout, stderr } = await execAsync(
    `"${pythonCmd}" "${scriptPath}" "${documentPath}" "${tempPath}"`
  );
  
  // Parse result and notify webview
  const result = JSON.parse(stdout);
  webviewPanel?.webview.postMessage({
    command: 'saveResult',
    success: result.success,
    error: result.error
  });
  
  // Trigger re-analysis and git commit
  if (result.success) {
    await reanalyzeDocument(documentPath);
    await autoCommit(documentPath, 'edit', { blockCount: blocks.length });
  }
}
```

### T2.7: Python Save Script (3 days)
**File:** `extension/scripts/save_document.py` (new)

```python
"""Save edited blocks back to .docx format."""

import json
import sys
from pathlib import Path
from docx import Document

def save_blocks_to_docx(docx_path: Path, blocks: list) -> dict:
    """
    Update .docx with edited block content.
    
    Strategy:
    1. Load original document
    2. Find each block by para_id (native w14:paraId) or hash fallback
    3. Update paragraph text and formatting
    4. Preserve non-block content (headers, styles)
    5. Save document
    """
    try:
        doc = Document(docx_path)
        
        # Build para_id → paragraph mapping
        para_id_map = extract_para_id_mapping(doc)
        
        updated = 0
        for block in blocks:
            para = find_paragraph_for_block(doc, block, para_id_map)
            if para:
                update_paragraph(para, block)
                updated += 1
        
        doc.save(docx_path)
        
        return {
            "success": True,
            "updated": updated,
            "total": len(blocks)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def update_paragraph(para, block):
    """Update paragraph text and formatting from block data."""
    # Clear existing runs
    for run in para.runs:
        run.clear()
    
    # Add new runs based on block.runs
    for run_data in block.get('runs', [{'text': block['text'], 'formats': []}]):
        run = para.add_run(run_data['text'])
        if 'bold' in run_data.get('formats', []):
            run.bold = True
        if 'italic' in run_data.get('formats', []):
            run.italic = True
        if 'underline' in run_data.get('formats', []):
            run.underline = True

if __name__ == '__main__':
    docx_path = Path(sys.argv[1])
    blocks_path = Path(sys.argv[2])
    
    with open(blocks_path) as f:
        blocks = json.load(f)
    
    result = save_blocks_to_docx(docx_path, blocks)
    print(json.dumps(result))
```

---

## UI/UX Design

### Editor Appearance

```
┌─────────────────────────────────────────────────────────────┐
│ [B] [I] [U]  │  [↶] [↷]  │  [💾 Save] Saved ✓              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1.  DEFINITIONS                                            │
│                                                             │
│  1.1  "Agreement" means this services agreement including   │
│       all schedules and annexes.                            │
│                                                             │
│  1.2  "Business Day" means any day other than a Saturday,  │
│       Sunday, or public holiday in England.                 │
│                                                             │
│  2.  SERVICES                                               │
│                                                             │
│  2.1  The Supplier shall provide the Services to the       │
│       Customer in accordance with this Agreement.           │
│       ████████████████ ← cursor here                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Formatting States

| State | Toolbar Button | Text Appearance |
|-------|----------------|-----------------|
| Normal | `[B]` | Regular text |
| Bold selected | `[B]` highlighted | **Bold text** |
| Italic selected | `[I]` highlighted | *Italic text* |
| Mixed selection | `[B]` partial | Mixed **bold** and normal |

---

## Testing Plan

### Unit Tests
- `test_editor.js`: Block editing, merge, split
- `test_formatting.js`: Apply/remove formats, run merging
- `test_save.js`: Block serialization

### Integration Tests
- `test_roundtrip.py`: Edit → Save → Re-analyze → Verify

### Manual Tests
1. **Text editing:**
   - Click to place cursor
   - Type new text
   - Delete with backspace
   - Undo/redo changes

2. **Formatting:**
   - Select text, apply bold
   - Verify toolbar button highlights
   - Toggle format off
   - Save and verify in Word

3. **Edge cases:**
   - Edit clause with complex numbering
   - Edit text in table cell
   - Edit very long paragraph

---

## Definition of Done

- [ ] Can edit any text block in document
- [ ] B/I/U formatting works correctly
- [ ] Undo/Redo functional (10+ levels)
- [ ] Save persists changes to .docx
- [ ] Changes visible when opened in Word
- [ ] No data loss on save (non-edited content preserved)
- [ ] Keyboard shortcuts working
- [ ] Unit tests passing
- [ ] Documentation updated

---

## Dependencies

- Sprint 1 complete (para_id matching for save targeting)
- No external editor libraries (custom implementation)

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ContentEditable quirks | High | Medium | Test across browsers, document workarounds |
| Formatting loss on save | Medium | High | Preserve original run structure where possible |
| Cursor position issues | Medium | Medium | Track selection carefully, test edge cases |
| Performance with large docs | Low | Medium | Virtualize rendering if needed |

---

## Future Enhancements (Out of Scope)

- Copy/paste from external sources
- Find and replace
- Style picker (Heading 1, Normal, etc.)
- Image handling
- Table editing
