# Sprint 3: Comments & Track Changes

**Duration:** 2 weeks  
**Goal:** Full commenting and revision tracking within the editor.

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

### US3.3: Reply to Comments
**As a** lawyer responding to counterparty comments,  
**I want** to reply to existing comments,  
**So that** we can have a threaded discussion.

**Acceptance Criteria:**
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

### Comment Data Model

```javascript
// Comment stored in block model
{
  id: "uuid",
  text: "This clause needs review",
  author: "John Smith",
  date: "2025-12-02T10:30:00Z",
  status: "active", // or "resolved"
  anchorBlockId: "block-uuid",
  anchorStart: 15,  // character offset
  anchorEnd: 45,
  replies: [
    {
      id: "reply-uuid",
      text: "I've updated the wording",
      author: "Jane Doe",
      date: "2025-12-03T14:00:00Z"
    }
  ]
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
- Reply to comment → verify threading

### Manual Tests
1. Open document with existing comments and track changes
2. Add new comment, verify anchor
3. Reply to comment, verify thread
4. Resolve comment, verify status
5. Accept/reject individual changes
6. Accept all changes

---

## Definition of Done

- [ ] All existing comments visible
- [ ] Can add new comments with anchor
- [ ] Can reply to comments
- [ ] Can resolve comments
- [ ] Track changes displayed correctly
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
