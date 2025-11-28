# Office-Word-MCP-Server Development Guide

## Project Overview

A Model Context Protocol (MCP) server exposing Microsoft Word document manipulation as standardized tools. Built on **FastMCP** (async framework) and **python-docx** (Office Open XML manipulation).

**Key Architecture**: Modular separation of tools → utilities → core functionality.

### Document Content Best Practices

**When adding text to documents:**
- **Default to `add_paragraph`** for inserting new text content
- **Match existing styles**: Inspect the document structure with `get_document_outline` to identify styles used in similar sections
- **Apply appropriate styles**: Use the `style` parameter to match the document's formatting conventions (e.g., 'Normal', 'Body Text', 'Quote')
- **Consistency is key**: New content should blend seamlessly with existing formatting

**After modifying documents (add/delete/edit), ALWAYS verify the result:**
- Use `get_document_outline` or `get_document_text` to confirm changes
- Check: Did new text appear in the correct location?
- Check: Were deletions limited to intended content only?
- Check: Did formatting/styles apply correctly?
- Report the verification results to the user

---

## Critical Architecture Patterns

### 1. **Tool Registration & Async Pattern**
- **Location**: `word_document_server/main.py` (line 330+)
- **Pattern**: All tools are async functions decorated with `@mcp.tool()`, even synchronous operations
- **Logging**: Custom `_logging_tool_decorator` wraps handlers; ALL tool calls auto-logged with request/response
- **Error Handling**: Wrap user-facing strings; never raise unstructured exceptions

```python
# Correct: async wrapper around file operation
@mcp.tool()
async def add_heading(filename: str, text: str, level: int = 1):
    filename = ensure_docx_extension(filename)
    # ... operation
    return "Success message"  # Always return string for user visibility
```

### 2. **Core Functionality Layers**
Three-layer model enforced across all features:
- **Tools** (`tools/*.py`): MCP interface, parameter validation, user error messages
- **Utilities** (`utils/*.py`): Reusable document operations (file I/O, text search, paragraph manipulation)
- **Core** (`core/*.py`): Low-level XML/OOXML manipulation (styles, footnotes, protection, tables)

*Example*: Adding a footnote:
1. **Tool** (`footnote_tools.add_footnote_to_document`) → validates filename
2. **Utility** (`document_utils.find_footnote_references`) → locates target
3. **Core** (`footnotes.add_footnote`) → manipulates XML directly

### 3. **Document State Management**
- **Load-Modify-Save**: Each tool loads doc, modifies in-memory, saves back
  ```python
  doc = Document(filename)
  # ... modifications
  doc.save(filename)
  ```
- **File Writeable Check**: Always call `check_file_writeable(filename)` before modification
- **Extension Handling**: Use `ensure_docx_extension(filename)` to normalize paths

### 4. **python-docx Limitations & Workarounds**
- **No direct XML API**: Use `docx.oxml.*` for advanced features (cell borders, shading, footnote customization)
- **Styles fragile**: Headers/tables fail with undefined styles → `core/styles.py` pre-ensures styles exist
- **Tables**: Copy via `core/tables.copy_table()`; manipulation via cell access (`table.cell(row, col)`)
- **Protected documents**: `msoffcrypto-tool` required for encrypted docs; `core/protection.py` handles

---

## Key Files & Entry Points

| File | Purpose |
|------|---------|
| `main.py` | FastMCP server initialization, tool registration, execute_plan orchestration |
| `tools/*.py` | 8 tool modules: document, content, format, protection, footnote, comment, review, extended |
| `core/*.py` | Styles, protection, footnotes, tables, unprotect (OOXML manipulation) |
| `utils/*.py` | Document utilities (text extraction, structure), extended utils (paragraph lookup, find/replace), file utils |
| `pyproject.toml` | Python 3.11+, depends: python-docx, fastmcp, msoffcrypto-tool, docx2pdf |

---

## Critical Developer Workflows

### Run the Server
```powershell
# Development (stdio transport, default)
python -m word_document_server.main

# HTTP transport (configurable via .env)
$env:MCP_TRANSPORT = "streamable-http"
$env:MCP_PORT = 8000
python -m word_document_server.main
```

### Environment Variables
- `MCP_TRANSPORT`: 'stdio', 'streamable-http', 'sse' (default: 'stdio')
- `MCP_HOST`, `MCP_PORT`, `MCP_PATH`: HTTP binding
- `MCP_DEBUG`: Set to '1' for DEBUG-level logging
- `FASTMCP_LOG_LEVEL`: Controls internal FastMCP verbosity

### Test Against Running Server
```powershell
# Terminal 1: Start server in streamable-http mode
$env:MCP_TRANSPORT = "streamable-http"; python -m word_document_server.main

# Terminal 2: Run test client
python tests/test_local_mcp.py
```

### MCP Config (Claude/Cursor)
Located in `mcp-config.json`. Uses SSE transport with Python venv.

---

## Code Patterns & Conventions

