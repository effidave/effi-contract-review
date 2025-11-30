# 🧬 MCP Tool Usage Guide for LLM Agents

## Purpose

This document defines how an LLM agent should interpret and execute the MCP tools made available by the effi-local MCP server.

When this file is active, agents should use these guidelines to:
- Select appropriate MCP tools based on user intent
- Execute tools with correct parameters
- Verify results after modifications
- Provide clear descriptions for the edit history log

---

## 1. Command Handling Logic

### Overview

When a user requests document operations, the LLM agent will:
1. Parse the natural-language request
2. Identify the **most relevant MCP tool** to achieve the goal
3. If multiple tools could apply, present clear **options** for confirmation
4. If the correct tool is **obvious**, execute it immediately
5. **Verify the result** after modifications
6. Provide a clear description suitable for the edit log

---

## 2. Tool Selection and Interpretation

### General Rules
- Interpret user instructions semantically, not literally
- Map verbs and objects to tools (e.g., "add a clause" → `add_paragraph_after_clause`, "find text" → `find_text_in_document`)
- If there is ambiguity, present a short list of possible tools with descriptions for confirmation

### 2.1 Tool Invocation Format

MCP tools are referenced by their registered names from the Word Document Server. Tool names match the function names in the server:

**Document Management:**
- `create_document` – create a new Word document
- `copy_document` – create a copy of an existing document
- `list_available_documents` – list all .docx files in a directory
- `convert_to_pdf` – convert Word document to PDF
- `get_document_outline` – get hierarchical structure of document
- `get_document_text` – extract all text from document
- `list_all_clause_numbers` – enumerate every clause ordinal detected in analysis artifacts

**Content Creation:**
- `add_heading` – add a heading to a document
- `add_paragraph` – add a paragraph with optional formatting
- `add_paragraph_after_clause` – insert paragraph after specific clause number
- `add_paragraphs_after_clause` – bulk insert multiple paragraphs after clause
- `insert_paragraph_after_clause` – add unnumbered paragraph after clause using ordinal lookup
- `add_table` – add a table to a document
- `add_picture` – add an image to a document
- `add_page_break` – insert a page break
- `list_all_clause_numbers` – enumerate available clause ordinals for reference
- `get_clause_text_by_ordinal` – fetch clause text (and continuations) by number, e.g., `5.2(a)`
- `replace_clause_text_by_ordinal` – overwrite a clause directly via ordinal without needing para_id
- `insert_paragraph_after_clause` – insert an unnumbered paragraph immediately after a clause
- `delete_clause_by_ordinal` – remove a clause plus any continuation blocks

**Text & Content Manipulation:**
- `search_and_replace` – find and replace text throughout document
- `delete_paragraph` – remove a paragraph from document
- `insert_numbered_list_near_text` – insert a numbered or bulleted list
- `replace_block_between_manual_anchors` – replace content between two markers
- `edit_run_text` – edit text within a specific run of a paragraph

**Comments:**
- `add_comment_for_paragraph` – add a comment to a paragraph
- `add_comment_after_text` – add a comment after specific text
- `get_all_comments` – extract all comments from document
- `get_comments_by_author` – filter comments by author name
- `get_comments_for_paragraph` – get comments on a specific paragraph

**Formatting & Analysis:**
- `format_text` – apply bold, italic, underline, color, font changes
- `set_background_highlight` – add background highlighting to text
- `create_custom_style` – define a custom paragraph style
- `get_paragraph_text_from_document` – extract specific paragraph text
- `find_text_in_document` – search for text and return locations

**Table Operations:**
- `format_table` – apply formatting to entire table
- `highlight_table_header` – format first row as header
- `set_table_cell_shading` – apply background color to cells
- `set_table_cell_alignment` – set text alignment in cells
- `auto_fit_table_columns` – auto-fit columns to content
- `merge_table_cells_vertical` – merge cells vertically
- `merge_table_cells_horizontal` – merge cells horizontally
- `format_table_cell_text` – apply text formatting to cell

**Parameters:**
- Each tool has required and optional parameters
- Parameters are passed as key-value pairs (e.g., `filename="contract.docx"`, `text="Hello"`, `level=1`)
- Required parameters must always be provided; optional parameters can be omitted to use defaults
- File paths should be absolute or relative to the working directory

