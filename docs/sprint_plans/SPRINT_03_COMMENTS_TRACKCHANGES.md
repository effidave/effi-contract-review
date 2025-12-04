# Sprint 3: Comments & Track Changes

**Duration:** 2 weeks  
**Goal:** Full commenting and revision tracking within the editor.

---

## Pre-Sprint Analysis

### Current State (What's Already Done)

**Comment Extraction** (`effilocal/mcp_server/core/comments.py`):
- ✅ Extracts comment_id, para_id, author, initials, date, text
- ✅ Status extraction from `commentsExtended.xml` (active/resolved)
- ✅ `is_resolved` and `done_flag` fields populated
- ✅ Paragraph index mapping via `w:commentReference` scanning
- ✅ MCP tools: `get_all_comments`, `get_comments_by_author`, `add_word_comment`

**Extension Webview** (`extension/src/webview/`):
- ✅ Block-based WYSIWYG editor (Sprint 2)
- ✅ BlockEditor class with contentEditable
- ✅ Toolbar with B/I/U, undo/redo, save
- ✅ Keyboard shortcuts (Ctrl+B/I/U/S/Z/Y)
- ✅ View/Edit mode toggle
- ✅ Extension ↔ webview messaging infrastructure
- ✅ Para_id matching for document identity (Sprint 1)

### Gaps to Fill

**Comment Enhancements Needed:**
- ❌ Anchor extraction (start/end character offsets from `w:commentRangeStart`/`w:commentRangeEnd`)
- ⏸️ Reply threading (deferred - show flat list for MVP)
- ❌ `resolve_comment()` function (update commentsExtended.xml done flag)
- ❌ `delete_comment()` function
- ❌ `reference_text` field always empty currently

**Track Changes (All New):**
- ❌ Revision extraction (parse `<w:ins>`, `<w:del>`, `<w:rPrChange>`)
- ❌ Accept/reject individual revisions
- ❌ Bulk accept/reject all

**UI Components (All New):**
- ❌ Comment panel sidebar
- ❌ Inline comment indicators in editor
- ❌ Context menu for adding comments
- ❌ Track changes visualization (ins/del styling)
- ❌ Accept/reject buttons

### Architectural Decisions

1. **Comments as Sidecar Data**: Keep comments separate from blocks, linked by para_id. This matches Word's architecture where comments are stored in separate XML parts.

2. **Revision Storage**: Store revisions inline within blocks during extraction (each block may contain multiple revisions). This simplifies rendering since changes are already position-mapped.

3. **Comment Panel Position**: Right sidebar (250px) that scrolls independently. Comments linked to visible blocks should scroll into view when block is focused.

4. **Extension Scripts Bridge**: Use Python scripts in `extension/scripts/` for comment/revision operations, matching the existing `save_blocks.py` pattern.

---

## Objectives

1. **Comment Display** - Show existing Word comments inline
2. **Add Comments** - Create new comments on selected text
3. **Track Changes View** - Visualize insertions, deletions, modifications
4. **Accept/Reject** - Process tracked changes individually or in bulk

---

## User Stories

### US3.1: View Comments
**As a** lawyer reviewing a contract,  
**I want** to see comments from other parties inline,  
**So that** I can understand their concerns without opening Word.

**Acceptance Criteria:**
- [ ] Comments visible as margin indicators
- [ ] Hover/click shows comment content
- [ ] Comment author and date visible
- [ ] Resolved vs active status shown
- [ ] Test: Open doc with comments → verify all visible

### US3.2: Add Comments
**As a** lawyer drafting a contract,  
**I want** to add comments to specific clauses,  
**So that** I can note issues for later or communicate with counterparties.

**Acceptance Criteria:**
- [ ] Select text → right-click → "Add Comment"
- [ ] Comment input appears
- [ ] Comment saved to .docx
- [ ] Comment linked to correct text range
- [ ] Test: Add comment → save → open in Word → verify comment

### US3.3: Reply to Comments *(Deferred to future sprint)*
**As a** lawyer responding to counterparty comments,  
**I want** to reply to existing comments,  
**So that** we can have a threaded discussion.

**Status:** Deferred - showing flat comment list for MVP

**Acceptance Criteria:** (Future Sprint)
- [ ] "Reply" option on existing comments
- [ ] Replies threaded under parent
- [ ] Replies saved to .docx
- [ ] Test: Reply → save → verify thread in Word

