#!/usr/bin/env python3
"""
Convert a Word document to LLM-optimized markdown using analyze_doc.

This script:
1. Runs analyze_doc on the input .docx file (or uses existing artifacts)
2. Uses blocks.jsonl and relationships.json for structure
3. Produces markdown with:
   - YAML frontmatter with document metadata
   - Clause index / table of contents
   - Main clauses as ## headings with [BEGIN/END EXPLANATION] markers
   - Sub-clauses with **bold** ordinals
   - Proper indentation based on hierarchy level
   - Annexes/Schedules properly separated from main body

Usage:
    python docx_to_llm_markdown.py <input.docx> [--output output.md] [--analysis-dir dir]
    python docx_to_llm_markdown.py <analysis_dir> [--output output.md]
    
Examples:
    # Convert docx, save analysis and markdown in folder named after the docx
    python docx_to_llm_markdown.py "contracts/Agreement.docx"
    # -> Creates contracts/Agreement/blocks.jsonl, contracts/Agreement/Agreement.md
    
    # Specify custom output location
    python docx_to_llm_markdown.py "contracts/Agreement.docx" --output custom.md
    
    # Use existing analysis directory
    python docx_to_llm_markdown.py "contracts/Agreement" --output report.md
"""

import json
import sys
import re
from pathlib import Path
from datetime import date
from typing import Optional


def run_analyze_doc(docx_path: Path, out_dir: Path) -> Path:
    """Run analyze_doc on a Word document and return the analysis directory."""
    from effilocal.flows.analyze_doc import analyze
    
    doc_id = docx_path.stem.replace(' ', '-')[:50]
    
    print(f"Analyzing: {docx_path}")
    analyze(docx_path, doc_id=doc_id, out_dir=out_dir)
    print(f"Analysis complete: {out_dir}")
    
    return out_dir


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
    
    return {r["block_id"]: r for r in data.get("relationships", [])}


def is_attachment_header(block: dict) -> Optional[tuple[str, str]]:
    """
    Check if block is an attachment (Schedule, Annex, etc.) header.
    Returns (attachment_type_and_ordinal, title) if so.
    Uses the 'attachment' field set by AttachmentTracker.
    """
    attachment = block.get("attachment")
    if attachment:
        att_type = attachment.get("type", "")
        ordinal = attachment.get("ordinal", "")
        title = attachment.get("title", "") or block.get("text", "")
        
        # Format like "Schedule 1" or "Annex A"
        header = f"{att_type.title()} {ordinal}".strip()
        return (header, title)
    
    # Fallback: check text for attachment patterns
    text = block.get("text", "")
    for keyword in ["Schedule", "Annex", "Appendix", "Exhibit", "Attachment"]:
        pattern = rf'^{keyword}\s+(\d+|[A-Z])\b'
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            header = f"{keyword} {match.group(1)}"
            title = text[match.end():].strip(' –-:')
            return (header, title or text)
    
    return None


def extract_clause_title_and_body(full_text: str) -> tuple[str, str]:
    """
    Extract short clause title and body text from a heading paragraph.
    
    Pattern: "TITLE.  Body text..." or "TITLE" (no body)
    The title ends at the first "." followed by whitespace.
    
    Returns: (title, body) where body may be empty string.
    """
    import re
    
    # Look for pattern: TITLE. followed by whitespace (1 or more spaces)
    # Match up to the first ". " (period followed by space)
    match = re.match(r'^(.+?\.)\s+(.+)$', full_text, re.DOTALL)
    if match:
        title = match.group(1).rstrip('.')  # Remove trailing period from title
        body = match.group(2).strip()
        return (title, body)
    
    # No body text - the whole thing is the title
    return (full_text.rstrip('.'), "")