**Quick Reference: Intent → Tool Mapping**

| User Request | Tool Name | Purpose |
|--------------|-----------|---------|
| "add a clause after 3.2" | `add_paragraph_after_clause()` | Insert numbered clause |
| "list the clause ordinals" | `list_all_clause_numbers()` | Discovery of available clause references |
| "find [text]" or "search for" | `find_text_in_document()` | Search document |
| "bold this text" | `format_text()` | Apply formatting to text range |
| "add a comment" | `add_comment_after_text()` | Attach comment to text |
| "show me all comments" | `get_all_comments()` | Retrieve document annotations |
| "add a heading" | `add_heading()` | Insert section heading |
| "find and replace" | `search_and_replace()` | Global find/replace |
| "delete paragraph 5" | `delete_paragraph()` | Remove paragraph |
| "show document structure" | `get_document_outline()` | Get hierarchical outline |

**Reporting Requirements:**
Always include in your response:
- The **exact tool name** invoked
- The **parameters** passed (redact sensitive values)
- The **verification results** (confirm changes were made)
- A **clear description** of what changed (for edit log)

### 2.2 Connection and Availability

The MCP server connection is managed by VS Code / Cursor IDE. Before executing any tool:

1. **Verify the connector is available** – If the MCP server is offline or disconnected, report:
   ```
   Execution: SKIPPED (MCP server not available)
   Suggestion: Verify Word Document Server is running and properly configured in mcp-config.json
   ```

2. **No session handshake required** – MCP protocol handles session state internally

3. **Tool execution is immediate** – Once a tool is invoked, the server processes it synchronously and returns results directly

4. **Error responses** – If a tool call fails, the server returns an error message. The agent must:
   - Report the exact error message
   - **Not retry automatically** unless the user explicitly approves
   - Suggest remediation (e.g., "file not found" → check file path)

---

## 3. Version Control & Edit History

**Important**: Version control is managed by the application's **EditHistory system** (see ARTIFACT_GUIDE.md). The LLM agent's role is to:
- Execute MCP tool requests on the current document
- Verify changes after execution
- Provide clear descriptions for the edit log

### Agent Responsibilities When Modifying Documents

When executing a tool **that modifies a document** (i.e., **does not start with** `get_`, `find_`, or `list_`):

1. **Describe the intended edit clearly**  
   Before execution, explain what will change and why

2. **Execute MCP tool on current document**  
   The application handles version control via edit log and checkpoints
   ```
   Example: add_paragraph_after_clause(
       filename="contract.docx",
       clause_number="3.2",
       text="The Recipient shall...",
       inherit_numbering=true
   )
   ```

3. **Verify changes after execution**  
   After modifying, use read-only tools to confirm:
   - `get_document_outline()` – Verify structure shows new clause
   - `find_text_in_document()` – Confirm text was added/changed
   - Report verification results to user

4. **Document the change for edit log**  
   Provide clear description including:
   - **What changed**: "Added confidentiality clause after 3.2"
   - **Why**: "User requested non-disclosure terms in Services section"
   - **MCP tool used**: Tool name + key parameters

### Response Format

Each response will include:
- ✅ **Tool used**: MCP tool name
- 🧠 **Reason**: Why this tool was chosen
- 📝 **Action**: What the tool did
- **Verification**: Confirmation that changes were made
- 📝 **Edit description**: Clear description for edit log

**Example Response:**
> ✅ Tool used: `add_paragraph_after_clause()`  
> 🧠 Reason: You asked to add a confidentiality clause after section 3.2  
> 📝 Action: Inserted new paragraph with inherit_numbering=true (creates clause 3.2.1)  
> Verification: Confirmed new clause appears with ordinal "3.2.1" via document outline  
> 📝 Edit description: "Added confidentiality obligations to clause 3.2"

---

## 4. Document Storage and Directory Structure

### Project Directory Structure

Documents are managed within the **EL_Projects** directory:
```
EL_Projects\[project name]\
  ├─ drafts\current_drafts\      # Working documents (.docx)
  ├─ analysis\                   # JSON artifacts (blocks, sections, relationships)
  ├─ history\                    # Edit log and checkpoints
  │   ├─ edit_log.jsonl          # Sequential edit history
  │   └─ checkpoints\            # Periodic .docx snapshots
  └─ precedents\                 # Reference documents
```

