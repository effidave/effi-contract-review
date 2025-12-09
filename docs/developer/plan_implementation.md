# Plan Tab Implementation (Steps 1-4)

This document describes the implementation of the Plan Tab feature for tracking LLM agent work tasks and MCP tool call edits.

## Overview

The Plan Tab allows solo lawyers to:
- Track work tasks during contract drafting/review sessions
- Log MCP tool calls (edits) against specific tasks
- View task history with associated edits
- Persist plans across sessions

## Architecture

The Plan uses a **separate WebviewPanel** from Contract Analysis, allowing side-by-side viewing.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VS Code Extension Host                            │
│                              (extension.ts)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────┐      ┌───────────────────────┐                   │
│  │  webviewPanel         │      │  planWebviewPanel     │                   │
│  │  "Contract Analysis"  │      │  "Work Plan"          │                   │
│  │  (effiContractViewer) │      │  (effiPlanViewer)     │                   │
│  └───────────┬───────────┘      └───────────┬───────────┘                   │
│              │                              │                               │
│              │    postMessage()             │    postMessage()              │
│              ▼                              ▼                               │
│  ┌───────────────────────────────────────────────────────────┐              │
│  │                    Message Handlers                       │              │
│  │  Contract: analyze, saveBlocks, getComments, ...          │              │
│  │  Plan: getPlan, addTask, updateTask, deleteTask, logEdit  │              │
│  └───────────────────────────────────────────────────────────┘              │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │  PlanProvider       │  │  PlanStorage        │  │  WorkPlan / Task    │  │
│  │  (business logic)   │──│  (file I/O)         │──│  (domain models)    │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
│                                      │                                      │
└──────────────────────────────────────┼──────────────────────────────────────┘
                                       │
                                       ▼
                          ┌─────────────────────────┐
                          │      File System        │
                          │                         │
                          │  <project>/             │
                          │  ├── plans/current/     │
                          │  │   ├── plan.md        │
                          │  │   └── plan.meta.json │
                          │  └── logs/              │
                          │      └── edits.jsonl    │
                          └─────────────────────────┘
```

### Webview Scripts

| Panel | Entry Point | Main Component | Purpose |
|-------|-------------|----------------|---------|
| Contract Analysis | `main.js` | BlockEditor, Toolbar | Document viewing/editing |
| Work Plan | `planMain.js` | PlanPanel | Task tracking |

Both share `style.css` for consistent VS Code theming.

## Step 1: Core Classes (77 tests)

**File:** `extension/src/models/workplan.ts`

### LegalDocument Class

Represents a document that a WorkPlan relates to:

```typescript
interface LegalDocumentOptions {
    id?: string;           // 8-char hex, auto-generated
    filename: string;      // Full path to .docx file
    displayName?: string;  // Friendly name (auto-derived if not provided)
    addedDate?: Date;      // When added to plan
}
```

**Key Methods:**
- `matchesFilename(filename)` - Case-insensitive, path-normalized comparison
- `toJSON()` / `fromJSON()` / `toYAML()` - Serialization

### Edit Class

Represents a single MCP tool call logged against a task.

```typescript
interface EditOptions {
    id?: string;           // 8-char hex, auto-generated if not provided
    taskId: string;        // ID of the parent task
    toolName: string;      // MCP tool name (e.g., "search_and_replace")
    request: Record<string, unknown>;   // Tool request parameters
    response: Record<string, unknown>;  // Tool response
    timestamp?: Date;      // Auto-set to now if not provided
}
```

**Key Methods:**
- `toJSON()` / `fromJSON()` - Serialization for storage
- `toJSONL()` - Single-line JSON for append-only log

### WorkTask Class

Represents a work item with status tracking.

```typescript
interface WorkTaskOptions {
    id?: string;           // 8-char hex, auto-generated
    title: string;
    description: string;
    status?: TaskStatus;   // 'pending' | 'in_progress' | 'completed' | 'blocked'
    ordinal?: number;      // Position in task list (0-based)
    creationDate?: Date;
    completionDate?: Date | null;
    editIds?: string[];    // IDs of associated edits
}
```

**Key Methods:**
- `start()` / `complete()` / `block()` / `reset()` - Status transitions
- `isOpen()` - Returns true if status is pending/in_progress/blocked
- `addEditId(id)` - Link an edit to this task
- `toJSON()` / `fromJSON()` / `toYAML()` - Serialization

### WorkPlan Class

Container for tasks with ordering and edit logging.

```typescript
class WorkPlan {
    tasks: WorkTask[];
    documents: LegalDocument[];  // Documents this plan relates to
    
