"""Document save flow with UUID embedding and git integration.

This module handles saving documents back to .docx format while:
1. Embedding block UUIDs as content controls
2. Auto-committing changes to git with meaningful messages
3. Preserving document formatting and structure
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from docx import Document

from effilocal.config.logging import get_logger
from effilocal.doc.uuid_embedding import embed_block_uuids, extract_block_uuids
from effilocal.util.git_ops import auto_commit, generate_commit_message, get_repo_root

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "save_with_uuids",
    "embed_uuids_in_document",
    "SaveResult",
]

LOGGER = get_logger(__name__)


class SaveResult:
    """Result of a save operation."""

    def __init__(
        self,
        *,
        success: bool,
        docx_path: Path | None = None,
        embedded_count: int = 0,
        commit_hash: str | None = None,
        error: str | None = None,
    ):
        self.success = success
        self.docx_path = docx_path
        self.embedded_count = embedded_count
        self.commit_hash = commit_hash
        self.error = error

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "docx_path": str(self.docx_path) if self.docx_path else None,
            "embedded_count": self.embedded_count,
            "commit_hash": self.commit_hash,
            "error": self.error,
        }


def embed_uuids_in_document(
    docx_path: Path,
    blocks: list[dict],
    *,
    save: bool = True,
    overwrite: bool = False,
) -> int:
    """Embed UUIDs from blocks into a document.

    Args:
        docx_path: Path to the .docx file
        blocks: List of block dicts with "id" and "para_idx" fields
        save: If True, save the document after embedding
        overwrite: If True, overwrite existing UUIDs

    Returns:
        Number of blocks successfully embedded
    """
    docx_path = Path(docx_path)

    if not docx_path.exists():
        LOGGER.error("Document not found: %s", docx_path)
        return 0

    document = Document(str(docx_path))
    embedded = embed_block_uuids(document, blocks, overwrite=overwrite)

    if save:
        document.save(str(docx_path))
        LOGGER.info("Saved document with %d embedded UUIDs: %s", len(embedded), docx_path)

    return len(embedded)


def save_with_uuids(
    docx_path: Path,
    blocks_path: Path | None = None,
    *,
    analysis_dir: Path | None = None,
    auto_git: bool = True,
    commit_message: str | None = None,
    additional_files: Sequence[Path] | None = None,
) -> SaveResult:
    """Embed UUIDs in document and optionally commit to git.

    This is the main save flow entry point. It:
    1. Loads blocks from blocks.jsonl (or provided path)
    2. Embeds UUIDs as content controls
    3. Optionally commits the document and analysis artifacts

    Args:
        docx_path: Path to the .docx file to save
        blocks_path: Path to blocks.jsonl. If None, inferred from analysis_dir.
        analysis_dir: Directory containing analysis artifacts
        auto_git: If True, auto-commit changes
        commit_message: Custom commit message (auto-generated if None)
        additional_files: Additional files to include in commit

    Returns:
        SaveResult with operation details
    """
    docx_path = Path(docx_path)

    # Determine blocks path
    if blocks_path is None and analysis_dir is not None:
        blocks_path = Path(analysis_dir) / "blocks.jsonl"

    if blocks_path is None or not blocks_path.exists():
        return SaveResult(
            success=False,
            error=f"Blocks file not found: {blocks_path}",
        )

    # Load blocks
    blocks: list[dict] = []
    try:
        with blocks_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    blocks.append(json.loads(line))
    except Exception as e:
        return SaveResult(
            success=False,
            error=f"Failed to load blocks: {e}",
        )

    if not blocks:
        return SaveResult(
            success=False,
            error="No blocks found in blocks.jsonl",
        )

    # Embed UUIDs
    try:
        embedded_count = embed_uuids_in_document(docx_path, blocks, save=True)
    except Exception as e:
        return SaveResult(
            success=False,
            error=f"Failed to embed UUIDs: {e}",
        )

    # Git commit if enabled
    commit_hash = None
    if auto_git:
        repo_root = get_repo_root(docx_path.parent)
        if repo_root:
            # Prepare files to commit
            files_to_commit = [docx_path]
            if analysis_dir:
                analysis_path = Path(analysis_dir)
                if analysis_path.exists():
                    # Add all analysis files
                    for f in analysis_path.glob("*.json"):
                        files_to_commit.append(f)
                    for f in analysis_path.glob("*.jsonl"):
                        files_to_commit.append(f)
            if additional_files:
                files_to_commit.extend(additional_files)

            # Generate commit message
            if commit_message is None:
                commit_message = generate_commit_message(
                    "save",
                    {"document_name": docx_path.name},
                )

            try:
                commit_hash = auto_commit(repo_root, commit_message, files_to_commit)
                if commit_hash:
                    LOGGER.info("Committed changes: %s", commit_hash[:8])
            except Exception as e:
                LOGGER.warning("Git commit failed: %s", e)

    return SaveResult(
        success=True,
        docx_path=docx_path,
        embedded_count=embedded_count,
        commit_hash=commit_hash,
    )


def create_checkpoint(
    docx_path: Path,
    analysis_dir: Path | None = None,
    *,
    note: str = "",
) -> SaveResult:
    """Create an explicit checkpoint commit.

    This is for "major save" operations where the user wants
    to create a named checkpoint in the git history.

    Args:
        docx_path: Path to the document
        analysis_dir: Directory containing analysis artifacts
        note: Optional note to include in commit message

    Returns:
        SaveResult with commit details
    """
    commit_message = generate_commit_message(
        "checkpoint",
        {
            "document_name": Path(docx_path).name,
            "note": note,
        },
    )

    return save_with_uuids(
        docx_path,
        analysis_dir=analysis_dir,
        auto_git=True,
        commit_message=commit_message,
    )