### Working with Documents

1. **MCP tools operate on documents in `drafts\current_drafts\`**
   - File paths provided by the application
   - Use absolute paths when provided
   - Example: `EL_Projects\Norton - R&D\drafts\current_drafts\contract.docx`

2. **Analysis artifacts stored in `analysis\` subdirectory**
   - Generated after document analysis
   - Contains: manifest.json, blocks.jsonl, sections.json, relationships.json
   - Use for navigation and search queries (see Section 6)

3. **Edit history managed in `history\` subdirectory**
   - Version control via edit_log.jsonl (append-only)
   - Checkpoints stored in `checkpoints\` folder
   - Agent provides descriptions for log entries
   - Application handles checkpoint creation

4. **Always confirm file locations in responses**
   - Use absolute paths provided by application
   - Report file locations for transparency
   - Example response:  
     > ✅ Added clause to `EL_Projects\Norton - R&D\drafts\current_drafts\contract.docx`

---

## 5. Ambiguity Handling

If the agent cannot determine the exact tool:
1. List the **top 2–3 candidates**
2. Include a short explanation of each tool's purpose
3. Ask for user confirmation before proceeding

**Example:**
> Possible tools for "insert content after the header":  
> - `add_paragraph()` – adds paragraph at end of document  
> - `add_paragraph_after_clause()` – inserts paragraph after specific clause number  
> - `insert_numbered_list_near_text()` – adds a numbered list near matching text  
> Which would you like to use?

---

## 6. Artifact Integration

The agent should reference **analysis artifacts** for enhanced capabilities:

### When to Use Artifacts

- **Navigation**: Find clauses by ordinal (e.g., "show clause 3.2.1")
- **Context**: Understand document structure before edits
- **Search**: Locate content using blocks.jsonl full-text search
- **Validation**: Verify edits by comparing artifact checksums

### Artifact Files

| File | Purpose | Location |
|------|---------|----------|
| `manifest.json` | Document metadata, checksums, detected schedules | `analysis/` |
| `blocks.jsonl` | All content blocks with text, numbering, para_id | `analysis/` |
| `sections.json` | Hierarchical section tree | `analysis/` |
| `relationships.json` | Parent/child relationships, full numbering metadata | `analysis/` |

### Example: Query Artifacts Before Editing

```python
# 1. Query artifacts to find clause 3.2
blocks = [json.loads(line) for line in open('analysis/blocks.jsonl')]
clause_3_2 = next(
    b for b in blocks 
    if b.get('list', {}).get('ordinal') == '3.2'
)

# 2. Use para_id or clause number for MCP tool
add_paragraph_after_clause(
    filename="contract.docx",
    clause_number="3.2",
    text="...",
    inherit_numbering=true
)

# 3. Application re-analyzes to update artifacts after edit
```

**See `ARTIFACT_GUIDE.md` for detailed artifact schemas and query patterns.**

---

## 7. Common Workflow Patterns

### **Pattern 1: Add Clause to Contract**
**Situation:** User wants to insert a new clause

**Workflow:**
1. Identify target location (clause number)
2. Execute ordinal-aware tools as needed:
   - Use `list_all_clause_numbers()` if the precise ordinal must be confirmed first
   - Retrieve existing text with `get_clause_text_by_ordinal()` when context is needed
   - Execute `add_paragraph_after_clause()` with `inherit_numbering=true` to add sibling clause
3. Verify with `get_document_outline()`
4. Provide edit description

**Example:**
```
User: "Add a confidentiality clause after section 3.2"

Agent executes:
- add_paragraph_after_clause(
    filename="contract.docx",
    clause_number="3.2",
    text="The Recipient shall keep confidential...",
    inherit_numbering=true
  )
- get_document_outline(filename="contract.docx")  # Verify

Agent reports:
✅ Tool used: add_paragraph_after_clause()
Verification: Confirmed new clause 3.2.1 appears in outline
📝 Edit description: "Added confidentiality obligations after clause 3.2"
```

---

### **Pattern 2: Search and Comment**
**Situation:** Find text and add annotation

**Workflow:**
1. Use `find_text_in_document()` to locate text
2. Use `add_comment_after_text()` to attach comment
3. Report location and comment ID

**Example:**
```
User: "Find 'indemnification' and add a comment asking for clarification"

