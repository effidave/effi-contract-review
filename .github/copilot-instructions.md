# Office-Word-MCP-Server Development Guide

## Project Overview

A Model Context Protocol (MCP) server exposing Microsoft Word document manipulation as standardized tools. Built on **FastMCP** (async framework) and **python-docx** (Office Open XML manipulation).

**Key Architecture**: Pristine upstream + override pattern.
- `word_document_server/` - Pristine upstream dependency (unmodified)
- `effilocal/mcp_server/` - Override layer with customizations
  - Import from upstream → selectively override → add contract-specific features
  - Three-layer model: tools → utilities → core functionality

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
- **Location**: `effilocal/mcp_server/main.py` (pristine upstream in `word_document_server/main.py`)
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
Three-layer model enforced across all features (primarily in upstream):
- **Tools** (`tools/*.py`): MCP interface, parameter validation, user error messages
- **Utilities** (`utils/*.py`): Reusable document operations (file I/O, text search, paragraph manipulation)
- **Core** (`core/*.py`): Low-level XML/OOXML manipulation (styles, footnotes, protection, tables)

*Example*: Adding a footnote (upstream):
1. **Tool** (`word_document_server/tools/footnote_tools.add_footnote_to_document`) → validates filename
2. **Utility** (`word_document_server/utils/document_utils.find_footnote_references`) → locates target
3. **Core** (`word_document_server/core/footnotes.add_footnote`) → manipulates XML directly

*Example*: effilocal override (comments with status):
1. **Tool** (`effilocal/mcp_server/tools/comment_tools.get_all_comments`) → MCP interface
2. **Core** (`effilocal/mcp_server/core/comments.extract_all_comments`) → Extends upstream, adds status tracking

Note: effilocal selectively implements layers - only overrides/extends what's needed, relies on upstream for rest.

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

**effilocal/mcp_server/ (Override Layer):**
| File | Purpose |
|------|---------||
| `main.py` | FastMCP server entry point, ~60 tool registrations |
| `tools/content_tools.py` | EXTENDED: add_heading with color, clause-based insertion |
| `tools/comment_tools.py` | OVERRIDDEN: Comment extraction with status tracking |
| `tools/attachment_tools.py` | NEW: Schedule/annex/exhibit insertion with para IDs |
| `tools/numbering_tools.py` | NEW: NumberingInspector for clause analysis |
| `tools/document_tools.py` | EXTENDED: save_document_as_markdown |
| `tools/format_tools.py` | EXTENDED: Background highlighting |
| `utils/document_utils.py` | EXTENDED: find_and_replace_text with whole_word_only, dual signature |
| `utils/hash.py` | NEW: SHA-256 utilities |
| `core/comments.py` | OVERRIDDEN: Status extraction from commentsExtended.xml |

**word_document_server/ (Pristine Upstream):**
- All core functionality: document creation, paragraphs, tables, styles, footnotes, protection
- Unmodified - sync with https://github.com/GongRzhe/Office-Word-MCP-Server

**Configuration:**
| File | Purpose |
|------|---------||
| `pyproject.toml` | Python 3.11+, two entry points: word_mcp_server (upstream) and effilocal_mcp_server (custom) |
| `mcp-config.json` | VS Code MCP client config pointing to effilocal server via stdio |

---

## Critical Developer Workflows

### Run the Server
```powershell
# Development (stdio transport, default)
python -m effilocal.mcp_server.main

# HTTP transport (configurable via .env)
$env:MCP_TRANSPORT = "streamable-http"
$env:MCP_PORT = 8000
python -m effilocal.mcp_server.main
```

### Environment Variables
- `MCP_TRANSPORT`: 'stdio', 'streamable-http', 'sse' (default: 'stdio')
- `MCP_HOST`, `MCP_PORT`, `MCP_PATH`: HTTP binding
- `MCP_DEBUG`: Set to '1' for DEBUG-level logging
- `FASTMCP_LOG_LEVEL`: Controls internal FastMCP verbosity

### Test Against Running Server
```powershell
# Terminal 1: Start server in streamable-http mode
$env:MCP_TRANSPORT = "streamable-http"; python -m effilocal.mcp_server.main

# Terminal 2: Run test client
python tests/test_local_mcp.py
```

