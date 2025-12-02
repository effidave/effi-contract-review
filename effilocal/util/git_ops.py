"""Git operations for hybrid commit workflow.

Provides functions for automated git commits when documents are saved,
with meaningful commit messages and version history retrieval.

Uses subprocess to call git directly (no gitpython dependency required).
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from effilocal.config.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "auto_commit",
    "generate_commit_message",
    "get_file_history",
    "restore_version",
    "is_git_repo",
    "get_repo_root",
    "CommitInfo",
]

LOGGER = get_logger(__name__)

# Commit message prefix for effi operations
EFFI_COMMIT_PREFIX = "[effi]"


@dataclass(frozen=True, slots=True)
class CommitInfo:
    """Information about a git commit."""

    hash: str
    short_hash: str
    author: str
    date: datetime
    message: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "hash": self.hash,
            "short_hash": self.short_hash,
            "author": self.author,
            "date": self.date.isoformat(),
            "message": self.message,
        }


def _run_git(
    *args: str,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a git command and return the result.

    Args:
        *args: Git command arguments (without 'git')
        cwd: Working directory for the command
        check: If True, raise on non-zero exit

    Returns:
        CompletedProcess with stdout/stderr

    Raises:
        subprocess.CalledProcessError: If check=True and command fails
    """
    cmd = ["git", *args]
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def is_git_repo(path: Path) -> bool:
    """Check if the given path is inside a git repository.

    Args:
        path: Path to check

    Returns:
        True if inside a git repository
    """
    try:
        result = _run_git("rev-parse", "--git-dir", cwd=path, check=False)
        return result.returncode == 0
    except Exception:
        return False


def get_repo_root(path: Path) -> Path | None:
    """Get the root directory of the git repository.

    Args:
        path: Path inside the repository

    Returns:
        Repository root path, or None if not in a repo
    """
    try:
        result = _run_git("rev-parse", "--show-toplevel", cwd=path, check=False)
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except Exception:
        pass
    return None


def has_changes(
    repo_path: Path,
    files: Sequence[Path] | None = None,
) -> bool:
    """Check if there are uncommitted changes.

    Args:
        repo_path: Path to repository root
        files: Optional list of specific files to check

    Returns:
        True if there are changes to commit
    """
    try:
        if files:
            # Check specific files
            for file_path in files:
                rel_path = file_path.relative_to(repo_path) if file_path.is_absolute() else file_path
                result = _run_git("status", "--porcelain", str(rel_path), cwd=repo_path, check=False)
                if result.stdout.strip():
                    return True
            return False
        else:
            # Check all files
            result = _run_git("status", "--porcelain", cwd=repo_path, check=False)
            return bool(result.stdout.strip())
    except Exception:
        return False


def auto_commit(
    repo_path: Path,
    message: str,
    files: Sequence[Path] | None = None,
    *,
    add_untracked: bool = True,
) -> str | None:
    """Stage specified files and commit if there are changes.

    Args:
        repo_path: Path to repository root
        message: Commit message
        files: List of files to stage. If None, stages all changes.
        add_untracked: If True, also add untracked files

    Returns:
        Commit hash if successful, None if nothing to commit

    Raises:
        subprocess.CalledProcessError: If git command fails
    """
    repo_path = Path(repo_path)

    if not is_git_repo(repo_path):
        LOGGER.warning("Not a git repository: %s", repo_path)
        return None

    # Stage files
    if files:
        for file_path in files:
            rel_path = file_path.relative_to(repo_path) if file_path.is_absolute() else file_path
            if file_path.exists():
                _run_git("add", str(rel_path), cwd=repo_path)
            else:
                # File might be deleted
                _run_git("add", "-u", str(rel_path), cwd=repo_path, check=False)
    else:
        if add_untracked:
            _run_git("add", "-A", cwd=repo_path)
        else:
            _run_git("add", "-u", cwd=repo_path)

    # Check if there are staged changes
    result = _run_git("diff", "--cached", "--quiet", cwd=repo_path, check=False)
    if result.returncode == 0:
        LOGGER.debug("No changes to commit")
        return None

    # Commit
    _run_git("commit", "-m", message, cwd=repo_path)

    # Get commit hash
    result = _run_git("rev-parse", "HEAD", cwd=repo_path)
    commit_hash = result.stdout.strip()

    LOGGER.info("Committed changes: %s", commit_hash[:8])
    return commit_hash


