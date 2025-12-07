"""
Clause lookup utilities for querying block data by paragraph ID.

This module provides a ClauseLookup class that enables efficient lookup of clause
information (ordinal, title, text) by para_id. It accepts either a pre-loaded list
of block dictionaries or a Path to a blocks.jsonl file.

Typical usage:
    # From file path
    lookup = ClauseLookup(analysis_dir / "blocks.jsonl")
    
    # Or from pre-loaded blocks
    lookup = ClauseLookup(blocks_list)
    
    # Query by para_id
    clause_num = lookup.get_clause_number("3DD8236A")  # e.g., "11.2"
    clause_title = lookup.get_clause_title("3DD8236A")  # e.g., "LIMITATION OF LIABILITY"
    clause_text = lookup.get_clause_text("3DD8236A")  # Full paragraph text
    clause_info = lookup.get_clause_info("3DD8236A")  # Dict with all fields
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Type hints only


def extract_clause_title_from_text(text: str) -> str:
    """
    Extract clause title from paragraph text.
    
    A title is defined as 5 or fewer words at the start of the text,
    followed by a period and then whitespace (or end of text).
    
    Args:
        text: The paragraph text to extract title from
        
    Returns:
        The extracted title, or empty string if no title pattern found
        
    Examples:
        >>> extract_clause_title_from_text("INDEMNIFICATION. Each party shall...")
        'INDEMNIFICATION'
        >>> extract_clause_title_from_text("License Grant. Subject to...")
        'License Grant'
        >>> extract_clause_title_from_text("The parties agree to...")
        ''
    """
    if not text:
        return ""
    
    # Strip leading whitespace
    text = text.strip()
    
    # Match: capital letter start, then up to 4 more words, then period, then space/end
    # Words can contain letters, numbers, &, -, commas
    # Must be 3-50 chars to exclude very short items like "A." or "AB."
    match = re.match(r'^([A-Z][^\s.]*(?:\s+[A-Za-z0-9&,\-]+){0,4})\.(?:\s|$)', text)
    if match:
        title = match.group(1).strip()
        # Must be at least 3 chars
        if len(title) < 3 or len(title) > 50:
            return ""
        
        # Reject if title contains obligation words (indicates a sentence, not a title)
        title_lower = title.lower()
        if any(word in title_lower.split() for word in ("shall", "must", "may")):
            return ""
        
        return title
    
    return ""


class ClauseLookup:
    """
    Provides efficient lookup of clause information by paragraph ID.
    
    Accepts either a list of block dictionaries (pre-loaded) or a Path to a 
    blocks.jsonl file. Builds an internal index keyed by para_id for fast lookups.
    
    Attributes:
        blocks: The list of block dictionaries
        _index: Internal dict mapping para_id to block dict
        
    Example:
        lookup = ClauseLookup(blocks_list)
        clause_num = lookup.get_clause_number("3DD8236A")
        clause_title = lookup.get_clause_title("3DD8236A")
    """
    
    def __init__(self, source: Path | list[dict[str, Any]]) -> None:
        """
        Initialize ClauseLookup from blocks list or file path.
        
        Args:
            source: Either a list of block dictionaries, or a Path to blocks.jsonl
            
        Raises:
            FileNotFoundError: If source is a Path that doesn't exist
            TypeError: If source is neither list nor Path
        """
        if isinstance(source, list):
            self.blocks = source
        elif isinstance(source, Path):
            if not source.exists():
                raise FileNotFoundError(f"Blocks file not found: {source}")
            self.blocks = self._load_jsonl(source)
        else:
            raise TypeError(f"source must be Path or list, got {type(source).__name__}")
        
        # Build para_id index
        self._blocks_by_para_id: dict[str, dict[str, Any]] = {}
        for block in self.blocks:
            para_id = block.get("para_id")
            if para_id:
                self._blocks_by_para_id[para_id] = block
    
    @staticmethod
    def _load_jsonl(path: Path) -> list[dict[str, Any]]:
        """Load blocks from a JSONL file."""
        blocks = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    blocks.append(json.loads(line))
        return blocks
    
    def get_clause_number(self, para_id: str) -> str | None:
        """
        Get the clause number (ordinal) for a paragraph.
        
        Args:
            para_id: The paragraph ID to look up
            
        Returns:
            The clause ordinal (e.g., "11.2", "5.1.3") without trailing period,
            or None if not found or not a numbered clause
        """
        block = self._blocks_by_para_id.get(para_id)
        if not block:
            return None
        
        list_info = block.get("list") or {}
        ordinal = list_info.get("ordinal", "")
        
        if not ordinal:
            return None
        
        # Strip trailing period and whitespace
        return ordinal.strip().rstrip('.')
    
    def get_clause_title(self, para_id: str) -> str | None:
        """
        Get the clause title for a paragraph.
        
        First checks for explicit heading.text field in the block (if source is not 'none').
        If not present, attempts to extract title from paragraph text.
        
        Args:
            para_id: The paragraph ID to look up
            
        Returns:
            The clause title, or None if not found
        """
        block = self._blocks_by_para_id.get(para_id)
        if not block:
            return None
        
        # Check for explicit heading.text first (skip fallback labels)
        heading_info = block.get("heading") or {}
        heading_source = heading_info.get("source", "")
        heading_text = heading_info.get("text", "")
        # Only use heading.text if it's from a real source (not 'none' fallback)
        if heading_text and heading_source not in ("none", ""):
            return heading_text
        
        # Fall back to extracting from paragraph text
        text = block.get("text", "")
        extracted = extract_clause_title_from_text(text)
        return extracted if extracted else None
    
    def get_clause_text(self, para_id: str) -> str | None:
        """
        Get the full text of a paragraph.
        
        Args:
            para_id: The paragraph ID to look up
            
        Returns:
            The paragraph text, or None if not found
        """
        block = self._blocks_by_para_id.get(para_id)
        if not block:
            return None
        
        return block.get("text")
    
    def get_clause_info(self, para_id: str) -> dict[str, Any] | None:
        """
        Get combined clause information for a paragraph.
        
        Args:
            para_id: The paragraph ID to look up
            
        Returns:
            Dictionary with keys: para_id, clause_number, clause_title, text.
            Returns None if para_id not found in index.
            Individual values may be None if not available.
        """
        block = self._blocks_by_para_id.get(para_id)
        if not block:
            return None
        
        return {
            "para_id": para_id,
            "clause_number": self.get_clause_number(para_id),
            "clause_title": self.get_clause_title(para_id),
            "text": self.get_clause_text(para_id),
        }
    
    @classmethod
    def from_docx_bytes(cls, docx_bytes: bytes) -> "ClauseLookup":
        """
        Create ClauseLookup from raw docx bytes.
        
        Writes bytes to a temp file, runs document analysis, and loads
        the resulting blocks.jsonl file. If blocks don't have native para_ids,
        generates synthetic ones based on para_idx.
        
        Args:
            docx_bytes: Raw bytes of a .docx document
            
        Returns:
            ClauseLookup instance with blocks from the analyzed document
            
        Raises:
            TypeError: If docx_bytes is None
            Exception: If document analysis fails (invalid docx, etc.)
        """
        if docx_bytes is None:
            raise TypeError("docx_bytes cannot be None")
        
        # Import here to avoid circular import
        from scripts.docx_to_llm_markdown import run_analyze_doc
        from effilocal.doc.uuid_embedding import generate_para_id
        
        # Write bytes to temp file for analyze_doc
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(docx_bytes)
            tmp_path = Path(tmp.name)
        
        # Create temp directory for analysis artifacts
        with tempfile.TemporaryDirectory() as tmp_dir:
            analysis_dir = Path(tmp_dir) / "analysis"
            
            try:
                # Run analyze_doc to extract blocks with numbering
                run_analyze_doc(tmp_path, analysis_dir)
                
                # Load blocks from generated file
                blocks_file = analysis_dir / "blocks.jsonl"
                if not blocks_file.exists():
                    # Return empty lookup if no blocks generated
                    return cls([])
                
                # Load blocks and ensure all have para_ids
                blocks = cls._load_jsonl(blocks_file)
                existing_ids: set[str] = set()
                
                # Collect existing para_ids
                for block in blocks:
                    pid = block.get("para_id")
                    if pid:
                        existing_ids.add(pid.upper())
                
                # Generate para_ids for blocks that don't have them
                for block in blocks:
                    if not block.get("para_id"):
                        new_id = generate_para_id(existing_ids)
                        block["para_id"] = new_id
                        existing_ids.add(new_id.upper())
                
                return cls(blocks)
            finally:
                # Clean up temp docx file
                tmp_path.unlink(missing_ok=True)
    
    def to_ordinal_map(self) -> dict[str, str]:
        """
        Convert lookup to para_id -> clause_number mapping.
        
        For backward compatibility with dict-based approach.
        
        Returns:
            Dictionary mapping para_id to ordinal (e.g., {"3DD8236A": "11.2"}).
            Only includes entries that have a non-empty ordinal.
        """
        result: dict[str, str] = {}
        for para_id in self._blocks_by_para_id:
            clause_num = self.get_clause_number(para_id)
            if clause_num:
                result[para_id] = clause_num
        return result
    
    def to_text_map(self) -> dict[str, str]:
        """
        Convert lookup to para_id -> text mapping.
        
        For backward compatibility with dict-based approach.
        
        Returns:
            Dictionary mapping para_id to paragraph text.
            Only includes entries that have non-empty text.
        """
        result: dict[str, str] = {}
        for para_id, block in self._blocks_by_para_id.items():
            text = block.get("text", "")
            if text:
                result[para_id] = text
        return result