    // Document management
    addDocument(doc: LegalDocument): boolean;  // No duplicates by filename
    removeDocument(id: string): boolean;
    getDocumentById(id: string): LegalDocument | undefined;
    getDocumentByFilename(filename: string): LegalDocument | undefined;
    hasDocument(filename: string): boolean;
    getDocumentEdits(): Edit[];  // Edits affecting any plan document
    
    // Task management
    addTaskAtEnd(task: WorkTask): void;
    addTaskAtStart(task: WorkTask): void;
    addTaskAtOrdinal(task: WorkTask, ordinal: number): void;  // 0-based
    removeTask(id: string): boolean;
    moveTask(id: string, newOrdinal: number): boolean;        // 0-based
    getTaskById(id: string): WorkTask | undefined;
    
    // Edit logging
    logEdit(edit: Edit): void;
    getEditsForTask(taskId: string): Edit[];
    get edits(): Edit[];  // All edits
    
    // Serialization
    toYAMLFrontmatter(): string;
    toPlanMd(): string;
    toJSON(): WorkPlanJSON;
    static fromYAMLFrontmatter(yaml: string): WorkPlan;
    static parsePlanMd(content: string): WorkPlan;
    static fromJSON(json: WorkPlanJSON): WorkPlan;
}
```

**Ordinal Convention:** All ordinal parameters are **0-based** (index 0 = first position). This was chosen because LLM agents are trained on code that predominantly uses 0-based indexing.

## Step 2: Persistence Layer (77 tests)

**File:** `extension/src/models/planStorage.ts`

### File Structure

```
<project>/
├── plans/
│   └── current/
│       ├── plan.md          # Human-readable YAML frontmatter + markdown
│       └── plan.meta.json   # Fast-loading JSON representation
└── logs/
    └── edits.jsonl          # Append-only edit log
```

### PlanStorage Class

```typescript
class PlanStorage {
    constructor(projectPath: string);
    
    // Directory management
    ensureDirectories(): Promise<void>;
    ensurePlanFile(): Promise<void>;
    
    // Plan persistence
    savePlan(plan: WorkPlan): Promise<void>;      // Saves plan.md
    savePlanMeta(plan: WorkPlan): Promise<void>;  // Saves plan.meta.json
    saveAll(plan: WorkPlan): Promise<void>;       // Saves both
    loadPlan(): Promise<WorkPlan | null>;         // Loads from plan.md
    loadPlanMeta(): Promise<WorkPlan | null>;     // Loads from plan.meta.json (faster)
    
    // Edit persistence
    appendEdit(edit: Edit): Promise<void>;        // Appends to edits.jsonl
    loadEdits(): Promise<Edit[]>;                 // Loads all edits
    loadEditsForTask(taskId: string): Promise<Edit[]>;
    
    // Edit retrieval (for auto-association)
    getEditsByIds(ids: string[]): Promise<Edit[]>;     // Retrieve by IDs (ordered)
    getAllEdits(): Promise<Edit[]>;                     // All edits from log
    getEditById(id: string): Promise<Edit | null>;      // Single edit lookup
    getNewEditsSince(cutoff: Date): Promise<Edit[]>;    // After timestamp
    getUnassociatedEdits(): Promise<Edit[]>;            // taskId is null
    getEditsForDocument(filename: string): Promise<Edit[]>; // By document
    