def is_main_clause_heading(block: dict) -> Optional[tuple[str, str, str]]:
    """
    Check if block is a main clause heading.
    Returns (ordinal, short_title, body_text) if it is, None otherwise.
    
    Main clause = level 0 with decimal format (like "1.", "2.", "1.0", "2.0") AND no attachment_id.
    """
    # Skip if this is inside an attachment
    if block.get("attachment_id"):
        return None
    
    # Skip if this is an attachment header
    if block.get("attachment"):
        return None
    
    block_type = block.get("type", "")
    list_info = block.get("list", {}) or {}
    heading_info = block.get("heading", {}) or {}
    text = block.get("text", "")
    
    level = list_info.get("level")
    ordinal = list_info.get("ordinal", "")
    format_type = list_info.get("format", "")
    
    # Only level 0 with decimal format
    if level == 0 and ordinal and format_type == "decimal":
        # Accept ordinals like "1.", "2." OR "1.0", "2.0" (pattern %1.0)
        # Must contain "." (to exclude pure numbers) and not have parentheses like "(1)"
        stripped = ordinal.rstrip()
        if "." in stripped and not stripped.startswith("("):
            full_title = heading_info.get("text", "") or ""
            if not full_title or full_title == "Body (no heading)":
                if block_type == "heading":
                    full_title = text
            
            # Clean ordinal: remove trailing ".0", ".", or spaces
            clean_ordinal = stripped.rstrip('0').rstrip('. ')
            
            if full_title and full_title != "Body (no heading)":
                short_title, body = extract_clause_title_and_body(full_title)
                return (clean_ordinal, short_title, body)
    
    return None


def get_ordinal_display(block: dict) -> str:
    """Get the ordinal display for a block (e.g., '1.1', '(a)', '(i)')."""
    list_info = block.get("list", {}) or {}
    ordinal = list_info.get("ordinal", "")
    return ordinal.strip() if ordinal else ""


def get_indent(depth: int) -> str:
    """Get indentation string based on hierarchy depth."""
    if depth is None or depth <= 0:
        return ""
    return "   " * depth


def format_block_text(block: dict, relationships: dict) -> str:
    """Format a single block's text with appropriate indentation and ordinal."""
    block_id = block.get("id", "")
    block_type = block.get("type", "")
    text = block.get("text", "").strip()
    list_info = block.get("list", {}) or {}
    style = block.get("style", "")
    
    # Get hierarchy depth from relationships (preferred) or fall back to list level
    rel = relationships.get(block_id, {})
    depth = rel.get("hierarchy_depth")
    if depth is None:
        depth = list_info.get("level") or 0
    
    ordinal = get_ordinal_display(block)
    
    if not text:
        return ""
    
    # Skip attachment headers (handled separately)
    if is_attachment_header(block):
        return ""
    
    # Skip main clause headings (handled separately)
    if is_main_clause_heading(block):
        return ""
    
    indent = get_indent(depth)
    
    if ordinal:
        return f"{indent}**{ordinal}** {text}\n"
    elif style and "DescriptiveHeading" in style:
        return f"\n### {text}\n"
    elif style and ("Parties" in style or "Background" in style):
        return f"{indent}{text}\n"
    else:
        return f"{indent}{text}\n"


def group_blocks_by_section(blocks: list[dict]) -> list[tuple[Optional[dict], list[dict]]]:
    """
    Group blocks by main clause or attachment.
    Returns list of (section_info, blocks) where section_info has 'type', 'ordinal', 'title', and optionally 'body'.
    """
    groups = []
    current_section = None
    current_blocks = []
    
    for block in blocks:
        # Check for attachment header
        att_info = is_attachment_header(block)
        if att_info:
            if current_blocks:
                groups.append((current_section, current_blocks))
            
            header, title = att_info
            current_section = {
                'type': 'attachment',
                'ordinal': header,
                'title': title,
                'body': ''
            }
            current_blocks = [block]
            continue
        
        # Check for main clause heading
        main_info = is_main_clause_heading(block)
        if main_info:
            if current_blocks:
                groups.append((current_section, current_blocks))
            
            ordinal, title, body = main_info
            current_section = {
                'type': 'main',
                'ordinal': ordinal,
                'title': title,
                'body': body
            }
            current_blocks = [block]
            continue
        
        current_blocks.append(block)
    
    if current_blocks:
        groups.append((current_section, current_blocks))
    
    return groups


