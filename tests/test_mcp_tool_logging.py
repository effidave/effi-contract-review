"""
Tests for MCP Tool Call Logging

Step 5b: Python MCP Server-side logging

Tests for:
- Tool call logging to edits.jsonl
- Log file creation and structure
- Project path derivation from filename
- Concurrent logging safety
- Log rotation/management
"""

import json
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

# Import the module we're testing (will create after tests)
from effilocal.mcp_server.tool_logging import (
    ToolCallLogger,
    get_project_path,
    log_tool_call,
    get_edits_log_path,
)


class TestProjectPathDerivation:
    """Test deriving project path from document filename."""
    
    def test_derives_project_from_drafts_path(self):
        """Standard path: EL_Projects/<project>/drafts/current_drafts/file.docx"""
        filename = "C:/Users/Test/EL_Projects/Acme/drafts/current_drafts/contract.docx"
        project_path = get_project_path(filename)
        assert project_path == "C:/Users/Test/EL_Projects/Acme"
    
    def test_derives_project_from_analysis_path(self):
        """Analysis path: EL_Projects/<project>/analysis/<filename>/blocks.jsonl"""
        filename = "C:/Users/Test/EL_Projects/Acme/analysis/contract/blocks.jsonl"
        project_path = get_project_path(filename)
        assert project_path == "C:/Users/Test/EL_Projects/Acme"
    
    def test_returns_none_for_unknown_path(self):
        """Unknown path structure returns None."""
        filename = "C:/Random/Path/document.docx"
        project_path = get_project_path(filename)
        assert project_path is None
    
    def test_handles_windows_backslashes(self):
        """Windows-style paths work correctly."""
        filename = "C:\\Users\\Test\\EL_Projects\\Acme\\drafts\\current_drafts\\contract.docx"
        project_path = get_project_path(filename)
        # Normalize to forward slashes for comparison
        assert project_path.replace("\\", "/") == "C:/Users/Test/EL_Projects/Acme"
    
    def test_handles_el_precedents(self):
        """EL_Precedents path structure."""
        filename = "C:/Users/Test/EL_Precedents/NDA/contracts/nda_template.docx"
        project_path = get_project_path(filename)
        assert project_path == "C:/Users/Test/EL_Precedents/NDA"


class TestEditsLogPath:
    """Test getting the edits.jsonl path for a project."""
    
    def test_returns_logs_edits_jsonl(self):
        """Returns <project>/logs/edits.jsonl path."""
        project_path = "C:/Users/Test/EL_Projects/Acme"
        log_path = get_edits_log_path(project_path)
        # Normalize for cross-platform comparison
        assert log_path.replace("\\", "/") == "C:/Users/Test/EL_Projects/Acme/logs/edits.jsonl"
    
    def test_handles_trailing_slash(self):
        """Handles project path with trailing slash."""
        project_path = "C:/Users/Test/EL_Projects/Acme/"
        log_path = get_edits_log_path(project_path)
        # Check the path ends correctly (platform-agnostic)
        assert log_path.endswith("edits.jsonl")
        assert "logs" in log_path


