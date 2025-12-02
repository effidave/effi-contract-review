# Sprint 2: WYSIWYG Editor Core

**Completed:** December 2025  
**Status:** ✅ All tests passing

---

## Overview

Sprint 2 replaced the read-only document view with a fully editable WYSIWYG interface. Users can now edit contract text directly in VS Code, apply formatting, and save changes back to the .docx file.

## Features Implemented

### 1. BlockEditor - Editable Document Interface

**Location:** `extension/src/webview/editor.js`

The BlockEditor class provides ContentEditable-based editing of document blocks.

**Key Class: `BlockEditor`**

```javascript
class BlockEditor {
    constructor(container, blocks, options)
    
    // Rendering
    render()                        // Render all blocks as editable divs
    renderBlock(block)              // Render single block with ordinal + text
    renderRuns(runs, text)          // Render formatted text spans
    
    // Editing
    handleInput(blockElement)       // Handle text input, update block model
    handleKeydown(event, block)     // Handle Enter (split) / Backspace (merge)
    applyFormat(format)             // Apply bold/italic/underline to selection
    
    // Selection
    getSelection()                  // Get current selection with block context
    saveSelection()                 // Save selection state
    restoreSelection()              // Restore selection after DOM update
    
    // History
    undo()                          // Undo last change
    redo()                          // Redo undone change
    pushSnapshot()                  // Save current state to history
    
    // State
    getBlocks()                     // Get all blocks
    getDirtyBlocks()                // Get only modified blocks
    markClean()                     // Clear dirty flags after save
}
```

**Block Structure:**
```javascript
{
    id: "uuid-here",
    text: "This is bold and normal text",
    list: { ordinal: "1.2.3", level: 2 },
    runs: [
        { start: 0, end: 8, formats: ["bold"] },
        { start: 8, end: 28, formats: [] }
    ],
    dirty: true  // Set when modified
}
```

**DOM Structure:**
```html
<div class="editor-block" data-id="uuid">
    <span class="block-ordinal-display">1.2.3</span>
    <div class="block-editable" contenteditable="true">
        <span class="fmt-bold">This is </span>
        <span>bold and normal text</span>
    </div>
</div>
```

### 2. Formatting System

**Run-Based Formatting:**

Text formatting is stored as "runs" - spans of text with specific formatting. When the user applies formatting:

1. Get current selection (start/end offsets within block)
2. Split existing runs at selection boundaries
3. Toggle format on affected runs
4. Merge adjacent runs with identical formatting

**Format Application:**
```javascript
applyFormat(format) {
    // format = 'bold' | 'italic' | 'underline'
    const sel = this.getSelection();
    if (!sel || sel.start === sel.end) return;
    
    // Split runs and toggle format
    this.splitRuns(sel.block, sel.start, sel.end);
    this.toggleFormatOnRange(sel.block, sel.start, sel.end, format);
    this.mergeAdjacentRuns(sel.block);
    
    // Re-render and restore cursor
    this.renderBlock(sel.block);
    this.restoreSelection();
}
```

### 3. Toolbar Component

**Location:** `extension/src/webview/toolbar.js`

**Key Class: `Toolbar`**

```javascript
class Toolbar {
    constructor(container, editor, options)
    
    render()                        // Render toolbar HTML
    setSaveStatus(status, message)  // Update save indicator
}
```

**Toolbar Layout:**
```
[B] [I] [U]  |  [↶] [↷]  |  [💾 Save] Saved ✓
```

**Buttons:**
| Button | Action | Shortcut |
|--------|--------|----------|
| **B** | Bold | Ctrl+B |
| *I* | Italic | Ctrl+I |
| <u>U</u> | Underline | Ctrl+U |
| ↶ | Undo | Ctrl+Z |
| ↷ | Redo | Ctrl+Y |
| Save | Save to .docx | Ctrl+S |

**Save Status Indicators:**
- `Saved ✓` (green) - No unsaved changes
- `Unsaved changes` (red) - Document modified
- `Saving...` (yellow) - Save in progress
- `Save failed` (red) - Error occurred

### 4. Keyboard Shortcuts

**Location:** `extension/src/webview/shortcuts.js`

**Key Class: `ShortcutManager`**

```javascript
class ShortcutManager {
    constructor(editor, handlers)
    
    attach(target)      // Attach keydown listener
    detach()            // Remove listener
}
```

