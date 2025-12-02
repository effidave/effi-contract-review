"""Document analysis flow that emits Sprint 1 JSON artifacts.

Supports UUID preservation across re-analysis:
- Extracts embedded UUIDs from content controls in .docx
- Matches new blocks to previous analysis by UUID, hash, then position
- Emits analysis_delta.json tracking what changed
"""

from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping

from effilocal.config.logging import get_logger
from effilocal.doc import (
    direct_docx,
    hierarchy,
    models,
    relationships,
    sections as section_builder,
)
from effilocal.doc.indexer import build_index
from effilocal.doc.manifest import build_manifest
from effilocal.doc.styles import analyze_styles
from effilocal.doc.uuid_embedding import extract_block_uuids, embed_block_uuids, assign_block_ids
from effilocal.util.hash import sha256_file
from effilocal.util.io import write_jsonl
from effilocal.mcp_server.core.comments import extract_all_comments
from docx import Document

LOGGER = get_logger(__name__)
SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"
DEFAULT_TOOL_VERSION = "sprint2-dev"


class AnalyzeError(RuntimeError):
    """Raised when the analyze flow cannot complete."""


def analyze(
    docx_path: Path,
    *,
    doc_id: str,
    out_dir: Path,
    emit_block_ranges: bool = True,
    emit_ltu_tree: bool = False,
    tool_version: str = DEFAULT_TOOL_VERSION,
    preserve_uuids: bool = True,
) -> dict[str, Path]:
    """
    Parse a ``.docx`` document into the JSON artifacts defined in Sprint 1.

    Args:
        docx_path: Path to the source Word document.
        doc_id: Stable UUID assigned to this document.
        out_dir: Target directory for JSON outputs.
        emit_block_ranges: When ``True`` (default) write per-block tag ranges.
        emit_ltu_tree: When ``True`` emit ``ltu_tree.json`` as a section summary.
        tool_version: Version string recorded in the manifest.
        preserve_uuids: When ``True`` (default), match new blocks to previous
            analysis by UUID/hash and preserve block IDs where possible.

    Returns:
        Mapping of artifact names to their absolute paths.
    """

    docx_path = Path(docx_path)
    out_dir = Path(out_dir)

    if not docx_path.exists():
        raise AnalyzeError(f"Source document not found: {docx_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Analyzing document path=%s doc_id=%s out_dir=%s preserve_uuids=%s", 
                docx_path, doc_id, out_dir, preserve_uuids)

    artifacts: dict[str, Path] = {}

    raw_dir = out_dir / "raw_docx"
    raw_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(docx_path, 'r') as zip_ref:
        zip_ref.extractall(raw_dir)
    artifacts["raw_docx"] = raw_dir

    # Extract embedded UUIDs from content controls
    embedded_uuids: dict[str, int] = {}
    if preserve_uuids:
        try:
            embedded_uuids = extract_block_uuids(docx_path)
            if embedded_uuids:
                LOGGER.info("Extracted %d embedded UUIDs from document", len(embedded_uuids))
        except Exception as e:
            LOGGER.warning("Failed to extract embedded UUIDs: %s", e)

    # Load previous blocks for matching
    old_blocks: list[dict] = []
    old_blocks_path = out_dir / "blocks.jsonl"
    if preserve_uuids and old_blocks_path.exists():
        try:
            with old_blocks_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        old_blocks.append(json.loads(line))
            LOGGER.info("Loaded %d blocks from previous analysis", len(old_blocks))
        except Exception as e:
            LOGGER.warning("Failed to load previous blocks: %s", e)

    blocks = list(direct_docx.iter_blocks(docx_path))
    attachments = _collect_attachments(blocks)
    if not blocks:
        LOGGER.warning("No textual blocks detected in document: path=%s", docx_path)

    # Assign IDs to blocks (they start with id=None)
    # Priority: para_id match > hash match with old blocks > position match > generate new
    id_stats = assign_block_ids(
        blocks,
        embedded_uuids=embedded_uuids if preserve_uuids else None,
        old_blocks=old_blocks if preserve_uuids else None,
    )
    LOGGER.info(
        "Block IDs assigned: from_para_id=%d, from_hash=%d, from_position=%d, generated=%d",
        id_stats.get("from_para_id", 0),
        id_stats.get("from_hash", 0),
        id_stats.get("from_position", 0),
        id_stats.get("generated", 0),
    )

    # Infer hierarchy AFTER ID assignment so parent/child references use final IDs
    hierarchy.infer_block_hierarchy(blocks)

    sections_payload = section_builder.assign_sections(blocks, doc_id)
    styles_payload = analyze_styles(blocks)
    relationships_payload = relationships.build_relationships(blocks)
    _strip_block_relationship_fields(blocks)

    tag_ranges: list[dict[str, object]] | None = None
    if emit_block_ranges:
        tag_ranges = [models.make_block_range(block["id"]) for block in blocks]

    blocks_path = out_dir / "blocks.jsonl"
    write_jsonl(blocks_path, blocks)
    artifacts["blocks.jsonl"] = blocks_path

    sections_path = out_dir / "sections.json"
    _write_json(sections_path, sections_payload)
    artifacts["sections.json"] = sections_path

    styles_path = out_dir / "styles.json"
    _write_json(styles_path, styles_payload)
    artifacts["styles.json"] = styles_path

    relationships_path = out_dir / "relationships.json"
    _write_json(
        relationships_path,
        {
            "doc_id": doc_id,
            "relationships": relationships_payload,
        },
    )
    artifacts["relationships.json"] = relationships_path

    tag_ranges_path: Path | None = None
    if tag_ranges is not None:
        tag_ranges_path = out_dir / "tag_ranges.jsonl"
        write_jsonl(tag_ranges_path, tag_ranges)
        artifacts["tag_ranges.jsonl"] = tag_ranges_path

    filemap = {
        "blocks": "blocks.jsonl",
        "sections": "sections.json",
        "styles": "styles.json",
    }
    index_payload = build_index(
        doc_id=doc_id,
        source_filename=docx_path.name,
        blocks=blocks,
        sections=sections_payload,
        filemap=filemap,
        tag_ranges=tag_ranges,
    )
    index_path = out_dir / "index.json"
    _write_json(index_path, index_payload)
    artifacts["index.json"] = index_path

    if emit_ltu_tree:
        ltu_tree_path = out_dir / "ltu_tree.json"
        ltu_tree_payload = {"doc_id": doc_id, "root": sections_payload.get("root", {})}
        _write_json(ltu_tree_path, ltu_tree_payload)
        artifacts["ltu_tree.json"] = ltu_tree_path
        LOGGER.info("LTU tree emitted to %s", ltu_tree_path)

    checksum_targets = {name: path for name, path in artifacts.items() if path.exists()}
    checksums = {name: sha256_file(path) for name, path in checksum_targets.items() if path.is_file()}

    manifest_payload = build_manifest(
        doc_id=doc_id,
        tool_version=tool_version,
        checksums=checksums,
        schema_dir=SCHEMA_DIR,
        fallback_heading_label=direct_docx.DEFAULT_FALLBACK_HEADING_LABEL,
        attachments=attachments,
    )
    manifest_path = out_dir / "manifest.json"
    _write_json(manifest_path, manifest_payload)
    artifacts["manifest.json"] = manifest_path

    # Emit analysis_delta.json tracking what changed
    if preserve_uuids and old_blocks:
        # Find new blocks (generated IDs, not matched to old)
        new_block_ids = []
        old_ids = {b.get("id") for b in old_blocks}
        for block in blocks:
            if block.get("id") not in old_ids:
                new_block_ids.append(block.get("id"))
        
        # Find deleted blocks (old IDs not in new)
        new_ids = {b.get("id") for b in blocks}
        deleted_block_ids = [b.get("id") for b in old_blocks if b.get("id") not in new_ids]
        
        # Find modified blocks (same ID but different hash)
        modified_block_ids = []
        old_blocks_by_id = {b.get("id"): b for b in old_blocks}
        for block in blocks:
            block_id = block.get("id")
            if block_id in old_blocks_by_id:
                old_hash = old_blocks_by_id[block_id].get("content_hash", "")
                new_hash = block.get("content_hash", "")
                if old_hash != new_hash:
                    modified_block_ids.append(block_id)
        
        delta_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "matched_from_para_id": id_stats.get("from_para_id", 0),
            "matched_from_hash": id_stats.get("from_hash", 0),
            "matched_from_position": id_stats.get("from_position", 0),
            "generated_new": id_stats.get("generated", 0),
            "new_blocks": new_block_ids,
            "deleted_blocks": deleted_block_ids,
            "modified_blocks": modified_block_ids,
        }
        delta_path = out_dir / "analysis_delta.json"
        _write_json(delta_path, delta_payload)
        artifacts["analysis_delta.json"] = delta_path
        LOGGER.info("Analysis delta emitted to %s", delta_path)

    # Extract EFFI_NOTES
    try:
        doc = Document(docx_path)
        all_comments = extract_all_comments(doc)
        notes = {}
        for c in all_comments:
            text = c.get('text', '')
            if text.startswith('EFFI_NOTE:'):
                note_content = text[len('EFFI_NOTE:'):].strip()
                para_idx = c.get('paragraph_index')
                if para_idx is not None:
                    notes[str(para_idx)] = note_content
        
        if notes:
            notes_path = out_dir / "notes.json"
            _write_json(notes_path, notes)
            artifacts["notes.json"] = notes_path
            LOGGER.info("Extracted %d notes to %s", len(notes), notes_path)
    except Exception as e:
        LOGGER.warning("Failed to extract notes: %s", e)

    # Embed UUIDs into the document for edit tracking
    # This allows the save flow to identify which paragraphs to update
    try:
        embedded = embed_block_uuids(docx_path, blocks, overwrite=False)
        LOGGER.info("Embedded %d UUIDs into document: %s", len(embedded), docx_path)
    except Exception as e:
        LOGGER.warning("Failed to embed UUIDs into document: %s", e)

    LOGGER.info("Document analysis completed successfully: doc_id=%s", doc_id)
    return artifacts


def _write_json(path: Path, payload: Mapping[str, object] | Iterable[object]) -> None:
    """Write JSON with UTF-8 encoding and a trailing newline."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _collect_attachments(blocks: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Extract attachment metadata from analyzer blocks in document order."""

    attachments: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for block in blocks:
        meta = block.get("attachment")
        if not isinstance(meta, Mapping):
            continue
        attachment_id = str(
            meta.get("attachment_id")
            or block.get("attachment_id")
            or block.get("id")
        )
        if attachment_id in seen:
            continue
        seen.add(attachment_id)
        attachment_payload: dict[str, Any] = {
            "attachment_id": attachment_id,
            "type": meta.get("type"),
            "ordinal": meta.get("ordinal"),
            "title": meta.get("title"),
            "parent_attachment_id": meta.get("parent_attachment_id"),
        }
        attachments.append(attachment_payload)
    return attachments


def _strip_block_relationship_fields(blocks: Iterable[MutableMapping[str, Any]]) -> None:
    """Remove hierarchy fields from blocks before writing to disk."""

    keys = ("parent_block_id", "child_block_ids", "sibling_ordinal", "restart_group_id")
    for block in blocks:
        for key in keys:
            block.pop(key, None)
