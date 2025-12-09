# VS Code Webview Architecture

## Overview

The Effi Contract Viewer extension uses VS Code webviews to display contract analysis data and work plan tasks. There are **two independent WebviewPanels**:

1. **Contract Analysis Panel** (`effiContractViewer`) - Document viewing and editing
2. **Work Plan Panel** (`effiPlanViewer`) - Task tracking and edit logging

These panels can be opened side-by-side for an integrated workflow.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VS Code Extension Host                            │
│                              (extension.ts)                                 │
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │  webviewPanel       │  │  planWebviewPanel   │  │  PlanProvider       │  │
│  │  (Contract Analysis)│  │  (Work Plan)        │  │  (Business Logic)   │  │
│  └──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘  │
│             │                        │                        │             │
│             │    postMessage()       │    postMessage()       │             │
│             │                        │                        │             │
└─────────────┼────────────────────────┼────────────────────────┼─────────────┘
              │                        │                        │
              ▼                        ▼                        ▼
┌─────────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│  Contract Analysis      │  │  Work Plan          │  │  File System        │
│  Webview                │  │  Webview            │  │                     │
│                         │  │                     │  │  plans/current/     │
│  ┌───────────────────┐  │  │  ┌───────────────┐  │  │    plan.md          │
│  │ main.js           │  │  │  │ planMain.js   │  │  │    plan.meta.json   │
│  │ editor.js         │  │  │  │ plan.js       │  │  │  logs/              │
│  │ toolbar.js        │  │  │  │               │  │  │    edits.jsonl      │
│  │ comments.js       │  │  │  │ PlanPanel     │  │  │                     │
│  │ shortcuts.js      │  │  │  │ class         │  │  │  analysis/          │
│  └───────────────────┘  │  │  └───────────────┘  │  │    blocks.jsonl     │
│                         │  │                     │  │    manifest.json    │
│  style.css (shared)     │  │  style.css (shared) │  │    index.json       │
└─────────────────────────┘  └─────────────────────┘  └─────────────────────┘
              │                        │                        ▲
              │                        │                        │
              └────────────────┬───────┴────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Python Scripts     │
                    │                     │
                    │  get_outline.py     │
                    │  save_blocks.py     │
                    │  manage_comments.py │
                    │  manage_revisions.py│
                    └─────────────────────┘
```

## Panel Lifecycle

### Contract Analysis Panel
- **Created by:** `showContractWebview()` or `analyzeAndLoadDocument()`
- **Command:** `effi-contract-viewer.showWebview`
- **Content:** `getWebviewContent()` returns HTML with main.js and editor scripts

### Work Plan Panel
- **Created by:** `showPlanWebview()`
- **Command:** `effi-contract-viewer.showPlan`
- **Content:** `getPlanWebviewContent()` returns HTML with planMain.js and plan.js

Both panels:
- Persist when hidden (`retainContextWhenHidden: true`)
- Can be revealed in the same or different view columns
- Communicate via `postMessage()` with the extension host

## Architecture Components

### 1. Extension Host (`extension.ts`)

The extension host runs in Node.js and has access to the VS Code API and file system.

**Key Responsibilities:**
- Creates and manages the webview panel
- Loads analysis artifacts from disk (`manifest.json`, `index.json`, `blocks.jsonl`)
- Executes Python scripts to generate outline data
- Handles messages from the webview
- Sends data to the webview via `postMessage()`

**Data Loading Flow:**
```typescript
loadAnalysisFromDirectory(analysisDir, projectPath)
  ├─> Load manifest.json (metadata)
  ├─> Load index.json (counts and stats)
  ├─> Execute get_outline.py → outline array
  ├─> Load blocks.jsonl → blocks array (full text)
  └─> Send all data to webview via postMessage