    // Combined operations
    loadWithEdits(): Promise<{ plan: WorkPlan | null; edits: Edit[] }>;
    getOrCreatePlan(): Promise<WorkPlan>;
}
```

### plan.md Format

```markdown
---
tasks:
  - id: "a1b2c3d4"
    title: "Review indemnity clause"
    description: "Check if indemnity limits are reasonable"
    status: "in_progress"
    ordinal: 0
    creationDate: "2025-12-09T10:30:00.000Z"
    completionDate: null
    editIds:
      - "e1f2g3h4"
---

## Task: Review indemnity clause

**Status:** in_progress

Check if indemnity limits are reasonable
```

### edits.jsonl Format

```json
{"id":"e1f2g3h4","taskId":"a1b2c3d4","toolName":"search_and_replace","request":{"filename":"contract.docx","find_text":"unlimited","replace_text":"capped at £1M"},"response":{"success":true,"replaced_count":1},"timestamp":"2025-12-09T10:35:00.000Z"}
```

## Step 3: Extension Integration (66 tests)

### PlanProvider Class

**File:** `extension/src/models/planProvider.ts`

Bridges the webview UI and storage layer.

```typescript
class PlanProvider {
    constructor(projectPath: string);
    
    // Initialization
    initialize(): Promise<void>;
    
    // Plan operations
    getPlan(): Promise<WorkPlan>;
    savePlan(plan: WorkPlan): Promise<OperationResult>;
    
    // Task operations
    addTask(title: string, description: string, options?: AddTaskOptions): Promise<AddTaskResult>;
    updateTask(taskId: string, updates: TaskUpdateOptions): Promise<OperationResult>;
    deleteTask(taskId: string): Promise<OperationResult>;
    moveTask(taskId: string, newOrdinal: number): Promise<OperationResult>;
    
    // Edit operations
    logEdit(taskId: string, toolName: string, request: object, response: object): Promise<LogEditResult>;
    getEditsForTask(taskId: string): Promise<Edit[]>;
    
    // Auto-association (links MCP tool calls to active task)
    getActiveTask(): WorkTask | null;                              // First in_progress task
    processUnassociatedEdits(): Promise<ProcessEditsResult>;       // Batch associate unassigned edits
    associateEditWithTask(editId: string, taskId: string): Promise<AssociateEditResult>;  // Manual link
    processNewEdits(): Promise<ProcessEditsResult>;                // Incremental since last timestamp
    getLastProcessedTimestamp(): Promise<Date | null>;             // Cursor tracking
    setLastProcessedTimestamp(timestamp: Date): Promise<void>;
    
    // Webview data
    toWebviewData(): object;
}
```

### Message Handlers

**File:** `extension/src/extension.ts`

Added to the `onDidReceiveMessage` switch statement:

| Message Command | Handler Function | Description |
|-----------------|------------------|-------------|
| `getPlan` | `handleGetPlan` | Load plan and send to webview |
| `savePlan` | `handleSavePlan` | Save plan to disk |
| `addTask` | `handleAddTask` | Add new task with optional positioning |
| `updateTask` | `handleUpdateTask` | Update task title/description/status |
| `deleteTask` | `handleDeleteTask` | Remove task from plan |
| `moveTask` | `handleMoveTask` | Reorder task (0-based ordinal) |
| `logEdit` | `handleLogEdit` | Log MCP tool call for a task |

### Message Protocol

**Request messages from webview:**

```typescript
// Get current plan
{ command: 'getPlan', projectPath: string }

// Save entire plan
{ command: 'savePlan', projectPath: string, plan: WorkPlanJSON }

// Add task
{ command: 'addTask', projectPath: string, title: string, description: string, options?: { position?: 'start' | 'end', ordinal?: number } }

