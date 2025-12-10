"""Work plan data models.

Python equivalents of the TypeScript WorkPlan, WorkTask, LegalDocument classes
from extension/src/models/workplan.ts.

These models are used by the Plan MCP tools to create and manage work plans.
They must be compatible with the TypeScript version for interop via plan.md
and plan.meta.json files.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal


# Type alias for task status
TaskStatus = Literal["pending", "in_progress", "completed", "blocked", "notes"]


def generate_id() -> str:
    """Generate a prefixed ID that won't be parsed as a number by YAML.
    
    Format: wt + 8-character hex = "wt1a2b3c4d"
    Matches TypeScript's generateId() in workplan.ts.
    """
    return "wt" + secrets.token_hex(4)


def normalize_path(path: str) -> str:
    """Normalize path for comparison (lowercase, forward slashes)."""
    return path.replace("\\", "/").lower()


@dataclass
class LegalDocument:
    """Represents a document that a WorkPlan relates to.
    
    Matches TypeScript LegalDocument class from workplan.ts.
    """
    filename: str
    id: str = field(default_factory=generate_id)
    display_name: str | None = None
    added_date: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        # Auto-derive display_name from filename if not provided
        if self.display_name is None:
            self.display_name = os.path.basename(self.filename)
    
    def matches_filename(self, filename: str) -> bool:
        """Check if this document matches a given filename (case-insensitive, path-normalized)."""
        return normalize_path(self.filename) == normalize_path(filename)
    
    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "id": self.id,
            "filename": self.filename,
            "displayName": self.display_name,
            "addedDate": self.added_date.isoformat() + "Z" if self.added_date.tzinfo is None else self.added_date.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> LegalDocument:
        """Deserialize from JSON dict."""
        added_date = data.get("addedDate")
        if added_date:
            # Handle both ISO formats
            if added_date.endswith("Z"):
                added_date = added_date[:-1]
            added_date = datetime.fromisoformat(added_date)
        else:
            added_date = datetime.now()
            
        return cls(
            id=data.get("id", generate_id()),
            filename=data["filename"],
            display_name=data.get("displayName"),
            added_date=added_date,
        )


@dataclass
class WorkTask:
    """Represents a single task in the work plan.
    
    Matches TypeScript WorkTask class from workplan.ts.
    """
    title: str
    description: str
    id: str = field(default_factory=generate_id)
    status: TaskStatus = "pending"
    ordinal: int = 0
    creation_date: datetime = field(default_factory=datetime.now)
    completion_date: datetime | None = None
    edit_ids: list[str] = field(default_factory=list)
    
    def start(self) -> None:
        """Start working on this task."""
        self.status = "in_progress"
    
    def complete(self) -> None:
        """Mark task as completed."""
        self.status = "completed"
        self.completion_date = datetime.now()
    
    def block(self) -> None:
        """Mark task as blocked."""
        self.status = "blocked"
    
    def reset(self) -> None:
        """Reset task to pending."""
        self.status = "pending"
        self.completion_date = None
    
    def convert_to_note(self) -> None:
        """Convert this task to a note."""
        self.status = "notes"
    
    def unblock(self) -> bool:
        """Unblock a blocked task (set to pending).
        
        Returns:
            True if task was unblocked, False if task was not blocked.
        """
        if self.status == "blocked":
            self.status = "pending"
            return True
        return False
    
    def is_open(self) -> bool:
        """Check if task is open (not completed and not a note)."""
        return self.status not in ("completed", "notes")
    
    def add_edit_id(self, edit_id: str) -> None:
        """Add an edit ID to this task."""
        if edit_id not in self.edit_ids:
            self.edit_ids.append(edit_id)
    
    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "ordinal": self.ordinal,
            "creationDate": self.creation_date.isoformat() + "Z" if self.creation_date.tzinfo is None else self.creation_date.isoformat(),
            "completionDate": (self.completion_date.isoformat() + "Z" if self.completion_date.tzinfo is None else self.completion_date.isoformat()) if self.completion_date else None,
            "editIds": list(self.edit_ids),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> WorkTask:
        """Deserialize from JSON dict."""
        creation_date = data.get("creationDate")
        if creation_date:
            if creation_date.endswith("Z"):
                creation_date = creation_date[:-1]
            creation_date = datetime.fromisoformat(creation_date)
        else:
            creation_date = datetime.now()
        
        completion_date = data.get("completionDate")
        if completion_date:
            if completion_date.endswith("Z"):
                completion_date = completion_date[:-1]
            completion_date = datetime.fromisoformat(completion_date)
        else:
            completion_date = None
            
        return cls(
            id=data.get("id", generate_id()),
            title=data["title"],
            description=data.get("description", ""),
            status=data.get("status", "pending"),
            ordinal=data.get("ordinal", 0),
            creation_date=creation_date,
            completion_date=completion_date,
            edit_ids=list(data.get("editIds", [])),
        )


@dataclass
class WorkPlan:
    """Container for tasks and documents.
    
    Matches TypeScript WorkPlan class from workplan.ts.
    """
    tasks: list[WorkTask] = field(default_factory=list)
    documents: list[LegalDocument] = field(default_factory=list)
    
    # =========================================================================
    # Task Management
    # =========================================================================
    
    def add_task_at_end(self, task: WorkTask) -> None:
        """Add a task at the end of the list."""
        task.ordinal = len(self.tasks)
        self.tasks.append(task)
    
    def add_task_at_start(self, task: WorkTask) -> None:
        """Add a task at the start of the list."""
        # Shift all existing tasks
        for t in self.tasks:
            t.ordinal += 1
        task.ordinal = 0
        self.tasks.insert(0, task)
    
    def add_task_at_ordinal(self, task: WorkTask, ordinal: int) -> None:
        """Add a task at a specific ordinal position (0-based)."""
        ordinal = max(0, min(ordinal, len(self.tasks)))
        
        # Shift tasks at or after this position
        for t in self.tasks:
            if t.ordinal >= ordinal:
                t.ordinal += 1
        
        task.ordinal = ordinal
        self.tasks.insert(ordinal, task)
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a task by ID. Returns True if found and removed."""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                removed_ordinal = task.ordinal
                self.tasks.pop(i)
                
                # Renumber remaining tasks
                for t in self.tasks:
                    if t.ordinal > removed_ordinal:
                        t.ordinal -= 1
                return True
        return False
    
    def get_task_by_id(self, task_id: str) -> WorkTask | None:
        """Get a task by its ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def move_task(self, task_id: str, new_ordinal: int) -> bool:
        """Move a task to a new ordinal position. Returns True if successful."""
        task = self.get_task_by_id(task_id)
        if not task:
            return False
        
        old_ordinal = task.ordinal
        new_ordinal = max(0, min(new_ordinal, len(self.tasks) - 1))
        
        if old_ordinal == new_ordinal:
            return True
        
        if old_ordinal < new_ordinal:
            # Moving down: shift tasks in between up
            for t in self.tasks:
                if old_ordinal < t.ordinal <= new_ordinal:
                    t.ordinal -= 1
        else:
            # Moving up: shift tasks in between down
            for t in self.tasks:
                if new_ordinal <= t.ordinal < old_ordinal:
                    t.ordinal += 1
        
        task.ordinal = new_ordinal
        
        # Re-sort tasks by ordinal
        self.tasks.sort(key=lambda t: t.ordinal)
        return True
    
    def get_active_task(self) -> WorkTask | None:
        """Get the first task with status 'in_progress'."""
        for task in self.tasks:
            if task.status == "in_progress":
                return task
        return None
    
    # =========================================================================
    # Document Management
    # =========================================================================
    
    def add_document(self, doc: LegalDocument) -> bool:
        """Add a document if not already present (by filename). Returns True if added."""
        if self.has_document(doc.filename):
            return False
        self.documents.append(doc)
        return True
    
    def remove_document(self, doc_id: str) -> bool:
        """Remove a document by ID. Returns True if found and removed."""
        for i, doc in enumerate(self.documents):
            if doc.id == doc_id:
                self.documents.pop(i)
                return True
        return False
    
    def get_document_by_id(self, doc_id: str) -> LegalDocument | None:
        """Get a document by its ID."""
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        return None
    
    def get_document_by_filename(self, filename: str) -> LegalDocument | None:
        """Get a document by its filename (case-insensitive, path-normalized)."""
        for doc in self.documents:
            if doc.matches_filename(filename):
                return doc
        return None
    
    def has_document(self, filename: str) -> bool:
        """Check if a document with this filename exists."""
        return self.get_document_by_filename(filename) is not None
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "tasks": [task.to_dict() for task in sorted(self.tasks, key=lambda t: t.ordinal)],
            "documents": [doc.to_dict() for doc in self.documents],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> WorkPlan:
        """Deserialize from JSON dict."""
        tasks = [WorkTask.from_dict(t) for t in data.get("tasks", [])]
        documents = [LegalDocument.from_dict(d) for d in data.get("documents", [])]
        return cls(tasks=tasks, documents=documents)
