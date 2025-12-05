#!/usr/bin/env python3
"""
Format a contract markdown file for optimal LLM consumption.

This script:
1. Adds clause placeholders with BEGIN/END markers
2. Cleans up Pandoc artifacts ({.mark}, escaped quotes, etc.)
3. Adds explicit sub-clause numbering (2.1, 2.2, etc.)
4. Properly indents sub-clauses and trailing paragraphs
5. Adds YAML frontmatter with document metadata
6. Creates a clause index at the top for easy navigation
"""

import re
import sys
from pathlib import Path
from datetime import date


def clean_pandoc_artifacts(content: str) -> str:
    """Remove Pandoc-specific markup artifacts."""
    # Remove {.mark} spans: \[[5]{.mark}\] -> [5]
    content = re.sub(r'\\\[(\[.*?\])\{\.mark\}\\\]', r'\1', content)
    # Also handle simpler cases: [text]{.mark} -> text
    content = re.sub(r'\[([^\]]+)\]\{\.mark\}', r'\1', content)
    # Remove {.underline} spans
    content = re.sub(r'\[([^\]]+)\]\{\.underline\}', r'_\1_', content)
    # Remove anchor spans: []{#a236056 .anchor}
    content = re.sub(r'\[\]\{#\w+ \.anchor\}', '', content)
    # Fix escaped quotes: \' -> '
    content = content.replace("\\'", "'")
    # Remove empty HTML comments
    content = re.sub(r'<!-- -->\n?', '', content)
    return content


def is_definition_item(text: str) -> bool:
    """Check if the line looks like a definition item (bold term followed by definition)."""
    # Matches: **Term**: definition or **Term** means...
    if re.match(r'^\*\*[^*]+\*\*[:\s]', text):
        return True
    if 'means' in text.lower()[:50] and '**' in text[:30]:
        return True
    return False


def is_main_clause_heading(text: str, clause_num: int) -> bool:
    """
    Determine if a numbered line is a main clause heading vs a sub-clause.
    
    Main clause headings are typically:
    - Short titles (< 50 chars before any punctuation)
    - Start with capital letter
    - Don't contain definitions (**term**: means...)
    - Don't start with "The", "If", "Where", "Subject to", etc.
    """
    if is_definition_item(text):
        return False
    
    # Get first sentence/phrase
    first_part = text.split('\n')[0].strip()
    
    # If it starts with lowercase, it's not a heading
    if first_part and first_part[0].islower():
        return False
    
    # If it's very long, it's probably content not a heading
    # But check up to first punctuation
    heading_part = re.split(r'[.,:;]', first_part)[0]
    if len(heading_part) > 50:
        return False
    
    # Common patterns that indicate content, not headings
    content_starters = [
        'The ', 'If ', 'Where ', 'Subject to', 'Without ', 'For ', 
        'Each ', 'Any ', 'In ', 'On ', 'To ', 'This ', 'Such ',
        'Unless ', 'During ', 'Either ', 'Both ', 'Neither ',
    ]
    for starter in content_starters:
        if first_part.startswith(starter):
            return False
    
    # If it ends with a colon after a short phrase, might be a heading
    # But "The Customer shall:" is content, not a heading
    if first_part.endswith(':') and len(first_part) > 30:
        return False
    
    return True


def get_line_indent(line: str) -> int:
    """Get the indentation level of a line (in spaces)."""
    return len(line) - len(line.lstrip())


def is_lettered_item(line: str) -> bool:
    """Check if line starts with (a), (b), (i), (ii), etc."""
    stripped = line.lstrip()
    return bool(re.match(r'^\([a-z]+\)\s', stripped) or re.match(r'^\([ivx]+\)\s', stripped))


def is_numbered_item(line: str) -> bool:
    """Check if line starts with a number like '1.' or '1.1'."""
    stripped = line.lstrip()
    return bool(re.match(r'^\d+\.', stripped))


def is_trailing_paragraph(line: str, prev_lines: list[str]) -> bool:
    """
    Check if a line is a trailing paragraph that belongs to a prior clause.
    
    Trailing paragraphs:
    - Follow a list of lettered items (a), (b), (c)
    - Start with lowercase or connecting words like "and", "or"
    - Are not themselves list items
    """
    stripped = line.strip()
    if not stripped:
        return False
    
    # If it's a list item itself, it's not trailing
    if is_lettered_item(line) or is_numbered_item(line):
        return False
    
    # If line starts with lowercase or connecting word, likely trailing
    trailing_starters = ['and ', 'or ', 'but ', 'provided ', 'subject ', 'unless ']
    first_word = stripped.split()[0].lower() if stripped.split() else ''
    
    if stripped[0].islower() or first_word in [s.strip() for s in trailing_starters]:
        # Check if recent lines had lettered items
        for prev in reversed(prev_lines[-10:]):
            if is_lettered_item(prev):
                return True
            if prev.strip() == '':
                continue
    
    return False


