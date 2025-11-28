# Numbering Tools Documentation

## Overview

The `numbering_tools.py` module provides three powerful tools for analyzing the numbering structure of Word documents using the effilocal NumberingInspector.

## Tools

### 1. analyze_document_numbering

Provides detailed analysis of numbered paragraphs in a document.

**Parameters:**
- `filename` (str): Path to the Word document
- `debug` (bool, optional): Include additional debug information
- `include_non_numbered` (bool, optional): Include paragraphs without numbering

**Returns:**
Formatted string with detailed information about:
- Total paragraphs and numbered paragraphs count
- For each numbered paragraph:
  - Rendered number (e.g., "1.1.1")
  - Hierarchy level
  - Numbering format
  - NumID and AbstractNumID
  - Paragraph text (truncated)

**Example Usage:**
```python
result = await analyze_document_numbering('document.docx', debug=False)
print(result)
```

### 2. get_numbering_summary

Provides a high-level statistical summary of numbering usage.

**Parameters:**
- `filename` (str): Path to the Word document

**Returns:**
Summary statistics including:
- Total and numbered paragraph counts
- Unique numbering styles count
- Breakdown of numbering formats used
- Hierarchy levels and their usage counts

**Example Usage:**
```python
result = await get_numbering_summary('document.docx')
print(result)
```

### 3. extract_outline_structure

Extracts a hierarchical outline view based on document numbering.

**Parameters:**
- `filename` (str): Path to the Word document
- `max_level` (int, optional): Maximum hierarchy depth to include (None for all)

**Returns:**
Hierarchical outline with:
- Indentation based on hierarchy level
- Rendered numbers
- Paragraph text (truncated for readability)

**Example Usage:**
```python
result = await extract_outline_structure('document.docx', max_level=2)
print(result)
```

## Features

- **effilocal Integration**: Uses the sophisticated NumberingInspector from effilocal for accurate analysis
- **Multiple Formats**: Supports decimal, roman numerals, bullets, and other Word numbering formats
- **Hierarchy Tracking**: Correctly identifies and displays multi-level numbering structures
- **Error Handling**: Gracefully handles missing files and documents without numbering
- **Optional Import**: Works with or without effilocal installed (provides helpful error message)

## Testing

Comprehensive test suite in `tests/test_numbering_analysis.py` with 12 tests covering:
- Analysis of decimal and roman numeral documents
- Summary generation
- Outline extraction with level limits
- Error handling for missing files
- Debug mode functionality
- Comparison of different numbering formats

All tests pass successfully.

## MCP Server Integration

The tools are registered as MCP tools in `main.py` and are available via:
- `analyze_document_numbering`
- `get_numbering_summary`
- `extract_outline_structure`

These can be called through the MCP protocol for integration with Claude and other AI tools.

## Example Output

### Numbering Summary
```
Numbering Summary for document.docx
================================================================================

Total paragraphs: 5
Numbered paragraphs: 5
Unique numbering styles: 1

Numbering Formats Used:
  unknown: 5 paragraph(s)

Hierarchy Levels Used:
  Level 0: 2 paragraph(s)
  Level 1: 2 paragraph(s)
  Level 2: 1 paragraph(s)
```

### Document Outline
```
Document Outline for document.docx
================================================================================

1. Section 1
  1.1 Section 1.1
    1.1.1 Section 1.1.1
  1.2 Section 1.2
2. Section 2
```

## Dependencies

- `effilocal.doc.numbering_inspector`: Core numbering analysis engine
- `word_document_server.utils.file_utils`: File validation utilities
- `pathlib`: Path handling
- `os`: File system operations

The tools gracefully handle cases where effilocal is not available, returning a helpful error message.