### MCP Config (VS Code/Copilot)
Located in `mcp-config.json`. Uses **stdio transport** with project Python venv.
- Server: `effilocal-document-server`
- Command: `.venv\Scripts\python.exe -m effilocal.mcp_server.main`
- Transport: stdio (MCP_TRANSPORT=stdio)
- VS Code acts as the MCP client, communicating via stdio

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
- `effilocal/mcp_server/core/comments.py` functions (OVERRIDDEN from upstream):
  - `extract_all_comments()`: Extracts comments + auto-merges status from commentsExtended
  - `extract_comment_data()`: Parses individual comment with para_id, status, is_resolved fields
  - `extract_comment_status_map()`: Builds paraId → status mapping from commentsExtended.xml
  - `merge_comment_status()`: Links status info to comment dictionaries
- Each comment object includes three status fields:
  - `status`: "active" or "resolved"
  - `is_resolved`: boolean (True if resolved)
  - `done_flag`: integer (0=active, 1=resolved, from w15:done)
- For documents without commentsExtended (older Word), defaults to status='active'
- Support for author filtering (`get_comments_by_author`), paragraph association

---

## Project-Specific Conventions

### Style Management
- Define styles via `core/styles.py` before using (headers, tables auto-initialized)
- Fallback to direct formatting if style application fails (Heading → Pt(16) bold)

### Protected/Encrypted Docs
- Pre-decrypt with `msoffcrypto-tool` before modifying
- `unprotect.py`: Remove restrictions; `protection.py`: Add/verify protections

### Override Pattern
effilocal uses selective override pattern:
- Import upstream tools: `from word_document_server.tools.content_tools import add_paragraph`
- Override specific functions: Define same-named async function in effilocal
- Add new tools: Create in effilocal/mcp_server/tools/ with `@mcp.tool()` decorator
- All tools registered in `effilocal/mcp_server/main.py`

### Contract-Specific Features (effilocal)

#### **Clause-Based Operations**
Tools for inserting content relative to specific clause numbers in contracts:

**`add_paragraph_after_clause(filename, clause_number, text, style, inherit_numbering)`**
- Locates clauses by their rendered number (e.g., "1.2.3", "5.1", "7(a)")
- Uses `NumberingInspector` from effilocal package to analyze document numbering
- Inserts new paragraph immediately after the target clause
- `inherit_numbering=True`: Creates sibling clause at same level (inherits numId and ilvl)
- `inherit_numbering=False`: Creates unnumbered paragraph after the clause
- Returns custom paragraph ID (UUID) for tracking inserted content

**`add_paragraphs_after_clause(filename, clause_number, paragraphs, inherit_numbering)`**
- Bulk version - inserts multiple paragraphs after a clause
- Each paragraph can have its own text and style
- Maintains hierarchical numbering if `inherit_numbering=True`

**Implementation Details**:
- Uses `effilocal.doc.numbering_inspector.NumberingInspector` to parse numbering.xml
- Matches clause numbers against rendered paragraph numbers
- Handles complex numbering formats (multi-level, legal style, lettered)
- Tags inserted paragraphs with `add_custom_para_id()` for tracking

#### **Attachment Insertion**
- **`add_custom_para_id(paragraph_element)`**: Tags paragraphs with UUIDs in custom XML properties
- Used for tracking schedules, annexes, exhibits inserted into contracts
- Returns UUID for reference in external systems

#### **Enhanced Search/Replace**
- **`whole_word_only`** parameter: Only match complete words (uses regex `\b` boundaries)
- **Split-run detection**: Identifies text spanning multiple formatting runs
- **Detailed output**: Before/After snippets, location info, replacement count
- **Dual signature**: Accepts Document object (tests) or filename string (tools)

#### **Comment Status Tracking**
- Extracts active/resolved status from commentsExtended.xml (Word 2012+)
- Links comments to status via `w14:paraId` / `w15:paraId` matching
- Returns structured comment data with `status`, `is_resolved`, `done_flag` fields

#### **UUID Embedding & Block Identity (Sprint 1)**
Block UUIDs are embedded directly into .docx documents for persistent tracking:

