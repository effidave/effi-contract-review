# Plan Tab Implementation

## Overview

The Plan Tab allows solo lawyers to track work tasks and MCP tool calls during contract drafting/review sessions. It is implemented as a **separate WebviewPanel** that can be opened side-by-side with Contract Analysis.

## Architecture

```
┌─────────────────────────────┐   ┌─────────────────────────────┐
│   Contract Analysis Panel   │   │      Work Plan Panel        │
│   (effiContractViewer)      │   │   (effiPlanViewer)          │
│                             │   │                             │
│   main.js, editor.js        │   │   planMain.js, plan.js      │
│   toolbar.js, comments.js   │   │   PlanPanel class           │
└──────────────┬──────────────┘   └──────────────┬──────────────┘
               │      postMessage()               │
               └──────────────┬───────────────────┘
                              ▼
               ┌──────────────────────────────────┐
               │       extension.ts               │
               │                                  │
               │  - showContractWebview()         │
               │  - showPlanWebview()             │
               │  - PlanProvider                  │
               │  - Message handlers              │
               └──────────────────────────────────┘
                              │
                              ▼
               ┌──────────────────────────────────┐
               │       File System                │
               │                                  │
               │  <project>/plans/current/        │
               │    ├── plan.md                   │
               │    └── plan.meta.json            │
               │  <project>/logs/                 │
               │    └── edits.jsonl               │
               └──────────────────────────────────┘
```

## Recommended Order

### 1. Core Classes (TypeScript) ✅ COMPLETE

- Edit class (simplest, no dependencies)
- WorkTask class (depends on Edit)
- WorkPlan class (depends on WorkTask)
- LegalDocument class (document references for WorkPlan)
- Unit tests for all class methods (77 tests)

**Files:** `extension/src/models/workplan.ts`, `extension/src/__tests__/workplan.test.ts`

#### LegalDocument Class

Represents a legal document that a WorkPlan relates to. Used to track which documents are being worked on and filter edits accordingly.

**Properties:**
- `id: string` - Unique 8-char hex ID
- `filename: string` - Full path to the .docx file
- `displayName: string` - Friendly name (auto-derived from filename if not provided)
- `addedDate: Date` - When the document was added to the plan

**Methods:**
- `matchesFilename(filename)` - Case-insensitive, path-normalized comparison
- `toJSON()` / `fromJSON()` - JSON serialization
- `toYAML()` - YAML-friendly object

#### WorkPlan Document Features

**Properties:**
- `documents: LegalDocument[]` - Documents this plan relates to

**Methods:**
- `addDocument(doc)` - Add a document (no duplicates by filename)
- `removeDocument(id)` - Remove by ID
- `getDocumentById(id)` / `getDocumentByFilename(filename)` - Lookups
- `hasDocument(filename)` - Check if document exists
- `getEditsForDocument(filename)` - Get edits affecting a specific document
- `getDocumentEdits()` - Get all edits affecting any plan document

**YAML Serialization:**
```yaml
---
documents:
  - id: doc12345
    filename: 'C:/Projects/Acme/drafts/nda.docx'
    displayName: NDA Draft
    addedDate: '2025-12-09T10:00:00.000Z'
tasks:
  - id: task1234
    ...
---
```

### 2. Persistence Layer ✅ COMPLETE

- edits.jsonl read/write utilities
- plan.md YAML frontmatter serialization/deserialization
- plan.meta.json save/load (for fast loading)
- Ensure folder/file creation if missing
- Tests for persistence (36 tests)

**Files:** `extension/src/models/planStorage.ts`, `extension/src/__tests__/planStorage.test.ts`

### 3. Extension Integration ✅ COMPLETE

- Wire PlanProvider into extension host (extension.ts)
- Add message handlers for webview ↔ extension communication
- Tests for message handling (51 tests)

**Files:** `extension/src/models/planProvider.ts`, `extension/src/__tests__/planIntegration.test.ts`

### 4. Webview UI ✅ COMPLETE

**Architecture Decision:** The Plan is a **separate WebviewPanel**, not a tab within the Contract Analysis webview. This matches how VS Code panels work:

- Contract Analysis = WebviewPanel (existing)
- Plan = WebviewPanel (new, separate)

**Benefits:**
- Can be opened side-by-side with Contract Analysis
- Independent lifecycle (close one without affecting other)
- Cleaner separation of concerns
- Simpler HTML/JS (no tab switching logic needed)

