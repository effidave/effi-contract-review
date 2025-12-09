"""Tests for Plan MCP tools.

Tests the Python plan models, storage, and MCP tools that allow
the LLM to create and manage work plans.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import pytest

from effilocal.mcp_server.plan.models import (
    WorkTask,
    WorkPlan,
    LegalDocument,
    generate_id,
    normalize_path,
)
from effilocal.mcp_server.plan.storage import (
    load_plan,
    save_plan,
    get_plan_dir,
    get_or_create_plan,
    _parse_plan_md,
    _generate_plan_md,
)
from effilocal.mcp_server.tools import plan_tools


# =============================================================================
# Model Tests
# =============================================================================

class TestGenerateId:
    """Tests for generate_id function."""
    
    def test_returns_8_char_hex(self):
        id = generate_id()
        assert len(id) == 8
        assert all(c in '0123456789abcdef' for c in id)
    
    def test_generates_unique_ids(self):
        ids = [generate_id() for _ in range(100)]
        assert len(set(ids)) == 100


class TestNormalizePath:
    """Tests for path normalization."""
    
    def test_normalizes_backslashes(self):
        assert normalize_path("C:\\Users\\Test\\file.docx") == "c:/users/test/file.docx"
    
    def test_lowercases_path(self):
        assert normalize_path("C:/Users/TEST/File.DOCX") == "c:/users/test/file.docx"


class TestLegalDocument:
    """Tests for LegalDocument class."""
    
    def test_creates_with_defaults(self):
        doc = LegalDocument(filename="C:/test/contract.docx")
        assert len(doc.id) == 8
        assert doc.filename == "C:/test/contract.docx"
        assert doc.display_name == "contract.docx"  # Auto-derived
        assert isinstance(doc.added_date, datetime)
    
    def test_creates_with_custom_values(self):
        date = datetime(2025, 1, 15, 10, 30)
        doc = LegalDocument(
            id="abc12345",
            filename="C:/test/contract.docx",
            display_name="NDA Draft",
            added_date=date,
        )
        assert doc.id == "abc12345"
        assert doc.display_name == "NDA Draft"
        assert doc.added_date == date
    
    def test_matches_filename_case_insensitive(self):
        doc = LegalDocument(filename="C:/Test/CONTRACT.docx")
        assert doc.matches_filename("c:/test/contract.docx")
        assert doc.matches_filename("C:\\Test\\CONTRACT.docx")
        assert not doc.matches_filename("C:/other/contract.docx")
    
    def test_to_dict(self):
        date = datetime(2025, 1, 15, 10, 30)
        doc = LegalDocument(
            id="abc12345",
            filename="C:/test/contract.docx",
            display_name="NDA",
            added_date=date,
        )
        data = doc.to_dict()
        assert data["id"] == "abc12345"
        assert data["filename"] == "C:/test/contract.docx"
        assert data["displayName"] == "NDA"
        assert data["addedDate"] == "2025-01-15T10:30:00Z"
    
    def test_from_dict(self):
        data = {
            "id": "abc12345",
            "filename": "C:/test/contract.docx",
            "displayName": "NDA",
            "addedDate": "2025-01-15T10:30:00Z",
        }
        doc = LegalDocument.from_dict(data)
        assert doc.id == "abc12345"
        assert doc.filename == "C:/test/contract.docx"
        assert doc.display_name == "NDA"
        assert doc.added_date == datetime(2025, 1, 15, 10, 30)


class TestWorkTask:
    """Tests for WorkTask class."""
    
    def test_creates_with_defaults(self):
        task = WorkTask(title="Review clause", description="Check the indemnity")
        assert len(task.id) == 8
        assert task.title == "Review clause"
        assert task.description == "Check the indemnity"
        assert task.status == "pending"
        assert task.ordinal == 0
        assert isinstance(task.creation_date, datetime)
        assert task.completion_date is None
        assert task.edit_ids == []
    
    def test_status_transitions(self):
        task = WorkTask(title="Test", description="")
        
        assert task.status == "pending"
        
        task.start()
        assert task.status == "in_progress"
        
        task.block()
        assert task.status == "blocked"
        
        task.complete()
        assert task.status == "completed"
        assert task.completion_date is not None
        
        task.reset()
        assert task.status == "pending"
        assert task.completion_date is None
    
    def test_is_open(self):
        task = WorkTask(title="Test", description="")
        
        assert task.is_open() == True
        task.complete()
        assert task.is_open() == False
    
    def test_add_edit_id(self):
        task = WorkTask(title="Test", description="")
        
        task.add_edit_id("edit1")
        assert task.edit_ids == ["edit1"]
        
        task.add_edit_id("edit2")
        assert task.edit_ids == ["edit1", "edit2"]
        
        # No duplicates
        task.add_edit_id("edit1")
        assert task.edit_ids == ["edit1", "edit2"]
    
    def test_to_dict(self):
        task = WorkTask(
            id="task1234",
            title="Review",
            description="Check clause",
            status="in_progress",
            ordinal=2,
        )
        data = task.to_dict()
        assert data["id"] == "task1234"
        assert data["title"] == "Review"
        assert data["description"] == "Check clause"
        assert data["status"] == "in_progress"
        assert data["ordinal"] == 2
        assert data["completionDate"] is None
        assert data["editIds"] == []
    
    def test_from_dict(self):
        data = {
            "id": "task1234",
            "title": "Review",
            "description": "Check clause",
            "status": "completed",
            "ordinal": 1,
            "creationDate": "2025-01-15T10:30:00Z",
            "completionDate": "2025-01-15T14:00:00Z",
            "editIds": ["e1", "e2"],
        }
        task = WorkTask.from_dict(data)
        assert task.id == "task1234"
        assert task.title == "Review"
        assert task.status == "completed"
        assert task.completion_date == datetime(2025, 1, 15, 14, 0)
        assert task.edit_ids == ["e1", "e2"]


class TestWorkPlan:
    """Tests for WorkPlan class."""
    
    def test_creates_empty(self):
        plan = WorkPlan()
        assert plan.tasks == []
        assert plan.documents == []
    
    def test_add_task_at_end(self):
        plan = WorkPlan()
        t1 = WorkTask(title="First", description="")
        t2 = WorkTask(title="Second", description="")
        
        plan.add_task_at_end(t1)
        plan.add_task_at_end(t2)
        
        assert len(plan.tasks) == 2
        assert plan.tasks[0].ordinal == 0
        assert plan.tasks[1].ordinal == 1
    
    def test_add_task_at_start(self):
        plan = WorkPlan()
        t1 = WorkTask(title="First", description="")
        t2 = WorkTask(title="Second", description="")
        
        plan.add_task_at_end(t1)
        plan.add_task_at_start(t2)
        
        assert plan.tasks[0].title == "Second"
        assert plan.tasks[0].ordinal == 0
        assert plan.tasks[1].title == "First"
        assert plan.tasks[1].ordinal == 1
    
    def test_add_task_at_ordinal(self):
        plan = WorkPlan()
        t1 = WorkTask(title="First", description="")
        t2 = WorkTask(title="Second", description="")
        t3 = WorkTask(title="Middle", description="")
        
        plan.add_task_at_end(t1)
        plan.add_task_at_end(t2)
        plan.add_task_at_ordinal(t3, 1)
        
        ordinals = [(t.title, t.ordinal) for t in sorted(plan.tasks, key=lambda x: x.ordinal)]
        assert ordinals == [("First", 0), ("Middle", 1), ("Second", 2)]
    
    def test_remove_task(self):
        plan = WorkPlan()
        t1 = WorkTask(id="t1", title="First", description="")
        t2 = WorkTask(id="t2", title="Second", description="")
        t3 = WorkTask(id="t3", title="Third", description="")
        
        plan.add_task_at_end(t1)
        plan.add_task_at_end(t2)
        plan.add_task_at_end(t3)
        
        assert plan.remove_task("t2") == True
        assert len(plan.tasks) == 2
        
        # Check ordinals were adjusted
        ordinals = [(t.id, t.ordinal) for t in sorted(plan.tasks, key=lambda x: x.ordinal)]
        assert ordinals == [("t1", 0), ("t3", 1)]
    
    def test_get_task_by_id(self):
        plan = WorkPlan()
        task = WorkTask(id="abc123", title="Test", description="")
        plan.add_task_at_end(task)
        
        assert plan.get_task_by_id("abc123") is task
        assert plan.get_task_by_id("nonexistent") is None
    
    def test_move_task(self):
        plan = WorkPlan()
        t1 = WorkTask(id="t1", title="First", description="")
        t2 = WorkTask(id="t2", title="Second", description="")
        t3 = WorkTask(id="t3", title="Third", description="")
        
        plan.add_task_at_end(t1)
        plan.add_task_at_end(t2)
        plan.add_task_at_end(t3)
        
        # Move t1 to position 2
        assert plan.move_task("t1", 2) == True
        
        ordinals = [(t.id, t.ordinal) for t in plan.tasks]
        assert ordinals == [("t2", 0), ("t3", 1), ("t1", 2)]
    
    def test_get_active_task(self):
        plan = WorkPlan()
        t1 = WorkTask(title="First", description="", status="pending")
        t2 = WorkTask(title="Second", description="", status="in_progress")
        t3 = WorkTask(title="Third", description="", status="pending")
        
        plan.add_task_at_end(t1)
        plan.add_task_at_end(t2)
        plan.add_task_at_end(t3)
        
        active = plan.get_active_task()
        assert active is t2
    
    def test_get_active_task_none(self):
        plan = WorkPlan()
        t1 = WorkTask(title="First", description="", status="pending")
        plan.add_task_at_end(t1)
        
        assert plan.get_active_task() is None
    
    def test_document_management(self):
        plan = WorkPlan()
        doc = LegalDocument(id="d1", filename="C:/test/contract.docx")
        
        assert plan.add_document(doc) == True
        assert plan.has_document("C:/test/contract.docx") == True
        assert plan.has_document("c:/test/CONTRACT.docx") == True
        
        # No duplicate
        doc2 = LegalDocument(filename="C:/test/contract.docx")
        assert plan.add_document(doc2) == False
        assert len(plan.documents) == 1
        
        assert plan.remove_document("d1") == True
        assert len(plan.documents) == 0
    
    def test_to_dict_and_from_dict(self):
        plan = WorkPlan()
        task = WorkTask(id="t1", title="Test", description="Desc", status="pending")
        doc = LegalDocument(id="d1", filename="C:/test.docx")
        
        plan.add_task_at_end(task)
        plan.add_document(doc)
        
        data = plan.to_dict()
        assert len(data["tasks"]) == 1
        assert len(data["documents"]) == 1
        
        restored = WorkPlan.from_dict(data)
        assert len(restored.tasks) == 1
        assert restored.tasks[0].id == "t1"
        assert len(restored.documents) == 1
        assert restored.documents[0].id == "d1"


# =============================================================================
# Storage Tests
# =============================================================================

class TestPlanStorage:
    """Tests for plan file storage."""
    
    def test_get_plan_dir(self):
        project = "C:/Users/Test/EL_Projects/Acme"
        result = get_plan_dir(project)
        # Check the path ends with plans/current (platform-agnostic)
        assert result.parts[-2:] == ("plans", "current")
    
    def test_save_and_load_plan(self, tmp_path):
        # Create a fake project structure
        project_path = tmp_path / "EL_Projects" / "TestProject"
        project_path.mkdir(parents=True)
        
        # Create and save a plan
        plan = WorkPlan()
        task = WorkTask(id="t1", title="Review", description="Check clause")
        doc = LegalDocument(id="d1", filename="contract.docx")
        plan.add_task_at_end(task)
        plan.add_document(doc)
        
        save_plan(str(project_path), plan)
        
        # Verify files were created
        assert (project_path / "plans" / "current" / "plan.md").exists()
        assert (project_path / "plans" / "current" / "plan.meta.json").exists()
        
        # Load and verify
        loaded = load_plan(str(project_path))
        assert loaded is not None
        assert len(loaded.tasks) == 1
        assert loaded.tasks[0].id == "t1"
        assert loaded.tasks[0].title == "Review"
        assert len(loaded.documents) == 1
    
    def test_load_nonexistent_plan(self, tmp_path):
        assert load_plan(str(tmp_path)) is None
    
    def test_get_or_create_plan(self, tmp_path):
        project_path = tmp_path / "EL_Projects" / "TestProject"
        project_path.mkdir(parents=True)
        
        # First call creates empty plan
        plan = get_or_create_plan(str(project_path))
        assert plan is not None
        assert len(plan.tasks) == 0
        
        # Add a task and save
        task = WorkTask(title="Test", description="")
        plan.add_task_at_end(task)
        save_plan(str(project_path), plan)
        
        # Second call loads existing plan
        plan2 = get_or_create_plan(str(project_path))
        assert len(plan2.tasks) == 1


class TestYAMLParsing:
    """Tests for YAML frontmatter parsing/generation."""
    
    def test_parse_plan_md(self):
        content = """---