**Registered Shortcuts:**
| Shortcut | Action |
|----------|--------|
| Ctrl+B | Toggle bold |
| Ctrl+I | Toggle italic |
| Ctrl+U | Toggle underline |
| Ctrl+S | Save document |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+Shift+Z | Redo (alternative) |

### 5. Save Flow

**Webview → Extension → Python**

1. **User clicks Save** (or Ctrl+S)
2. **Webview** calls `saveEdits()` which:
   - Gets dirty blocks from editor
   - Posts `saveBlocks` message to extension
   - Shows "Saving..." status

3. **Extension** receives message and:
   - Writes blocks to temp JSON file
   - Calls Python `save_blocks.py` script
   - Waits for result

4. **Python script**:
   - Loads document
   - Extracts UUID → paragraph mapping
   - Updates matched paragraphs with new text/formatting
   - Saves document

5. **Extension** sends result back:
   - `saveComplete` or `saveError` message
   - Toolbar updates status accordingly

**Save Script:** `extension/scripts/save_blocks.py`

```python
def save_blocks_to_document(doc_path: str, blocks_path: str) -> dict:
    # Load blocks from JSON
    # Load document
    # Extract UUID map
    # Update paragraphs by UUID
    # Save document
    return {"success": True, "block_count": N}
```

### 6. Edit Mode Toggle

The Full Text view now has an "Edit Mode" toggle button:

- **📖 View Mode** - Read-only display (original)
- **✏️ Edit Mode** - Editable with toolbar

Clicking the button switches between modes. Edit mode:
- Shows the editor toolbar
- Makes blocks editable
- Enables formatting and save

---

## Extension Integration

### Script Loading

Editor scripts are loaded before main.js in the webview HTML:

```html
<script src="${editorUri}"></script>
<script src="${toolbarUri}"></script>
<script src="${shortcutsUri}"></script>
<script src="${scriptUri}"></script>
```

### Message Handlers

**New webview → extension messages:**

| Message | Payload | Handler |
|---------|---------|---------|
| `saveBlocks` | `{blocks, documentPath}` | `saveBlocksToDocument()` |

**New extension → webview messages:**

| Message | Payload | Purpose |
|---------|---------|---------|
| `saveComplete` | `{message}` | Notify save success |
| `saveError` | `{message}` | Notify save failure |

---

## File Structure

```
extension/src/webview/
├── editor.js        # BlockEditor class
├── toolbar.js       # Toolbar component
├── shortcuts.js     # ShortcutManager
├── main.js          # Integration (modified)
└── style.css        # Editor styles (added)

extension/scripts/
└── save_blocks.py   # Save edited blocks to .docx
```

---

## Styling

**New CSS Classes:**

```css
/* Editor container */
.editor-container { }
.editor-toolbar-container { }

/* Editable blocks */
.editor-block { }
.editor-block:focus-within { }
.editor-block.dirty { }

/* Non-editable ordinal */
.block-ordinal-display { }

/* Editable text area */
.block-editable { }
.block-editable:focus { }

/* Formatting classes */
.fmt-bold { font-weight: 700; }
.fmt-italic { font-style: italic; }
.fmt-underline { text-decoration: underline; }

/* Toolbar */
.editor-toolbar { }
.toolbar-btn { }
.toolbar-btn.active { }
.save-status { }
```

---

## Usage Example

### Editing a Clause

1. Open contract document in VS Code
2. Click book icon to open Contract Analysis panel
3. Navigate to **Full Text** tab
4. Click **✏️ Edit Mode** button
5. Click on any clause text to place cursor
6. Make edits:
   - Type to insert text
   - Select text and click **B** for bold
   - Press Ctrl+Z to undo
7. Click **Save** or press Ctrl+S
8. Changes are saved to .docx file

### Programmatic Block Update

```javascript
// In webview context
const blocks = blockEditor.getBlocks();

// Modify a block
blocks[0].text = "Updated text";
blocks[0].runs = [{ start: 0, end: 12, formats: ["bold"] }];
blocks[0].dirty = true;

// Re-render
blockEditor.render();

// Save
saveEdits();
```

---

## Known Limitations

1. **Table Editing**: Tables are displayed but not editable in this sprint
2. **Complex Formatting**: Only B/I/U supported; styles, fonts, colors not yet implemented
3. **Large Documents**: No virtualization; may be slow with 500+ blocks
4. **Copy/Paste**: Pasting formatted text may lose formatting

---

## Future Enhancements

- Find and replace
- Style picker (Heading, Normal, etc.)
- Table cell editing
- Image support
- Copy/paste with formatting preservation
- Virtualized rendering for large documents
