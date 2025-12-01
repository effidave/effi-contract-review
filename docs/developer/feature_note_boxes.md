# Note Box Feature Implementation

## Overview
The Note Box feature allows users to add personal notes to specific clauses or paragraphs within the VS Code Webview. These notes are persisted directly into the source Word document (`.docx`) as comments, ensuring that annotations travel with the file.

## Architecture

### 1. User Interface (Webview)
- **Component**: Editable `<textarea>` elements added to the right of each document block in the Webview.
- **Event Handling**: 
  - Listens for `change` events (triggered on blur/focus loss).
  - Sends a `saveNote` message to the extension host with:
    - `blockId`: The unique ID of the block from `blocks.jsonl`.
    - `paraIdx`: The paragraph index in the Word document.
    - `text`: The content of the note.
- **Data Loading**: On startup, the Webview receives a map of existing notes (`notesMap`) and pre-populates the text areas.

### 2. Extension Host (VS Code)
- **Message Handling**: The `extension.ts` handles the `saveNote` command.
- **Process Execution**: Spawns a Python process (`manage_notes.py`) to perform the actual document modification.
- **Environment**: Uses the project's Python virtual environment (`.venv`) to ensure dependencies are available.

### 3. Python Bridge (`manage_notes.py`)
- **Role**: Acts as an intermediary between the VS Code extension and the MCP tools.
- **Functionality**:
  - `get_notes`: Retrieves all comments starting with `EFFI_NOTE:` and maps them to paragraph indices.
  - `save_note`: Calls MCP tools to add or update comments.
- **Integration**: Imports `effilocal.mcp_server.tools.comment_tools` to leverage standardized MCP functionality.

### 4. MCP Server Integration
The feature relies on enhancements to the Effi Local MCP Server:

#### Core Enhancements (`effilocal/mcp_server/core/comments.py`)
- **Paragraph Mapping**: The `extract_all_comments` function was updated to scan the document body and map comments to their `paragraph_index`. This is crucial for linking comments back to the correct text block in the UI.
- **Status Support**: Maintains compatibility with the comment status tracking (active/resolved) from `commentsExtended.xml`.

#### Tool Enhancements (`effilocal/mcp_server/tools/comment_tools.py`)
- **`update_comment`**: A new tool added to allow modifying the text of an existing comment by its ID.
- **`add_comment_for_paragraph`**: Used to create new notes attached to specific paragraphs.

## Data Persistence Format
- **Storage**: Word Comments (`comments.xml`).
- **Format**: Notes are prefixed with `EFFI_NOTE:` to distinguish them from regular document comments.
  - Example: `EFFI_NOTE: This clause needs review.`
- **Location**: Anchored to the specific paragraph index corresponding to the block in the analysis.

## Workflow
1. **Load**: 
   - Extension calls `manage_notes.py get_notes`.
   - Script fetches comments via MCP, filters for `EFFI_NOTE:`, and returns a map of `para_idx -> text`.
   - Webview renders blocks and fills text areas.
2. **Save**:
   - User edits text and clicks away.
   - Webview sends `saveNote`.
   - Extension calls `manage_notes.py save_note`.
   - Script checks for existing `EFFI_NOTE:` comment on that paragraph.
   - Calls `update_comment` (if exists) or `add_comment_for_paragraph` (if new).
   - Word document is updated.