tasks:
  - id: t1
    title: Review clause
    description: Check indemnity
    status: pending
    ordinal: 0
    creationDate: '2025-01-15T10:30:00Z'
    completionDate: null
    editIds: []
documents: []
---

# Work Plan

## 1. Review clause
**Status:** pending

Check indemnity
"""
        plan = _parse_plan_md(content)
        assert plan is not None
        assert len(plan.tasks) == 1
        assert plan.tasks[0].id == "t1"
        assert plan.tasks[0].title == "Review clause"
    
    def test_generate_plan_md(self):
        plan = WorkPlan()
        task = WorkTask(id="t1", title="Test Task", description="Description here")
        plan.add_task_at_end(task)
        
        content = _generate_plan_md(plan)
        
        assert "---" in content
        assert "Test Task" in content
        assert "Description here" in content
        assert "# Work Plan" in content


# =============================================================================
# Tool Tests
# =============================================================================

@pytest.fixture
def project_dir(tmp_path):
    """Create a fake project directory structure."""
    project = tmp_path / "EL_Projects" / "TestProject"
    drafts = project / "drafts" / "current_drafts"
    drafts.mkdir(parents=True)
    
    # Create a dummy document
    doc_path = drafts / "contract.docx"
    doc_path.write_bytes(b"dummy")
    
    return project, str(doc_path)


class TestPlanTools:
    """Tests for Plan MCP tools."""
    
    @pytest.mark.asyncio
    async def test_get_work_plan_empty(self, project_dir):
        project, filename = project_dir
        
        result = await plan_tools.get_work_plan(filename)
        data = json.loads(result)
        
        assert data["summary"]["taskCount"] == 0
        assert data["summary"]["documentCount"] == 0
        assert data["plan"]["tasks"] == []
    
    @pytest.mark.asyncio
    async def test_add_task(self, project_dir):
        project, filename = project_dir
        
        result = await plan_tools.add_task(
            filename, "Review indemnity", "Check for mutual obligations"
        )
        
        assert "Task added" in result
        assert "Review indemnity" in result
        
        # Verify plan was saved
        plan = load_plan(str(project))
        assert len(plan.tasks) == 1
        assert plan.tasks[0].title == "Review indemnity"
    
    @pytest.mark.asyncio
    async def test_add_task_at_start(self, project_dir):
        project, filename = project_dir
        
        await plan_tools.add_task(filename, "First", "")
        await plan_tools.add_task(filename, "Second", "", position="start")
        
        plan = load_plan(str(project))
        titles = [t.title for t in sorted(plan.tasks, key=lambda x: x.ordinal)]
        assert titles == ["Second", "First"]
    
    @pytest.mark.asyncio
    async def test_update_task(self, project_dir):
        project, filename = project_dir
        
        # Add a task
        result = await plan_tools.add_task(filename, "Original", "Original desc")
        task_id = result.split("id: ")[1].split(",")[0]
        
        # Update it
        result = await plan_tools.update_task(
            filename, task_id, 
            title="Updated", 
            status="in_progress"
        )
        
        assert "updated" in result
        
        plan = load_plan(str(project))
        task = plan.get_task_by_id(task_id)
        assert task.title == "Updated"
        assert task.status == "in_progress"
    
    @pytest.mark.asyncio
    async def test_delete_task(self, project_dir):
        project, filename = project_dir
        
        # Add and delete
        result = await plan_tools.add_task(filename, "To Delete", "")
        task_id = result.split("id: ")[1].split(",")[0]
        
        result = await plan_tools.delete_task(filename, task_id)
        assert "deleted" in result
        
        plan = load_plan(str(project))
        assert len(plan.tasks) == 0
    
    @pytest.mark.asyncio
    async def test_start_and_complete_task(self, project_dir):
        project, filename = project_dir
        
        # Add a task
        result = await plan_tools.add_task(filename, "Test", "")
        task_id = result.split("id: ")[1].split(",")[0]
        
        # Start it
        result = await plan_tools.start_task(filename, task_id)
        assert "in_progress" in result
        
        plan = load_plan(str(project))
        assert plan.get_task_by_id(task_id).status == "in_progress"
        
        # Complete it
        result = await plan_tools.complete_task(filename, task_id)
        assert "completed" in result
        
        plan = load_plan(str(project))
        task = plan.get_task_by_id(task_id)
        assert task.status == "completed"
        assert task.completion_date is not None
    
    @pytest.mark.asyncio
    async def test_move_task(self, project_dir):
        project, filename = project_dir
        
        # Add three tasks
        r1 = await plan_tools.add_task(filename, "First", "")
        r2 = await plan_tools.add_task(filename, "Second", "")
        r3 = await plan_tools.add_task(filename, "Third", "")
        
        task_id = r1.split("id: ")[1].split(",")[0]
        
        # Move first to last
        result = await plan_tools.move_task(filename, task_id, 2)
        assert "moved" in result
        
        plan = load_plan(str(project))
        titles = [t.title for t in sorted(plan.tasks, key=lambda x: x.ordinal)]
        assert titles == ["Second", "Third", "First"]
    
    @pytest.mark.asyncio
    async def test_add_plan_document(self, project_dir):
        project, filename = project_dir
        
        result = await plan_tools.add_plan_document(filename, "Contract Draft")
        assert "Document added" in result
        assert "Contract Draft" in result
        
        plan = load_plan(str(project))
        assert len(plan.documents) == 1
        assert plan.documents[0].display_name == "Contract Draft"
    
    @pytest.mark.asyncio
    async def test_add_plan_document_no_duplicate(self, project_dir):
        project, filename = project_dir
        
        await plan_tools.add_plan_document(filename)
        result = await plan_tools.add_plan_document(filename)
        
        assert "already tracked" in result
    
    @pytest.mark.asyncio
    async def test_remove_plan_document(self, project_dir):
        project, filename = project_dir
        
        result = await plan_tools.add_plan_document(filename)
        doc_id = result.split("id: ")[1].rstrip(")")
        
        result = await plan_tools.remove_plan_document(filename, doc_id)
        assert "removed" in result
        
        plan = load_plan(str(project))
        assert len(plan.documents) == 0
    
    @pytest.mark.asyncio
    async def test_list_plan_documents(self, project_dir):
        project, filename = project_dir
        
        await plan_tools.add_plan_document(filename, "Doc 1")
        
        result = await plan_tools.list_plan_documents(filename)
        data = json.loads(result)
        
        assert len(data) == 1
        assert data[0]["displayName"] == "Doc 1"
    
    @pytest.mark.asyncio
    async def test_invalid_project_path(self, tmp_path):
        # File not in a recognized project structure
        invalid_file = tmp_path / "random" / "file.docx"
        invalid_file.parent.mkdir(parents=True)
        invalid_file.write_bytes(b"dummy")
        
        result = await plan_tools.get_work_plan(str(invalid_file))
        assert "Error" in result
        assert "Cannot determine project path" in result
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_task(self, project_dir):
        project, filename = project_dir
        
        result = await plan_tools.update_task(filename, "nonexistent", title="New")
        assert "Error" in result
        assert "not found" in result