```

**Message Handling:**
```typescript
webview.onDidReceiveMessage((message) => {
  switch (message.command) {
    case 'ready': // Webview initialized, send data
    case 'sendToChat': // User wants to copy clauses to chat
    case 'jumpToClause': // Navigate to clause (future)
  }
})
```

### 2. Webview Content (`main.js` + `style.css`)

The webview runs in a sandboxed iframe with restricted access. It can only communicate with the extension via message passing.

**Key State:**
- `currentData`: Latest data received from extension
- `allBlocks`: Array of all blocks from blocks.jsonl
- `selectedClauses`: Set of selected clause IDs (shared across views)
- `activeTab`: Current active tab ('outline' or 'fulltext')

**Message Flow:**
```javascript
// Extension → Webview
window.addEventListener('message', (event) => {
  switch (event.data.command) {
    case 'updateData': // New analysis data available
    case 'noAnalysis': // No analysis found
    case 'refresh': // Re-render current data
  }
})

// Webview → Extension
vscode.postMessage({
  command: 'sendToChat',
  clauseIds: [...],
  query: '...'
})
```

### 3. HTML Structure (`extension.ts` - `getWebviewContent()`)

The HTML is generated dynamically with CSP (Content Security Policy) for security:

```html
<div id="app">
  <div class="header"><!-- Title + toolbar --></div>
  
  <div class="content">
    <div id="loading"><!-- Initial placeholder --></div>
    
    <div id="data-view">
      <!-- Document Info Section -->
      <div id="doc-info"></div>
      
      <!-- Tabbed View Section -->
      <div class="tabs">
        <button id="outline-tab" class="active">Outline</button>
        <button id="fulltext-tab">Full Text</button>
      </div>
      <div id="outline-content"></div>
      <div id="fulltext-content"></div>
      
      <!-- Shared Chat Controls -->
      <div class="chat-query-box">
        <input type="checkbox" class="clause-checkbox" />
        <textarea id="chat-query"></textarea>
        <button id="send-to-chat"></button>
      </div>
      
      <!-- Schedules Section -->
      <div id="schedules"></div>
    </div>
  </div>
</div>
```

## Dual-View Feature Implementation

### Problem Statement
Users need to:
1. See a compact outline view for navigation
2. See full text of each clause/block
3. Select clauses in either view with synchronized checkboxes
4. Always send full text to chat (not truncated outline text)

### Solution Architecture

#### Tab System
Two tabs share the same checkbox state via a `Set` of selected clause IDs:

**Outline Tab (`renderOutlineView`):**
- Shows hierarchical structure with indentation
- Displays: checkbox + ordinal + truncated text (one line)
- Uses `data.outline` array from Python `get_outline.py` script
- Lightweight for quick navigation

**Full Text Tab (`renderFullTextView`):**
- Shows complete block text from `blocks.jsonl`
- Displays: checkbox + ordinal + full text in card layout
- Uses `allBlocks` array loaded from `blocks.jsonl`
- Each block shown in a styled card with full content

#### Checkbox State Synchronization

```javascript
// Central state store
const selectedClauses = new Set();

// Unified handler for all checkboxes
function handleCheckboxChange(id, checked) {
  if (checked) {
    selectedClauses.add(id);
  } else {
    selectedClauses.delete(id);
  }
  
  // Sync ALL checkboxes with this ID across both views
  document.querySelectorAll(`.clause-checkbox[data-id="${id}"]`)
    .forEach(cb => cb.checked = checked);
  
  updateSelectionCount();
}
```

**How It Works:**
1. User clicks checkbox in either view
2. `handleCheckboxChange()` updates the central `Set`
3. All checkboxes with that `data-id` are updated (both views)
4. Selection count updates in UI

#### Data Flow for "Send to Chat"

```
User clicks "Send to Chat"
  ↓
webview: sendToChat()
  ↓
postMessage({ command: 'sendToChat', clauseIds: [...], query: '...' })
  ↓
extension: sendClausesToChat(clauseIds, query)
  ↓
Execute get_clause_details.py with clause IDs
  ↓
Python: Load blocks.jsonl, filter by IDs, return full text
  ↓
extension: Format as "Clause {ordinal}: {full_text}"
  ↓