### US3.4: Resolve Comments
**As a** lawyer who addressed a comment,  
**I want** to mark it as resolved,  
**So that** I can track which issues are closed.

**Acceptance Criteria:**
- [ ] "Resolve" button on comments
- [ ] Resolved comments visually distinct (grayed/collapsed)
- [ ] Resolved status saved to .docx
- [ ] Test: Resolve → save → verify in Word

### US3.5: Track Changes Display
**As a** lawyer reviewing a redlined contract,  
**I want** to see what changed since the last version,  
**So that** I can focus my review on modified clauses.

**Acceptance Criteria:**
- [ ] Insertions shown with green background + underline
- [ ] Deletions shown with red strikethrough
- [ ] Change author visible on hover
- [ ] Changes linked to specific blocks
- [ ] Test: Open doc with tracked changes → verify display

### US3.6: Accept/Reject Changes
**As a** lawyer finalizing a contract,  
**I want** to accept or reject individual changes,  
**So that** I can produce a clean final version.

**Acceptance Criteria:**
- [ ] "Accept" / "Reject" buttons per change
- [ ] "Accept All" / "Reject All" bulk actions
- [ ] Accepted changes become permanent
- [ ] Rejected changes removed
- [ ] Test: Accept some, reject others → save → verify in Word

---

## Technical Design

### Existing Implementation Details

**Current Comment Data Structure** (from `extract_comment_data()` in `comments.py`):
```python
{
    'id': 'comment_1',           # Internal sequential ID
    'comment_id': '0',           # Word's w:id attribute
    'para_id': '3DD8236A',       # w14:paraId - links to commentsExtended.xml
    'author': 'John Smith',
    'initials': 'JS',
    'date': '2025-12-02T10:30:00Z',
    'text': 'Comment text content',
    'paragraph_index': 5,        # Index in document body (via w:commentReference scan)
    'in_table': False,
    'reference_text': '',        # TODO: Currently always empty - need to extract
    'status': 'active',          # From commentsExtended.xml ('active' or 'resolved')
    'is_resolved': False,        # Boolean convenience
    'done_flag': 0               # Raw value (0=active, 1=resolved)
}
```

**Status Extraction Mechanism:**
- `commentsExtended.xml` contains `w15:commentEx` elements with `w15:paraId` and `w15:done`
- `extract_comment_status_map()` builds a mapping: `{para_id: {status, done, is_resolved}}`
- `merge_comment_status()` links status to comments via para_id matching

**Existing MCP Tools** (in `effilocal/mcp_server/main.py`):
- `get_all_comments` - Calls `extract_all_comments()`
- `get_comments_by_author` - Filters by author name
- `add_word_comment` - Creates new comment (from upstream word_document_server)
- `add_word_comment_near_text` - Adds comment near specific text

### Enhanced Comment Data Model

```javascript
// Extended from current implementation
{
  id: "comment_1",
  comment_id: "0",
  para_id: "3DD8236A",
  author: "John Smith",
  initials: "JS",
  date: "2025-12-02T10:30:00Z",
  text: "This clause needs review",
  status: "active",
  is_resolved: false,
  done_flag: 0,
  paragraph_index: 5,
  
  // NEW: Anchor information (paragraph-level for MVP)
  anchor: {
    para_id: "3DD8236A",          // Paragraph the comment is attached to
    text: "anchored text"          // The text the comment references (nice-to-have)
  }
  
  // DEFERRED: Reply threading (flat list for MVP)
  // parent_comment_id: null,
  // replies: [...]
}
```

### Track Change Data Model

```javascript
// Change stored as revision
{
  id: "change-uuid",
  type: "insert" | "delete" | "modify",
  blockId: "block-uuid",
  author: "John Smith",
  date: "2025-12-02T10:30:00Z",
  // For insert:
  insertedText: "new text",
  insertPosition: 25,
  // For delete:
  deletedText: "old text",
  deleteStart: 10,
  deleteEnd: 20,
  // For modify:
  originalText: "old",
  newText: "new",
  position: 30
}
```

