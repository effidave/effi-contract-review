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
from pathlib import Path
from typing import Any


def extract_clause_title_from_text(text: str) -> str:
    """
    Extract clause title from paragraph text.
    
    Handles two patterns:
    1. ALL CAPS titles (e.g., "LIMITATION OF LIABILITY." -> "LIMITATION OF LIABILITY")
    2. Title Case titles (e.g., "Indemnification." -> "Indemnification")
    
    Args:
        text: The paragraph text to extract title from
        
    Returns:
        The extracted title, or empty string if no title pattern found
        
    Examples:
        >>> extract_clause_title_from_text("INDEMNIFICATION. Each party shall...")
        'INDEMNIFICATION'
        >>> extract_clause_title_from_text("Limitation of Liability. Subject to...")
        'Limitation of Liability'
        >>> extract_clause_title_from_text("The parties agree to...")
        ''
    """
    if not text:
        return ""
    
    # ALL CAPS title pattern (e.g., "INDEMNIFICATION.", "LIMITATION OF LIABILITY.")
    match = re.match(r'^([A-Z][A-Z\s&,\-]*)\.(?:\s|$)', text)
    if match:
        title = match.group(1).strip()
        # Must be at least 3 chars and all uppercase (excluding spaces/punctuation)
        if len(title) >= 3 and title.replace(' ', '').replace('&', '').replace(',', '').replace('-', '').isupper():
            return title
    
    # Title Case pattern (e.g., "Indemnification.", "Limitation of Liability.")
    match = re.match(r'^([A-Z][a-z]+(?:\s+(?:[A-Z][a-z]+|&|of|and|the|in|to|for))*)\.(?:\s|$)', text)
    if match:
        title = match.group(1).strip()
        if len(title) <= 50:
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
        
        First checks for explicit heading.text field in the block.
        If not present, attempts to extract title from paragraph text.
        
        Args:
            para_id: The paragraph ID to look up
            
        Returns:
            The clause title, or None if not found
        """
        block = self._blocks_by_para_id.get(para_id)
        if not block:
            return None
        
        # Check for explicit heading.text first
        heading_info = block.get("heading") or {}
        heading_text = heading_info.get("text", "")
        if heading_text:
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
