# Effi Contract Review - Context Setup for LLM Development Sessions

**Last Updated:** December 5, 2025  
**Current Sprint:** Sprint 3 - Comments & Track Changes  
**Current Phase:** Phase 1, Day 3-4 (Comment Panel UI)

---

## Quick Start for New Sessions

When starting a new development session, share this file with the LLM and state:
> "You will shortly continue work on Sprint 3 Phase 1 - Comment Panel UI. Read `docs/CONTEXT_SETUP.md` for context. Let me know once you have read it."

The LLM should then read this document and also:
1. Read the sprint plan at `docs/sprint_plans/SPRINT_03_COMMENTS_TRACKCHANGES.md`
2. Review the current implementation state (see Section 4 below)
3. Confirm understanding of context.

Once the LLM is told to start the work, the LLM should then complete the work, making sure to always:
4. Follow TDD: write tests first, then implement until tests pass

---

## 1. Project Overview

### What Is This?

**Effi Contract Review** is a VS Code extension + MCP server for solo lawyers to:
- Edit Word contracts directly in VS Code (WYSIWYG webview)
- Use LLM assistance for contract review, issue identification, and drafting
- Maintain version control and audit trails via Git integration
- Work with precedent documents for consistent drafting

### Target User

Solo lawyer (you, David) drafting commercial contracts. The application runs locally, with only outbound HTTPS to the selected LLM via VS Code's Chat interface.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     VS Code Extension                            │
│  extension/src/                                                  │
│  ├── extension.ts         (Extension host, commands, messaging) │
│  ├── projectProvider.ts   (Tree view for projects)              │
│  └── webview/             (WYSIWYG editor in browser context)   │
│       ├── main.js         (Entry point, message handling)       │
│       ├── editor.js       (BlockEditor - contentEditable)       │
│       ├── toolbar.js      (Formatting toolbar)                  │
│       ├── comments.js     (CommentPanel - IN PROGRESS)          │
│       ├── shortcuts.js    (Keyboard shortcuts)                  │
│       └── style.css       (Styling)                             │
├─────────────────────────────────────────────────────────────────┤
│                    MCP Server (Python)                           │
│  effilocal/mcp_server/                                          │
│  ├── main.py              (FastMCP server, tool registration)   │
│  ├── tools/               (MCP tool implementations)            │
│  ├── core/                (Low-level document manipulation)     │
│  │    └── comments.py     (Comment extraction with status)      │
│  └── utils/               (Shared utilities)                    │
├─────────────────────────────────────────────────────────────────┤
│                    Document Processing                           │
│  effilocal/doc/           (Document analysis pipeline)          │
│  ├── uuid_embedding.py    (Para_id extraction/matching)         │
│  ├── content_hash.py      (SHA-256 hash for fallback matching)  │
│  └── numbering_inspector/ (Clause numbering analysis)           │
├─────────────────────────────────────────────────────────────────┤
│  word_document_server/    (Pristine upstream - DO NOT MODIFY)   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Technical Decisions

| Decision | Implementation |
|----------|----------------|
| Block ID Matching | Native `w14:paraId` (Word-assigned), with SHA-256 hash fallback |
| Document Format | `.docx` ↔ JSON artifacts (blocks.jsonl, sections.json) ↔ webview |
| Extension ↔ Server | MCP protocol via stdio transport |
| Git Integration | Auto-commit on save with `[effi]` prefix |
| LLM Integration | Via VS Code Chat API (model selected by user) |

---

## 2. Sprint Status

### Completed Sprints

| Sprint | Theme | Status |
|--------|-------|--------|
| **S1** | Foundation & UUID Persistence | ✅ Complete |
| **S2** | WYSIWYG Editor Core | ✅ Complete |

### Current Sprint: S3 - Comments & Track Changes

**Goal:** Full commenting and revision tracking within the editor.

**Phase 1: Comment Display & Basic Interaction (Week 1)**

| Task | Status | Notes |
|------|--------|-------|
| Day 1-2: Backend Enhancement | ✅ Complete | `comments.py` enhanced with status, resolve/unresolve |
| Day 3-4: Comment Panel UI | 🔄 **IN PROGRESS** | `comments.js` skeleton exists, needs integration |
| Day 5: Integration & Testing | ⏳ Not Started | Wire up to editor, test with real docs |

**Deferred Items (explicitly out of scope for this sprint):**
- Reply threading (show flat list only)
- Formatting changes tracking (`<w:rPrChange>`)
- Multi-author color coding

### Upcoming Sprints

| Sprint | Theme | Status |
|--------|-------|--------|
| **S3** Phase 2 | Track Changes | ⏳ After Phase 1 |
| **S3** Phase 3 | Comment Creation | ⏳ After Phase 2 |
| **S4** | LLM Chat Integration | ⏳ Future |
| **S5** | Multi-Phase Review Workflow | ⏳ Future |
| **S6** | Precedent Bank & Tagging | ⏳ Future |
| **S7** | Project Management & UX | ⏳ Future |

