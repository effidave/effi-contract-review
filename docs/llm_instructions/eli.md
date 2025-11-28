# 🧬 EL Instruction Document

## Purpose

This document defines how an LLM should interpret and execute the MCP tools made available by the effi-local MCP server.

When this file is active, any message starting with:

> **“Ask EL [instructions]”**

will trigger the LLM to interpret `[instructions]`, determine the correct document-handling tool(s) to use, and execute the tool(s) safely and transparently.

---

## 1. Command Handling Logic

### Overview

When you type **“Ask EL [instruction]”**, the LLM will:
1. Parse your natural-language request.
2. Identify the **most relevant EL tool** to achieve your goal.
3. If multiple tools could apply, the LLM will show you clear **options**.
4. If the correct tool is **obvious**, the LLM will execute it immediately.

---

## 2. Tool Selection and Interpretation

### General Rules
- the LLM interprets your instruction semantically, not literally.
- It maps verbs and objects to tools (e.g., “create a document” → `create_document`, “find text” → `find_text_in_document`).
- If there is ambiguity, the LLM will present a short list of possible tools with descriptions for your confirmation.

### 2.1 Tool Invocation Format

When invoking an MCP tool, the LLM will reference the tool by its registered name from the Word Document Server. Tool names are simple identifiers matching the function names in the server:

**Document Management:**
- `create_document` – create a new Word document
- `copy_document` – create a copy of an existing document
- `list_available_documents` – list all .docx files in a directory
- `convert_to_pdf` – convert Word document to PDF

**Content Creation:**
- `add_heading` – add a heading to a document
- `add_paragraph` – add a paragraph with optional formatting
- `add_table` – add a table to a document
- `add_picture` – add an image to a document
- `add_page_break` – insert a page break
- `add_comment_for_paragraph` – add a comment to a paragraph
- `add_comment_after_text` – add a comment after specific text

**Text & Content Manipulation:**
- `search_and_replace` – find and replace text throughout document
- `delete_paragraph` – remove a paragraph from document
- `insert_numbered_list_near_text` – insert a numbered or bulleted list
- `replace_block_between_manual_anchors` – replace content between two markers
- `edit_run_text` – edit text within a specific run of a paragraph (use where text is split across runs)


**Formatting & Analysis:**
- `format_text` – apply bold, italic, underline, color, font changes
- `set_background_highlight` – add background highlighting to text
- `create_custom_style` – define a custom paragraph style
- `get_paragraph_text_from_document` – extract specific paragraph text
- `find_text_in_document` – search for text and return locations
- `get_all_comments` – extract all comments from document
- `get_comments_by_author` – filter comments by author name
- `get_comments_for_paragraph` – get comments on a specific paragraph

**Parameters:**
- Each tool has required and optional parameters
- Parameters are passed as key-value pairs (e.g., `filename="Report.docx"`, `text="Hello"`, `level=1`)
- Required parameters must always be provided; optional parameters can be omitted to use defaults
- File paths should be relative to the working directory or absolute paths

**Quick Reference: Trigger → Tool Mapping**

| User Request | Tool Name | Purpose |
|--------------|-----------|---------|
| "bold this text" or "make it underline" | `format_text()` | Apply formatting to text range |
| "find [text]" or "search for" | `find_text_in_document()` | Search document |
| "add a table" | `add_table()` | Create table with data |
| "create a new version" | `copy_document()` | Branch/version document |
| "comment on [text]" or "leave a note" | `add_comment_after_text()` | Attach comment to text |
| "extract comments" | `get_all_comments()` or `get_comments_by_author()` | Retrieve document annotations |
| "add a heading" or "add a title" | `add_heading()` | Insert heading |
| "find and replace" or "change all instances" | `search_and_replace()` | Global find/replace |
| "delete paragraph" | `delete_paragraph()` | Remove paragraph |
| "add a list" | `insert_numbered_list_near_text()` | Insert bullet/numbered list |

**Reporting Requirements:**
Always include in your response:
- The **exact tool name** invoked
- The **parameters** passed (redact sensitive values like passwords)
- The **raw output** from the server in a labeled block (*From MCP server*)
- Any **post-processing** applied to the output before presenting results

### 2.2 Connection and Availability

The MCP server connection is managed by VS Code / Cursor IDE. Before executing any tool:

1. **Verify the connector is available** – If the MCP server is offline or disconnected, report:
   ```
   Execution: SKIPPED (MCP server not available)
   Suggestion: Verify Word Document Server is running and properly configured in mcp-config.json
   ```

2. **No session handshake required** – MCP protocol handles session state internally; the LLM does not need to manage session IDs or initialization headers.

3. **Tool execution is immediate** – Once a tool is invoked, the server processes it synchronously and returns results directly. There is no queueing or delayed response.

4. **Error responses** – If a tool call fails, the server returns an error message with details. The LLM must:
   - Report the exact error message
   - **Not retry automatically** unless the user explicitly approves
   - Suggest remediation (e.g., "file not found" → check file path)

### Example Interpretation Table

| Example Command | the LLM Chooses Tool |
|------------------|----------------------|
| “Create a new document called *ProjectPlan.docx*” | `create_document()` |
| “Find the paragraph containing *Budget Summary*” | `find_text_in_document()` |
| “Make paragraph 2 bold” | `format_text()` (after creating a versioned copy) |
| “Extract all comments from version 3” | `get_all_comments()` |
| “Merge *Summary.docx* and *Appendix.docx*” | `merge_documents()` (after copying target doc) |

---

## 3. Version Control Rules

When the LLM executes a tool **that modifies a document** (i.e., **does not start with** `get_`, `find_`, or `list_`):

1. **Always make a copy first.**  
   Before modifying, the LLM uses `copy_document()` to create a new version.