### UI Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ [B] [I] [U]  │  [↶] [↷]  │  [💾 Save]  │  [📝 Track: ON]           │
├───────────────────────────────────────────────────┬─────────────────┤
│                                                   │ Comments        │
│  1.1  "Agreement" means this services             │ ┌─────────────┐ │
│       agreement ████████████████ including       │ │ 📝 J.Smith  │ │
│       all schedules.    ↑ inserted                │ │ Dec 2, 10:30│ │
│                                                   │ │ "Is this    │ │
│  1.2  "Business Day" means any day other         │ │  broad      │ │
│       than Saturday or ████████ public           │ │  enough?"   │ │
│       holiday.          ↑ deleted                 │ │ [Reply]     │ │
│                                                   │ │ [Resolve]   │ │
│                                                   │ └─────────────┘ │
│                                                   │                 │
│  2.1  The Supplier shall provide the             │ ┌─────────────┐ │
│       Services to the Customer...                 │ │ ✓ Resolved  │ │
│                                                   │ │ "Fixed"     │ │
│                                                   │ └─────────────┘ │
└───────────────────────────────────────────────────┴─────────────────┘
```

---

## Technical Tasks

### T3.1: Comment Extraction Enhancement (2 days)
**File:** `effilocal/mcp_server/core/comments.py` (modify)

Already extracts comments with status. Enhance to include:
- Anchor position (start/end character offsets)
- Reply threading
- Block ID association

```python
def extract_all_comments(doc_path: str) -> list:
    """
    Extract comments with full metadata.
    
    Returns:
    [
        {
            "id": "123",
            "text": "Comment text",
            "author": "John Smith",
            "date": "2025-12-02T10:30:00Z",
            "status": "active",
            "para_id": "3DD8236A",  # Word's paragraph ID
            "anchor": {
                "start": 15,
                "end": 45,
                "text": "anchored text"
            },
            "replies": [...]
        }
    ]
    """
```

### T3.2: Track Changes Extraction (3 days)
**File:** `effilocal/mcp_server/core/revisions.py` (new)

```python
def extract_revisions(doc_path: str) -> list:
    """
    Extract tracked changes from document.
    
    Parses:
    - <w:ins> (insertions)
    - <w:del> (deletions)
    - <w:rPrChange> (formatting changes)
    """

def accept_revision(doc_path: str, revision_id: str) -> dict:
    """Accept a specific revision, making it permanent."""

def reject_revision(doc_path: str, revision_id: str) -> dict:
    """Reject a revision, removing the change."""

def accept_all_revisions(doc_path: str) -> dict:
    """Accept all tracked changes."""
```

### T3.3: Comment Panel Component (2 days)
**File:** `extension/src/webview/comments.js` (new)

```javascript
class CommentPanel {
  constructor(container, comments) {
    this.container = container;
    this.comments = comments;
  }
  
  render() {
    // Render comment cards with replies
  }
  
  highlightAnchor(commentId) {
    // Highlight associated text in editor
  }
  
  addComment(blockId, start, end, text) {
    // Create new comment
  }
  
  addReply(commentId, text) {
    // Add reply to existing comment
  }
  
  resolveComment(commentId) {
    // Mark as resolved
  }
}
```

### T3.4: Inline Change Display (2 days)
**File:** `extension/src/webview/track-changes.js` (new)

```javascript
function renderBlockWithChanges(block, revisions) {
  // Build HTML with change annotations
  let html = '';
  let offset = 0;
  
  // Sort revisions by position
  const sorted = revisions
    .filter(r => r.blockId === block.id)
    .sort((a, b) => a.position - b.position);
  
  for (const rev of sorted) {
    // Add text before this change
    html += escapeHtml(block.text.slice(offset, rev.position));
    
    if (rev.type === 'insert') {
      html += `<ins class="change" data-id="${rev.id}">${escapeHtml(rev.insertedText)}</ins>`;
    } else if (rev.type === 'delete') {
      html += `<del class="change" data-id="${rev.id}">${escapeHtml(rev.deletedText)}</del>`;
    }
    
    offset = rev.position + (rev.type === 'delete' ? 0 : rev.insertedText.length);
  }
  
  html += escapeHtml(block.text.slice(offset));
  return html;
}
```

### T3.5: Accept/Reject UI (2 days)
**File:** `extension/src/webview/change-actions.js` (new)

```javascript
function renderChangeActions(revision) {
  return `
    <span class="change-actions" data-id="${revision.id}">
      <button class="accept-btn" title="Accept">✓</button>
      <button class="reject-btn" title="Reject">✗</button>
    </span>
  `;
}

