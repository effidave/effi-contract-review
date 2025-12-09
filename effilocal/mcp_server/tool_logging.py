"""
MCP Tool Call Logging

Step 5b: Python MCP Server-side logging

Provides automatic logging of MCP tool calls to edits.jsonl in the project directory.
This allows the VS Code extension to see what tools were called and associate
them with work plan tasks.

Features:
- Automatic project path derivation from document filename
- Thread-safe append-only logging to edits.jsonl
- Decorator for easy tool wrapping
- Compatible with both sync and async functions
"""

import json
import os
import re
import threading
import functools
import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Union
import hashlib


# Thread lock for safe concurrent writes
_write_lock = threading.Lock()


def generate_id() -> str:
    """Generate a unique 8-character hex ID."""
    import secrets
    return secrets.token_hex(4)


def get_project_path(filename: str) -> Optional[str]:
    """
    Derive project path from a document filename.
    
    Supports these path structures:
    - EL_Projects/<project>/drafts/current_drafts/<file>.docx
    - EL_Projects/<project>/analysis/<filename>/...
    - EL_Precedents/<project>/contracts/<file>.docx
    - EL_Precedents/<project>/analysis/...
    
    Args:
        filename: Path to the document
        
    Returns:
        Project path (e.g., "C:/Users/Test/EL_Projects/Acme") or None
    """
    if not filename:
        return None
    
    # Normalize path separators
    normalized = filename.replace("\\", "/")
    
    # Pattern 1: EL_Projects/<project>/...
    match = re.search(r"(.*?/EL_Projects/[^/]+)", normalized)
    if match:
        return match.group(1)
    
    # Pattern 2: EL_Precedents/<project>/...
    match = re.search(r"(.*?/EL_Precedents/[^/]+)", normalized)
    if match:
        return match.group(1)
    
    return None


def get_edits_log_path(project_path: str) -> str:
    """
    Get the path to edits.jsonl for a project.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        Full path to edits.jsonl
    """
    # Remove trailing slash if present
    project_path = project_path.rstrip("/\\")
    return os.path.join(project_path, "logs", "edits.jsonl")


class ToolCallLogger:
    """
    Logger for MCP tool calls.
    
    Writes tool call records to edits.jsonl in the project's logs directory.
    Thread-safe for concurrent writes.
    """
    
    def __init__(self, project_path: str):
        """
        Initialize logger for a project.
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = project_path
        self.logs_dir = os.path.join(project_path, "logs")
        self.edits_path = os.path.join(self.logs_dir, "edits.jsonl")
    
    def _ensure_directory(self) -> None:
        """Ensure the logs directory exists."""
        os.makedirs(self.logs_dir, exist_ok=True)
    
    def log(
        self,
        tool_name: str,
        request: Dict[str, Any],
        response: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Log a tool call.
        
        Args:
            tool_name: Name of the tool that was called
            request: Request parameters
            response: Response from the tool (string or dict)
            
        Returns:
            The logged entry
        """
        # Create entry
        entry = {
            "id": generate_id(),
            "taskId": None,  # Server doesn't know active task; extension associates later
            "toolName": tool_name,
            "request": request,
            "response": response if isinstance(response, dict) else {"result": response},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Thread-safe write
        with _write_lock:
            self._ensure_directory()
            with open(self.edits_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        
        return entry


def log_tool_call(
    tool_name: str,
    request: Dict[str, Any],
    response: Union[str, Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Convenience function to log a tool call.
    
    Derives project path from the 'filename' parameter in the request.
    
    Args:
        tool_name: Name of the tool
        request: Request parameters (should contain 'filename')
        response: Response from the tool
        
    Returns:
        The logged entry, or None if project path couldn't be derived
    """
    filename = request.get("filename")
    if not filename:
        return None
    
    project_path = get_project_path(filename)
    if not project_path:
        return None
    
    logger = ToolCallLogger(project_path)
    return logger.log(tool_name, request, response)


def with_logging(func: Callable) -> Callable:
    """
    Decorator to add logging to an MCP tool function.
    
    Works with both sync and async functions.
    Logs the tool name, request parameters, and response.
    If the function raises an exception, logs the error and re-raises.
    
    The function must have a 'filename' parameter for project path derivation.
    If project path can't be derived, the function executes without logging.
    
    Example:
        @with_logging
        def search_and_replace(filename: str, find_text: str, replace_text: str):
            # ... implementation
            return result
    """
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        # Get the filename from kwargs or first positional arg
        filename = kwargs.get("filename")
        if filename is None and args:
            filename = args[0]
        
        # Build request dict from kwargs
        request = dict(kwargs)
        if "filename" not in request and filename:
            request["filename"] = filename
        
        project_path = get_project_path(filename) if filename else None
        
        try:
            result = func(*args, **kwargs)
            
            # Log if we have a project path
            if project_path:
                logger = ToolCallLogger(project_path)
                logger.log(func.__name__, request, result)
            
            return result
            
        except Exception as e:
            # Log the error
            if project_path:
                logger = ToolCallLogger(project_path)
                logger.log(func.__name__, request, {"error": str(e)})
            raise
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Get the filename from kwargs or first positional arg
        filename = kwargs.get("filename")
        if filename is None and args:
            filename = args[0]
        
        # Build request dict from kwargs
        request = dict(kwargs)
        if "filename" not in request and filename:
            request["filename"] = filename
        
        project_path = get_project_path(filename) if filename else None
        
        try:
            result = await func(*args, **kwargs)
            
            # Log if we have a project path
            if project_path:
                logger = ToolCallLogger(project_path)
                logger.log(func.__name__, request, result)
            
            return result
            
        except Exception as e:
            # Log the error
            if project_path:
                logger = ToolCallLogger(project_path)
                logger.log(func.__name__, request, {"error": str(e)})
            raise
    
    # Return appropriate wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