**UUID Embedding** (`effilocal/doc/uuid_embedding.py`):
- **`embed_block_uuids(doc, blocks)`**: Wraps paragraphs in SDT content controls with UUID tags
- **`extract_block_uuids(doc)`**: Extracts UUID → paragraph index mapping from document
- **`remove_all_uuid_controls(doc)`**: Strips effi SDTs while preserving content
- Tag format: `<w:tag w:val="effi:block:<uuid>"/>`
- UUIDs survive Word save/close/reopen cycles

**Content Hash Fallback** (`effilocal/doc/content_hash.py`):
- **`match_blocks_by_hash(old_blocks, new_blocks)`**: Three-phase matching:
  1. UUID match (from embedded content controls)
  2. Hash match (SHA-256 of normalized text)
  3. Position match (proximity heuristics)
- Returns `MatchResult` with matched pairs and unmatched lists

**Git Integration** (`effilocal/util/git_ops.py`):
- **`auto_commit(repo, message, files)`**: Stage and commit if changes exist
- **`generate_commit_message(action, details)`**: Format: `[effi] <action>: <summary>`
- **`get_file_history(repo, file)`**: Retrieve commit history for a file
- Supports checkpoint commits for explicit save points

**Analysis with UUID Preservation** (`effilocal/flows/analyze_doc.py`):
- Re-analysis extracts embedded UUIDs and matches to previous blocks
- Emits `analysis_delta.json` tracking matched/new/deleted/modified blocks
- Use `preserve_uuids=True` (default) for incremental analysis

**Save Flow** (`effilocal/flows/save_doc.py`):
- **`save_with_uuids(docx_path, blocks_path)`**: Embed UUIDs and optionally git commit
- **`create_checkpoint(docx_path, note)`**: Create named checkpoint commit

### Building/Packaging
```bash
hatch build        # Wheel + sdist
python -m pip install -e .  # Editable install for development
```

---

## Common Implementation Tasks

**Adding a new tool**:
1. Determine if it's NEW (effilocal only) or OVERRIDE (extends upstream)
2. For NEW: Create in `effilocal/mcp_server/tools/` (async, returns string)
3. For OVERRIDE: Create in `effilocal/mcp_server/tools/` with same name, import upstream if needed
4. Add utility in `effilocal/mcp_server/utils/` if complex logic needed
5. Register in `effilocal/mcp_server/main.py` with `@mcp.tool()` decorator
6. Write tests in `tests/` - use Document objects for utilities, filenames for tools
7. Test via `pytest` or direct server call with `test_local_mcp.py`

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
- **FastMCP**: 2.8.1+ (async MCP framework)
- **msoffcrypto-tool**: 5.4.2+ (document decryption)
- **docx2pdf**: 0.1.8 (Word → PDF conversion)

Note: After migration, `word_document_server` is pristine upstream. All customizations in `effilocal/mcp_server/`.

---

## Debug Workflow

1. **Enable logging**: Set `MCP_DEBUG=1` or modify `setup_logging()` in `effilocal/mcp_server/main.py`
2. **Inspect tool calls**: Check `effilocal.mcp_server.tools` logger (auto-captures requests/responses)
3. **Manual testing**: Use `tests/test_local_mcp.py` with HTTP transport
4. **Document inspection**: Load saved `.docx` in Word or `zipfile` to inspect `document.xml`

---

## Testing Notes

**Test Suite**: 146 tests (100% passing)
- Framework: pytest 9.0.1
- Run: `cd tests; pytest -v`
- Coverage:
  - `test_uuid_embedding.py` - UUID embedding/extraction via content controls
  - `test_content_hash.py` - Block matching by hash with fallback strategies
  - `test_git_ops.py` - Git commit, history, and checkpoint operations
  - `test_search_and_replace.py` - find_and_replace_text with whole_word_only, split-run detection
  - `test_comment_status*.py` - Comment extraction with status tracking
  - `test_local_mcp.py` - MCP protocol integration via HTTP transport
  - `test_mcp_tools_availability.py` - Tool registration verification

**Testing Approach**:
- Unit tests for utilities (dual signature support, count calculations)
- Integration tests via direct function calls (pass Document objects)
- Tool tests via async invocation (pass filenames, return strings)
- Create test documents in `tests/` directory for safe experimentation