class TestToolCallLogger:
    """Test the ToolCallLogger class."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_creates_log_directory(self, temp_project):
        """Creates logs directory if it doesn't exist."""
        logger = ToolCallLogger(temp_project)
        logger.log("test_tool", {"arg": "value"}, "result")
        
        logs_dir = os.path.join(temp_project, "logs")
        assert os.path.exists(logs_dir)
    
    def test_creates_edits_jsonl(self, temp_project):
        """Creates edits.jsonl file."""
        logger = ToolCallLogger(temp_project)
        logger.log("test_tool", {"arg": "value"}, "result")
        
        edits_path = os.path.join(temp_project, "logs", "edits.jsonl")
        assert os.path.exists(edits_path)
    
    def test_logs_tool_name(self, temp_project):
        """Logged entry includes tool name."""
        logger = ToolCallLogger(temp_project)
        logger.log("search_and_replace", {}, "done")
        
        edits_path = os.path.join(temp_project, "logs", "edits.jsonl")
        with open(edits_path) as f:
            entry = json.loads(f.readline())
        
        assert entry["toolName"] == "search_and_replace"
    
    def test_logs_request_object(self, temp_project):
        """Logged entry includes request object."""
        logger = ToolCallLogger(temp_project)
        request = {"filename": "doc.docx", "find_text": "old", "replace_text": "new"}
        logger.log("search_and_replace", request, "done")
        
        edits_path = os.path.join(temp_project, "logs", "edits.jsonl")
        with open(edits_path) as f:
            entry = json.loads(f.readline())
        
        assert entry["request"] == request
    
    def test_logs_response_string(self, temp_project):
        """Logged entry includes string response as object."""
        logger = ToolCallLogger(temp_project)
        logger.log("tool", {}, "Success: 3 replacements made")
        
        edits_path = os.path.join(temp_project, "logs", "edits.jsonl")
        with open(edits_path) as f:
            entry = json.loads(f.readline())
        
        assert entry["response"] == {"result": "Success: 3 replacements made"}
    
    def test_logs_response_object(self, temp_project):
        """Logged entry includes object response directly."""
        logger = ToolCallLogger(temp_project)
        response = {"success": True, "count": 5}
        logger.log("tool", {}, response)
        
        edits_path = os.path.join(temp_project, "logs", "edits.jsonl")
        with open(edits_path) as f:
            entry = json.loads(f.readline())
        
        assert entry["response"] == response
    
    def test_includes_timestamp(self, temp_project):
        """Logged entry includes ISO timestamp."""
        logger = ToolCallLogger(temp_project)
        logger.log("tool", {}, "result")
        
        edits_path = os.path.join(temp_project, "logs", "edits.jsonl")
        with open(edits_path) as f:
            entry = json.loads(f.readline())
        
        assert "timestamp" in entry
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
    
    def test_includes_unique_id(self, temp_project):
        """Logged entry includes unique ID."""
        logger = ToolCallLogger(temp_project)
        logger.log("tool", {}, "result")
        
        edits_path = os.path.join(temp_project, "logs", "edits.jsonl")
        with open(edits_path) as f:
            entry = json.loads(f.readline())
        
        assert "id" in entry
        assert len(entry["id"]) >= 8  # At least 8 chars
    
    def test_appends_multiple_entries(self, temp_project):
        """Multiple log calls append to file."""
        logger = ToolCallLogger(temp_project)
        logger.log("tool1", {}, "r1")
        logger.log("tool2", {}, "r2")
        logger.log("tool3", {}, "r3")
        
        edits_path = os.path.join(temp_project, "logs", "edits.jsonl")
        with open(edits_path) as f:
            lines = f.readlines()
        
        assert len(lines) == 3
        assert json.loads(lines[0])["toolName"] == "tool1"
        assert json.loads(lines[1])["toolName"] == "tool2"
        assert json.loads(lines[2])["toolName"] == "tool3"
    
    def test_generates_unique_ids(self, temp_project):
        """Each entry has a unique ID."""
        logger = ToolCallLogger(temp_project)
        logger.log("tool", {}, "r1")
        logger.log("tool", {}, "r2")
        
        edits_path = os.path.join(temp_project, "logs", "edits.jsonl")
        with open(edits_path) as f:
            lines = f.readlines()
        
        id1 = json.loads(lines[0])["id"]
        id2 = json.loads(lines[1])["id"]
        assert id1 != id2


class TestLogToolCallFunction:
    """Test the convenience log_tool_call function."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory structure."""
        temp_dir = tempfile.mkdtemp()
        # Create EL_Projects structure
        project_dir = os.path.join(temp_dir, "EL_Projects", "TestProject")
        drafts_dir = os.path.join(project_dir, "drafts", "current_drafts")
        os.makedirs(drafts_dir)
        
        yield {
            "base": temp_dir,
            "project": project_dir,
            "drafts": drafts_dir
        }
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_logs_from_filename(self, temp_project):
        """Logs based on document filename."""
        doc_path = os.path.join(temp_project["drafts"], "contract.docx")
        
        # Create a dummy file
        with open(doc_path, "w") as f:
            f.write("dummy")
        
        log_tool_call(
            "search_and_replace",
            {"filename": doc_path, "find_text": "old"},
            "replaced"
        )
        
        edits_path = os.path.join(temp_project["project"], "logs", "edits.jsonl")
        assert os.path.exists(edits_path)
    
    def test_returns_none_for_unknown_path(self):
        """Returns None if project path can't be derived."""
        result = log_tool_call(
            "tool",
            {"filename": "/unknown/path/doc.docx"},
            "result"
        )
        assert result is None
    
    def test_returns_log_entry_on_success(self, temp_project):
        """Returns the logged entry on success."""
        doc_path = os.path.join(temp_project["drafts"], "contract.docx")
        with open(doc_path, "w") as f:
            f.write("dummy")
        
        result = log_tool_call(
            "my_tool",
            {"filename": doc_path},
            "done"
        )
        
        assert result is not None
        assert result["toolName"] == "my_tool"