Agent executes:
- find_text_in_document(filename="contract.docx", search_text="indemnification")
  → Returns: paragraph_index=12
- add_comment_after_text(
    filename="contract.docx",
    search_text="indemnification",
    comment_text="Please clarify scope of indemnification"
  )

Agent reports:
✅ Found "indemnification" in paragraph 12
✅ Added comment requesting clarification
```

---

### **Pattern 3: Query Artifacts for Navigation**
**Situation:** User wants to see document structure or find specific sections

**Workflow:**
1. Load artifacts from `analysis/` folder
2. Query sections.json for hierarchy
3. Filter blocks.jsonl for content
4. Present results to user

**Example:**
```
User: "Show me all clauses in the Definitions section"

Agent executes:
- Read analysis/sections.json → find "Definitions" section
- Read analysis/blocks.jsonl → filter by section_id
- Filter blocks with list.ordinal (numbered clauses)

Agent reports:
Definitions Section (clause 1):
  1.1 "Agreement" means...
  1.2 "Confidential Information" means...
  1.3 "Effective Date" means...
```

---

### **Pattern 4: Format Table**
**Situation:** Apply formatting to table

**Workflow:**
1. Use `highlight_table_header()` for header formatting
2. Use `set_table_cell_shading()` for specific cells
3. Use `auto_fit_table_columns()` for sizing

**Example:**
```
User: "Make the first table header blue with white text"

Agent executes:
- highlight_table_header(
    filename="contract.docx",
    table_index=0,
    header_color="0066CC",
    text_color="FFFFFF"
  )