// Update task
{ command: 'updateTask', projectPath: string, taskId: string, updates: { title?: string, description?: string, status?: TaskStatus } }

// Delete task
{ command: 'deleteTask', projectPath: string, taskId: string }

// Move task
{ command: 'moveTask', projectPath: string, taskId: string, newOrdinal: number }

// Log edit
{ command: 'logEdit', projectPath: string, taskId: string, toolName: string, request: object, response: object }
```

**Response messages to webview:**

```typescript
// Plan data
{ command: 'planData', plan: { tasks: WorkTaskJSON[] } }

// Plan saved
{ command: 'planSaved', success: true }

// Task added
{ command: 'taskAdded', task: WorkTaskJSON, success: true }

// Task updated
{ command: 'taskUpdated', taskId: string, success: true }

// Task deleted
{ command: 'taskDeleted', taskId: string, success: true }

// Task moved
{ command: 'taskMoved', taskId: string, newOrdinal: number, success: true }

// Edit logged
{ command: 'editLogged', edit: EditJSON, taskId: string, success: true }

// Error
{ command: 'planError', error: string }
```

## Step 4: Webview UI (59 tests)

**Architecture:** The Plan is a **separate WebviewPanel** from Contract Analysis. This allows:
- Opening Plan side-by-side with Contract Analysis
- Independent lifecycle (close one without affecting other)
- Cleaner separation of concerns

**Files:**
- `extension/src/webview/plan.js` - PlanPanel class implementation
- `extension/src/webview/planMain.js` - Plan webview entry point
- `extension/src/webview/__tests__/plan.test.js` - Comprehensive tests
- `extension/src/webview/style.css` - Plan panel CSS styles
- `extension/src/extension.ts` - showPlanWebview, getPlanWebviewContent, plan handlers

### PlanPanel Class

JavaScript webview component for task management UI.

```javascript
class PlanPanel {
    constructor(container, vscode, options = {});
    
    // Data management
    setTasks(tasks);         // Set all tasks
    getSelectedTask();       // Get currently selected task
    
    // Task operations
    addTask(task);           // Add new task to list
    updateTask(taskId, updates);  // Update task properties
    deleteTask(taskId);      // Remove task
    moveTask(taskId, newOrdinal); // Reorder task
    
    // Filtering
    setFilter(filter);       // 'all' | 'pending' | 'in_progress' | 'completed' | 'blocked'
    
