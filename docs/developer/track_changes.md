# Track Changes Implementation Guide

This document explains how the effi-contract-review system handles Microsoft Word track changes (insertions and deletions) in `.docx` documents.

## Overview

Word documents with track changes contain revision markup that standard `python-docx` paragraph handling doesn't fully support. Specifically:

- **Insertions** (`w:ins` elements): Text added by a reviewer, containing `w:t` text elements
- **Deletions** (`w:del` elements): Text removed by a reviewer, containing `w:delText` elements

The standard `paragraph.text` property in python-docx excludes text inside `w:ins` elements, which means inserted content wouldn't appear in the extracted text.

## The Problem

When processing a paragraph like:

```xml
<w:p>
  <w:r><w:t>The </w:t></w:r>
  <w:ins w:author="John"><w:r><w:t>quick</w:t></w:r></w:ins>
  <w:del w:author="Jane"><w:r><w:delText>brown </w:delText></w:r></w:del>
  <w:r><w:t> fox</w:t></w:r>
</w:p>
```

- `paragraph.text` returns: `"The  fox"` (missing "quick", has double space)
- **We need**: `"The quick fox"` (visible text only)

## Solution: Option A Data Model

We implemented **Option A** - a data model where:

1. **`text` field**: Contains only **visible** text (normal runs + insertions, NO deletions)
2. **`runs` field**: Contains all runs including deletions, with:
   - Normal/insert runs: `start`/`end` positions map to the visible text
   - Delete runs: **Zero-width** (`start == end`) with `deleted_text` field

### Example Output

```json
{
  "text": "The quick fox",
  "runs": [
    { "start": 0, "end": 4, "formats": [] },
    { "start": 4, "end": 9, "formats": ["insert"], "author": "John" },
    { "start": 9, "end": 9, "formats": ["delete"], "deleted_text": "brown ", "author": "Jane" },
    { "start": 9, "end": 13, "formats": [] }
  ]
}
```

This model ensures:
- Text is always what the user sees (no deleted content cluttering the text)
- Deletions are still tracked with their position and original content
- The editor can render strikethrough for deletions at the correct position

## Key Modules

### `effilocal/doc/amended_paragraph.py`

The core class that wraps python-docx paragraphs to handle track changes:

```python
from effilocal.doc.amended_paragraph import AmendedParagraph, iter_amended_paragraphs

# Wrap a single paragraph
amended = AmendedParagraph(paragraph)
visible_text = amended.amended_text  # "The quick fox"
runs = amended.amended_runs          # List of run dicts with positions

# Iterate all paragraphs in a document
for amended in iter_amended_paragraphs(doc):
    print(amended.amended_text)
```

#### Key Properties

| Property | Description |
|----------|-------------|
| `amended_text` | Visible text only (includes w:ins, excludes w:delText) |
| `amended_runs` | List of run dicts with start/end, formats, author, date |

#### Run Dictionary Structure

```python
{
    'start': int,           # Position in amended_text
    'end': int,             # Position in amended_text (== start for deletes)
    'formats': List[str],   # ['bold', 'italic', 'insert', 'delete', etc.]
    'author': str | None,   # Revision author (for insert/delete)
    'date': str | None,     # Revision date ISO format
    'deleted_text': str,    # Only present for delete runs
}
```

### `effilocal/doc/runs.py`

Lower-level run extraction with formatting support:

```python
from effilocal.doc.runs import add_runs_to_block

# Add runs to an existing block dict
block = {'text': 'Some text', ...}
add_runs_to_block(block, paragraph)
# block now has 'runs' key with Option A model
```

### Integration Points

#### `effilocal/doc/pipeline.py`

The `AnalysisPipeline.process_paragraph()` method automatically:
1. Creates an `AmendedParagraph` wrapper
2. Uses `amended_text` for the block's text field
3. Adds `runs` field with Option A model

```python
def process_paragraph(self, paragraph: Paragraph) -> Block | None:
    amended = AmendedParagraph(paragraph)
    
    build_result, next_section_id = build_paragraph_block(
        paragraph,
        self._current_section_id,
        hash_provider=self._hash_tracker.next_hash,
        amended=amended,  # Pass amended paragraph
    )
    
    # Add runs with Option A model
    block['runs'] = amended.amended_runs
```

#### `effilocal/doc/paragraphs.py`

The `build_paragraph_block()` function accepts an optional `amended` parameter:

