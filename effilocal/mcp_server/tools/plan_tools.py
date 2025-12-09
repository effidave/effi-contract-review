"""Plan MCP tools.

MCP tools for creating and managing WorkPlans. These allow the LLM to:
- View the current work plan
- Add, update, and delete tasks
- Change task status (start, complete, block)
- Track which documents the plan relates to
"""

from __future__ import annotations

import json
from typing import Optional

from effilocal.mcp_server.plan.models import (
    WorkPlan,
    WorkTask,
    LegalDocument,
    TaskStatus,
)
from effilocal.mcp_server.plan.storage import (
    get_or_create_plan_from_filename,
    save_plan_from_filename,
    load_plan_from_filename,
    get_project_path,
)


async def get_work_plan(filename: str) -> str:
    """
    Get the current work plan for a project.
    
    Args:
        filename: Path to any document in the project (used to derive project path)
        
    Returns:
        JSON representation of the work plan, or error message
    """
    plan, project_path = get_or_create_plan_from_filename(filename)
    if plan is None:
        return f"Error: Cannot determine project path from '{filename}'. Expected path like EL_Projects/<project>/..."
    
    data = plan.to_dict()
    
    # Add summary info
    task_count = len(plan.tasks)
    completed = sum(1 for t in plan.tasks if t.status == "completed")
    in_progress = sum(1 for t in plan.tasks if t.status == "in_progress")
    pending = sum(1 for t in plan.tasks if t.status == "pending")
    blocked = sum(1 for t in plan.tasks if t.status == "blocked")
    
    summary = {
        "projectPath": project_path,
        "taskCount": task_count,
        "completed": completed,
        "inProgress": in_progress,
        "pending": pending,
        "blocked": blocked,
        "documentCount": len(plan.documents),
    }
    
    result = {
        "summary": summary,
        "plan": data,
    }
    
    return json.dumps(result, indent=2)


async def add_task(
    filename: str,
    title: str,
    description: str,
    position: str = "end",
    ordinal: Optional[int] = None,
) -> str:
    """
    Add a new task to the work plan.
    
    Args:
        filename: Path to any document in the project (used to derive project path)
        title: Short title for the task
        description: Detailed description of what needs to be done
        position: Where to add the task: "start", "end" (default), or "at" (requires ordinal)
        ordinal: 0-based position when position="at"
        
    Returns:
        Success message with task ID, or error message
    """
    plan, project_path = get_or_create_plan_from_filename(filename)
    if plan is None:
        return f"Error: Cannot determine project path from '{filename}'"
    
    task = WorkTask(title=title, description=description)
    
    if position == "start":
        plan.add_task_at_start(task)
    elif position == "at" and ordinal is not None:
        plan.add_task_at_ordinal(task, ordinal)
    else:
        plan.add_task_at_end(task)
    
    if not save_plan_from_filename(filename, plan):
        return "Error: Failed to save plan"
    
    return f"Task added: '{title}' (id: {task.id}, ordinal: {task.ordinal})"


async def update_task(
    filename: str,
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
) -> str:
    """
    Update an existing task's properties.
    
    Args:
        filename: Path to any document in the project
        task_id: ID of the task to update
        title: New title (optional)
        description: New description (optional)
        status: New status: "pending", "in_progress", "completed", "blocked" (optional)
        
    Returns:
        Success message or error message
    """
    plan, project_path = get_or_create_plan_from_filename(filename)
    if plan is None:
        return f"Error: Cannot determine project path from '{filename}'"
    
    task = plan.get_task_by_id(task_id)
    if task is None:
        return f"Error: Task '{task_id}' not found"
    
    changes = []
    
    if title is not None:
        task.title = title
        changes.append(f"title='{title}'")
    
    if description is not None:
        task.description = description
        changes.append("description updated")
    
    if status is not None:
        if status not in ("pending", "in_progress", "completed", "blocked"):
            return f"Error: Invalid status '{status}'. Must be pending, in_progress, completed, or blocked"
        task.status = status
        changes.append(f"status={status}")
        
        # Set completion date if completed
        if status == "completed":
            from datetime import datetime
            task.completion_date = datetime.now()
        elif status != "completed" and task.completion_date is not None:
            task.completion_date = None
    
    if not changes:
        return "No changes specified"
    
    if not save_plan_from_filename(filename, plan):
        return "Error: Failed to save plan"
    
    return f"Task '{task_id}' updated: {', '.join(changes)}"