**Implementation:**
- [x] Create `plan.js` webview script (PlanPanel class)
- [x] Create `planMain.js` entry point for Plan webview
- [x] Add `getPlanWebviewContent()` function in extension.ts
- [x] Add `planWebviewPanel` variable and `showPlanWebview()` function
- [x] Register `effi-contract-viewer.showPlan` command
- [x] Add CSS for plan styling (task cards, status badges, progress bar)
- [x] Comprehensive UI tests (77 tests in `plan.test.js`)

**Files:**
- `extension/src/webview/plan.js` - PlanPanel class
- `extension/src/webview/planMain.js` - Plan webview entry point
- `extension/src/webview/__tests__/plan.test.js` - 77 tests
- `extension/src/webview/style.css` - Plan panel styles
- `extension/src/extension.ts` - showPlanWebview, getPlanWebviewContent

### 5. LLM/MCP Integration ✅ COMPLETE

Automatic logging of MCP tool calls as Edit objects.

#### 5a. TypeScript McpToolLogger (Extension-side)

**Features:**
- McpToolLogger service for tracking active tasks and logging edits
- Active task management (set/clear/get based on task status)
- Automatic task association when status changes to `in_progress`
- Tool call recording with start/complete pattern for async operations
- Event notifications (`onEditLogged`, `onActiveTaskChanged`)
- Session statistics (edit count, tool usage by name)
- Recent edits history

**Files:**
- `extension/src/models/mcpToolLogger.ts` - McpToolLogger service
- `extension/src/__tests__/mcpToolLogger.test.ts` - 39 tests

#### 5b. Python MCP Server Logging (Server-side)

Logs tool calls at the MCP server level so all Copilot interactions are captured.

**Features:**
- `ToolCallLogger` class for append-only logging to `edits.jsonl`
- `get_project_path()` derives project from document filename
- `@with_logging` decorator for easy tool wrapping
- Thread-safe concurrent writes
- Works with both sync and async functions
- Error logging (captures exceptions)

**How It Works:**
```
Copilot → MCP Server → @with_logging decorator → Tool executes
                              ↓
                       Logs to <project>/logs/edits.jsonl
                              ↓
                       Extension reads edits.jsonl
                              ↓
                       User associates with tasks in Plan UI
```

**Files:**
- `effilocal/mcp_server/tool_logging.py` - ToolCallLogger and decorator
- `tests/test_mcp_tool_logging.py` - 27 tests

**Usage:**
```python
from effilocal.mcp_server.tool_logging import with_logging

@with_logging
async def search_and_replace(filename: str, find_text: str, replace_text: str):
    # ... implementation
    return result  # Automatically logged!
```

#### 5c. Edit Retrieval (Extension reads from log)

The extension reads edits from `edits.jsonl` and can look up full edit details by ID.

**PlanStorage Edit Retrieval Methods:**
- `getEditsByIds(ids)` - Retrieve specific edits by their IDs (in requested order)
- `getAllEdits()` - Load all edits from the log
- `getEditById(id)` - Get a single edit by ID
- `getNewEditsSince(cutoff)` - Get edits after a timestamp
- `getUnassociatedEdits()` - Get edits with null taskId (not yet linked to a task)
- `getEditsForDocument(filename)` - Get edits affecting a specific document

**Linking Strategy (Option C):**
1. Python MCP server logs tool calls to `edits.jsonl` with `taskId: null`
2. Extension watches/polls for new entries
3. Extension checks if edit's filename matches a plan document
4. If there's an active task (status = `in_progress`), links the edit via `WorkTask.editIds`
5. Plan stores only edit IDs; full details retrieved from log when needed

**Benefits:**
- Plan file stays small (just IDs, not duplicated data)
- Edit log is source of truth for request/response details
- Lazy loading - only fetch edit details when needed
- Audit trail preserved - log is append-only

**Files:**
- `extension/src/models/planStorage.ts` - Edit retrieval methods
- `extension/src/__tests__/planStorage.test.ts` - 77 tests (including edit retrieval)

#### 5d. Auto-Association (Extension links edits to tasks)

Automatic association of new edits with the currently active task.

**PlanProvider Auto-Association Methods:**
- `getActiveTask()` - Returns the first task with `status: 'in_progress'`
- `processUnassociatedEdits()` - Batch process all unassociated edits
- `associateEditWithTask(editId, taskId)` - Manually link an edit to a task
- `processNewEdits()` - Incremental processing since last timestamp
- `getLastProcessedTimestamp()` / `setLastProcessedTimestamp()` - Cursor tracking