Copy to clipboard + show notification
```

**Key Point:** The extension always fetches full text from `blocks.jsonl` using the selected clause IDs, regardless of which tab the user is viewing.

## File Structure

```
extension/
├── src/
│   ├── extension.ts           # Extension host (Node.js)
│   │                          # - showContractWebview()
│   │                          # - showPlanWebview()
│   │                          # - Message handlers for both panels
│   ├── models/
│   │   ├── workplan.ts        # WorkPlan, WorkTask, Edit classes
│   │   ├── planStorage.ts     # File I/O for plans and edits
│   │   └── planProvider.ts    # Business logic bridge
│   └── webview/
│       ├── main.js            # Contract Analysis webview logic
│       ├── editor.js          # BlockEditor class (Sprint 2)
│       ├── toolbar.js         # Formatting toolbar (Sprint 2)
│       ├── shortcuts.js       # Keyboard shortcuts (Sprint 2)
│       ├── comments.js        # Comment panel (Sprint 3)
│       ├── plan.js            # PlanPanel class (Plan feature)
│       ├── planMain.js        # Plan webview entry point
│       ├── style.css          # VS Code theme-aware styles (shared)
│       └── __tests__/
│           └── plan.test.js   # 77 PlanPanel tests
├── scripts/
│   ├── get_outline.py         # Generate outline from artifacts
│   ├── get_clause_details.py  # Fetch full text for clause IDs
│   ├── save_blocks.py         # Save edited blocks to .docx (Sprint 2)
│   ├── save_document.py       # Save with UUID embedding (Sprint 1)
│   ├── manage_comments.py     # Comment resolve/unresolve (Sprint 3)
│   ├── manage_revisions.py    # Track changes (Sprint 3)
│   └── get_history.py         # Git version history (Sprint 1)
└── dist/                      # Compiled output
```

## Python Integration

The extension bridges VS Code (TypeScript) with the Python analysis tools:

### get_outline.py
**Purpose:** Generate hierarchical outline from analysis artifacts

**Input:** `analysis_dir` path  
**Output:** JSON with outline array
```json
{
  "success": true,
  "outline": [
    {
      "id": "block-uuid",
      "ordinal": "1.2.3",
      "text": "Clause text preview...",
      "level": 2,
      "type": "clause"
    }
  ]
}
```

### get_clause_details.py
**Purpose:** Fetch full text for specific clause IDs

**Input:** `analysis_dir` path + clause IDs via stdin  
**Output:** JSON with full clause data
```json
{
  "success": true,
  "clauses": [
    {
      "id": "block-uuid",
      "ordinal": "1.2.3",
      "text": "Full clause text here...",
      "level": 2,
      "section_id": "section-uuid"
    }
  ]
}
```

## Styling with VS Code Themes

All styles use CSS variables that VS Code provides:

```css
color: var(--vscode-foreground);
background: var(--vscode-editor-background);
border-color: var(--vscode-panel-border);
```

**Key Variables:**
- `--vscode-foreground` / `--vscode-background`
- `--vscode-button-*` (primary, secondary, hover)
- `--vscode-input-*` (background, border, foreground)
- `--vscode-list-*` (hover, active backgrounds)
- `--vscode-focusBorder` (active element highlight)

This ensures the webview matches the user's color theme (light/dark/custom).

## Security: Content Security Policy

The webview uses a strict CSP to prevent XSS attacks:

```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'none'; 
               style-src ${webview.cspSource} 'unsafe-inline'; 
               script-src 'nonce-${nonce}';">
