"""
Fix accidental line breaks in PDF-to-text conversions.

Heuristics:
1. Merge lines that end mid-sentence (no terminal punctuation, lowercase continuation)
2. Preserve numbered/bulleted list structure
3. Preserve section headers (ALL CAPS, "Section X", etc.)
4. Detect and preserve table-like structures
5. Merge split list items (e.g., "i." followed by text on next line)
"""

import re
import sys
from pathlib import Path


def is_section_header(line: str) -> bool:
    """Check if line is a section header."""
    line = line.strip()
    if not line:
        return False
    # "Section X –" pattern
    if re.match(r'^Section\s+\d+', line, re.IGNORECASE):
        return True
    # All caps headers (but not single words or acronyms)
    if len(line) > 10 and line.isupper():
        return True
    return False


def is_list_item_start(line: str) -> bool:
    """Check if line starts a list item."""
    line = line.strip()
    # Numbered: 1., 1.1, a., i., ii., etc.
    if re.match(r'^(\d+\.|\d+\.\d+|[a-z]\.|\([a-z]\)|[ivx]+\.|[ivx]+\))\s', line, re.IGNORECASE):
        return True
    # Bullet points
    if line.startswith(('•', '-', '*', '–', '—')):
        return True
    return False


def is_roman_numeral_continuation(line: str) -> bool:
    """Check if line is a roman numeral list continuation like 'ii.' or 'iii.'"""
    return bool(re.match(r'^[ivx]+\.\s', line.strip(), re.IGNORECASE))


def is_letter_continuation(line: str) -> bool:
    """Check if line continues with letter enumeration."""
    return bool(re.match(r'^[a-z]\.\s', line.strip()))


def ends_with_sentence_terminal(line: str) -> bool:
    """Check if line ends with sentence-ending punctuation."""
    line = line.rstrip()
    if not line:
        return True
    # Ends with period, question mark, exclamation, or colon
    return line[-1] in '.?!:;'


def starts_with_lowercase(line: str) -> bool:
    """Check if line starts with lowercase letter."""
    line = line.strip()
    if not line:
        return False
    return line[0].islower()


def is_percentage_line(line: str) -> bool:
    """Check if line is primarily a percentage value (table-like)."""
    line = line.strip()
    return bool(re.match(r'^[\d]+%$', line))


def is_table_row(line: str) -> bool:
    """Check if line looks like a table row."""
    line = line.strip()
    # Multiple percentage values or currency values
    if re.search(r'(\d+%\s+){2,}', line):
        return True
    if re.search(r'(£[\d,]+\s+){2,}', line):
        return True
    # Tab-separated or heavily spaced values
    if '\t' in line and len(line.split('\t')) >= 3:
        return True
    return False


def is_form_field(line: str) -> bool:
    """Check if line is a form field like 'Yes No' checkboxes."""
    line = line.strip()
    if line == 'Yes No':
        return True
    if re.match(r'^(Yes|No)\s+(Yes|No)$', line):
        return True
    return False


def looks_like_continuation(prev_line: str, curr_line: str) -> bool:
    """Determine if curr_line should be merged with prev_line."""
    prev = prev_line.strip()
    curr = curr_line.strip()
    
    if not prev or not curr:
        return False
    
    # Don't merge section headers
    if is_section_header(curr):
        return False
    
    # Don't merge new list items
    if is_list_item_start(curr):
        return False
    
    # Don't merge form fields
    if is_form_field(curr):
        return False
    
    # Don't merge table rows
    if is_table_row(curr):
        return False
    
    # Don't merge standalone percentages
    if is_percentage_line(curr):
        return False
    
    # Merge if previous line doesn't end with terminal punctuation
    # and current line starts with lowercase
    if not ends_with_sentence_terminal(prev) and starts_with_lowercase(curr):
        return True
    
    # Merge hyphenated words split across lines
    if prev.endswith('-') and curr[0].islower():
        return True
    
    # Merge if prev ends with common continuation patterns
    continuation_endings = ('the', 'a', 'an', 'and', 'or', 'of', 'to', 'for', 'in', 'on', 'at', 'by', 'with', 'that', 'which', 'who')
    prev_words = prev.lower().split()
    if prev_words and prev_words[-1] in continuation_endings:
        return True
    
    return False


def merge_split_list_items(lines: list[str]) -> list[str]:
    """Merge list items that were split across lines."""
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check for standalone roman numerals or letters that should join next line
        if re.match(r'^[ivx]+\.$', stripped, re.IGNORECASE) or re.match(r'^[a-z]\.$', stripped):
            # This is just a numeral, merge with next non-empty line
            if i + 1 < len(lines) and lines[i + 1].strip():
                result.append(stripped + ' ' + lines[i + 1].strip())
                i += 2
                continue
        
        result.append(line)
        i += 1
    
    return result


def fix_linebreaks(text: str) -> str:
    """Fix accidental line breaks in the text."""
    lines = text.split('\n')
    
    # First pass: merge standalone list markers
    lines = merge_split_list_items(lines)
    
    # Second pass: merge continuation lines
    result = []
    i = 0
    
    while i < len(lines):
        current = lines[i]
        
        # Collect lines that should be merged
        merged = current.rstrip()
        
        while i + 1 < len(lines) and looks_like_continuation(merged, lines[i + 1]):
            i += 1
            next_line = lines[i].strip()
            
            # Handle hyphenated words
            if merged.endswith('-'):
                merged = merged[:-1] + next_line
            else:
                merged = merged + ' ' + next_line
        
        result.append(merged)
        i += 1
    
    # Third pass: clean up excessive blank lines
    final = []
    blank_count = 0
    for line in result:
        if not line.strip():
            blank_count += 1
            if blank_count <= 2:  # Allow max 2 consecutive blank lines
                final.append(line)
        else:
            blank_count = 0
            final.append(line)
    
    return '\n'.join(final)


def process_file(input_path: str, output_path: str = None):
    """Process a file and fix line breaks."""
    path = Path(input_path)
    
    if not path.exists():
        print(f"Error: File not found: {input_path}")
        return
    
    text = path.read_text(encoding='utf-8')
    fixed = fix_linebreaks(text)
    
    if output_path:
        out = Path(output_path)
    else:
        out = path.with_stem(path.stem + '_fixed')
    
    out.write_text(fixed, encoding='utf-8')
    print(f"Fixed: {path} -> {out}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fix_pdf_linebreaks.py <input_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    process_file(input_file, output_file)