def add_clause_structure(content: str) -> tuple[str, list[dict]]:
    """
    Add explicit clause numbering and collect clause index.
    
    Handles:
    - Main clause headings (## N. Title)
    - Sub-clauses with explicit numbering (**N.M** text)
    - Lettered items (a), (b) with proper indentation
    - Trailing paragraphs that belong to parent clauses
    - Pandoc's inconsistent indentation (items at column 0 that should be indented)
    
    Returns (modified_content, clause_index)
    """
    lines = content.split('\n')
    result = []
    clause_index = []
    
    # State tracking
    current_main_clause = 0
    current_sub_clause = 0
    in_sub_clause_context = False  # Are we inside a numbered sub-clause?
    in_lettered_list = False  # Are we inside a (a), (b), (c) list?
    sub_clause_indent = 4  # Standard indent for sub-clauses
    letter_list_indent = 8  # Standard indent for lettered items
    last_letter_seen = None  # Track which letter we last saw
    
    # Patterns
    # Matches: "1. Title" or "12. Title" at start of line (main clause candidate)
    main_clause_pattern = re.compile(r'^(\d+)\.\s+(.+)$')
    # Matches: "    1.  Text" - indented numbered item (sub-clause)
    indented_sub_pattern = re.compile(r'^(\s{2,})(\d+)\.\s+(.+)$')
    # Matches lettered items: (a), (b), (i), (ii) etc
    letter_pattern = re.compile(r'^\s*\(([a-z]+|[ivx]+)\)\s+(.+)$', re.IGNORECASE)
    # Annex/Schedule headers
    annex_pattern = re.compile(r'^(Annex|Schedule|Exhibit)\s+(\d+)', re.IGNORECASE)
    # HTML comment (Pandoc artifact)
    html_comment_pattern = re.compile(r'^<!--.*-->$')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        indent = get_line_indent(line)
        
        # === SKIP HTML COMMENTS ===
        if html_comment_pattern.match(stripped):
            i += 1
            continue
        
        # === ANNEX/SCHEDULE HEADERS ===
        if annex_pattern.match(stripped):
            match = annex_pattern.match(stripped)
            annex_type = match.group(1)
            annex_num = match.group(2)
            
            clause_index.append({
                'number': f'{annex_type} {annex_num}',
                'title': stripped,
                'type': 'annex'
            })
            
            result.append(f'[BEGIN EXPLANATION: {stripped}]')
            result.append('')
            result.append('[END EXPLANATION]')
            result.append('')
            result.append(f'## {stripped}')
            in_lettered_list = False
            i += 1
            continue
        
        # === INDENTED SUB-CLAUSE (e.g., "    1.  Text") ===
        if indented_sub_pattern.match(line) and current_main_clause > 0:
            match = indented_sub_pattern.match(line)
            orig_indent = match.group(1)
            sub_num = int(match.group(2))
            sub_text = match.group(3).strip()
            
            current_sub_clause = sub_num
            in_sub_clause_context = True
            in_lettered_list = False
            sub_clause_indent = len(orig_indent)
            
            # Add explicit numbering with proper indent
            full_number = f'{current_main_clause}.{sub_num}'
            result.append(f'{orig_indent}**{full_number}** {sub_text}')
            i += 1
            continue
        
        # === LETTERED ITEMS (a), (b), etc. ===
        letter_match = letter_pattern.match(stripped)
        if letter_match:
            letter = letter_match.group(1).lower()
            letter_text = letter_match.group(2)
            
            # Determine proper indentation
            if in_sub_clause_context:
                proper_indent = ' ' * (sub_clause_indent + 4)
            else:
                proper_indent = ' ' * 8
            
            in_lettered_list = True
            last_letter_seen = letter
            letter_list_indent = len(proper_indent)
            
            result.append(f'{proper_indent}({letter}) {letter_text}')
            i += 1
            continue
        
        # === NON-INDENTED NUMBERED LINE ===
        if main_clause_pattern.match(line) and indent == 0:
            match = main_clause_pattern.match(line)
            clause_num = int(match.group(1))
            clause_text = match.group(2).strip()
            
            if is_main_clause_heading(clause_text, clause_num):
                # This is a real main clause heading
                current_main_clause = clause_num
                current_sub_clause = 0
                in_sub_clause_context = False
                in_lettered_list = False
                
                # Add to index
                clause_index.append({
                    'number': str(clause_num),
                    'title': clause_text,
                    'type': 'main'
                })
                
                # Add explanation placeholder and heading
                result.append(f'[BEGIN EXPLANATION: Clause {clause_num} - {clause_text}]')
                result.append('')
                result.append('[END EXPLANATION]')
                result.append('')
                result.append(f'## {clause_num}. {clause_text}')
            elif current_main_clause > 0:
                # Orphaned sub-clause at root level - renumber under current main
                current_sub_clause += 1
                in_sub_clause_context = True
                in_lettered_list = False
                full_number = f'{current_main_clause}.{current_sub_clause}'
                # Indent it to match other sub-clauses
                result.append(f'    **{full_number}** {clause_text}')
            else:
                # No context, keep as-is
                result.append(line)
            i += 1
            continue
        
        # === BLANK LINES ===
        if not stripped:
            result.append(line)
            i += 1
            continue
        
        # === UNINDENTED CONTENT THAT SHOULD BE INDENTED ===
        # If we're in a lettered list and this line is at column 0,
        # it's probably a continuation or trailing paragraph
        if indent == 0 and stripped and (in_lettered_list or in_sub_clause_context):
            # Check if it's a trailing paragraph (starts with "and", lowercase, etc.)
            first_word = stripped.split()[0].lower() if stripped.split() else ''
            trailing_starters = ['and', 'or', 'but', 'provided', 'subject', 'unless', 'in', 'to']
            
            if stripped[0].islower() or first_word in trailing_starters:
                # This is trailing content - indent appropriately
                if in_lettered_list:
                    proper_indent = ' ' * sub_clause_indent
                else:
                    proper_indent = '    '
                result.append(f'{proper_indent}{stripped}')
                i += 1
                continue
        
        # === CONTINUATION LINES (wrapped text) ===
        # Lines with small indent (< 4) that follow content
        if 0 < indent < 4 and stripped and len(result) > 0:
            # This is likely a wrapped line continuation
            prev_line = result[-1] if result else ''
            if prev_line.strip() and not prev_line.strip().endswith(('.', ';', ':')):
                # Append to previous line
                result[-1] = result[-1].rstrip() + ' ' + stripped
                i += 1
                continue
        
        # === DEFAULT: REGULAR CONTENT ===
        result.append(line)
        i += 1
    
    return '\n'.join(result), clause_index