```python
def build_paragraph_block(
    paragraph: Paragraph,
    current_section_id: str,
    *,
    hash_provider: Callable[[str], str],
    amended: Optional[AmendedParagraph] = None,  # NEW
) -> tuple[dict[str, Any] | ParagraphBlock | None, str]:
    # Uses amended.amended_text if provided
    if amended is not None:
        text = amended.amended_text.strip()
    else:
        text = paragraph.text.strip()
```

#### `effilocal/doc/tables.py`

Table cells also use `AmendedParagraph` for track changes support:

```python
def _get_amended_cell_content(cell) -> tuple[str, List[Dict[str, Any]]]:
    """Get amended text and runs for all paragraphs in a table cell."""
    for para in cell.paragraphs:
        amended = AmendedParagraph(para)
        # Combine text and adjust run positions...
```

## Revision Management

For accepting/rejecting revisions programmatically, see:

- **`effilocal/doc/revisions.py`**: Core extraction and accept/reject logic
- **`effilocal/mcp_server/tools/manage_revisions.py`**: MCP tool interface

```python
from effilocal.doc.revisions import (
    extract_revisions,
    accept_revision,
    reject_revision,
    accept_all_revisions,
    reject_all_revisions,
)

# Get all revisions
revisions = extract_revisions(doc)

# Accept a specific revision
accept_revision(doc, revision_id="1")

# Accept all
count = accept_all_revisions(doc)
doc.save(path)
```

## Editor Integration

The VS Code extension's BlockEditor (`extension/src/webview/editor.js`) renders track changes using the `runs` field:

```javascript
_renderFormattedText(text, runs) {
    // For each run, wrap in appropriate elements
    if (formats.includes('insert')) {
        html += `<ins class="revision-insert" ...>${escaped}</ins>`;
    } else if (formats.includes('delete')) {
        // Zero-width delete: render deleted_text in strikethrough
        html += `<del class="revision-delete" ...>${run.deleted_text}</del>`;
    }
}
```

## Testing

Run the track changes test suite:

```powershell
cd tests
..\.venv\Scripts\python.exe -m pytest test_amended_paragraph.py test_runs_extraction.py test_revisions.py test_manage_revisions.py -v
```

### Test Files

| File | Tests | Description |
|------|-------|-------------|
| `test_amended_paragraph.py` | 18 | AmendedParagraph class and Option A model |
| `test_runs_extraction.py` | 16 | Run extraction with formatting |
| `test_revisions.py` | 27 | Revision extraction and accept/reject |
| `test_manage_revisions.py` | 20 | MCP tool interface |

## XML Namespaces

Track changes use these Word XML namespaces:

```python
from docx.oxml.ns import qn

# Main namespace
qn('w:ins')      # Insertion element
qn('w:del')      # Deletion element
qn('w:t')        # Normal text
qn('w:delText')  # Deleted text

# Attributes
qn('w:author')   # Revision author
qn('w:date')     # Revision date
qn('w:id')       # Revision ID
```

## Common Patterns

### Checking for Track Changes

```python
def has_track_changes(doc: Document) -> bool:
    """Check if document has any track changes."""
    body = doc.element.body
    return (
        body.find('.//' + qn('w:ins')) is not None or
        body.find('.//' + qn('w:del')) is not None
    )
```

### Getting Revision Statistics

```python
from effilocal.doc.revisions import extract_revisions

revisions = extract_revisions(doc)
insertions = [r for r in revisions if r['type'] == 'insertion']
deletions = [r for r in revisions if r['type'] == 'deletion']
print(f"Found {len(insertions)} insertions, {len(deletions)} deletions")
```

### Processing with Track Changes Awareness

```python
from effilocal.doc.amended_paragraph import iter_amended_paragraphs

for amended in iter_amended_paragraphs(doc):
    # Text without deleted content
    text = amended.amended_text
    
    # Check for revisions
    runs = amended.amended_runs
    has_insertions = any('insert' in r.get('formats', []) for r in runs)
    has_deletions = any('delete' in r.get('formats', []) for r in runs)
    
    if has_insertions or has_deletions:
        print(f"Paragraph has revisions: {text[:50]}...")
```

## Future Considerations

1. **Editor updates for zero-width deletes**: The editor currently handles delete runs, but may need refinement for edge cases with adjacent deletions.

2. **Move tracking**: Word tracks text moves as paired delete+insert. Currently treated as separate revisions.

3. **Comment threading**: Comments can have replies and status (resolved/active). See `effilocal/mcp_server/core/comments.py` for status extraction.