def generate_commit_message(
    action: str,
    details: dict | None = None,
) -> str:
    """Generate a formatted commit message.

    Format: [effi] <action>: <summary>

    Args:
        action: The action type (edit, analyze, checkpoint, save)
        details: Optional details to include in the message

    Returns:
        Formatted commit message
    """
    details = details or {}

    if action == "analyze":
        doc_name = details.get("document_name", "document")
        return f"{EFFI_COMMIT_PREFIX} analyze: {doc_name}"

    elif action == "edit":
        doc_name = details.get("document_name", "document")
        changes = details.get("changes", "")
        if changes:
            return f"{EFFI_COMMIT_PREFIX} edit: {doc_name} - {changes}"
        return f"{EFFI_COMMIT_PREFIX} edit: {doc_name}"

    elif action == "checkpoint":
        doc_name = details.get("document_name", "document")
        note = details.get("note", "")
        if note:
            return f"{EFFI_COMMIT_PREFIX} checkpoint: {doc_name} - {note}"
        return f"{EFFI_COMMIT_PREFIX} checkpoint: {doc_name}"

    elif action == "save":
        doc_name = details.get("document_name", "document")
        return f"{EFFI_COMMIT_PREFIX} save: {doc_name}"

    else:
        summary = details.get("summary", action)
        return f"{EFFI_COMMIT_PREFIX} {action}: {summary}"


def get_file_history(
    repo_path: Path,
    file_path: Path,
    *,
    max_commits: int = 50,
) -> list[CommitInfo]:
    """Get commit history for a specific file.

    Args:
        repo_path: Path to repository root
        file_path: Path to the file
        max_commits: Maximum number of commits to return

    Returns:
        List of CommitInfo objects, newest first
    """
    repo_path = Path(repo_path)
    file_path = Path(file_path)

    if not is_git_repo(repo_path):
        return []

    rel_path = file_path.relative_to(repo_path) if file_path.is_absolute() else file_path

    # Get log with format: hash|short_hash|author|date|message
    format_str = "%H|%h|%an|%aI|%s"
    result = _run_git(
        "log",
        f"--max-count={max_commits}",
        f"--format={format_str}",
        "--",
        str(rel_path),
        cwd=repo_path,
        check=False,
    )

    if result.returncode != 0:
        return []

    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 4)
        if len(parts) != 5:
            continue

        try:
            commit_date = datetime.fromisoformat(parts[3])
        except ValueError:
            commit_date = datetime.now()

        commits.append(
            CommitInfo(
                hash=parts[0],
                short_hash=parts[1],
                author=parts[2],
                date=commit_date,
                message=parts[4],
            )
        )

    return commits


def get_file_at_commit(
    repo_path: Path,
    file_path: Path,
    commit_hash: str,
) -> bytes | None:
    """Get the content of a file at a specific commit.

    Args:
        repo_path: Path to repository root
        file_path: Path to the file
        commit_hash: Git commit hash

    Returns:
        File content as bytes, or None if not found
    """
    repo_path = Path(repo_path)
    file_path = Path(file_path)

    rel_path = file_path.relative_to(repo_path) if file_path.is_absolute() else file_path

    try:
        result = subprocess.run(
            ["git", "show", f"{commit_hash}:{rel_path}"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None


def restore_version(
    repo_path: Path,
    file_path: Path,
    commit_hash: str,
    *,
    create_backup: bool = True,
) -> Path | None:
    """Restore a file to a previous version from git history.

    Args:
        repo_path: Path to repository root
        file_path: Path to the file to restore
        commit_hash: Git commit hash to restore from
        create_backup: If True, create a backup of current version

    Returns:
        Path to the restored file, or None if restore failed
    """
    repo_path = Path(repo_path)
    file_path = Path(file_path)

    content = get_file_at_commit(repo_path, file_path, commit_hash)
    if content is None:
        LOGGER.error("Could not retrieve file at commit: %s", commit_hash)
        return None

    # Create backup if requested and file exists
    if create_backup and file_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".backup_{timestamp}{file_path.suffix}")
        backup_path.write_bytes(file_path.read_bytes())
        LOGGER.info("Created backup: %s", backup_path)

    # Write restored content
    file_path.write_bytes(content)
    LOGGER.info("Restored %s to commit %s", file_path.name, commit_hash[:8])

    return file_path


def get_effi_commits(
    repo_path: Path,
    *,
    max_commits: int = 100,
) -> list[CommitInfo]:
    """Get all commits made by effi (with [effi] prefix).

    Args:
        repo_path: Path to repository root
        max_commits: Maximum number of commits to return

    Returns:
        List of effi-related CommitInfo objects, newest first
    """
    repo_path = Path(repo_path)

    if not is_git_repo(repo_path):
        return []

    format_str = "%H|%h|%an|%aI|%s"
    result = _run_git(
        "log",
        f"--max-count={max_commits}",
        f"--format={format_str}",
        f"--grep={EFFI_COMMIT_PREFIX}",
        cwd=repo_path,
        check=False,
    )

    if result.returncode != 0:
        return []

    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 4)
        if len(parts) != 5:
            continue

        try:
            commit_date = datetime.fromisoformat(parts[3])
        except ValueError:
            commit_date = datetime.now()

        commits.append(
            CommitInfo(
                hash=parts[0],
                short_hash=parts[1],
                author=parts[2],
                date=commit_date,
                message=parts[4],
            )
        )

    return commits