---

## 3. Development Workflow

### Test-Driven Development (TDD)

**This project follows strict TDD:**

1. **Write comprehensive tests FIRST** - tests should FAIL initially
2. **Implement the feature** - make tests pass
3. **Refactor** - clean up while keeping tests green

Example workflow:
```bash
# 1. Write tests
# tests/test_comment_panel_integration.py

# 2. Run tests (should fail)
cd tests
pytest test_comment_panel_integration.py -v

# 3. Implement feature
# extension/src/webview/comments.js

# 4. Run tests again (should pass)
pytest test_comment_panel_integration.py -v
```

### Code Quality Standards

Follow these guides strictly:
- `.github/clean_code_principles.md` - CLEAN code principles
- `.github/python_style_guide.md` - Python-specific conventions
- `.github/copilot-instructions.md` - Project-specific patterns

Key principles:
- **Small functions** (< 20-30 lines)
- **Type hints everywhere** (Python)
- **JSDoc comments** (JavaScript)
- **Meaningful names** over comments
- **Early returns** to reduce nesting
- **No magic numbers** - use constants

### Environment Setup

**Python:**
```powershell
# Activate virtual environment
C:\Users\DavidSant\effi-contract-review\.venv\Scripts\Activate.ps1

# Run tests
cd tests
pytest -v

# Run specific test file
pytest test_comment_features.py -v
```

**Node.js (for extension):**
```powershell
# Node.js location
$env:PATH = 'C:\Users\DavidSant\node-v25.2.1-win-x64;' + $env:PATH

# Compile extension
cd extension
npm run compile
```

**MCP Server:**
```powershell
# Run server (stdio mode - default)
python -m effilocal.mcp_server.main

# Run with HTTP transport (for testing)
$env:MCP_TRANSPORT = "streamable-http"
python -m effilocal.mcp_server.main
```

---

## 4. Current Implementation State

### What Exists (Sprint 3 Phase 1 Backend)

**`effilocal/mcp_server/core/comments.py`** - Complete:
- `extract_all_comments()` - Extracts comments with full metadata
- `extract_comment_status_map()` - Gets active/resolved from commentsExtended.xml
- `merge_comment_status()` - Links status to comments via para_id
- `resolve_comment()` - Marks comment as resolved
- `unresolve_comment()` - Marks comment as active
- `extract_reference_text()` - Gets anchored text for a comment
- `get_all_reference_texts()` - Batch extraction of anchored text

**`extension/src/webview/comments.js`** - Skeleton exists:
- `CommentPanel` class with constructor, setComments, setFilter
- Renders flat list of comments with author, date, status
- Filter buttons (All/Active/Resolved)
- Click handler to scroll to referenced block
- Resolve/Unresolve action buttons
- **NOT YET INTEGRATED** with main.js or editor

### What Needs Implementation (Day 3-4 Tasks)

1. **Add right sidebar container to webview HTML** (`main.js`)
   - Container div for CommentPanel
   - CSS layout (flexbox/grid) to position sidebar

2. **Wire CommentPanel to BlockEditor** (`main.js`)
   - Load comments when document loads
   - Call `commentPanel.setComments(comments)` with data
   - Implement `onScrollToBlock(paraId)` callback
   - Implement `onHighlightBlock(paraId)` callback
   - Implement `onResolve(commentId)` / `onUnresolve(commentId)` callbacks

3. **Add inline comment indicators in editor**
   - Small icon in margin next to paragraphs with comments
   - Click icon to scroll sidebar to that comment

4. **Extension ↔ Webview messaging for comments**
   - Message: `loadComments` - send comments to webview
   - Message: `resolveComment` - call MCP tool to resolve
   - Message: `unresolveComment` - call MCP tool to unresolve

5. **CSS for comment panel** (`style.css`)
   - Right sidebar styling (250px width, border, scroll)
   - Comment card styling (see Sprint 3 plan for details)

### Test Document

Use for testing: `EL_Projects/Test Project/drafts/current_drafts/HJ9 (TRACKED).docx`
- Contains both comments and tracked changes
- Good variety of comment statuses

---

## 5. File Locations Reference

### Key Files to Know

| Purpose | Location |
|---------|----------|
| Sprint 3 Plan | `docs/sprint_plans/SPRINT_03_COMMENTS_TRACKCHANGES.md` |
| Extension Entry | `extension/src/extension.ts` |
| Webview Main | `extension/src/webview/main.js` |
| Block Editor | `extension/src/webview/editor.js` |
| Comment Panel | `extension/src/webview/comments.js` |
| Webview Styles | `extension/src/webview/style.css` |
| Comment Backend | `effilocal/mcp_server/core/comments.py` |
| MCP Server Main | `effilocal/mcp_server/main.py` |
| Test Files | `tests/test_comment_*.py` |

### Test Files Related to Comments

- `tests/test_comment_features.py` - Comment extraction tests
- `tests/test_comment_status.py` - Status extraction tests  
- `tests/test_comment_status_integration.py` - Full integration tests

