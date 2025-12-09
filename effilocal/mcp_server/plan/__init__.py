"""Plan management for MCP server.

Python equivalents of the TypeScript WorkPlan, WorkTask, LegalDocument classes.
Used by Plan MCP tools to create and manage work plans.
"""

from effilocal.mcp_server.plan.models import (
    WorkTask,
    WorkPlan,
    LegalDocument,
    TaskStatus,
    generate_id,
)
from effilocal.mcp_server.plan.storage import (
    load_plan,
    save_plan,
    get_plan_dir,
)

__all__ = [
    "WorkTask",
    "WorkPlan",
    "LegalDocument",
    "TaskStatus",
    "generate_id",
    "load_plan",
    "save_plan",
    "get_plan_dir",
]