2. **Version suffix format:**  
   the LLM appends `_vN` to the filename to represent the version number:
   ```
   Report.docx → Report_v1.docx → Report_v2.docx → Report_v3.docx
   ```

3. **Editing an older version (branching behavior):**  
   If you ask to edit an earlier version:
   - the LLM creates a **new version continuing the global sequence** (not overwriting existing versions).  
   - It also **tags the source version** for traceability.

   **Example:**
   ```
   Existing files: Report_v1.docx, Report_v2.docx, Report_v3.docx
   You request: "Edit version 1"
   → the LLM creates: Report_v4_from_v1.docx
   ```

   the LLM will explain this in the response:
   > “Edited version 1 and saved as `Report_v4_from_v1.docx` to preserve version continuity.”

   If you later say, “make this the new main version,” the LLM can rename it or mark it as current.

4. **Editing without specifying a version:**  
   - the LLM assumes you mean the **most recent version**.
   - It creates the **next incremented version**:
     ```
     Proposal_v3.docx → Proposal_v4.docx
     ```

5. **Response details:**  
   Each response will include:
   - ✅ Tool used  
   - 🧠 Why it was chosen  
   - 📝 Action performed  
   - 🆟️ Resulting version filename  

---

## 🗁 3.1. Document Storage and Directory Rules