function setupChangeActions() {
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('accept-btn')) {
      const id = e.target.closest('.change-actions').dataset.id;
      acceptChange(id);
    } else if (e.target.classList.contains('reject-btn')) {
      const id = e.target.closest('.change-actions').dataset.id;
      rejectChange(id);
    }
  });
}

async function acceptChange(revisionId) {
  vscode.postMessage({
    command: 'acceptRevision',
    revisionId: revisionId
  });
}
```

### T3.6: Context Menu for Comments (1 day)
**File:** `extension/src/webview/context-menu.js` (new)

```javascript
function showContextMenu(x, y, options) {
  const menu = document.createElement('div');
  menu.className = 'context-menu';
  menu.style.left = `${x}px`;
  menu.style.top = `${y}px`;
  
  options.forEach(opt => {
    const item = document.createElement('div');
    item.className = 'context-menu-item';
    item.textContent = opt.label;
    item.onclick = () => {
      opt.action();
      menu.remove();
    };
    menu.appendChild(item);
  });
  
  document.body.appendChild(menu);
}

// Usage on text selection
editor.onContextMenu((selection) => {
  showContextMenu(event.clientX, event.clientY, [
    { label: '📝 Add Comment', action: () => addCommentDialog(selection) },
    { label: '📋 Copy', action: () => copySelection(selection) }
  ]);
});
```

### T3.7: Comment Save Flow (1 day)
**File:** `extension/scripts/save_comments.py` (new)

```python
def add_comment(doc_path: str, para_id: str, start: int, end: int, text: str, author: str) -> dict:
    """Add a new comment to the document."""
    
def add_reply(doc_path: str, comment_id: str, text: str, author: str) -> dict:
    """Add a reply to an existing comment."""
    
def resolve_comment(doc_path: str, comment_id: str) -> dict:
    """Mark a comment as resolved."""
```

---

## CSS Styling

```css
/* Track changes */
ins.change {
  background-color: rgba(0, 200, 0, 0.2);
  text-decoration: underline;
  text-decoration-color: green;
}

del.change {
  background-color: rgba(255, 0, 0, 0.2);
  text-decoration: line-through;
  text-decoration-color: red;
}

.change-actions {
  display: inline-block;
  margin-left: 4px;
}

.change-actions button {
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 2px 4px;
}

/* Comments panel */
.comment-panel {
  width: 250px;
  border-left: 1px solid var(--vscode-panel-border);
  overflow-y: auto;
}

.comment-card {
  padding: 12px;
  border-bottom: 1px solid var(--vscode-panel-border);
}

.comment-card.resolved {
  opacity: 0.6;
}

.comment-author {
  font-weight: bold;
  font-size: 12px;
}

.comment-date {
  font-size: 11px;
  color: var(--vscode-descriptionForeground);
}

.comment-text {
  margin-top: 8px;
}

.comment-actions {
  margin-top: 8px;
}

/* Context menu */
.context-menu {
  position: fixed;
  background: var(--vscode-menu-background);
  border: 1px solid var(--vscode-menu-border);
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  z-index: 1000;
}

.context-menu-item {
  padding: 8px 16px;
  cursor: pointer;
}