def extract_document_title(blocks: list[dict], source_name: str) -> str:
    """Try to extract document title from early blocks or use source name.
    
    Looks for:
    1. DescriptiveHeading with "Terms", "Agreement", "Contract" etc.
    2. Early short paragraph (< 100 chars) with title keywords (before any numbered content)
    3. First heading block (type=heading) with title keywords
    4. Falls back to source name
    """
    title_keywords = ["Terms", "Agreement", "Contract", "Conditions", "License", "Licence", 
                      "Order", "Trial", "Services", "Supply"]
    
    # First pass: look for DescriptiveHeading with key contract terms
    for block in blocks[:15]:
        style = block.get("style", "")
        text = block.get("text", "").strip()
        
        if "DescriptiveHeading" in style and text:
            # Skip explanatory notes
            if text.startswith("[") or text.startswith("•"):
                continue
            # Check for contract-like title
            if any(kw in text for kw in title_keywords):
                return text
    
    # Second pass: look for early short paragraphs with title keywords (before numbered content)
    for block in blocks[:10]:
        text = block.get("text", "").strip()
        list_info = block.get("list", {}) or {}
        
        # Stop if we hit numbered content
        if list_info.get("ordinal"):
            break
        
        # Short paragraph with title keywords is likely the document title
        if text and len(text) < 100 and any(kw.upper() in text.upper() for kw in title_keywords):
            # Skip if it looks like a definition or clause body
            if text.startswith('"') or text.startswith("("):
                continue
            return text
    
    # Third pass: look for first heading type with title keywords
    for block in blocks[:15]:
        if block.get("type") == "heading":
            heading = block.get("heading", {}) or {}
            title = heading.get("text", "") or block.get("text", "")
            if title and not title.startswith("(") and title != "Body (no heading)":
                # Prefer headings with title keywords
                if any(kw in title for kw in title_keywords):
                    return title
    
    # Fourth pass: any heading
    for block in blocks[:15]:
        if block.get("type") == "heading":
            heading = block.get("heading", {}) or {}
            title = heading.get("text", "") or block.get("text", "")
            if title and not title.startswith("(") and title != "Body (no heading)":
                return title
    
    return source_name


def generate_frontmatter(title: str, source: str, groups: list[tuple[dict, list[dict]]]) -> str:
    """Generate YAML frontmatter with document metadata."""
    # Count clauses and attachments
    main_clauses = []
    attachments = []
    
    for section_info, _ in groups:
        if section_info:
            ordinal = section_info.get('ordinal', '')
            section_title = section_info.get('title', '')
            section_type = section_info.get('type', '')
            
            if section_title and section_title != "Body (no heading)":
                if section_type == 'attachment':
                    attachments.append({'ordinal': ordinal, 'title': section_title})
                else:
                    main_clauses.append({'ordinal': ordinal, 'title': section_title})
    
    # Build YAML
    lines = [
        "---",
        f'title: "{title}"',
        f'source: "{source}"',
        'format: llm-optimized',
        f'generated: "{date.today().isoformat()}"',
        'purpose: Legal document formatted for LLM analysis with clause explanation markers',
        f'total_main_clauses: {len(main_clauses)}',
        f'total_attachments: {len(attachments)}',
        '',
        'clauses:',
    ]
    
    for clause in main_clauses:
        lines.append(f'  - ordinal: "{clause["ordinal"]}"')
        lines.append(f'    title: "{clause["title"][:80]}"')
    
    if attachments:
        lines.append('')
        lines.append('attachments:')
        for att in attachments:
            lines.append(f'  - ordinal: "{att["ordinal"]}"')
            lines.append(f'    title: "{att["title"][:80]}"')
    
    lines.append('---')
    lines.append('')
    
    return '\n'.join(lines)


