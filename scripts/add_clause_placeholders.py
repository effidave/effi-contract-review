#!/usr/bin/env python3
"""
Add clause explanation placeholders above numbered clauses in markdown files.

Inserts HTML comment placeholders before each numbered clause heading to allow
for explanatory annotations to be added later.
"""

import re
import sys
from pathlib import Path


def is_definition_item(title: str) -> bool:
    """
    Check if the line looks like a definition item rather than a clause heading.
    
    Definition items typically start with bold terms like:
    - **Agreement**: means...
    - **Customer Data**: the data...
    - **Confidential Information** has the meaning...
    """
    # Starts with bold marker - these are definition terms
    if title.startswith('**'):
        return True
    # Contains "means" early on (definition language)
    if 'means' in title.lower()[:50]:
        return True
    return False


def is_clause_heading(title: str) -> bool:
    """
    Check if the title looks like a proper clause heading.
    
    Clause headings are typically short, capitalized titles like:
    - Interpretation
    - Licence terms
    - Data protection
    - Term and termination
    
    NOT full sentences or paragraphs like:
    - "The Customer shall not:"
    - "The rights provided under this Agreement are granted..."
    """
    # Skip definition items
    if is_definition_item(title):
        return False
    
    # Get just the first line, stripped
    first_part = title.split('\n')[0].strip()
    
    # Skip items that start with lowercase
    if first_part and first_part[0].islower():
        return False
    
    # Clause headings are typically short - 2-4 words, < 40 chars
    # If it's longer, it's probably a paragraph start, not a heading
    if len(first_part) > 40:
        return False
    
    # Clause headings typically don't end with ":"
    if first_part.endswith(':'):
        return False
    
    # Clause headings don't start with "The " (sentence start)
    if first_part.startswith('The '):
        return False
    
    return True


def add_clause_placeholders(content: str) -> str:
    """
    Insert [BEGIN/END EXPLANATION] placeholder blocks above each numbered clause.
    
    Uses LLM-friendly markers that are visible content, not hidden comments.
    Only adds placeholders for actual clause headings, not definition lists
    or numbered paragraphs within clauses.
    """
    lines = content.split('\n')
    result = []
    
    # Pattern for main numbered clauses: "1.  Title" or "10. Title"
    # Can have 1+ spaces after the period
    main_clause_pattern = re.compile(r'^(\d+)\.\s+(.+)$')
    
    # Pattern for Annex/Schedule headers
    annex_pattern = re.compile(r'^(Annex|Schedule|Exhibit)\s+\d+', re.IGNORECASE)
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for main clause (e.g., "1.  Interpretation")
        if main_clause_pattern.match(line):
            match = main_clause_pattern.match(line)
            clause_num = match.group(1)
            clause_title = match.group(2).strip()
            
            # Only add placeholder if it's a real clause heading, not a definition
            if is_clause_heading(clause_title):
                result.append(f'[BEGIN EXPLANATION: Clause {clause_num} - {clause_title}]')
                result.append('')
                result.append('[END EXPLANATION]')
                result.append('')
            
            result.append(line)
        
        # Check for Annex/Schedule headers
        elif annex_pattern.match(line.strip()):
            header = line.strip()
            result.append(f'[BEGIN EXPLANATION: {header}]')
            result.append('')
            result.append('[END EXPLANATION]')
            result.append('')
            result.append(line)
        
        else:
            result.append(line)
        
        i += 1
    
    return '\n'.join(result)


def process_file(input_path: str, output_path: str = None) -> None:
    """Process a markdown file and add clause placeholders."""
    input_file = Path(input_path)
    
    if not input_file.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)
    
    content = input_file.read_text(encoding='utf-8')
    processed = add_clause_placeholders(content)
    
    # Default to overwriting the same file, or write to output_path
    output_file = Path(output_path) if output_path else input_file
    output_file.write_text(processed, encoding='utf-8')
    
    print(f"Processed: {input_file}")
    print(f"Output: {output_file}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python add_clause_placeholders.py <input.md> [output.md]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    process_file(input_path, output_path)
