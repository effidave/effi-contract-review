"""Artifact loader and query interface for analyzed documents.

Provides efficient loading and indexing of JSON artifacts produced by the
analysis pipeline, enabling fast queries for webview display and MCP tool targeting.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from effilocal.config.logging import get_logger

LOGGER = get_logger(__name__)


class ArtifactLoader:
    """Load and query document artifacts efficiently.
    
    Usage:
        loader = ArtifactLoader('EL_Projects/My Project/analysis')
        
        # Find clause by number
        clause = loader.find_clause_by_ordinal('3.2.1')
        
        # Get all blocks in a clause group (main + continuations)
        group = loader.get_clause_group(clause['id'])
        
        # Get section blocks
        blocks = loader.get_section_blocks(section_id)
        
        # List schedules
        schedules = loader.get_schedules()
    """
    
    def __init__(self, analysis_dir: str | Path):
        """Load artifacts from analysis directory.
        
        Args:
            analysis_dir: Path to directory containing artifact files
                         (manifest.json, blocks.jsonl, sections.json, etc.)
        
        Raises:
            FileNotFoundError: If required artifact files are missing
            json.JSONDecodeError: If artifact files are malformed
        """
        self.analysis_dir = Path(analysis_dir)
        
        if not self.analysis_dir.exists():
            raise FileNotFoundError(f"Analysis directory not found: {self.analysis_dir}")
        
        LOGGER.info("Loading artifacts from %s", self.analysis_dir)
        
        # Load core artifacts
        self.manifest = self._load_json('manifest.json')
        self.sections = self._load_json('sections.json')
        self.relationships = self._load_json('relationships.json')
        self.styles = self._load_json('styles.json')
        self.index = self._load_json('index.json')
        
        # Load blocks (line-delimited JSON)
        self.blocks = self._load_blocks()
        
        LOGGER.info(
            "Loaded %d blocks, %d sections, %d attachments",
            len(self.blocks),
            self.index.get('section_count', 0),
            self.index.get('attachment_count', 0),
        )
        
        # Build indexes for fast lookups
        self.blocks_by_id: Dict[str, Dict[str, Any]] = {
            b['id']: b for b in self.blocks
        }
        self.blocks_by_ordinal: Dict[str, Dict[str, Any]] = self._index_by_ordinal()
        self.blocks_by_para_id: Dict[str, Dict[str, Any]] = self._index_by_para_id()
        self.sections_by_id: Dict[str, Dict[str, Any]] = self._index_sections()
        self.relationships_by_block_id: Dict[str, Dict[str, Any]] = {
            r['block_id']: r for r in self.relationships.get('relationships', [])
        }
        
        LOGGER.debug(
            "Built indexes: %d blocks_by_id, %d blocks_by_ordinal, %d sections_by_id",
            len(self.blocks_by_id),
            len(self.blocks_by_ordinal),
            len(self.sections_by_id),
        )
    
    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Load a JSON artifact file."""
        path = self.analysis_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Required artifact not found: {path}")
        
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    
    def _load_blocks(self) -> List[Dict[str, Any]]:
        """Load blocks from line-delimited JSON file."""
        path = self.analysis_dir / 'blocks.jsonl'
        if not path.exists():
            raise FileNotFoundError(f"Required artifact not found: {path}")
        
        blocks = []
        with open(path, encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    blocks.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    LOGGER.error("Failed to parse block at line %d: %s", line_num, exc)
                    raise
        
        return blocks
    
    def _index_by_ordinal(self) -> Dict[str, Dict[str, Any]]:
        """Build index of blocks by clause ordinal (e.g., '3.2.1')."""
        index = {}
        for block in self.blocks:
            list_meta = block.get('list')
            if list_meta and 'ordinal' in list_meta:
                ordinal = list_meta['ordinal']
                if ordinal in index:
                    LOGGER.warning(
                        "Duplicate ordinal '%s' found: block %s and %s",
                        ordinal,
                        index[ordinal]['id'],
                        block['id'],
                    )
                index[ordinal] = block
        return index
    
    def _index_by_para_id(self) -> Dict[str, Dict[str, Any]]:
        """Build index of blocks by Word paragraph ID."""
        index = {}
        for block in self.blocks:
            para_id = block.get('para_id')
            if para_id:
                index[para_id] = block
        return index
    
    def _index_sections(self) -> Dict[str, Dict[str, Any]]:
        """Build flat index of all sections by ID."""
        index = {}
        
        def index_recursive(section: Dict[str, Any]) -> None:
            section_id = section.get('id')
            if section_id:
                index[section_id] = section
            for child in section.get('children', []):
                index_recursive(child)
        
        # Index from root
        for section in self.sections.get('root', {}).get('children', []):
            index_recursive(section)
        
        return index
    
    # Query methods
    
    def find_clause_by_ordinal(self, ordinal: str) -> Optional[Dict[str, Any]]:
        """Find block by clause number.
        
        Args:
            ordinal: Clause number (e.g., '3.2.1', '5.', '7(a)')
        
        Returns:
            Block dict or None if not found
        """
        return self.blocks_by_ordinal.get(ordinal)
    
    def find_block_by_para_id(self, para_id: str) -> Optional[Dict[str, Any]]:
        """Find block by Word paragraph ID.
        
        Args:
            para_id: Word's internal paragraph ID (e.g., '3DD8236A')
        
        Returns:
            Block dict or None if not found
        """
        return self.blocks_by_para_id.get(para_id)
    
    def get_clause_group(self, block_id: str) -> List[Dict[str, Any]]:
        """Get main clause and all continuation paragraphs.
        
        Args:
            block_id: ID of any block in the clause group
        
        Returns:
            List of blocks in clause group (main clause + continuations)
        """
        block = self.blocks_by_id.get(block_id)
        if not block:
            return []
        
        clause_group_id = block.get('clause_group_id')
        if not clause_group_id:
            return [block]
        
        return [
            b for b in self.blocks
            if b.get('clause_group_id') == clause_group_id
        ]
    
    def get_section_blocks(self, section_id: str) -> List[Dict[str, Any]]:
        """Get all blocks in a section.
        
        Args:
            section_id: Section UUID
        
        Returns:
            List of blocks in the section (may be empty)
        """
        section = self.sections_by_id.get(section_id)
        if not section:
            return []
        
        block_ids = section.get('block_ids', [])
        return [
            self.blocks_by_id[bid]
            for bid in block_ids
            if bid in self.blocks_by_id
        ]
    
    def get_section_path(self, section_id: str) -> List[str]:
        """Get breadcrumb path from root to section.
        
        Args:
            section_id: Section UUID
        
        Returns:
            List of section titles from root to target
            (e.g., ['Interpretation', 'Definitions'])
        """
        def find_path(sections: List[Dict[str, Any]], target_id: str, path: List[str]) -> Optional[List[str]]:
            for section in sections:
                current_path = path + [section.get('title', '')]
                if section.get('id') == target_id:
                    return current_path
                children = section.get('children', [])
                if children:
                    result = find_path(children, target_id, current_path)
                    if result:
                        return result
            return None
        
        root_sections = self.sections.get('root', {}).get('children', [])
        return find_path(root_sections, section_id, []) or []
    
    def get_schedules(self) -> List[Dict[str, Any]]:
        """Get all detected schedules/annexes.
        
        Returns:
            List of attachment metadata dicts from manifest
        """
        return self.manifest.get('attachments', [])
    
    def get_schedule_blocks(self, attachment_id: str) -> List[Dict[str, Any]]:
        """Get all blocks in a specific schedule/annex.
        
        Args:
            attachment_id: Attachment UUID
        
        Returns:
            List of blocks with matching attachment_id
        """
        return [
            b for b in self.blocks
            if b.get('attachment_id') == attachment_id
        ]
    
    def search_blocks(
        self,
        text: Optional[str] = None,
        block_type: Optional[str] = None,
        style: Optional[str] = None,
        has_numbering: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Search blocks by text, type, style, or numbering.
        
        Args:
            text: Text substring to search for (case-insensitive)
            block_type: Block type filter ('paragraph', 'list_item', 'heading', 'table')
            style: Style name filter
            has_numbering: Filter for numbered (True) or unnumbered (False) blocks
        
        Returns:
            List of matching blocks
        """
        results = self.blocks
        
        if text is not None:
            text_lower = text.lower()
            results = [b for b in results if text_lower in b.get('text', '').lower()]
        
        if block_type is not None:
            results = [b for b in results if b.get('type') == block_type]
        
        if style is not None:
            results = [b for b in results if b.get('style') == style]
        
        if has_numbering is not None:
            if has_numbering:
                results = [b for b in results if b.get('list') is not None]
            else:
                results = [b for b in results if b.get('list') is None]
        
        return results
    
    def get_relationship(self, block_id: str) -> Optional[Dict[str, Any]]:
        """Get relationship metadata for a block.
        
        Args:
            block_id: Block UUID
        
        Returns:
            Relationship dict or None if not found
        """
        return self.relationships_by_block_id.get(block_id)
    
    def get_parent_block(self, block_id: str) -> Optional[Dict[str, Any]]:
        """Get parent block in hierarchy.
        
        Args:
            block_id: Block UUID
        
        Returns:
            Parent block dict or None if no parent (root block)
        """
        rel = self.get_relationship(block_id)
        if not rel:
            return None
        
        parent_id = rel.get('parent_block_id')
        if not parent_id:
            return None
        
        return self.blocks_by_id.get(parent_id)
    
    def get_child_blocks(self, block_id: str) -> List[Dict[str, Any]]:
        """Get direct child blocks in hierarchy.
        
        Args:
            block_id: Block UUID
        
        Returns:
            List of child blocks
        """
        rel = self.get_relationship(block_id)
        if not rel:
            return []
        
        child_ids = rel.get('child_block_ids', [])
        return [
            self.blocks_by_id[cid]
            for cid in child_ids
            if cid in self.blocks_by_id
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get document statistics.
        
        Returns:
            Dict with block counts, section counts, etc.
        """
        return {
            'doc_id': self.manifest.get('doc_id'),
            'block_count': len(self.blocks),
            'section_count': len(self.sections_by_id),
            'attachment_count': len(self.get_schedules()),
            'numbered_blocks': len([b for b in self.blocks if b.get('list')]),
            'hierarchy_depth': self.sections.get('hierarchy_depth', 0),
            'style_count': len(self.styles.get('styles', [])),
        }