async def delete_task(filename: str, task_id: str) -> str:
    """
    Delete a task from the work plan.
    
    Args:
        filename: Path to any document in the project
        task_id: ID of the task to delete
        
    Returns:
        Success message or error message
    """
    plan, project_path = get_or_create_plan_from_filename(filename)
    if plan is None:
        return f"Error: Cannot determine project path from '{filename}'"
    
    task = plan.get_task_by_id(task_id)
    if task is None:
        return f"Error: Task '{task_id}' not found"
    
    title = task.title
    if not plan.remove_task(task_id):
        return f"Error: Failed to remove task '{task_id}'"
    
    if not save_plan_from_filename(filename, plan):
        return "Error: Failed to save plan"
    
    return f"Task deleted: '{title}' (id: {task_id})"


async def move_task(filename: str, task_id: str, new_ordinal: int) -> str:
    """
    Move a task to a new position in the list.
    
    Args:
        filename: Path to any document in the project
        task_id: ID of the task to move
        new_ordinal: New 0-based position
        
    Returns:
        Success message or error message
    """
    plan, project_path = get_or_create_plan_from_filename(filename)
    if plan is None:
        return f"Error: Cannot determine project path from '{filename}'"
    
    task = plan.get_task_by_id(task_id)
    if task is None:
        return f"Error: Task '{task_id}' not found"
    
    old_ordinal = task.ordinal
    if not plan.move_task(task_id, new_ordinal):
        return f"Error: Failed to move task '{task_id}'"
    
    if not save_plan_from_filename(filename, plan):
        return "Error: Failed to save plan"
    
    return f"Task '{task.title}' moved from position {old_ordinal} to {new_ordinal}"


async def start_task(filename: str, task_id: str) -> str:
    """
    Start working on a task (set status to in_progress).
    
    Args:
        filename: Path to any document in the project
        task_id: ID of the task to start
        
    Returns:
        Success message or error message
    """
    return await update_task(filename, task_id, status="in_progress")


async def complete_task(filename: str, task_id: str) -> str:
    """
    Mark a task as completed.
    
    Args:
        filename: Path to any document in the project
        task_id: ID of the task to complete
        
    Returns:
        Success message or error message
    """
    return await update_task(filename, task_id, status="completed")


async def block_task(filename: str, task_id: str) -> str:
    """
    Mark a task as blocked.
    
    Args:
        filename: Path to any document in the project
        task_id: ID of the task to block
        
    Returns:
        Success message or error message
    """
    return await update_task(filename, task_id, status="blocked")


async def add_plan_document(filename: str, display_name: Optional[str] = None) -> str:
    """
    Add a document to the work plan's document list.
    
    This tracks which documents the plan relates to. When the filename is a document
    being worked on, this adds it to the plan's tracked documents.
    
    Args:
        filename: Path to the document to add
        display_name: Optional friendly name (defaults to filename)
        
    Returns:
        Success message with document ID, or error message
    """
    plan, project_path = get_or_create_plan_from_filename(filename)
    if plan is None:
        return f"Error: Cannot determine project path from '{filename}'"
    
    # Check if already tracked
    if plan.has_document(filename):
        existing = plan.get_document_by_filename(filename)
        return f"Document already tracked: '{existing.display_name}' (id: {existing.id})"
    
    doc = LegalDocument(filename=filename, display_name=display_name)
    plan.add_document(doc)
    
    if not save_plan_from_filename(filename, plan):
        return "Error: Failed to save plan"
    
    return f"Document added: '{doc.display_name}' (id: {doc.id})"


async def remove_plan_document(filename: str, document_id: str) -> str:
    """
    Remove a document from the work plan's document list.
    
    Args:
        filename: Path to any document in the project (for project path derivation)
        document_id: ID of the document to remove
        
    Returns:
        Success message or error message
    """
    plan, project_path = get_or_create_plan_from_filename(filename)
    if plan is None:
        return f"Error: Cannot determine project path from '{filename}'"
    
    doc = plan.get_document_by_id(document_id)
    if doc is None:
        return f"Error: Document '{document_id}' not found"
    
    display_name = doc.display_name
    if not plan.remove_document(document_id):
        return f"Error: Failed to remove document '{document_id}'"
    
    if not save_plan_from_filename(filename, plan):
        return "Error: Failed to save plan"
    
    return f"Document removed: '{display_name}' (id: {document_id})"


async def list_plan_documents(filename: str) -> str:
    """
    List all documents tracked by the work plan.
    
    Args:
        filename: Path to any document in the project
        
    Returns:
        JSON array of documents, or error message
    """
    plan, project_path = get_or_create_plan_from_filename(filename)
    if plan is None:
        return f"Error: Cannot determine project path from '{filename}'"
    
    docs = [doc.to_dict() for doc in plan.documents]
    return json.dumps(docs, indent=2)