Agent reports:
✅ Applied blue header formatting (color: #0066CC) to table 1
📝 Edit description: "Formatted table header with blue background"
```

---

## 8. Common Mistakes to Avoid (Anti-Patterns)

### [X] Don't Use the Wrong Tool
**Mistake:** Using `search_and_replace()` when you need `format_text()`
- `search_and_replace()` changes **content** (text replacement)
- `format_text()` changes **appearance** (bold, color, font)

**Correct:** If user says "make that bold," use `format_text()` not `search_and_replace()`

---

### [X] Don't Skip Verification After Modifications
**Mistake:** Modifying a document without verifying the change

```
// INCOMPLETE:
add_paragraph_after_clause(filename="contract.docx", clause_number="3.2", text="...")
// No verification!

// CORRECT:
add_paragraph_after_clause(filename="contract.docx", clause_number="3.2", text="...")
get_document_outline(filename="contract.docx")  # Confirm new clause appears
```

**Note:** Version control is handled by the application's EditHistory system.

---

### [X] Don't Assume Paragraph Indices Are Stable
**Mistake:** Using cached paragraph indices after modifications

```
// Paragraph indices CHANGE after deletions/insertions:
para_info = get_paragraph_text_from_document(..., paragraph_index=5)
delete_paragraph(..., paragraph_index=2)  // Now paragraph 5 is at index 4!
format_text(..., paragraph_index=5, ...)  // WRONG INDEX!
```

**Correct approach:** Re-query document structure after modifications, or use search-based approaches (`find_text_in_document()`, clause numbers).

---

### ❌ Don't Try to Modify Non-Existent Content
**Mistake:** Attempting operations on invalid indices or missing text

```
// These will fail:
format_text(..., paragraph_index=99, ...)  // Out of range
add_comment_after_text(..., search_text="[text not in doc]", ...)
```

**Correct approach:** Always validate before modifying:
1. Use `find_text_in_document()` or `get_paragraph_text_from_document()` first
2. Confirm the index/text exists
3. Then perform modification

---

### ❌ Don't Forget to Provide Clear Edit Descriptions
**Mistake:** Vague descriptions like "Updated document"

**Correct:** Specific descriptions for edit log:
- ✅ "Added confidentiality obligations to clause 3.2"
- ✅ "Deleted outdated warranty terms from Schedule 1"
- ✅ "Formatted table header with blue background"
- ❌ "Made changes"
- ❌ "Updated file"

---

## 9. Critical Tool Details

### ⚠️ **CRITICAL: Indexing is 0-Based**

All **paragraph indices**, **table indices**, **row indices**, and **column indices** are **zero-based**:
- First paragraph = index `0`
- Second paragraph = index `1`
- First table = index `0`

If a document has 5 paragraphs, valid indices are 0, 1, 2, 3, 4. Index 5 will cause an **out of range** error.

**Important:** After modifications that remove paragraphs, index numbering shifts. Always re-query the document if making multiple edits in sequence.

---

### Key Parameters

**`inherit_numbering` (for add_paragraph_after_clause):**
- `true` → Creates sibling clause at same level (e.g., after 3.2 creates 3.3)
- `false` → Creates unnumbered paragraph after the clause

**`whole_word_only` (for search_and_replace):**
- `true` → Only match complete words (uses regex `\b` boundaries)
- `false` → Match partial words

**`style` (for add_paragraph, add_heading):**
- Match existing document styles for consistency
- Use `get_document_outline()` to identify styles in use
- Common styles: 'Normal', 'Body Text', 'Heading 1', 'Quote'

---

## 10. Execution Guardrails

To ensure reliable, verifiable, and non-fabricated tool execution:

### Core Principles

- **Never claim a tool was used unless it actually executed**
- **Never fabricate or infer tool output** – file names, lists, or counts must come directly from MCP server responses
- **Stop immediately** if a tool or connector is unavailable – no simulated or placeholder results
- Every response must include a clearly labeled **Execution Status**:

```text
Execution: SUCCESS | FAILED (reason) | SKIPPED (awaiting confirmation / connector not available)
```

### Standard Response Structure

| Field | Description |
|---|---|
| **Execution** | `SUCCESS`, `FAILED`, or `SKIPPED` (include reason) |
| **Tool used** | Tool name (e.g., `add_paragraph_after_clause`) |
| **Tool call** | Full resolved call with arguments (redact secrets) |
| **Reason** | Mapping from user request to tool function |
| **Action** | What the tool was asked to do |
| **Raw output** | Verbatim MCP server response in fenced block |
| **Verification** | Results from verification tools (if modification) |
| **Edit description** | Clear description for history log (if modification) |

**Example:**

```text
Execution: SUCCESS
Tool used: add_paragraph_after_clause
Tool call: add_paragraph_after_clause(filename="contract.docx", clause_number="3.2", text="...", inherit_numbering=true)
From MCP server (raw):
"Paragraph added after clause 3.2 with custom para_id: 7f3e8a9b-..."
Verification: Confirmed clause 3.2.1 appears in document outline
Edit description: "Added confidentiality obligations after clause 3.2"
```

**If no results:**
```text
Execution: SUCCESS
From MCP server (raw): "No matches found"
```

**If connector unavailable:**
```text
Execution: SKIPPED (connector not available)
Suggestion: Verify MCP server connection in VS Code configuration.
```

### Output Presentation Rules

- **Always** echo the exact tool call and show the **verbatim MCP server response**
- Label all raw data consistently: `From MCP server (raw):`
- **Never** synthesize, guess, or infer content
- If a server returns an empty result, the only valid completion is:
  ```text
  Execution: SUCCESS
  From MCP server (raw): []
  No results found.
  ```

---

## 11. Summary

| Category | Agent Behavior |
|-----------|--------------|
| Tool Selection | Auto-detect from user intent or present options |
| Modifications | Execute on current document, verify changes |
| Version Control | Managed by application EditHistory system |
| Storage | `EL_Projects\[project]\drafts\current_drafts\` |
| Artifacts | Reference `analysis\` folder for navigation/queries |
| Edit History | Provide clear descriptions for `history\edit_log.jsonl` |
| Verification | Always confirm changes after modifications |
| Transparency | Report tool used, reason, action, verification results |
| Error Handling | Never fabricate results, report failures clearly |

---

## Reference

- **ARTIFACT_GUIDE.md** – Detailed artifact schemas and integration patterns
- **MCP Server Config** – `mcp-config.json` in workspace root
- **Analysis CLI** – `python -m effilocal.cli analyze <file.docx> --doc-id <uuid> --out <dir>`
- **Test Documents** – `tests/` directory for safe experimentation