### Example Projects

- `EL_Projects/Test Project/` - Test documents including HJ9 (TRACKED).docx
- `EL_Projects/Lamplight/` - Real project with sample contracts

---

## 6. Key Patterns & Conventions

### MCP Tool Pattern (Python)

```python
@mcp.tool()
async def tool_name(filename: str, param: str) -> str:
    """Tool description for MCP registration.
    
    Args:
        filename: Path to the document
        param: Description of parameter
        
    Returns:
        Success message string (ALWAYS return string, not dict)
    """
    filename = ensure_docx_extension(filename)
    # ... implementation
    return f"Success: {result}"  # User-visible message
```

### Extension ↔ Webview Messaging

**Extension to Webview:**
```typescript
panel.webview.postMessage({ command: 'loadComments', comments: [...] });
```

**Webview to Extension:**
```javascript
vscode.postMessage({ command: 'resolveComment', commentId: '123' });
```

**Handle in Extension:**
```typescript
panel.webview.onDidReceiveMessage(message => {
    switch (message.command) {
        case 'resolveComment':
            // Call MCP tool
            break;
    }
});
```

### Comment Data Structure

```javascript
{
    id: "comment_1",           // Internal ID
    comment_id: "0",           // Word's w:id
    para_id: "3DD8236A",       // Links to paragraph
    author: "John Smith",
    initials: "JS",
    date: "2025-12-02T10:30:00Z",
    text: "Comment text",
    paragraph_index: 5,        // Index in document
    reference_text: "the text being commented on",
    status: "active",          // "active" or "resolved"
    is_resolved: false,
    done_flag: 0               // 0=active, 1=resolved
}
```

---

## 7. Testing Conventions

### Python Tests (pytest)

```python
# tests/test_feature.py
import pytest

def test_feature_returns_expected_value() -> None:
    """Descriptive test name explains what we're testing."""
    # Arrange
    input_data = create_test_input()
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_value
```

### JavaScript Tests (Jest)

```javascript
// extension/src/webview/__tests__/comments.test.js
describe('CommentPanel', () => {
    it('should render comments in flat list', () => {
        // Arrange
        const container = document.createElement('div');
        const panel = new CommentPanel(container);
        
        // Act
        panel.setComments([{ id: '1', text: 'Test' }]);
        
        // Assert
        expect(container.querySelectorAll('.comment-item').length).toBe(1);
    });
});
```

---

## 8. Common Issues & Solutions

### Issue: Extension not compiling
```powershell
# Ensure Node.js is in PATH
$env:PATH = 'C:\Users\DavidSant\node-v25.2.1-win-x64;' + $env:PATH
cd extension
npm run compile
```

### Issue: Python module not found
```powershell
# Ensure venv is activated
C:\Users\DavidSant\effi-contract-review\.venv\Scripts\Activate.ps1
# Check you're in the right directory
cd C:\Users\DavidSant\effi-contract-review
```

### Issue: MCP server connection fails
```powershell
# Test with HTTP transport
$env:MCP_TRANSPORT = "streamable-http"
$env:MCP_PORT = 8000
python -m effilocal.mcp_server.main
# Then test with tests/test_local_mcp.py
```

### Issue: Word document won't open after modification
- Check XML validity - we use native `w14:paraId` not custom tags
- Custom `w:tag` inside `w:pPr` violates OOXML schema
- Use Word's "Open and Repair" feature if needed

---

## 9. Next Steps (Current Session)

### Immediate Task: Sprint 3 Phase 1, Day 3-4

**Goal:** Integrate CommentPanel into the webview editor

**Steps:**
1. Write integration tests for CommentPanel ↔ Editor interaction
2. Add sidebar container to `main.js` HTML
3. Wire up CommentPanel with callbacks
4. Add inline comment indicators to blocks
5. Implement extension messaging for resolve/unresolve
6. Test with `HJ9 (TRACKED).docx`

**Definition of Done:**
- [ ] Comments visible in right sidebar when document loads
- [ ] Clicking comment scrolls to referenced paragraph
- [ ] Referenced paragraph highlights when comment selected
- [ ] Resolve/Unresolve buttons work (call MCP tool, update UI)
- [ ] Filter buttons (All/Active/Resolved) work
- [ ] All tests pass

---

## 10. Reference Documents

| Document | Purpose |
|----------|---------|
| `docs/sprint_plans/SPRINT_ROADMAP.md` | Full sprint plan overview |
| `docs/sprint_plans/SPRINT_03_*.md` | Detailed Sprint 3 plan |
| `.github/copilot-instructions.md` | Architecture & tool patterns |
| `.github/clean_code_principles.md` | CLEAN code guidelines |
| `.github/python_style_guide.md` | Python conventions |
| `docs/ARTIFACT_GUIDE.md` | JSON artifact format reference |
| `docs/USER_GUIDE.md` | End-user documentation |

---

*This document should be updated at the end of each development session to reflect current status.*