def create_frontmatter(title: str, clause_index: list[dict]) -> str:
    """Create YAML frontmatter with document metadata and clause index."""
    frontmatter = f'''---
title: "{title}"
type: contract
format: llm-optimized
generated: "{date.today().isoformat()}"
clauses:
'''
    
    for clause in clause_index:
        frontmatter += f'  - number: "{clause["number"]}"\n'
        frontmatter += f'    title: "{clause["title"]}"\n'
        frontmatter += f'    type: {clause["type"]}\n'
    
    frontmatter += '---\n\n'
    
    return frontmatter


def create_clause_index_section(clause_index: list[dict]) -> str:
    """Create a markdown section listing all clauses for quick reference."""
    section = '# Clause Index\n\n'
    section += '| # | Title | Type |\n'
    section += '|---|-------|------|\n'
    
    for clause in clause_index:
        section += f'| {clause["number"]} | {clause["title"]} | {clause["type"]} |\n'
    
    section += '\n---\n\n'
    return section


def format_for_llm(content: str, title: str) -> str:
    """Apply all formatting transformations."""
    # Step 1: Clean Pandoc artifacts
    content = clean_pandoc_artifacts(content)
    
    # Step 2: Add clause structure and collect index
    content, clause_index = add_clause_structure(content)
    
    # Step 3: Create frontmatter
    frontmatter = create_frontmatter(title, clause_index)
    
    # Step 4: Create clause index section
    index_section = create_clause_index_section(clause_index)
    
    # Step 5: Combine
    return frontmatter + index_section + content


def process_file(input_path: str, output_path: str = None) -> None:
    """Process a markdown file for LLM consumption."""
    input_file = Path(input_path)
    
    if not input_file.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)
    
    content = input_file.read_text(encoding='utf-8')
    
    # Default to same filename with -llm suffix
    if output_path:
        output_file = Path(output_path)
    else:
        output_file = input_file.with_stem(input_file.stem + '-llm')
    
    # Use output filename for title (strip -llm suffix if present)
    title_source = output_file.stem
    if title_source.endswith('-llm'):
        title_source = title_source[:-4]
    
    processed = format_for_llm(content, title_source)
    
    output_file.write_text(processed, encoding='utf-8')
    
    print(f"Processed: {input_file}")
    print(f"Output: {output_file}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python format_contract_for_llm.py <input.md> [output.md]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    process_file(input_path, output_path)