```

**What This Does:**
- `default-src 'none'` - Block everything by default
- `style-src` - Only allow styles from extension files
- `script-src 'nonce-...'` - Only allow scripts with matching nonce
- No eval, no inline scripts (except with nonce)

## Development Workflow

### Building the Extension
```bash
cd extension
npm install          # Install dependencies
npm run compile      # Build once
npm run watch        # Build on file changes
```

### Testing Changes
1. Make changes to `extension.ts`, `main.js`, or `style.css`
2. Run `npm run compile` (or use watch mode)
3. Press `F5` in VS Code to launch Extension Development Host
4. Open a contract document and click the book icon
5. Use VS Code Developer Tools: `Help > Toggle Developer Tools`

### Debugging Tips

**Extension Host (Node.js):**
- Use `console.log()` - shows in Debug Console
- Set breakpoints in `extension.ts`
- Check terminal output for Python script errors

**Webview (Browser):**
- Right-click webview > Inspect Element
- Console logs appear in Developer Tools
- Check Network tab for CSP violations
- Use `console.log(JSON.stringify(data))` for complex objects

## Common Tasks

### Adding a New Section to the Webview

1. Add HTML structure in `getWebviewContent()`:
```typescript
<div class="section">
  <h2>My New Section</h2>
  <div id="my-section"></div>