**Auto-Association Flow:**
```
edits.jsonl → getUnassociatedEdits()
                    ↓
            Filter by plan.documents
                    ↓
            Check for active task (in_progress)
                    ↓
            Add editId to task.editIds
                    ↓
            Save plan
```

**ProcessEditsResult:**
```typescript
interface ProcessEditsResult {
    processed: number;      // Edits successfully associated
    skipped: number;        // Edits filtered out (wrong document, already linked)
    errors: string[];       // Any errors encountered
    noActiveTask: boolean;  // True if no task was in_progress
}
```

**Incremental Processing:**
- `lastProcessedTimestamp` stored in `plan.meta.json`
- `processNewEdits()` only processes edits newer than this timestamp
- Prevents reprocessing on each poll cycle

**Files:**
- `extension/src/models/planProvider.ts` - Auto-association methods
- `extension/src/__tests__/planIntegration.test.ts` - 66 tests (including 12 auto-association tests)

#### 5e. Plan MCP Tools (LLM can create/manage plans)

Python MCP tools that allow the LLM to create and manage WorkPlans directly.

**Available Tools:**

| Tool | Description |
|------|-------------|
| `get_work_plan(filename)` | Get current plan with tasks, documents, and summary stats |
| `add_task(filename, title, description, position?, ordinal?)` | Add a new task (position: start/end/at) |
| `update_task(filename, task_id, title?, description?, status?)` | Update task properties |
| `delete_task(filename, task_id)` | Remove a task |
| `move_task(filename, task_id, new_ordinal)` | Reorder a task |
| `start_task(filename, task_id)` | Set status to in_progress |
| `complete_task(filename, task_id)` | Set status to completed |
| `block_task(filename, task_id)` | Set status to blocked |
| `add_plan_document(filename, display_name?)` | Track a document in the plan |
| `remove_plan_document(filename, document_id)` | Stop tracking a document |
| `list_plan_documents(filename)` | List all tracked documents |

**Project Path Derivation:**
All tools use `filename` (a document in the project) to derive the project path.
Supports `EL_Projects/<project>/...` and `EL_Precedents/<project>/...` structures.

**Files:**
- `effilocal/mcp_server/plan/models.py` - Python WorkPlan, WorkTask, LegalDocument classes
- `effilocal/mcp_server/plan/storage.py` - YAML/JSON file I/O
- `effilocal/mcp_server/tools/plan_tools.py` - MCP tool implementations
- `tests/test_plan_mcp_tools.py` - 45 tests

## Project Path Derivation

The Plan needs a `projectPath` to know where to store `plans/` and `logs/` directories.

**Strategy:** Derive from `currentDocumentPath`:
```
EL_Projects/<project>/drafts/current_drafts/<file>.docx
         ↓
EL_Projects/<project>/  ← projectPath
```

This matches the existing `getAnalysisDir()` pattern.

## File Structure

```
<project>/
├── analysis/<filename>/     # Contract analysis artifacts
├── plans/
│   └── current/
│       ├── plan.md          # Human-readable YAML + markdown
│       └── plan.meta.json   # Fast-loading JSON
├── logs/
│   └── edits.jsonl          # Append-only edit log
└── drafts/
    └── current_drafts/
        └── <file>.docx
```

## Test Summary

| Step | Test File | Tests |
|------|-----------|-------|
| 1. Core Classes + LegalDocument | workplan.test.ts | 77 |
| 2. Persistence + Edit Retrieval | planStorage.test.ts | 77 |
| 3. Integration + Auto-Association | planIntegration.test.ts | 66 |
| 4. Webview UI | plan.test.js | 59 |
| 5a. TS MCP Integration | mcpToolLogger.test.ts | 39 |
| 5b. Python MCP Logging | test_mcp_tool_logging.py | 27 |
| 5e. Plan MCP Tools | test_plan_mcp_tools.py | 45 |
| 6. Markdown Rendering | markdown.test.js | 58 |
| **Total** | | **448** |

### 6. Markdown Rendering ✅ COMPLETE

Task descriptions support markdown syntax, which is rendered as HTML in the Plan panel.

#### Implementation

