#!/usr/bin/env python3
"""
Convert analyze_doc artifacts (blocks.jsonl, relationships.json) to LLM-optimized markdown.

This script produces markdown with:
- YAML frontmatter with document metadata
- Table of contents / clause index
- Main clauses as ## headings
- Sub-clauses with **bold** ordinals
- Proper indentation based on hierarchy level
- [BEGIN EXPLANATION] / [END EXPLANATION] markers for each main clause

Usage:
    python blocks_to_llm_markdown.py <analysis_dir> <output_file>
    
Example:
    python blocks_to_llm_markdown.py "EL_Projects/Test Project/analysis/Norton R&D Services Agreement (DRAFT) - HJ8" output.md
"""

import json
import sys
from pathlib import Path
from typing import Optional
from collections import defaultdict


def load_blocks(analysis_dir: Path) -> list[dict]:
    """Load blocks from blocks.jsonl."""
    blocks_file = analysis_dir / "blocks.jsonl"
    blocks = []
    with open(blocks_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                blocks.append(json.loads(line))
    return blocks


def load_relationships(analysis_dir: Path) -> dict[str, dict]:
    """Load relationships and return as block_id -> relationship mapping."""
    rel_file = analysis_dir / "relationships.json"
    with open(rel_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Create lookup by block_id
    return {r["block_id"]: r for r in data.get("relationships", [])}


def get_main_clause_heading(block: dict, in_schedule: bool = False) -> Optional[tuple[str, str]]:
    """
    Check if block is a main clause heading.
    Returns (ordinal, title) if it is, None otherwise.
    
    Main clause = heading type with list.level == 0 AND decimal format (like "1.", "2.")
    We exclude non-clause items like "(1)", "(A)" which are parties/background sections.
    
    Also detects Schedule headings (e.g., "Schedule 1", "Schedule 2").
    
    When in_schedule=True, we don't treat numbered items as main clauses - they're
    Schedule sub-headings instead.
    """
    block_type = block.get("type", "")
    list_info = block.get("list", {}) or {}
    heading_info = block.get("heading", {}) or {}
    style = block.get("style", "")
    text = block.get("text", "")
    attachment_id = block.get("attachment_id")
    
    level = list_info.get("level")
    ordinal = list_info.get("ordinal", "")
    format_type = list_info.get("format", "")
    
    # Check for Schedule headers (has "Schedule" style or ordinal)
    schedule_info = is_schedule_header(block)
    if schedule_info:
        return (schedule_info, text)
    
    # If we're inside a Schedule, numbered items aren't main clause headings
    # They're Schedule-specific section headings
    if in_schedule or attachment_id:
        return None
    
    # Only consider level 0 with decimal format as main clauses (e.g., "1.", "2.")
    # Exclude parenthetical formats like "(1)", "(A)", "(a)" which are parties/background
    if level == 0 and ordinal:
        # Must be decimal format AND end with "." (not parentheses)
        if format_type == "decimal" and ordinal.rstrip().endswith("."):
            # Get the title
            title = heading_info.get("text", "") or ""
            # Fallback: if heading source is none or fallback, use text for title if it's a heading type
            if (not title or title == "Body (no heading)") and block_type == "heading":
                title = text
            
            # Clean ordinal - remove trailing dot
            clean_ordinal = ordinal.rstrip('. ')
            
            # Skip if no real title (just "Body (no heading)")
            if title == "Body (no heading)" or not title:
                return None
                
            return (clean_ordinal, title)
    
    return None


def is_schedule_header(block: dict) -> Optional[str]:
    """Check if block is a Schedule header. Returns Schedule info if so."""
    text = block.get("text", "")
    style = block.get("style", "")
    list_info = block.get("list", {}) or {}
    ordinal = list_info.get("ordinal", "")
    
    # Check for Schedule style or ordinal containing "Schedule"
    if style == "Schedule" or (ordinal and "schedule" in ordinal.lower()):
        # This is a Schedule header
        return ordinal or f"Schedule: {text[:30]}"
    
    # Also check for text-based Schedule detection (fallback)
    import re
    if text.lower().startswith("schedule"):
        match = re.match(r'^(Schedule\s+\d+)', text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def get_ordinal_display(block: dict) -> str:
    """Get the ordinal display for a block (e.g., '1.1', '(a)', '(i)')."""
    list_info = block.get("list", {}) or {}
    ordinal = list_info.get("ordinal", "")
    return ordinal.strip() if ordinal else ""


def get_indent(level: int) -> str:
    """Get indentation string based on hierarchy level."""
    if level is None or level <= 0:
        return ""
    # Use 3 spaces per level (common for legal docs)
    return "   " * level


def format_block_text(block: dict, relationships: dict, in_schedule: bool = False) -> str:
    """
    Format a single block's text with appropriate indentation and ordinal.
    """
    block_id = block.get("id", "")
    block_type = block.get("type", "")
    text = block.get("text", "").strip()
    list_info = block.get("list", {}) or {}
    style = block.get("style", "")
    
    level = list_info.get("level") or 0
    ordinal = get_ordinal_display(block)
    format_type = list_info.get("format", "")
    
    # Get hierarchy depth from relationships if available
    rel = relationships.get(block_id, {})
    hierarchy_depth = rel.get("hierarchy_depth", level)
    
    if not text:
        return ""
    
    # Skip Schedule headers (handled separately as ## headers)
    if is_schedule_header(block):
        return ""
    
    # Skip main clause headings (handled separately as ## headers)
    if get_main_clause_heading(block, in_schedule=in_schedule):
        return ""
    
    # Determine indentation based on list level
    # Level 0 = no indent (or for non-decimal items at level 0)
    # Level 1+ = appropriate indentation
    indent = get_indent(level)
    
    # Format based on block type and content
    if ordinal:
        # Has an ordinal - format appropriately
        return f"{indent}**{ordinal}** {text}"
    elif style and "DescriptiveHeading" in style:
        # Section descriptors like "BACKGROUND", "Agreed terms"
        return f"\n### {text}\n"
    elif style and ("Parties" in style or "Background" in style):
        # Party/background items without ordinals rendered
        return f"{indent}{text}"
    else:
        # Regular paragraph or other content
        return f"{indent}{text}"


def group_blocks_by_main_clause(blocks: list[dict]) -> list[tuple[Optional[tuple[str, str]], list[dict]]]:
    """
    Group blocks by their main clause.
    Returns list of (main_clause_info, blocks) where main_clause_info is (ordinal, title) or None.
    
    Also tracks Schedule context - within Schedules, numbered items are treated as
    section headings rather than main clauses.
    """
    groups = []
    current_main = None
    current_blocks = []
    in_schedule = False
    
    for block in blocks:
        # Check if this starts a Schedule
        schedule_header = is_schedule_header(block)
        if schedule_header:
            in_schedule = True
            # Save previous group if any
            if current_blocks:
                groups.append((current_main, current_blocks))
            # Start new Schedule group
            current_main = (schedule_header, block.get("text", schedule_header))
            current_blocks = [block]
            continue
        
        # Check for main clause heading (passing Schedule context)
        main_info = get_main_clause_heading(block, in_schedule=in_schedule)
        
        if main_info:
            # If we found a main clause (not in Schedule), reset Schedule flag
            if not in_schedule:
                in_schedule = False
            
            # Save previous group if any
            if current_blocks:
                groups.append((current_main, current_blocks))
            
            # Start new group
            current_main = main_info
            current_blocks = [block]
        else:
            current_blocks.append(block)
    
    # Don't forget the last group
    if current_blocks:
        groups.append((current_main, current_blocks))
    
    return groups


def extract_document_title(blocks: list[dict], analysis_dir: Path) -> str:
    """Try to extract document title from the first heading or use directory name."""
    for block in blocks[:10]:  # Check first 10 blocks
        if block.get("type") == "heading":
            heading = block.get("heading", {}) or {}
            title = heading.get("text", "") or block.get("text", "")
            if title and not title.startswith("(") and title != "Body (no heading)":
                return title
    # Fallback to analysis directory name (which usually has the document name)
    return analysis_dir.name.replace(" - ", " ").strip()


def generate_yaml_frontmatter(title: str, analysis_dir: Path) -> str:
    """Generate YAML frontmatter for the document."""
    return f"""---
title: "{title}"
source: "{analysis_dir.name}"
purpose: Legal document formatted for LLM analysis with clause explanations
format_version: "2.0"
---

"""


def generate_clause_index(groups: list[tuple[Optional[tuple[str, str]], list[dict]]]) -> str:
    """Generate a clause index / table of contents."""
    lines = ["## Clause Index\n"]
    
    for main_info, _ in groups:
        if main_info:
            ordinal, title = main_info
            # Skip entries without proper titles
            if title and title != "Body (no heading)":
                lines.append(f"- **{ordinal}** {title}")
    
    lines.append("\n---\n")
    return "\n".join(lines)


def convert_to_markdown(analysis_dir: Path) -> str:
    """
    Convert analysis artifacts to LLM-optimized markdown.
    """
    blocks = load_blocks(analysis_dir)
    relationships = load_relationships(analysis_dir)
    
    # Extract title
    title = extract_document_title(blocks, analysis_dir)
    
    # Group blocks by main clause
    groups = group_blocks_by_main_clause(blocks)
    
    # Build output
    output = []
    
    # Add YAML frontmatter
    output.append(generate_yaml_frontmatter(title, analysis_dir))
    
    # Add clause index
    output.append(generate_clause_index(groups))
    
    # Process each group
    for main_info, group_blocks in groups:
        # Track if we're in a Schedule
        in_schedule = False
        if main_info:
            ordinal, title = main_info
            # Check if this is a Schedule
            if ordinal.lower().startswith("schedule"):
                in_schedule = True
            
            # Add main clause/schedule heading
            output.append(f"\n## {ordinal}. {title}\n")
            output.append("[BEGIN EXPLANATION]\n")
            output.append("[END EXPLANATION]\n")
        
        # Process blocks in the group
        for i, block in enumerate(group_blocks):
            block_type = block.get("type", "")
            list_info = block.get("list", {}) or {}
            level = list_info.get("level", 0) or 0
            
            # Skip the main clause/Schedule heading block itself (already rendered as ##)
            if main_info and i == 0:
                continue
            
            formatted = format_block_text(block, relationships, in_schedule=in_schedule)
            if formatted:
                output.append(formatted)
    
    return "\n".join(output)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    analysis_dir = Path(sys.argv[1])
    
    if not analysis_dir.exists():
        print(f"Error: Analysis directory not found: {analysis_dir}")
        sys.exit(1)
    
    if not (analysis_dir / "blocks.jsonl").exists():
        print(f"Error: blocks.jsonl not found in {analysis_dir}")
        sys.exit(1)
    
    # Determine output file
    if len(sys.argv) >= 3:
        output_file = Path(sys.argv[2])
    else:
        output_file = analysis_dir / "document-llm.md"
    
    # Convert
    markdown = convert_to_markdown(analysis_dir)
    
    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"Converted to: {output_file}")
    print(f"Total characters: {len(markdown)}")


if __name__ == "__main__":
    main()
