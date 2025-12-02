# Effi Contract Editor - User Guide

A guide for lawyers using the Effi Contract Editor in VS Code.

---

## Getting Started

### Opening a Contract

1. Open VS Code
2. Navigate to your project folder (e.g., `EL_Projects/MyProject/`)
3. Find your contract in `drafts/current_drafts/`
4. Click the **📚 book icon** in the editor toolbar to analyze the document

The Contract Analysis panel will open showing your document structure.

---

## Viewing Your Contract

### Outline View

The **Outline** tab shows a compact hierarchical view of your contract:

- Numbered clauses with proper indentation
- Checkboxes for selecting clauses
- Quick navigation to any section

Use this view when you need to:
- Get an overview of the contract structure
- Jump to a specific clause
- Select multiple clauses for LLM analysis

### Full Text View

The **Full Text** tab shows complete clause text:

- Every paragraph displayed in full
- Checkboxes synchronized with Outline view
- Note boxes for annotations

Use this view when you need to:
- Read the complete contract text
- Edit clauses (in Edit Mode)
- Add notes to specific clauses

---

## Editing Your Contract

### Entering Edit Mode

1. Go to the **Full Text** tab
2. Click the **✏️ Edit Mode** button (top right of content area)
3. The toolbar appears with formatting buttons

### Making Edits

**Basic Text Editing:**
- Click on any clause text to place your cursor
- Type to insert new text
- Use Backspace/Delete to remove text
- Press Enter to create a new paragraph

**Text Formatting:**
| Action | Toolbar Button | Keyboard Shortcut |
|--------|----------------|-------------------|
| Bold | **B** | Ctrl+B |
| Italic | *I* | Ctrl+I |
| Underline | U | Ctrl+U |

To format text:
1. Select the text you want to format
2. Click the format button OR use the keyboard shortcut
3. Click again to remove formatting

**Undo/Redo:**
- Click **↶** or press Ctrl+Z to undo
- Click **↷** or press Ctrl+Y to redo
- Up to 50 levels of undo available

### Saving Your Changes

1. Click the **💾 Save** button OR press Ctrl+S
2. Watch the status indicator:
   - "Saving..." - Save in progress
   - "Saved ✓" - Changes saved successfully
   - "Save failed" - Error occurred (check message)

**Important:** Your changes are saved directly to the .docx file. The document can be opened in Microsoft Word to verify changes.

### Exiting Edit Mode

Click the **📖 View Mode** button to return to read-only view.

---

## Version Control

### Automatic Versioning

Every time you save, your changes are automatically versioned using Git:

- A snapshot is created with timestamp
- Commit message includes what changed
- Full history preserved for audit trail

### Viewing Version History

1. Open Command Palette (Ctrl+Shift+P)
2. Type "Effi: Show Version History"
3. Browse the list of previous versions
4. Each entry shows:
   - Date and time
   - Author
   - Summary of changes

### Creating a Checkpoint

Before making major changes, create a named checkpoint:

1. Open Command Palette (Ctrl+Shift+P)
2. Type "Effi: Save Checkpoint"
3. Enter a note describing this version (e.g., "Before restructuring Section 5")
4. Checkpoint is created with your note

---

## Using LLM Chat for Contract Review

### Selecting Clauses for Analysis

1. Check the boxes next to clauses you want to analyze
2. Clauses can be selected in either Outline or Full Text view
3. The selection count shows at the bottom

### Asking Questions

1. Type your question in the text box at the bottom
2. Click **Ask Copilot**
3. The selected clauses + your question are copied to clipboard
4. Copilot Chat opens (if available)
5. Paste (Ctrl+V) to send the context to the LLM

**Example Questions:**
- "Are there any unusual liability provisions in these clauses?"
- "Compare the indemnity clauses to standard market terms"
- "Identify any missing protections for the customer"

---

## Notes and Annotations

### Adding Notes to Clauses

Each clause in Full Text view has a note box on the right:

1. Click in the note box next to any clause
2. Type your notes
3. Notes are saved automatically when you click away

### Note Suggestions

Use notes for:
- Questions to raise with the other party
- Internal review comments
- References to relevant precedents
- Drafting reminders

---

## Best Practices

### Before Editing

1. **Review in Outline first** - Understand the structure
2. **Create a checkpoint** - Before major changes
3. **Select relevant clauses** - For LLM context

### While Editing

1. **Save frequently** - Ctrl+S after each significant change
2. **Use formatting sparingly** - Bold for definitions, avoid over-formatting
3. **Keep paragraph structure** - Don't merge unrelated clauses

### After Editing

1. **Verify in Word** - Open the .docx to check formatting
2. **Review version history** - Ensure changes are tracked
3. **Share the .docx** - The file is the source of truth

---

## Keyboard Shortcuts Reference

| Action | Shortcut |
|--------|----------|
| Bold | Ctrl+B |
| Italic | Ctrl+I |
| Underline | Ctrl+U |
| Undo | Ctrl+Z |
| Redo | Ctrl+Y |
| Save | Ctrl+S |

---

## Troubleshooting

### "No analysis found" message

The document hasn't been analyzed yet. Click the book icon to analyze.

### Changes not appearing in Word

1. Ensure you clicked Save (check for "Saved ✓")
2. Close and reopen the document in Word
3. Check the correct .docx file is being opened

### Formatting looks different in Word

Some formatting may render slightly differently. The underlying document structure is preserved.

### "Save failed" error

1. Check the document isn't open in another application
2. Verify you have write permission to the file
3. Check the error message for details

---

## Getting Help

- **Command Palette**: Ctrl+Shift+P → type "Effi" to see all commands
- **Developer Tools**: Help → Toggle Developer Tools (for debugging)
- **Documentation**: See `docs/` folder in project repository