**Library:** [marked](https://github.com/markedjs/marked) v12.0.0

**Bundle Architecture:**
The Plan webview uses a bundled script (`dist/planBundle.js`) that includes:
- `marked` library for markdown parsing
- `plan.js` (PlanPanel component)
- `planMain.js` (webview initialization)

**esbuild Configuration:**
```javascript
// Build 1: Extension host bundle (Node.js)
const extensionCtx = await esbuild.context({
    entryPoints: ['src/extension.ts'],
    platform: 'node',
    outfile: 'dist/extension.js',
    // ...
});

// Build 2: Plan webview bundle (Browser)
const planWebviewCtx = await esbuild.context({
    entryPoints: ['src/webview/planBundle.js'],
    platform: 'browser',
    format: 'iife',
    outfile: 'dist/planBundle.js',
    // ...
});
```

#### Sanitization (XSS Protection)

The `sanitizeMarkdownHtml()` function uses a whitelist approach:

**ALLOWED_TAGS:**
```javascript
['p', 'br', 'strong', 'b', 'em', 'i', 'u', 'code', 'pre',
 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
 'blockquote', 'hr']
```

**ALLOWED_ATTRIBUTES:**
```javascript
{
    'a': ['href', 'title'],
    '*': []  // No global attributes
}
```

**Dangerous Patterns Blocked:**
- `<script>`, `<style>`, `<iframe>`, `<object>`, `<embed>`, `<form>`, `<img>`
- Event handlers: `onclick`, `onmouseover`, `onerror`, etc.
- Dangerous URLs: `javascript:`, `data:`, `vbscript:`

**Environment Support:**
- **Browser:** Uses DOMParser for robust HTML parsing
- **Node.js (tests):** Falls back to regex-based sanitization

#### Rendering Flow

```
task.description (markdown string)
        ↓
   renderMarkdown()
        ↓
   marked.parse()  → raw HTML
        ↓
   sanitizeMarkdownHtml()  → safe HTML
        ↓
   descEl.innerHTML = result
```

In `_renderTask()`:
```javascript
if (task.description) {
    descEl.innerHTML = renderMarkdown(task.description);
} else {
    descEl.textContent = '(Click to add description)';
}
```

#### CSS Styling

Markdown elements inside `.task-description` are styled in `style.css`:

| Element | Styling |
|---------|---------|
| `p` | Margin: 0 0 0.5em 0 |
| `strong`, `b` | font-weight: 600 |
| `em`, `i` | font-style: italic |
| `code` | Monospace, light background, 11px |
| `pre` | Block code with padding, overflow scroll |
| `ul`, `ol` | Indented lists |
| `a` | Blue link color, underline on hover |
| `h1-h6` | Sized headers (16px down to 12px) |
| `blockquote` | Left border, italic, light background |
| `hr` | Thin divider line |

#### Files

| File | Purpose |
|------|---------|
| `extension/src/webview/planBundle.js` | Bundle entry point (imports marked + plan.js + planMain.js) |
| `extension/src/webview/plan.js` | `renderMarkdown()`, `sanitizeMarkdownHtml()`, `ALLOWED_TAGS`, `ALLOWED_ATTRIBUTES` |
| `extension/src/webview/style.css` | CSS for `.task-description` markdown elements |
| `extension/esbuild.js` | Two-bundle build configuration |
| `extension/src/extension.ts` | `getPlanWebviewContent()` loads planBundle.js |
| `extension/src/webview/__tests__/markdown.test.js` | 58 tests |

#### Tests

The `markdown.test.js` file contains 58 tests covering:

- **sanitizeMarkdownHtml (32 tests)**
  - Allowed tags (p, strong, em, code, pre, ul, ol, li, a, br, h1-h6, blockquote)
  - Disallowed tags (script, style, iframe, object, embed, form, img)
  - Dangerous attributes (onclick, onmouseover, javascript:, data:)
  - Edge cases (empty, null, undefined, nested, mixed)

- **renderMarkdown (15 tests)**
  - Bold, italic, code, code blocks
  - Lists (ordered, unordered)
  - Links, headings, blockquotes
  - Complex markdown, sanitization

- **Constants (8 tests)**
  - ALLOWED_TAGS includes safe tags, excludes dangerous
  - ALLOWED_ATTRIBUTES allows href, blocks event handlers

- **Integration (3 tests)**
  - Markdown renders to HTML, sanitization works, empty handling

## Further Considerations

- **TDD Approach:** Write tests first, then implement
- **0-based ordinals:** LLM-friendly API (ordinal 0 = first position)
