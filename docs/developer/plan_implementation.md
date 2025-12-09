# Plan Tab Implementation (Steps 1-3)

This document describes the implementation of the Plan Tab feature for tracking LLM agent work tasks and MCP tool call edits.

## Overview

The Plan Tab allows solo lawyers to:
- Track work tasks during contract drafting/review sessions
- Log MCP tool calls (edits) against specific tasks
- View task history with associated edits
- Persist plans across sessions

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Webview UI    │────▶│  PlanProvider    │────▶│  PlanStorage    │
│  (Plan Tab)     │◀────│  (extension.ts)  │◀────│  (File System)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                       │                        │
        │                       │                        ▼
        │                       │              ┌─────────────────────┐
        │                       │              │  plans/current/     │
        │                       │              │    plan.md          │
        │                       │              │    plan.meta.json   │
        │                       │              │  logs/              │
        │                       │              │    edits.jsonl      │
        │                       │              └─────────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────┐     ┌──────────────────┐
│  WorkPlan       │     │  WorkTask        │
│  (domain model) │────▶│  (domain model)  │
└─────────────────┘     └──────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  Edit            │
                        │  (domain model)  │
                        └──────────────────┘
```

## Step 1: Core Classes (50 tests)

**File:** `extension/src/models/workplan.ts`

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

## Step 2: Persistence Layer (36 tests)

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

## Step 3: Extension Integration (51 tests)

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

## Test Coverage

| Test Suite | File | Tests |
|------------|------|-------|
| Core Classes | `workplan.test.ts` | 50 |
| Persistence | `planStorage.test.ts` | 36 |
| Integration | `planIntegration.test.ts` | 51 |
| **Total** | | **137** |

## Next Steps

### Step 4: Webview UI
- Add tab bar with "Contract Analysis" and "Plan" tabs
- Create Plan tab content (task list, task details)
- Implement View/Edit toggle
- Wire up auto-save on edit

### Step 5: LLM/MCP Integration
- Hook MCP tool calls to automatically log Edit objects
- Associate edits with the current active task
- Provide task context to LLM for better responses

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