    // Message handling
    handleMessage(message);  // Handle VS Code webview messages
}
```

### UI Features

**Task List:**
- Displays all tasks with title, status, and ordinal
- Click to select task
- Status badge coloring (pending=blue, in_progress=yellow, completed=green, blocked=red)
- Expandable task items to show description and edit log

**Task Actions:**
- Add new task (button or keyboard shortcut)
- Edit task inline
- Delete task with optional confirmation
- Move task up/down in list
- Status change dropdown

**Filtering:**
- Filter by status: All, Pending, In Progress, Completed, Blocked
- Filter persists during session
- Count indicators for each status

**Edit Log Display:**
- Shows MCP tool calls associated with each task
- Tool name, timestamp, and request/response preview
- Expandable for full details

**Progress Bar:**
- Visual indicator of completion progress
- Shows "X of Y completed" text

**Keyboard Navigation:**
- Arrow keys to navigate between tasks
- Enter to select/expand task
- Delete/Backspace to delete with confirmation
- Escape to deselect

### CSS Styling

Added to `style.css`:
- `.plan-webview` - Body class for plan webview
- `.plan-panel` - Main panel container
- `.plan-header` - Panel header with title and add button
- `.plan-task-list` - Scrollable task list container
- `.plan-task-item` - Individual task styling
- `.plan-status-badge` - Status indicator badges
- `.plan-progress-bar` - Completion progress visualization
- `.plan-filter-controls` - Filter button group
- `.plan-edit-log` - Edit history display

### planMain.js Entry Point

Initializes the Plan webview:
- Acquires VS Code API
- Gets initial project path from page data
- Creates PlanPanel instance
- Handles messages from extension
- Sends 'ready' message on DOM ready

### Extension Integration

**extension.ts changes:**
- Added `planWebviewPanel` variable for separate panel
- Added `currentProjectPath` variable (derived from document path)
- Added `showPlanWebview()` function to create/reveal Plan panel
- Added `getPlanWebviewContent()` function for Plan HTML
- Added `getProjectDir()` helper function
- Registered `effi-contract-viewer.showPlan` command
- Plan message handlers moved to `showPlanWebview` message switch

## Test Coverage

| Test Suite | File | Tests |
|------------|------|-------|
| Core Classes + LegalDocument | `workplan.test.ts` | 77 |
| Persistence + Edit Retrieval | `planStorage.test.ts` | 77 |
| Integration + Auto-Association | `planIntegration.test.ts` | 66 |
| Webview UI | `plan.test.js` | 59 |
| **Total** | | **279** |

## Step 5: LLM/MCP Integration (Complete)

See [plan_tab.md](./plan_tab.md) for full details on:

- **5a. TypeScript McpToolLogger** - Extension-side tracking service (39 tests)
- **5b. Python MCP Server Logging** - `@with_logging` decorator for tool calls (27 tests)
- **5c. Edit Retrieval** - PlanStorage methods to read from edits.jsonl
- **5d. Auto-Association** - PlanProvider links new edits to active task
- **5e. Plan MCP Tools** - Python MCP tools for LLM plan management (45 tests)

### Plan MCP Tools

The LLM can now create and manage WorkPlans directly via MCP tools:

| Tool | Description |
|------|-------------|
| `get_work_plan(filename)` | Get plan with tasks, documents, summary stats |
| `add_task(filename, title, description, position?, ordinal?)` | Add task at start/end/ordinal |
| `update_task(filename, task_id, title?, description?, status?)` | Modify task |
| `delete_task(filename, task_id)` | Remove task |
| `move_task(filename, task_id, new_ordinal)` | Reorder task |
| `start_task(filename, task_id)` | Set status to in_progress |
| `complete_task(filename, task_id)` | Set status to completed |
| `block_task(filename, task_id)` | Set status to blocked |
| `add_plan_document(filename, display_name?)` | Track document |
| `remove_plan_document(filename, document_id)` | Untrack document |
| `list_plan_documents(filename)` | List tracked documents |

**Files:**
- `effilocal/mcp_server/plan/models.py` - Python WorkPlan, WorkTask, LegalDocument
- `effilocal/mcp_server/plan/storage.py` - YAML/JSON file I/O
- `effilocal/mcp_server/tools/plan_tools.py` - MCP tool implementations
- `tests/test_plan_mcp_tools.py` - 45 tests

**Total Tests:** 390 (279 TypeScript + 39 McpToolLogger + 27 Python logging + 45 Plan tools)

## Design Decisions

### Why 0-based ordinals?
LLM agents are trained on code that uses 0-based array indexing. When an agent calls `addTask` with `ordinal: 0`, it naturally expects that to mean "first position". Using 1-based indexing would cause confusion and bugs.

### Why separate edits.jsonl?
Edits are append-only and can grow large. Storing them separately:
1. Allows fast append without rewriting the entire file
2. Keeps plan.md readable and focused on task structure
3. Enables future features like edit search/filtering

### Why both plan.md and plan.meta.json?
- `plan.md`: Human-readable, can be viewed/edited in any text editor
- `plan.meta.json`: Fast loading for programmatic access, no YAML parsing overhead

### Why PlanProvider as intermediary?
Separating concerns:
- `PlanStorage`: Low-level file I/O
- `PlanProvider`: Business logic, caching, initialization
- Message handlers: Thin wrappers for webview communication
