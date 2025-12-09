"""Plan file storage.

Handles reading and writing plan.md (YAML frontmatter) and plan.meta.json files.
Matches the TypeScript PlanStorage class from extension/src/models/planStorage.ts.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

import yaml

from effilocal.mcp_server.plan.models import WorkPlan
from effilocal.mcp_server.tool_logging import get_project_path


def get_plan_dir(project_path: str) -> Path:
    """Get the plan directory for a project."""
    return Path(project_path) / "plans" / "current"


def get_plan_md_path(project_path: str) -> Path:
    """Get the path to plan.md for a project."""
    return get_plan_dir(project_path) / "plan.md"


def get_plan_meta_path(project_path: str) -> Path:
    """Get the path to plan.meta.json for a project."""
    return get_plan_dir(project_path) / "plan.meta.json"


def ensure_plan_directories(project_path: str) -> None:
    """Ensure plan directories exist."""
    plan_dir = get_plan_dir(project_path)
    plan_dir.mkdir(parents=True, exist_ok=True)


def load_plan(project_path: str) -> Optional[WorkPlan]:
    """
    Load a WorkPlan from disk.
    
    Tries plan.meta.json first (faster), falls back to plan.md (YAML frontmatter).
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        WorkPlan if found, None if no plan exists
    """
    # Try fast JSON first
    meta_path = get_plan_meta_path(project_path)
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return WorkPlan.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            pass  # Fall through to YAML
    
    # Try YAML frontmatter
    md_path = get_plan_md_path(project_path)
    if md_path.exists():
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            return _parse_plan_md(content)
        except Exception:
            pass
    
    return None


def load_plan_from_filename(filename: str) -> Optional[WorkPlan]:
    """
    Load a WorkPlan from disk, deriving project path from filename.
    
    Args:
        filename: Path to a document in the project
        
    Returns:
        WorkPlan if found, None if no plan exists or project can't be derived
    """
    project_path = get_project_path(filename)
    if not project_path:
        return None
    return load_plan(project_path)


def save_plan(project_path: str, plan: WorkPlan) -> None:
    """
    Save a WorkPlan to disk.
    
    Writes both plan.md (YAML frontmatter + markdown) and plan.meta.json (fast loading).
    
    Args:
        project_path: Path to the project directory
        plan: WorkPlan to save
    """
    ensure_plan_directories(project_path)
    
    # Write JSON (fast loading)
    meta_path = get_plan_meta_path(project_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(plan.to_dict(), f, indent=2)
    
    # Write YAML frontmatter + markdown
    md_path = get_plan_md_path(project_path)
    content = _generate_plan_md(plan)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)


def save_plan_from_filename(filename: str, plan: WorkPlan) -> bool:
    """
    Save a WorkPlan to disk, deriving project path from filename.
    
    Args:
        filename: Path to a document in the project
        plan: WorkPlan to save
        
    Returns:
        True if saved successfully, False if project can't be derived
    """
    project_path = get_project_path(filename)
    if not project_path:
        return False
    save_plan(project_path, plan)
    return True


def get_or_create_plan(project_path: str) -> WorkPlan:
    """
    Get existing plan or create a new empty one.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        Existing WorkPlan or new empty WorkPlan
    """
    plan = load_plan(project_path)
    if plan is None:
        plan = WorkPlan()
    return plan


def get_or_create_plan_from_filename(filename: str) -> tuple[Optional[WorkPlan], Optional[str]]:
    """
    Get existing plan or create a new empty one, deriving project path from filename.
    
    Args:
        filename: Path to a document in the project
        
    Returns:
        Tuple of (WorkPlan, project_path) or (None, None) if project can't be derived
    """
    project_path = get_project_path(filename)
    if not project_path:
        return None, None
    return get_or_create_plan(project_path), project_path


# =============================================================================
# YAML Frontmatter Parsing/Generation
# =============================================================================

def _parse_plan_md(content: str) -> Optional[WorkPlan]:
    """Parse plan.md YAML frontmatter into a WorkPlan."""
    # Extract YAML frontmatter
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None
    
    yaml_content = match.group(1)
    try:
        data = yaml.safe_load(yaml_content)
        if not data:
            return WorkPlan()
        return WorkPlan.from_dict(data)
    except yaml.YAMLError:
        return None


def _generate_plan_md(plan: WorkPlan) -> str:
    """Generate plan.md content with YAML frontmatter and markdown body."""
    # Generate YAML frontmatter
    data = plan.to_dict()
    yaml_content = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    # Generate markdown body
    body_lines = ["", "# Work Plan", ""]
    
    for task in sorted(plan.tasks, key=lambda t: t.ordinal):
        body_lines.append(f"## {task.ordinal + 1}. {task.title}")
        body_lines.append(f"**Status:** {task.status}")
        body_lines.append("")
        if task.description:
            body_lines.append(task.description)
            body_lines.append("")
    
    if not plan.tasks:
        body_lines.append("_No tasks yet._")
        body_lines.append("")
    
    body = "\n".join(body_lines)
    
    return f"---\n{yaml_content}---\n{body}"