.context-menu-item:hover {
  background: var(--vscode-menu-selectionBackground);
}
```

---

## Testing Plan

### Unit Tests
- `test_comment_extraction.py`: Parse comments with all metadata
- `test_revision_extraction.py`: Parse tracked changes
- `test_comment_panel.js`: Render and interaction

### Integration Tests
- Add comment → save → reopen → verify
- Accept change → save → verify in Word
- Resolve comment → verify status persists

### Manual Tests
1. Open document with existing comments and track changes
2. Add new comment, verify anchor
3. Reply to comment, verify thread
4. Resolve comment, verify status
5. Accept/reject individual changes
6. Accept all changes

---

## Definition of Done

- [ ] All existing comments visible (flat list)
- [ ] Can add new comments with paragraph-level anchor
- [ ] ~~Can reply to comments~~ (Deferred)
- [ ] Can resolve comments
- [ ] Track changes displayed correctly (insertions/deletions only)
- [ ] Can accept/reject individual changes
- [ ] All changes persist to .docx
- [ ] Unit tests passing
- [ ] Documentation updated

---

## Dependencies

- Sprint 2 complete (editor foundation)
- Existing comment extraction in `effilocal/mcp_server/core/comments.py`

---

## Notes

- Word's comment IDs are not stable across saves; use internal tracking
- Track changes may have complex overlapping; handle edge cases
- Consider "compare versions" feature for future sprint

---

## Implementation Phases

### Phase 1: Comment Display & Basic Interaction (Week 1)

**Day 1-2: Backend Enhancement**
1. Enhance `extract_all_comments()` to populate `paragraph_index` reliably (paragraph-level anchoring)
2. Extract `reference_text` (the text the comment is attached to) - nice to have
3. ~~Add reply threading support~~ → Deferred: show flat list for MVP
4. Create `resolve_comment()` function to update `commentsExtended.xml`

**Day 3-4: Comment Panel UI**
1. Create `extension/src/webview/comments.js` - CommentPanel class
2. Add right sidebar container to webview HTML
3. Implement comment card rendering with author, date, status
4. Add inline comment indicators (small icon in margin next to anchored text)
5. Hover/click interaction to highlight anchored text

**Day 5: Integration & Testing**
1. Load comments alongside blocks in extension
2. Wire up CommentPanel to blockEditor
3. Test with real documents containing comments
4. Handle resolved vs active visual distinction

### Phase 2: Track Changes (Week 2, Days 1-3)

**Day 1: Revision Extraction**
1. Create `effilocal/mcp_server/core/revisions.py`
2. Parse `<w:ins>` elements (insertions) - author, date, text, position
3. Parse `<w:del>` elements (deletions) - author, date, original text, position
4. ~~Parse `<w:rPrChange>` formatting changes~~ → Deferred to future sprint
5. Map revisions to blocks via paragraph index
6. Test with `HJ9 (TRACKED).docx`

**Day 2: Track Changes Display**
1. Create `extension/src/webview/track-changes.js`
2. Render insertions with green underline, deletions with red strikethrough
3. Show author on hover via title attribute
4. Add CSS styling for ins/del elements

**Day 3: Accept/Reject**
1. Implement `accept_revision()` - remove `<w:ins>` wrapper, keep text
2. Implement `reject_revision()` - remove `<w:ins>` element entirely
3. For deletions: accept = remove text, reject = restore text
4. Add toolbar buttons for "Accept All" / "Reject All"

### Phase 3: Comment Creation & Reply (Week 2, Days 4-5)

**Day 4: Add Comment Flow**
1. Create context menu on text selection
2. Add comment input dialog/popover
3. Create `extension/scripts/add_comment.py`
4. Wire up to existing MCP `add_word_comment` tool

**Day 5: Reply & Resolve**
1. Add "Reply" button to comment cards
2. Create `add_reply()` function in Python
3. Add "Resolve" button that updates status
4. Final integration testing and polish

---

## Open Questions (Resolved)

1. **Comment Anchor Precision**: Should we track character offsets within runs, or is paragraph-level anchoring sufficient for MVP?
   - ✅ **Decision**: Start with paragraph-level anchoring (matches current para_id linkage). Enhance later if needed.

2. **Reply Threading Priority**: Should we implement threaded reply display?
   - ✅ **Decision**: Show flat list for MVP. Threading can be added in future sprint.

3. **Track Changes Scope**: Should we handle formatting changes (`<w:rPrChange>`)?
   - ✅ **Decision**: Focus on text insertions/deletions only. Ignore formatting changes in this sprint.

4. **Test Documents**: Where are sample documents with comments and tracked changes?
   - ✅ **Decision**: Use `HJ9 (TRACKED).docx` in `EL_Projects/Test Project/drafts/current_drafts/` - has both comments and tracked changes.

5. **Track Changes Toggle**: Should we have a "Show/Hide Track Changes" toggle, or always show them?
   - *Recommendation*: Always show with clear visual distinction. Add toggle in future sprint.

6. **Multi-Author Colors**: Should different authors have different highlight colors (like Word)?
   - *Recommendation*: Defer to future sprint. Use consistent green/red for MVP.

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Complex nested revisions | Rendering breaks | Flatten to sequential changes during extraction |
| Comment ranges span paragraphs | Anchor mismatch | Link to first paragraph, note limitation |
| Word ID instability | Lost references | Use para_id as stable anchor, track by position |
| Large documents slow | Poor UX | Lazy-load comments panel, virtualize if needed |

