# Work Plan Tools

You can use Work Plan tools to track your progress when reviewing or editing contracts. Plans help organize your work into tasks and automatically log the changes you make.

## Getting Started

When you start working on a document, register it and create tasks:

```
1. Add the document to the plan (add_plan_document)
2. Create tasks for what needs to be done (add_task)
3. Start working on a task (start_task)
4. Do the work (search_and_replace, add_comment, etc.)
5. Mark the task complete (complete_task)
6. Move to the next task
```

## Available Tools

### View the Plan

**get_work_plan(filename)**

See the current plan with all tasks and their status.

```
get_work_plan(filename="C:/EL_Projects/Acme/drafts/current_drafts/nda.docx")
```

Returns a summary showing task counts by status, plus full task and document details.

---

### Manage Tasks

**add_task(filename, title, description, position?, ordinal?)**

Add a new task to the plan.

```
add_task(
    filename="C:/EL_Projects/Acme/drafts/current_drafts/nda.docx",
    title="Review indemnity clause",
    description="Check if indemnity is mutual and reasonably capped"
)
```

Options:
- `position="end"` (default) - Add at the end
- `position="start"` - Add at the beginning
- `position="at"` with `ordinal=2` - Insert at a specific position (0-based)

**update_task(filename, task_id, title?, description?, status?)**

Change a task's title, description, or status.

```
update_task(
    filename="...",
    task_id="a1b2c3d4",
    description="Updated scope: also check liability caps"
)
```

**delete_task(filename, task_id)**

Remove a task from the plan.

**move_task(filename, task_id, new_ordinal)**

Reorder a task (0-based position).

---

### Task Status

Tasks have five statuses: `pending`, `in_progress`, `completed`, `blocked`, `notes`

**start_task(filename, task_id)**

Begin working on a task. Sets status to `in_progress`.

Always start a task before doing related work - this links your tool calls to the task.

**complete_task(filename, task_id)**

Mark a task as finished. Sets status to `completed` and records completion time.

**block_task(filename, task_id)**

Mark a task as blocked (waiting on something external).

**unblock_task(filename, task_id)**

Remove blocked status, returning to `pending`. Only works on blocked tasks.

---

### Notes Status

The `notes` status is special - it's for non-actionable items like reference information, decisions made, or context that doesn't need completing.

**Key difference:** Notes don't count towards progress. If you have 5 tasks and 2 notes, the progress shows "X of 5" (not "X of 7").

**convert_to_note(filename, task_id)**

Convert any task to a note. Sets status to `notes`.

```
convert_to_note(
    filename="C:/EL_Projects/Acme/drafts/current_drafts/nda.docx",
    task_id="a1b2c3d4"
)
```

**convert_to_task(filename, task_id)**

Convert a note back to an actionable task. Sets status to `pending`.

Returns a warning if the item wasn't actually a note (but still converts it).

**When to use notes:**
- Recording a decision: "Client confirmed 3-year term is acceptable"
- Reference information: "Key contact: John Smith, Legal Counsel"
- Context for future work: "Previous version had unlimited liability - this was negotiated down"

---

### Track Documents

**add_plan_document(filename, display_name?)**

Register a document that this plan relates to.

```
add_plan_document(
    filename="C:/EL_Projects/Acme/drafts/current_drafts/nda.docx",
    display_name="Acme NDA"
)
```

If you don't provide a display_name, the filename is used.

**remove_plan_document(filename, document_id)**

Stop tracking a document.

**list_plan_documents(filename)**

See all documents tracked by the plan.

---

## Example: Contract Review Workflow

When asked to review a contract, follow this pattern:

### Step 1: Set up the plan

```
# Register the document
add_plan_document(
    filename="C:/EL_Projects/Acme/drafts/current_drafts/nda.docx",
    display_name="Acme NDA Review"
)

# Create tasks based on what needs reviewing
add_task(filename="...", title="Review indemnity provisions", 
         description="Check for mutual indemnification and reasonable caps")

add_task(filename="...", title="Check confidentiality term",
         description="Verify the 3-year term is appropriate for this deal")

add_task(filename="...", title="Review termination rights",
         description="Ensure client has adequate termination rights")

add_task(filename="...", title="Flag unusual provisions",
         description="Identify any non-standard clauses that need attention")
```

### Step 2: Work through each task

```
# Start the first task
start_task(filename="...", task_id="<id from add_task>")

# Do the actual review work
get_document_outline(filename="...")
get_clause_text_by_ordinal(filename="...", clause_number="8.1")

# Make changes or add comments
add_comment_for_paragraph(
    filename="...",
    paragraph_index=45,
    comment_text="For Client: This indemnity is one-sided. Consider negotiating mutual indemnification."
)

# Complete the task
complete_task(filename="...", task_id="...")

# Move to next task
start_task(filename="...", task_id="<next task id>")
```

### Step 3: Check progress

```
get_work_plan(filename="...")
```

This shows how many tasks are completed vs remaining.

---

## Important Notes

1. **One task at a time**: Only one task should be `in_progress` at once. Complete or block the current task before starting another.

2. **Tool calls are logged**: When you use document tools (search_and_replace, add_comment, etc.), they are automatically logged to `edits.jsonl`. The extension can link these logs to your active task.

3. **Plans are per-project**: The project is determined from the filename path. All documents in `EL_Projects/Acme/...` share the same plan.

4. **Plans persist**: Tasks and progress are saved to disk. If the conversation ends and resumes, you can call `get_work_plan` to see the current state.

5. **No explicit "create plan"**: Plans are created automatically when you add the first task or document. Just start adding tasks.

---

## Quick Reference

| Tool | Purpose |
|------|---------|
| `get_work_plan` | View current plan and progress |
| `add_task` | Create a new task |
| `update_task` | Modify task details |
| `delete_task` | Remove a task |
| `move_task` | Reorder tasks |
| `start_task` | Begin work (→ in_progress) |
| `complete_task` | Finish work (→ completed) |
| `block_task` | Mark as waiting (→ blocked) |
| `unblock_task` | Remove blocked status (→ pending) |
| `convert_to_note` | Convert to non-actionable note |
| `convert_to_task` | Convert note back to task |
| `add_plan_document` | Track a document |
| `remove_plan_document` | Untrack a document |
| `list_plan_documents` | List tracked documents |
