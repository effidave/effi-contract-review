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
- Unit tests for all class methods (50 tests)

**Files:** `extension/src/models/workplan.ts`, `extension/src/__tests__/workplan.test.ts`

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

### 5. LLM/MCP Integration

- Hook MCP tool calls to log Edit objects automatically
- Tests for edit logging

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
| 1. Core Classes | workplan.test.ts | 50 |
| 2. Persistence | planStorage.test.ts | 36 |
| 3. Integration | planIntegration.test.ts | 51 |
| 4. Webview UI | plan.test.js | 77 |
| **Total** | | **214** |

## Further Considerations

- **TDD Approach:** Write tests first, then implement
- **0-based ordinals:** LLM-friendly API (ordinal 0 = first position)
- **Parallel panels:** Plan and Contract Analysis can be open simultaneously