class TestConcurrentLogging:
    """Test concurrent/parallel logging safety."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_handles_concurrent_writes(self, temp_project):
        """Multiple rapid writes don't corrupt file."""
        import threading
        
        logger = ToolCallLogger(temp_project)
        errors = []
        
        def write_entry(n):
            try:
                logger.log(f"tool_{n}", {"index": n}, f"result_{n}")
            except Exception as e:
                errors.append(e)
        
        # Spawn multiple threads
        threads = [threading.Thread(target=write_entry, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        
        # Verify all entries were written
        edits_path = os.path.join(temp_project, "logs", "edits.jsonl")
        with open(edits_path) as f:
            lines = f.readlines()
        
        assert len(lines) == 20
        
        # Verify each line is valid JSON
        for line in lines:
            json.loads(line)


class TestToolLoggingDecorator:
    """Test the logging decorator for MCP tools."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory structure."""
        temp_dir = tempfile.mkdtemp()
        project_dir = os.path.join(temp_dir, "EL_Projects", "TestProject")
        drafts_dir = os.path.join(project_dir, "drafts", "current_drafts")
        os.makedirs(drafts_dir)
        
        yield {
            "base": temp_dir,
            "project": project_dir,
            "drafts": drafts_dir
        }
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_decorator_logs_sync_function(self, temp_project):
        """Decorator logs sync function calls."""
        from effilocal.mcp_server.tool_logging import with_logging
        
        @with_logging
        def my_tool(filename: str, text: str):
            return f"Added: {text}"
        
        doc_path = os.path.join(temp_project["drafts"], "test.docx")
        with open(doc_path, "w") as f:
            f.write("dummy")
        
        result = my_tool(filename=doc_path, text="Hello")
        
        assert result == "Added: Hello"
        
        edits_path = os.path.join(temp_project["project"], "logs", "edits.jsonl")
        assert os.path.exists(edits_path)
        
        with open(edits_path) as f:
            entry = json.loads(f.readline())
        
        assert entry["toolName"] == "my_tool"
        assert entry["request"]["text"] == "Hello"
    
    @pytest.mark.asyncio
    async def test_decorator_logs_async_function(self, temp_project):
        """Decorator logs async function calls."""
        from effilocal.mcp_server.tool_logging import with_logging
        
        @with_logging
        async def my_async_tool(filename: str, value: int):
            return {"success": True, "value": value * 2}
        
        doc_path = os.path.join(temp_project["drafts"], "test.docx")
        with open(doc_path, "w") as f:
            f.write("dummy")
        
        result = await my_async_tool(filename=doc_path, value=21)
        
        assert result == {"success": True, "value": 42}
        
        edits_path = os.path.join(temp_project["project"], "logs", "edits.jsonl")
        with open(edits_path) as f:
            entry = json.loads(f.readline())
        
        assert entry["toolName"] == "my_async_tool"
        assert entry["response"] == {"success": True, "value": 42}
    
    def test_decorator_handles_errors(self, temp_project):
        """Decorator logs even when function raises."""
        from effilocal.mcp_server.tool_logging import with_logging
        
        @with_logging
        def failing_tool(filename: str):
            raise ValueError("Something went wrong")
        
        doc_path = os.path.join(temp_project["drafts"], "test.docx")
        with open(doc_path, "w") as f:
            f.write("dummy")
        
        with pytest.raises(ValueError):
            failing_tool(filename=doc_path)
        
        # Error should still be logged
        edits_path = os.path.join(temp_project["project"], "logs", "edits.jsonl")
        with open(edits_path) as f:
            entry = json.loads(f.readline())
        
        assert entry["toolName"] == "failing_tool"
        assert "error" in entry["response"]
        assert "Something went wrong" in entry["response"]["error"]
    
    def test_decorator_skips_logging_for_unknown_path(self):
        """Decorator doesn't fail for unknown paths, just skips logging."""
        from effilocal.mcp_server.tool_logging import with_logging
        
        @with_logging
        def tool_unknown_path(filename: str):
            return "done"
        
        result = tool_unknown_path(filename="/unknown/path/doc.docx")
        
        assert result == "done"  # Function still works
        # No log file created (no project path)


class TestNoTaskIdInServerLogging:
    """Verify that server-side logging doesn't require taskId."""
    
    @pytest.fixture
    def temp_project(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_taskId_is_null_by_default(self, temp_project):
        """taskId field is null since server doesn't know active task."""
        logger = ToolCallLogger(temp_project)
        logger.log("tool", {}, "result")
        
        edits_path = os.path.join(temp_project, "logs", "edits.jsonl")
        with open(edits_path) as f:
            entry = json.loads(f.readline())
        
        assert entry.get("taskId") is None
    
    def test_extension_can_associate_later(self, temp_project):
        """Entry has all info needed for extension to associate with task."""
        logger = ToolCallLogger(temp_project)
        logger.log("search_and_replace", {"filename": "doc.docx"}, "replaced 3")
        
        edits_path = os.path.join(temp_project, "logs", "edits.jsonl")
        with open(edits_path) as f:
            entry = json.loads(f.readline())
        
        # Extension can use these to match/associate
        assert "id" in entry
        assert "timestamp" in entry
        assert "toolName" in entry
        assert "request" in entry
        assert "response" in entry