</div>
```

2. Add render function in `main.js`:
```javascript
function renderMySection(data) {
  const el = document.getElementById('my-section');
  if (!el) return;
  el.innerHTML = `<div>...</div>`;
}
```

3. Call from `renderData()`:
```javascript
function renderData(data) {
  // ... existing code
  renderMySection(data);
}
```

4. Add styles in `style.css`:
```css
#my-section {
  padding: 12px;
  /* ... */
}
```

### Adding a New Message Type

**Extension → Webview:**
```typescript
// In extension.ts
webviewPanel?.webview.postMessage({
  command: 'myNewCommand',
  data: { /* ... */ }
});
```

```javascript
// In main.js
window.addEventListener('message', event => {
  switch (event.data.command) {
    case 'myNewCommand':
      handleMyCommand(event.data.data);
      break;
  }
});
```

**Webview → Extension:**
```javascript
// In main.js
vscode.postMessage({
  command: 'myNewAction',
  payload: { /* ... */ }
});
```

```typescript
// In extension.ts
webview.onDidReceiveMessage(async (message) => {
  switch (message.command) {
    case 'myNewAction':
      await handleMyAction(message.payload);
      break;
  }
});
```

## Recent Changes (Nov-Dec 2025)

### Plan Tab Feature: Separate WebviewPanel (Dec 2025)
**Problem:** Users need to track work tasks and MCP tool calls during contract review sessions.

**Architecture Decision:** Implemented as a **separate WebviewPanel** rather than a tab within Contract Analysis.

**Benefits:**
- Can be opened side-by-side with Contract Analysis
- Independent lifecycle (close one without affecting other)
- Cleaner separation of concerns
- Simpler HTML/JS (no tab switching logic needed)

**Changes Made:**
1. **extension.ts:**
   - Added `planWebviewPanel` variable
   - Added `currentProjectPath` variable (derived from document path)
   - Added `showPlanWebview()` function
   - Added `getPlanWebviewContent()` function
   - Added `getProjectDir()` helper
   - Registered `effi-contract-viewer.showPlan` command
   - Added Plan message handlers (getPlan, addTask, updateTask, etc.)

2. **planMain.js** - Entry point for Plan webview:
   - Acquires VS Code API
   - Gets initial project path from page data
   - Creates PlanPanel instance
   - Handles messages from extension

3. **plan.js** - PlanPanel class:
   - Task list with CRUD operations
   - Status filtering and progress bar
   - Edit log display
   - Keyboard navigation

4. **TypeScript models:**
   - `workplan.ts` - WorkPlan, WorkTask, Edit, LegalDocument classes
   - `planStorage.ts` - File I/O for plans and edits + edit retrieval
   - `planProvider.ts` - Business logic bridge + auto-association

5. **Python Plan MCP Tools** (new):
   - `effilocal/mcp_server/plan/models.py` - Python equivalents of TypeScript classes
   - `effilocal/mcp_server/plan/storage.py` - YAML/JSON file I/O
   - `effilocal/mcp_server/tools/plan_tools.py` - MCP tools for LLM plan management

**Test Coverage:** 279 Plan TypeScript tests + 111 MCP integration tests (39 McpToolLogger + 27 Python logging + 45 Plan tools) = **390 total**

See: [plan_tab.md](./plan_tab.md), [plan_implementation.md](./plan_implementation.md)

### Sprint 3: Comments & Track Changes (Dec 2025)
**Problem:** Users needed to manage Word comments and track changes from the webview.

**Changes Made:**
1. **CommentPanel class** (`comments.js`) - Toggle panel showing all comments
2. **Comment status tracking** - Active/resolved status via commentsExtended.xml
3. **Resolve/unresolve actions** - Update comment status in document
4. **Track changes support** - Accept/reject individual or all revisions
5. **Python scripts** - manage_comments.py, manage_revisions.py

See: [sprint-3-comments-implementation.md](./sprint-3-comments-implementation.md)

### Sprint 2: WYSIWYG Editor (Dec 2025)
**Problem:** Users needed to edit documents directly in the webview, not just view them.

**Changes Made:**
1. **BlockEditor class** (`editor.js`) - ContentEditable-based editing
2. **Toolbar component** (`toolbar.js`) - B/I/U formatting, undo/redo, save
3. **Keyboard shortcuts** (`shortcuts.js`) - Ctrl+B/I/U/S/Z/Y
4. **Edit mode toggle** - Switch between view and edit modes
5. **Save flow** - Webview → Extension → Python → .docx update
6. **Run-based formatting** - Text formatting stored as runs with start/end positions

**Key Design Decision:**
Use custom ContentEditable implementation rather than a framework (Lexical, ProseMirror) since our editing needs are block-based and relatively simple.

See: [sprint-2-wysiwyg-editor.md](./sprint-2-wysiwyg-editor.md)

### Sprint 1: Block ID Persistence (Dec 2025)
**Problem:** Document identity needed to survive external edits and re-analysis.

**Changes Made:**
1. **Para_id matching** - Native `w14:paraId` attributes used to match blocks to paragraphs
2. **Hash fallback** - SHA-256 matching when para_ids are unavailable
3. **Git integration** - Auto-commit on save with meaningful messages
4. **Re-analysis stability** - Block IDs preserved when re-parsing document

See: [sprint-1-uuid-persistence.md](./sprint-1-uuid-persistence.md)

### Dual-Tab Implementation (Nov 2025)
**Problem:** Users needed to see both compact outline and full text, with synchronized selection state.

**Changes Made:**
1. **HTML Structure** - Added tab buttons and two content divs
2. **Tab Switching** - `setupTabs()` manages active tab state
3. **Blocks Loading** - Extension loads `blocks.jsonl` alongside outline
4. **Shared Checkboxes** - `handleCheckboxChange()` syncs state across views
5. **Full Text View** - New `renderFullTextView()` displays complete block text
6. **Chat Integration** - Always sends full text via `get_clause_details.py`

**Key Design Decision:**
Keep selection state in a `Set` and sync all matching checkboxes, rather than maintaining separate state per view. This ensures consistency and simplifies the mental model.

## Troubleshooting

### Webview Shows Blank/White Screen
- Check Developer Tools Console for errors
- Verify CSP is not blocking resources
- Check that `scriptUri` and `styleUri` are correct
- Ensure nonce matches between CSP and script tag

### Checkboxes Not Syncing
- Verify both views use `data-id` attribute with same ID
- Check `handleCheckboxChange()` is called from both views
- Use DevTools to inspect checkbox elements and their IDs

### Python Scripts Failing
- Check extension's Debug Console for stderr output
- Verify Python environment is accessible from extension
- Test scripts manually: `python scripts/get_outline.py path/to/analysis`
- Check that effilocal module is in Python path

### Styles Not Applying
- Verify CSS variable names: `var(--vscode-*)`
- Check for typos in class names
- Use DevTools Elements tab to inspect computed styles
- Remember: styles are scoped to the webview iframe

## Resources

- [VS Code Extension API](https://code.visualstudio.com/api)
- [Webview API Guide](https://code.visualstudio.com/api/extension-guides/webview)
- [VS Code Theme Colors](https://code.visualstudio.com/api/references/theme-color)
- [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