1. **Default Project Directory**  
   - All EL documents — including new files and versioned copies — are created and managed within the user’s **EL Projects directory** at:  
     ```
     EL_Projects\[project name]\
     ```
   - The `[project name]` folder corresponds to the name of the active or referenced project.  
     For example:  
     - *Project “SolarAnalysis”* → `EL_Projects\SolarAnalysis\`  
     - *Project “BidPrep”* → `EL_Projects\BidPrep\`

2. **If the Directory Doesn’t Exist**  
   - Before attempting any operation that creates or modifies a document, the LLM must check whether the target project folder exists.  
   - If it **does not exist**, the LLM will **pause execution** and prompt:  
     > “The folder `EL_Projects\[project name]\` doesn’t exist.  
     > Would you like me to create it before continuing?”

   - Once confirmed, the LLM will issue a command (via the appropriate tool or API call) to create the directory before proceeding.

3. **File Placement**  
   - All **new documents**, **copied versions**, and **generated outputs** (e.g., PDFs or merged files) are saved in the **same project folder**.  
   - Versioned copies retain the same naming structure and remain colocated:
     ```
     EL_Projects\SolarAnalysis\Report.docx
     EL_Projects\SolarAnalysis\Report_v1.docx
     EL_Projects\SolarAnalysis\Report_v2.docx
     ```

4. **Cross-Project Operations**  
   - When commands involve multiple projects (e.g., merging two files from different projects), the LLM will:
     1. Keep source files in their original locations.  
     2. Create the **resulting file** in the **first project folder mentioned** unless another destination is specified.  
     3. Explicitly state where the resulting file was saved.

5. **Directory Confirmation**  
   - For transparency, the LLM will always confirm the working directory when creating or modifying any file.  
   - Example response:  
     > ✅ Created `Summary_v2.docx` in  
     > `EL_Projects\BidPrep\`  
     > 🧠 Used: `copy_document()` before applying `add_heading()`.

---

## 4. Result Explanation Format

After executing a command, the LLM must report clearly:

**Example Response:**
> ✅ Tool used: `add_heading()`  
> 🧠 Reason: You asked to add a section heading, which maps directly to `add_heading`.  
> 📝 Action: Added “Executive Summary” (level 2 heading) in *Proposal_v3.docx*.  
> 🆟️ New version: `Proposal_v3.docx`

---

## 5. Ambiguity Handling

If the LLM cannot determine the exact tool:
1. It will list **the top 2–3 candidates**.
2. Each tool will include a short explanation of its purpose.
3. the LLM will ask for your confirmation before continuing.

**Example:**
> Possible tools for “insert something after the header”:  
> - `insert_str_content_near_text()` – insert text near a matching string (use `content_style="Heading 1"` for headers).  
> - `insert_numbered_list_near_text_tool()` – adds a numbered list near a specific section.  
> Which would you like to use?

---

## 5.1 Common Workflow Patterns

To maximize efficiency, agents should recognize these reusable patterns:

### **Pattern 1: Modify a Document Safely**
**Situation:** User wants to edit an existing document
**Workflow:**
1. `copy_document(filename="original.docx", new_filename="original_v1.docx")`
2. Perform modification (e.g., `add_heading()`, `format_text()`, `search_and_replace()`)
3. Report new version name

**Why:** Preserves original; maintains version history

---

### **Pattern 2: Search and Update**
**Situation:** Find text and apply formatting or content changes
**Workflow:**
1. `find_text_in_document(filename="doc.docx", search_text="[target]")` → Returns paragraph indices
2. Based on results, use either:
   - `format_text()` – if changing appearance
   - `search_and_replace()` – if changing content
   - `add_comment_after_text()` – if adding annotation

**Why:** Locate-then-act prevents blind modifications

---

### **Pattern 3: Batch Extract Information**
**Situation:** Need multiple pieces of info from same document(s)
**Workflow:**
Use `execute_plan()` with parallel phase to fetch comments and text locations simultaneously

**Why:** Parallel execution is faster than sequential calls

---

### **Pattern 4: Version Branching**
**Situation:** Create a new branch from an older version
**Workflow:**
1. `copy_document(filename="Report_v2.docx", new_filename="Report_v5_from_v2.docx")` → Uses `_vN_from_vM` naming
2. Make edits on new file
3. Explain: "Created branch to preserve version history"

**Why:** Allows non-linear version control; recovers old work

---

### **Pattern 5: Multi-Step Content Replacement**
**Situation:** Replace entire section or block
**Workflow:**
- If replacing text, check the markers with the user first before replacing the text between markers: `replace_block_between_manual_anchors()`

---

## 6. Comprehensive Tool Reference

This section provides detailed specifications for all available tools, including required/optional parameters, return values, and error conditions.

---

⚠️ **CRITICAL: Indexing is 0-Based**

All **paragraph indices**, **table indices**, **row indices**, and **column indices** are **zero-based**:
- First paragraph = index `0`
- Second paragraph = index `1`
- First table = index `0`
- First row = index `0`
- First column = index `0`

If a document has 5 paragraphs, valid indices are 0, 1, 2, 3, 4. Index 5 will cause an **out of range** error.

**Important:** After modifications that remove paragraphs, index numbering shifts. Always re-query the document if making multiple edits in sequence.

---

### 🗂 **Document Management Tools**

#### `create_document`
**Purpose:** Create a new Word document

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Path/filename for new document (`.docx` auto-added) |
| `title` | string | ❌ | — | Document title (metadata) |
| `author` | string | ❌ | — | Document author (metadata) |

**Returns:** Success message with filename

**Errors:**
- File already exists
- Invalid file path
- Permission denied

**Example:**
```
create_document(filename="Report.docx", title="Q1 Analysis", author="David")
```

---

#### `copy_document`
**Purpose:** Create a copy of an existing document (used for versioning)

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Source document path |
| `new_filename` | string | ✅ | — | Destination filename |

**Returns:** Success message with new filename path

**Errors:**
- Source file not found
- Destination file already exists
- Permission denied

**Example:**
```
copy_document(filename="Report.docx", new_filename="Report_v1.docx")
```

---

#### `list_available_documents`
**Purpose:** List all Word documents in a directory

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `directory` | string | ❌ | `.` (current) | Directory path to scan |

**Returns:** Array of `.docx` filenames

**Errors:**
- Directory not found
- Permission denied

**Example:**
```
list_available_documents(directory="EL_Projects\MyProject\")
```

---

#### `convert_to_pdf`
**Purpose:** Convert Word document to PDF format

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Source Word document path |
| `output_filename` | string | ❌ | `[filename].pdf` | Output PDF filename |

**Returns:** Success message with PDF path

**Errors:**
- Source file not found
- Conversion failed
- Invalid output path

**Example:**
```
convert_to_pdf(filename="Report_v2.docx", output_filename="Report_v2.pdf")
```

---

### 🔍 **Extraction and Analysis Tools**

#### `find_text_in_document`
**Purpose:** Search for text and return matching locations

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document to search |
| `search_text` | string | ✅ | — | Text to find (case-insensitive) |

**Returns:** List of matches with paragraph indices and positions

**Errors:**
- File not found
- Text not found (returns empty list)

**Example:**
```
find_text_in_document(filename="Report.docx", search_text="Budget Summary")
```

---

#### `get_paragraph_text_from_document`
**Purpose:** Extract text from a specific paragraph

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `paragraph_index` | integer | ✅ | — | Paragraph number (0-based) |

**Returns:** Paragraph text content

**Errors:**
- File not found
- Paragraph index out of range

**Example:**
```
get_paragraph_text_from_document(filename="Report.docx", paragraph_index=2)
```

---

#### `get_all_comments`
**Purpose:** Extract all comments from document with metadata

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |

**Returns:** JSON object with:
- `success` (boolean) – operation status
- `comments` (array) – comment objects, each with: `text`, `author`, `initials`, `status` (active/resolved), `paragraph_index`
- `total_comments` (integer) – count of comments

**Errors:**
- File not found
- No comments found (returns empty comments array)

**Example:**
```
get_all_comments(filename="Report.docx")
```

**Sample Response:**
```json
{
  "success": true,
  "comments": [{"text": "Review this", "author": "David", "initials": "DS", "status": "active", "paragraph_index": 2}],
  "total_comments": 1
}
```

---

#### `get_comments_by_author`
**Purpose:** Filter comments by author name

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `author` | string | ✅ | — | Author name to filter (case-sensitive) |

**Returns:** JSON object with:
- `success` (boolean) – operation status
- `author` (string) – the author filter applied
- `comments` (array) – matching comment objects
- `total_comments` (integer) – count of matching comments

**Errors:**
- File not found
- Author name empty
- Author not found (returns empty comments array)

**Example:**
```
get_comments_by_author(filename="Report.docx", author="David")
```

---

#### `get_comments_for_paragraph`
**Purpose:** Get comments attached to a specific paragraph

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `paragraph_index` | integer | ✅ | — | Paragraph number (0-based) |

**Returns:** JSON object with:
- `success` (boolean) – operation status
- `paragraph_index` (integer) – the paragraph index queried
- `paragraph_text` (string) – text content of the paragraph (for context)
- `comments` (array) – comment objects on that paragraph
- `total_comments` (integer) – count of comments on paragraph

**Errors:**
- File not found
- Paragraph index negative or out of range
- No comments on paragraph (returns empty comments array)

**Example:**
```
get_comments_for_paragraph(filename="Report.docx", paragraph_index=5)
```o comments on paragraph (returns empty array)

**Example:**
```
get_comments_for_paragraph(filename="Report.docx", paragraph_index=5)
```

---

### ✍️ **Content Creation & Manipulation Tools**

#### `add_heading`
**Purpose:** Add a heading to document

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `text` | string | ✅ | — | Heading text |
| `level` | integer | ❌ | 1 | Level 1-9 (1=largest, 9=smallest) |
| `font_name` | string | ❌ | — | Font family (e.g., 'Helvetica') |
| `font_size` | integer | ❌ | — | Font size in points |
| `bold` | boolean | ❌ | — | Make bold |
| `italic` | boolean | ❌ | — | Make italic |
| `border_bottom` | boolean | ❌ | false | Add bottom border |

**Returns:** Success message

**Errors:**
- File not found
- File not writable
- Invalid level

**Example:**
```
add_heading(filename="Report.docx", text="Executive Summary", level=1, bold=true)
```

---

#### `add_paragraph`
**Purpose:** Add a paragraph with optional formatting

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `text` | string | ✅ | — | Paragraph text |
| `style` | string | ❌ | — | Paragraph style name |
| `font_name` | string | ❌ | — | Font family |
| `font_size` | integer | ❌ | — | Font size in points |
| `bold` | boolean | ❌ | — | Make bold |
| `italic` | boolean | ❌ | — | Make italic |
| `color` | string | ❌ | — | Text color (hex RGB, e.g., '000000') |

**Returns:** Success message

**Errors:**
- File not found
- File not writable
- Invalid style

**Example:**
```
add_paragraph(filename="Report.docx", text="This is the main content.", bold=false, font_size=12)
```

---

#### `add_table`
**Purpose:** Add a table with data

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `rows` | integer | ✅ | — | Number of rows |
| `cols` | integer | ✅ | — | Number of columns |
| `data` | array of arrays | ❌ | — | Data to populate (row-major) |

**Returns:** Success message

**Errors:**
- File not found
- File not writable
- Data dimensions mismatch

**Example:**
```
add_table(filename="Report.docx", rows=3, cols=2, data=[["Name", "Value"], ["Item1", "100"], ["Item2", "200"]])
```

---

#### `add_picture`
**Purpose:** Add an image to document

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `image_path` | string | ✅ | — | Path to image file |
| `width` | number | ❌ | — | Image width in inches |

**Returns:** Success message

**Errors:**
- Document not found
- Image file not found
- Invalid image format
- File not writable

**Example:**
```
add_picture(filename="Report.docx", image_path="C:\Images\logo.png", width=2.5)
```

---

#### `add_page_break`
**Purpose:** Insert a page break

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |

**Returns:** Success message

**Errors:**
- File not found
- File not writable

**Example:**
```
#### `add_comment_for_paragraph`
**Purpose:** Add a comment to a specific paragraph

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `paragraph_index` | integer | ✅ | — | Paragraph number (0-based) |
| `comment_text` | string | ✅ | — | Comment content |
| `author` | string | ❌ | — | Comment author name |
| `initials` | string | ❌ | — | Author initials |

**Returns:** JSON object with:
- `success` (boolean) – operation status
- `action` (string) – "add_comment_for_paragraph"
- `comment_id` (integer) – ID of newly created comment
- `filename` (string) – document path
- `paragraph_index` (integer) – target paragraph
- `author` (string) – comment author
- `initials` (string) – author initials

**Errors:**
- File not found
- Paragraph index negative or out of range
- File not writable

**Example:**
```
add_comment_for_paragraph(filename="Report.docx", paragraph_index=3, comment_text="Needs revision", author="David", initials="DS")
```

---

#### `add_comment_after_text`
**Purpose:** Add a comment attached to the first occurrence of specific text

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `search_text` | string | ✅ | — | Text to find (searches in text runs, case-sensitive) |
| `comment_text` | string | ✅ | — | Comment content |
| `author` | string | ❌ | — | Comment author name |
| `initials` | string | ❌ | — | Author initials |

**Returns:** JSON object with:
- `success` (boolean) – operation status
- `action` (string) – "add_comment_after_text"
- `comment_id` (integer) – ID of newly created comment
- `filename` (string) – document path
- `search_text` (string) – text that was found and commented
- `author` (string) – comment author
- `initials` (string) – author initials

**Errors:**
- File not found
- Search text not found in document (searches within text runs)
- File not writable
- Search text cannot be empty

**Example:**
```
add_comment_after_text(filename="Report.docx", search_text="Budget Summary", comment_text="Please update with latest figures", author="David", initials="DS")
```

---

### **Text & Content Manipulation Tools**

#### `search_and_replace`
**Purpose:** Find and replace all instances of text

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `find_text` | string | ✅ | — | Text to find |
| `replace_text` | string | ✅ | — | Replacement text |

**Returns:** Number of replacements made

**Errors:**
- File not found
- Text not found (returns 0)
- File not writable

**Example:**
```
search_and_replace(filename="Report.docx", find_text="2024", replace_text="2025")
```

---

#### `delete_paragraph`
**Purpose:** Remove a paragraph from document

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `paragraph_index` | integer | ✅ | — | Paragraph number (0-based) |

**Returns:** Success message

**Errors:**
- File not found
- Paragraph index out of range
- File not writable

**Example:**
```
delete_paragraph(filename="Report.docx", paragraph_index=2)
```

---

#### `insert_numbered_list_near_text`
**Purpose:** Insert a numbered or bulleted list before/after target text

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `target_text` | string | ❌ | — | Text to find (or use `target_paragraph_index`) |
| `target_paragraph_index` | integer | ❌ | — | Paragraph number (0-based) |
| `list_items` | array | ✅ | — | Array of strings for list items |
| `position` | string | ❌ | 'after' | 'before' or 'after' target |
| `bullet_type` | string | ❌ | 'bullet' | 'bullet' or 'number' |

**Returns:** Success message

**Errors:**
- File not found
- Target text/paragraph not found
- File not writable

**Example:**
```
insert_numbered_list_near_text(filename="Report.docx", target_text="Requirements:", list_items=["Item 1", "Item 2", "Item 3"], bullet_type="number")
```

---

#### `replace_block_between_manual_anchors`
**Purpose:** Replace content between two marker texts

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `start_anchor_text` | string | ✅ | — | Start marker text |
| `end_anchor_text` | string | ❌ | — | End marker text (optional) |
| `new_paragraphs` | array | ✅ | — | Replacement paragraphs |

**Returns:** Success message

**Errors:**
- File not found
- Anchor text not found
- File not writable

**Example:**
```
replace_block_between_manual_anchors(filename="Report.docx", start_anchor_text="<!-- START: Summary -->", end_anchor_text="<!-- END: Summary -->", new_paragraphs=["Updated summary paragraph"])
```

---

#### `edit_run_text`
**Purpose:** Edit text within a specific run of a paragraph (handles split runs where text spans multiple formatting regions)

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `paragraph_index` | integer | ✅ | — | Paragraph number (0-based) |
| `run_index` | integer | ✅ | — | Run number within paragraph (0-based) |
| `new_text` | string | ✅ | — | Replacement text for the run |

**Returns:** Success message

**Errors:**
- File not found
- Paragraph index out of range
- Run index out of range
- File not writable

**Example:**
```
edit_run_text(filename="Report.docx", paragraph_index=5, run_index=0, new_text="Updated content")
```

**Use Case:** When `search_and_replace()` detects text spans multiple runs (formatting breaks within a single text span), use `edit_run_text()` to directly edit the specific run where changes are needed.

---

### 🎨 **Formatting & Styles Tools**

#### `format_text`
**Purpose:** Apply formatting to specific text range in a paragraph

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `paragraph_index` | integer | ✅ | — | Paragraph number (0-based) |
| `start_pos` | integer | ✅ | — | Starting character position |
| `end_pos` | integer | ✅ | — | Ending character position |
| `bold` | boolean | ❌ | — | Make bold |
| `italic` | boolean | ❌ | — | Make italic |
| `underline` | boolean | ❌ | — | Add underline |
| `color` | string | ❌ | — | Text color (hex RGB) |
| `font_name` | string | ❌ | — | Font family |
| `font_size` | integer | ❌ | — | Font size in points |

**Returns:** Success message

**Errors:**
- File not found
- Paragraph index out of range
- Invalid character range
- File not writable

**Example:**
```
format_text(filename="Report.docx", paragraph_index=2, start_pos=0, end_pos=10, bold=true, color="FF0000")
```

---

#### `set_background_highlight`
**Purpose:** Add background highlight to text

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `paragraph_index` | integer | ✅ | — | Paragraph number (0-based) |
| `start_pos` | integer | ✅ | — | Starting character position |
| `end_pos` | integer | ✅ | — | Ending character position |
| `color` | string | ❌ | '0000FF' | Highlight color (hex RGB) |
| `use_shading` | boolean | ❌ | true | Use shading vs highlight |

**Returns:** Success message

**Errors:**
- File not found
- Paragraph index out of range
- Invalid character range
- File not writable

**Example:**
```
set_background_highlight(filename="Report.docx", paragraph_index=1, start_pos=5, end_pos=25, color="FFFF00")
```

---

#### `create_custom_style`
**Purpose:** Define a custom paragraph style

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `style_name` | string | ✅ | — | Name for new style |
| `bold` | boolean | ❌ | — | Make bold |
| `italic` | boolean | ❌ | — | Make italic |
| `font_size` | integer | ❌ | — | Font size in points |
| `font_name` | string | ❌ | — | Font family |
| `color` | string | ❌ | — | Text color (hex RGB) |
| `base_style` | string | ❌ | 'Normal' | Base style to inherit from |

**Returns:** Success message

**Errors:**
- File not found
- Style already exists
- Invalid base style
- File not writable

**Example:**
```
create_custom_style(filename="Report.docx", style_name="Executive", bold=true, font_size=14, base_style="Normal")
```

---

### **Table Operations Tools**

#### `add_table`
**Purpose:** Add a table to document with optional data

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `rows` | integer | ✅ | — | Number of rows |
| `cols` | integer | ✅ | — | Number of columns |
| `data` | array of arrays | ❌ | — | Data to populate (row-major order) |

**Returns:** Success message

**Errors:**
- File not found
- File not writable
- Data dimensions mismatch

**Example:**
```
add_table(filename="Report.docx", rows=4, cols=3, data=[["Header 1", "Header 2", "Header 3"], ["Row1Col1", "Row1Col2", "Row1Col3"]])
```

---

#### `format_table`
**Purpose:** Apply formatting to entire table (borders, style, shading)

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `table_index` | integer | ✅ | — | Table number (0-based) |
| `border_color` | string | ❌ | — | Border color (hex RGB) |
| `border_size` | integer | ❌ | — | Border width in points |
| `header_shading` | string | ❌ | — | Header row background color (hex RGB) |
| `row_shading` | string | ❌ | — | Alternating row color (hex RGB) |

**Returns:** Success message

**Errors:**
- File not found
- Table index out of range
- File not writable

**Example:**
```
format_table(filename="Report.docx", table_index=0, border_color="000000", border_size=2, header_shading="CCCCCC")
```

---

#### `highlight_table_header`
**Purpose:** Format the first row of a table as header

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `table_index` | integer | ✅ | — | Table number (0-based) |
| `header_color` | string | ❌ | '4472C4' | Header background color (hex RGB) |
| `text_color` | string | ❌ | 'FFFFFF' | Header text color (hex RGB) |

**Returns:** Success message

**Errors:**
- File not found
- Table index out of range
- File not writable

**Example:**
```
highlight_table_header(filename="Report.docx", table_index=0, header_color="003366", text_color="FFFFFF")
```

---

#### `set_table_cell_shading`
**Purpose:** Apply background color to specific table cells

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `table_index` | integer | ✅ | — | Table number (0-based) |
| `row_index` | integer | ✅ | — | Row number (0-based) |
| `col_index` | integer | ✅ | — | Column number (0-based) |
| `color` | string | ✅ | — | Cell background color (hex RGB) |

**Returns:** Success message

**Errors:**
- File not found
- Table/row/column index out of range
- File not writable

**Example:**
```
set_table_cell_shading(filename="Report.docx", table_index=0, row_index=1, col_index=2, color="FFFF00")
```

---

#### `set_table_cell_alignment`
**Purpose:** Set text alignment in specific table cell

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `table_index` | integer | ✅ | — | Table number (0-based) |
| `row_index` | integer | ✅ | — | Row number (0-based) |
| `col_index` | integer | ✅ | — | Column number (0-based) |
| `horizontal` | string | ❌ | — | 'left', 'center', 'right' |
| `vertical` | string | ❌ | — | 'top', 'center', 'bottom' |

**Returns:** Success message

**Errors:**
- File not found
- Table/row/column index out of range
- Invalid alignment value
- File not writable

**Example:**
```
set_table_cell_alignment(filename="Report.docx", table_index=0, row_index=0, col_index=1, horizontal="center", vertical="center")
```

---

#### `set_table_alignment_all`
**Purpose:** Set alignment for all cells in a table

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `table_index` | integer | ✅ | — | Table number (0-based) |
| `horizontal` | string | ❌ | — | 'left', 'center', 'right' |
| `vertical` | string | ❌ | — | 'top', 'center', 'bottom' |

**Returns:** Success message

**Errors:**
- File not found
- Table index out of range
- Invalid alignment value
- File not writable

**Example:**
```
set_table_alignment_all(filename="Report.docx", table_index=0, horizontal="center", vertical="top")
```

---

#### `set_table_cell_padding`
**Purpose:** Set internal padding (margins) for table cells

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `table_index` | integer | ✅ | — | Table number (0-based) |
| `row_index` | integer | ✅ | — | Row number (0-based) |
| `col_index` | integer | ✅ | — | Column number (0-based) |
| `top` | number | ❌ | — | Top padding in inches |
| `bottom` | number | ❌ | — | Bottom padding in inches |
| `left` | number | ❌ | — | Left padding in inches |
| `right` | number | ❌ | — | Right padding in inches |

**Returns:** Success message

**Errors:**
- File not found
- Table/row/column index out of range
- File not writable

**Example:**
```
set_table_cell_padding(filename="Report.docx", table_index=0, row_index=1, col_index=0, top=0.1, bottom=0.1, left=0.1, right=0.1)
```

---

#### `set_table_column_width`
**Purpose:** Set width of table column

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `table_index` | integer | ✅ | — | Table number (0-based) |
| `col_index` | integer | ✅ | — | Column number (0-based) |
| `width` | number | ✅ | — | Width value |
| `unit` | string | ❌ | 'inches' | 'inches', 'cm', 'points', 'percent' |

**Returns:** Success message

**Errors:**
- File not found
- Table/column index out of range
- Invalid width value
- File not writable

**Example:**
```
set_table_column_width(filename="Report.docx", table_index=0, col_index=1, width=2.5, unit="inches")
```

---

#### `auto_fit_table_columns`
**Purpose:** Auto-fit all columns in table to content

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `table_index` | integer | ✅ | — | Table number (0-based) |

**Returns:** Success message

**Errors:**
- File not found
- Table index out of range
- File not writable

**Example:**
```
auto_fit_table_columns(filename="Report.docx", table_index=0)
```

---

#### `merge_table_cells_vertical`
**Purpose:** Merge cells vertically in a column

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `table_index` | integer | ✅ | — | Table number (0-based) |
| `col_index` | integer | ✅ | — | Column number (0-based) |
| `start_row` | integer | ✅ | — | Starting row (0-based) |
| `end_row` | integer | ✅ | — | Ending row (0-based, inclusive) |

**Returns:** Success message

**Errors:**
- File not found
- Table/column/row index out of range
- Invalid range (end < start)
- File not writable

**Example:**
```
merge_table_cells_vertical(filename="Report.docx", table_index=0, col_index=0, start_row=1, end_row=3)
```

---

#### `merge_table_cells_horizontal`
**Purpose:** Merge cells horizontally in a row

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `table_index` | integer | ✅ | — | Table number (0-based) |
| `row_index` | integer | ✅ | — | Row number (0-based) |
| `start_col` | integer | ✅ | — | Starting column (0-based) |
| `end_col` | integer | ✅ | — | Ending column (0-based, inclusive) |

**Returns:** Success message

**Errors:**
- File not found
- Table/row/column index out of range
- Invalid range (end < start)
- File not writable

**Example:**
```
merge_table_cells_horizontal(filename="Report.docx", table_index=0, row_index=0, start_col=0, end_col=2)
```

---

#### `format_table_cell_text`
**Purpose:** Apply text formatting to specific table cell

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | string | ✅ | — | Document path |
| `table_index` | integer | ✅ | — | Table number (0-based) |
| `row_index` | integer | ✅ | — | Row number (0-based) |
| `col_index` | integer | ✅ | — | Column number (0-based) |
| `bold` | boolean | ❌ | — | Make bold |
| `italic` | boolean | ❌ | — | Make italic |
| `underline` | boolean | ❌ | — | Add underline |
| `color` | string | ❌ | — | Text color (hex RGB) |
| `font_name` | string | ❌ | — | Font family |
| `font_size` | integer | ❌ | — | Font size in points |

**Returns:** Success message

**Errors:**
- File not found
- Table/row/column index out of range
- File not writable

**Example:**
```
format_table_cell_text(filename="Report.docx", table_index=0, row_index=0, col_index=1, bold=true, color="0066CC", font_size=12)
```

---

### **Advanced Orchestration Tool**

#### `execute_plan`
**Purpose:** Execute multiple coordinated tool calls in phases

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `plan` | object | ✅ (or `plan_json`) | — | Plan object with phases and calls |
| `plan_json` | string | ✅ (or `plan`) | — | JSON string version of plan |

**Plan Structure:**
```json
{
  "plan": [
    {
      "phase": "phase_name",
      "calls": [
        {
          "tool": "tool_name",
          "args": {"param": "value"},
          "id": "unique_id"
        }
      ]
    }
  ]
}
```

**Returns:** Object with `success` (boolean), `context` (results by ID), `phases` (execution details)

**Errors:**
- Invalid plan structure
- Tool not found
- Any call failure stops execution

**Example:**
See Section 6 Orchestration Plans above.

---

### **Orchestration Plans (`execute_plan`)**

- Use `execute_plan` when a request needs a coordinated batch of tool calls (for example, pulling metadata and full text for several documents at once).
- Provide either a parsed `plan` object or a JSON string via `plan_json`. Each plan must include a `plan` array of phases. Any phase with a `calls` list dispatches all of its calls together; the next phase waits for every call in the previous phase to finish.
- Every call entry needs a `tool` name, optional `id`, and an `args` object. Use {"$ref": "<call-id>"} inside `args` to feed the result of a prior call into a later call.
- The response exposes a `context` dictionary keyed by call ids and a `phases` array that details each call so you can cite the exact outputs in your final answer. If any call fails, `execute_plan` reports `success: False`, includes the error detail, and stops the plan.
- `code` phases (arbitrary Python snippets) are blocked and must never be requested.

**Example plan payload**

```json
{
  "plan": [
    {
      "phase": "fan-out",
      "calls": [
        {
          "tool": "get_document_info_or_content",
          "args": {"filename": "Contracts/msa_v7.docx", "request_type": "info"},
          "id": "info:msa"
        },
        {
          "tool": "get_document_info_or_content",
          "args": {"filename": "Contracts/msa_v7.docx", "request_type": "text"},
          "id": "text:msa"
        }
      ]
    },
    {
      "phase": "collect",
      "calls": [
        {
          "tool": "merge_documents",
          "args": {
            "primary_filename": {"$ref": "info:msa"},
            "secondary_filename": "Contracts/appendix.docx"
          },
          "id": "merge:msa"
        }
      ]
    }
  ]
}
```

When you report results, include the `execute_plan` call first, then summarize the relevant entries from the returned `context` (for example, reference `context["info:msa"]`), and finally list any follow-up actions triggered by the plan.

---

### 📘 Summary

| Category | Description |
|-----------|--------------|
| **Document Management** | Discover, create, copy, and convert Word files |
| **Content Creation & Manipulation** | Add or modify content (headings, paragraphs, targeted inserts, comments, etc.) |
| **Extraction and Analysis** | Extract structured content or search within documents |
| **Formatting & Styles** | Apply rich formatting, styles, and table layouts |
| **Comments** | Add, retrieve or filter document comments |


---

## 7. Common Mistakes to Avoid (Anti-Patterns)

### ❌ Don't Use the Wrong Tool for the Job
**Mistake:** Using `search_and_replace()` when you need `format_text()`
- `search_and_replace()` changes **content** (text replacement)
- `format_text()` changes **appearance** (bold, color, font)

If user says "make that bold," use `format_text()` not `search_and_replace()`.

**Mistake:** Using `add_paragraph()` when you need `insert_numbered_list_near_text()`
- `add_paragraph()` appends to end of document
- `insert_numbered_list_near_text()` places list relative to target text

---

### ❌ Don't Skip Versioning for Modifications
**Mistake:** Modifying a document without first creating a copy
```
// WRONG:
add_heading(filename="Report.docx", ...)  // Overwrites original!

// CORRECT:
copy_document(filename="Report.docx", new_filename="Report_v1.docx")
add_heading(filename="Report_v1.docx", ...)
```

**Exception:** Read-only operations (`get_*`, `find_*`, `list_*`) do not require copying.

---

### ❌ Don't Assume Paragraph Indices Are Stable
**Mistake:** Using cached paragraph indices after modifications
```
// Paragraph indices CHANGE after deletions/insertions:
para_info = get_paragraph_text_from_document(..., paragraph_index=5)
delete_paragraph(..., paragraph_index=2)  // Now paragraph 5 is at index 4!
format_text(..., paragraph_index=5, ...)  // WRONG INDEX!
```

**Correct approach:** Refetch document structure if making multi-step edits, or use search-based approaches (`find_text_in_document()`, `replace_block_between_manual_anchors()`).

---

### ❌ Don't Assume Relative Paths Work Universally
**Mistake:** Mixing relative and absolute paths
```
// May fail inconsistently:
copy_document(filename="Report.docx", new_filename="../backups/Report_v1.docx")
```

**Correct approach:** Always use **absolute paths** or paths relative to a known directory (`EL_Projects\[project]\`).

---

### ❌ Don't Try to Modify Non-Existent Content
**Mistake:** Attempting operations on invalid indices or missing text
```
// These will fail:
format_text(..., paragraph_index=99, ...)  // Out of range
delete_paragraph(..., paragraph_index=-1, ...)  // Invalid index
add_comment_after_text(..., search_text="[text not in doc]", ...)
```

**Correct approach:** Always validate before modifying:
1. Use `find_text_in_document()` or `get_paragraph_text_from_document()` first
2. Confirm the index/text exists
3. Then perform modification

---

### ❌ Don't Forget Array/JSON Structure for Complex Parameters
**Mistake:** Passing flat strings instead of arrays for `list_items` or `data`
```
// WRONG:
insert_numbered_list_near_text(..., list_items="Item 1, Item 2")
add_table(..., data="Header1, Header2, Row1Col1, Row1Col2")

// CORRECT:
insert_numbered_list_near_text(..., list_items=["Item 1", "Item 2"])
add_table(..., data=[["Header1", "Header2"], ["Row1Col1", "Row1Col2"]])
```

---

## 8. Safety and Integrity Rules

Before any modifying operation:
- The **original file is never altered**.
- A **new version** is always created.
- All actions are logged and described in plain English.
- You can always work on older versions explicitly.

---

## 9. Example Scenarios

### **Scenario 1 – Create**
```
User: Ask EL to create a document named Report.docx with a title “Q1 Analysis”
→ the LLM: Uses create_document()
✅ Creates Report.docx
```

### **Scenario 2 – Edit**
```
User: Ask EL to bold paragraph 2
→ the LLM: Copies document, applies format_text()
🆟️ Creates Report_v2.docx
```

### **Scenario 3 – Branch from old version**
```
User: Ask EL to update version 1 with new logo
→ the LLM: Copies Report_v1.docx → Report_v4_from_v1.docx
✅ Applies add_picture()
🧠 Explains this is a new branch copy
```

### **Scenario 4 – Ambiguous request**
```
User: Ask EL to add a note after the introduction
→ the LLM: Offers two options: add_paragraph or insert_str_content_near_text
```

---

## 10. Version Naming Convention

| Case | New File Name |
|------|----------------|
| Default modification | `_vN` |
| Branch from older version | `_vM_from_vN` |
| Manual rename requested | Uses user-provided name with `_v#` suffix added automatically if omitted |

Example sequence:
```
Proposal.docx → Proposal_v1.docx → Proposal_v2.docx
→ Proposal_v3.docx → Proposal_v4_from_v2.docx
```

---

## 11. Error Handling

If a command fails:
- the LLM will show the **tool called**, **parameters used**, and **the error message**.
- It will not attempt retries unless you explicitly approve.
- the LLM will always confirm which file (and version) was being modified.

---

## 12. ✅ Summary Table

| Category | the LLM Behavior |
|-----------|------------------|
| Trigger Phrase | “Ask EL [instruction]” |
| Tool Selection | Auto-detects or presents options |
| Modifications | Always create new copies |
| Versioning | `_v1`, `_v2`, `_v3`, `_v4_from_v2`, etc. |
| Storage | `EL_Projects\[project name]\` |
| Directory Check | Prompt user if missing project folder |
| Safety | Original document never edited |
| Transparency | Explains tool used, reason, and new version |
| Default Target | Most recent document version |


---

## 13. Execution Guardrails: No-Hallucination & Enforcement

To ensure reliable, verifiable, and non-fabricated tool execution, these guardrails apply to **all connector/tool interactions** (e.g., EL, API, Model Context Protocol tools).

---

### Table of Contents
- [11.1 Core Principles](#111-core-principles)
- [11.2 Standard Response Structure](#112-standard-response-structure)
- [11.3 Output Presentation Rules](#113-output-presentation-rules)
- [11.4 Example — Read-Only Listing Command](#114-example--read-only-listing-command)
- [11.5 Compliance Summary](#115-compliance-summary)

---

### 11.1 Core Principles

- **Never claim a tool was used unless it actually executed.**  
- **Never fabricate or infer tool output** — file names, lists, or counts must come directly from connector payloads.  
- **Stop immediately** if a tool or connector is unavailable — no simulated or placeholder results.  
- Every response must include a clearly labeled **Execution Status** line:

```text
Execution: SUCCESS | FAILED (reason) | SKIPPED (awaiting confirmation / connector not available)
```

---

### 11.2 Standard Response Structure

All tool operations must follow this reporting schema:

| Field | Description |
|---|---|
| **Execution** | `SUCCESS`, `FAILED`, or `SKIPPED` (include reason) |
| **Tool used** | Tool name (e.g., `list_available_documents`) |
| **Tool call** | Full resolved call with arguments (redact secrets) |
| **Reason** | Mapping from user request to tool function |
| **Action** | What the tool was asked to do |
| **Raw output** | Verbatim connector payload in a fenced block labeled *From EL* (limit: first 100 items or 2 KB) |
| **Post-processing** | Optional — filters applied (e.g., `.docx` only) |
| **Result / Version** | New filename, record ID, or version tag (if applicable) |

**Example format:**

```text
Execution: SUCCESS
Tool used: list_available_documents
Tool call: list_available_documents(directory="EL_Projects\ToolTest\")
From EL (raw):
["ToolTest_Overview.docx", "ToolTest_Specifications_v1.docx"]
```

**If no results:**

```text
Execution: SUCCESS
From EL (raw): []
No documents found.
```

**If connector unavailable:**

```text
Execution: SKIPPED (connector not available)
Suggestion: Verify EL connection in Model Context Protocol configuration.
```

**If directory missing:**

```text
Execution: FAILED (directory not found)
Remedy: Create folder EL_Projects\ToolTest\ ? [Yes/No]
```

---

### 11.3 Output Presentation Rules

- **Always** echo the exact tool call and show the **verbatim connector payload**.  
- Label all raw data consistently:

```text
From EL (raw):
[actual connector response]
```

- **Never** synthesize, guess, or infer content.  
- Truncate long payloads to **first 100 items / 2 KB**.  
- If a connector returns an empty array, the only valid completion is:

```text
Execution: SUCCESS
From EL (raw): []
No documents found.
```

---

### 11.4 Example — Read-Only Listing Command

**User request:**

```text
Ask EL to list all .docx files for the ToolTest project
```

**Expected flow:**

1. Run readiness checks (server, tool, directory).  
2. Execute:

   ```text
   list_available_documents(directory="EL_Projects\ToolTest\")
   ```

3. Display *From EL (raw)* block with raw array.  
4. Apply a `.docx` client-side filter and present final list.

**If no `.docx` files found:**

```text
Execution: SUCCESS
From EL (raw): []
No .docx files found.
Suggestion: Verify the folder exists.
```

---

### 11.5 Compliance Summary

#### ✅ Do
- Report connector payloads exactly as returned.  
- Include structured status, call, and output blocks in every response.  
- Use *SKIPPED* or *FAILED* with clear reasons when applicable.

#### 🚫 Don’t
- Invent or simulate tool outputs.  
- Assume success when a tool did not run.  
- Continue generation after reporting connector unavailability.

---