### 1. **String Return Convention**
ALL tools return strings (not dicts/objects). Status/errors always human-readable:
```python
# ✓ Correct
return f"Heading '{text}' added to {filename}"
return f"Cannot modify document: {error_message}"

# ✗ Wrong (breaks MCP protocol for string-only tools)
return {"success": True, "filename": filename}
```

### 2. **Parameter Naming & Validation**
- `filename`: Path to document (auto-adds `.docx` extension)
- File paths relative to cwd unless absolute
- Validate types early; convert strings to int for indices/levels
```python
try:
    level = int(level)
except (ValueError, TypeError):
    return "Invalid parameter: level must be an integer"
```

### 3. **Feature: Multi-Phase Orchestration**
`execute_plan` tool supports concurrent tool execution across phases:
```json
{
  "plan": [
    {
      "phase": "setup",
      "calls": [
        {"tool": "create_document", "args": {"filename": "doc.docx"}, "id": "doc1"},
        {"tool": "add_heading", "args": {"filename": {"$ref": "doc1"}, "text": "Title"}}
      ]
    }
  ]
}
```
Phases run sequentially; calls within phases run concurrently. `{"$ref": "id"}` resolves prior results.

### 4. **Footnote/Endnote Implementation**
- Stored in separate XML streams (`footnotes.xml`, `endnotes.xml`)
- `core/footnotes.py`: Adds footnote, maintains ID integrity, finds references
- Style customization via `customize_footnote_style()` modifies format symbols
- Conversion: `convert_footnotes_to_endnotes()` moves + rebinds references

### 5. **Comment Extraction with Status Tracking**
- Comments stored in separate `comments.xml` part
- Comment status (active/resolved) stored in `commentsExtended.xml` (Word 2012+)
- **Linking mechanism**: `w14:paraId` in comments.xml matched with `w15:paraId` in commentsExtended.xml
- `core/comments.py` functions:
  - `extract_all_comments()`: Extracts comments + auto-merges status from commentsExtended
  - `extract_comment_status_map()`: Builds paraId → status mapping from commentsExtended.xml
  - `merge_comment_status()`: Links status info to comment dictionaries
- Each comment object includes three status fields:
  - `status`: "active" or "resolved"
  - `is_resolved`: boolean (True if resolved)
  - `done_flag`: integer (0=active, 1=resolved, from w15:done)
- For documents without commentsExtended (older Word), defaults to status='active'
- `utils/document_utils.extract_comments()`: Parses comment ranges + metadata
- Support for author filtering, paragraph association

---

## Project-Specific Conventions

### Style Management
- Define styles via `core/styles.py` before using (headers, tables auto-initialized)
- Fallback to direct formatting if style application fails (Heading → Pt(16) bold)

### Protected/Encrypted Docs
- Pre-decrypt with `msoffcrypto-tool` before modifying
- `unprotect.py`: Remove restrictions; `protection.py`: Add/verify protections

### Extended Tools (Activation)
Some tools in `tools/extended_document_tools.py` require tool activation in `main.py`:
- Search `@mcp.tool()` decorators to see which are active
- Commonly wrapped tools: text formatting, table cell operations, paragraph replacement

### Building/Packaging
```bash
hatch build        # Wheel + sdist
python -m pip install -e .  # Editable install for development
```

---

## Common Implementation Tasks

**Adding a new tool**:
1. Create function in `tools/new_feature_tools.py` (async, returns string)
2. Add utility in `utils/new_feature_utils.py` if complex
3. Register in `main.py` with `@mcp.tool()` decorator
4. Test via `test_local_mcp.py` or direct server call

**Modifying document structure**:
1. Use `docx.Document()` for high-level ops (paragraphs, tables)
2. Drop to `docx.oxml.*` for low-level XML (cell properties, custom formatting)
3. Always save with `doc.save(filename)` at the end

**Handling special formats** (bold, colors, borders):
- Text: Use `run.bold`, `run.font.color.rgb`
- Cells: Use `set_cell_border()`, `parse_xml()` for complex XML
- Tables: Pre-apply header styles via `apply_table_style()`

---

## Dependencies & Compatibility

- **Python**: 3.11+ required (f-strings, type hints)
- **python-docx**: 1.1.2+ (Office Open XML manipulation)
- **FastMCP**: 2.8.1+ (async MCP framework; requires patches in `patches.py`)
- **msoffcrypto-tool**: 5.4.2+ (document decryption)
- **docx2pdf**: 0.1.8 (Word → PDF conversion)

FastMCP patches applied in `word_document_server/patches.py` before import to handle protocol quirks.

---

## Debug Workflow

1. **Enable logging**: Set `MCP_DEBUG=1` or modify `setup_logging()` in `main.py`
2. **Inspect tool calls**: Check `word_document_server.tools` logger (auto-captures requests/responses)
3. **Manual testing**: Use `tests/test_local_mcp.py` with HTTP transport
4. **Document inspection**: Load saved `.docx` in Word or `zipfile` to inspect `document.xml`

---

## Testing Notes

- Unit tests minimal; integration testing via MCP protocol invocation
- Test client (`tests/test_local_mcp.py`) sends JSON-RPC to running server
- Create test documents in repo root (`test.docx`, `foo.docx`) for safe experimentation