def generate_clause_index(groups: list[tuple[Optional[dict], list[dict]]]) -> str:
    """Generate a clause index / table of contents."""
    lines = ["# Clause Index\n"]
    lines.append("| # | Title | Type |")
    lines.append("|---|-------|------|")
    
    for section_info, _ in groups:
        if section_info:
            ordinal = section_info.get('ordinal', '')
            title = section_info.get('title', '')
            section_type = section_info.get('type', '')
            
            if title and title != "Body (no heading)":
                lines.append(f"| {ordinal} | {title[:60]} | {section_type} |")
    
    lines.append("\n---\n")
    return "\n".join(lines)


def convert_to_markdown(analysis_dir: Path, source_name: str) -> str:
    """Convert analysis artifacts to LLM-optimized markdown."""
    blocks = load_blocks(analysis_dir)
    relationships = load_relationships(analysis_dir)
    
    doc_title = extract_document_title(blocks, source_name)
    groups = group_blocks_by_section(blocks)
    
    output = []
    output.append(generate_frontmatter(doc_title, source_name, groups))
    output.append(generate_clause_index(groups))
    
    # Track if we've rendered the document title yet
    title_rendered = False
    
    for section_info, section_blocks in groups:
        if section_info:
            ordinal = section_info.get('ordinal', '')
            section_title = section_info.get('title', '')
            section_type = section_info.get('type', '')
            section_body = section_info.get('body', '')
            
            # Format section header (just the short title)
            if section_type == 'attachment':
                output.append(f"\n## {ordinal} – {section_title}\n")
            else:
                output.append(f"\n## {ordinal}. {section_title}\n")
            
            # If there's body text from the heading, render it as a paragraph
            if section_body:
                output.append(f"{section_body}\n")
        
        # Process blocks in the section
        for i, block in enumerate(section_blocks):
            # Skip the section header block itself
            if section_info and i == 0:
                continue
            
            block_text = block.get("text", "").strip()
            
            # Check if this block is the document title - format as h1
            if not title_rendered and block_text == doc_title:
                output.append(f"# {doc_title}\n")
                title_rendered = True
                continue
            
            formatted = format_block_text(block, relationships)
            if formatted:
                output.append(formatted)
    
    return "\n".join(output)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Convert a Word document to LLM-optimized markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert docx, auto-create analysis folder and markdown
  python docx_to_llm_markdown.py "contracts/Agreement.docx"
  # -> Creates contracts/Agreement/blocks.jsonl, contracts/Agreement/Agreement.md

  # Specify custom output file
  python docx_to_llm_markdown.py "contracts/Agreement.docx" --output report.md

  # Use existing analysis directory
  python docx_to_llm_markdown.py "contracts/Agreement" --output report.md
"""
    )
    parser.add_argument("input", help="Input .docx file or existing analysis directory")
    parser.add_argument("--output", "-o", help="Output markdown file (default: <name>.md in analysis folder)")
    parser.add_argument("--analysis-dir", "-a", help="Analysis output directory (default: folder named after docx)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Error: Input not found: {input_path}")
        sys.exit(1)
    
    # Determine if input is a .docx file or analysis directory
    if input_path.suffix.lower() == '.docx':
        # Analysis directory: same location as docx, named after the docx stem
        if args.analysis_dir:
            analysis_dir = Path(args.analysis_dir)
        else:
            analysis_dir = input_path.parent / input_path.stem
        
        source_name = input_path.stem
        
        # Run analyze_doc
        run_analyze_doc(input_path, analysis_dir)
    else:
        # Assume it's an analysis directory
        analysis_dir = input_path
        source_name = analysis_dir.name
        
        if not (analysis_dir / "blocks.jsonl").exists():
            print(f"Error: blocks.jsonl not found in {analysis_dir}")
            sys.exit(1)
    
    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        # Default: <source_name>.md in the analysis folder
        output_file = analysis_dir / f"{source_name}.md"
    
    # Convert
    markdown = convert_to_markdown(analysis_dir, source_name)
    
    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"Analysis: {analysis_dir}")
    print(f"Output: {output_file}")
    print(f"Total characters: {len(markdown)}")


if __name__ == "__main__":
    main()
