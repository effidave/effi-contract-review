# Effi Contract Viewer Extension

Interactive VS Code extension for viewing and navigating analyzed Word contract documents.

## Prerequisites

1. **Node.js** (v18 or higher) - [Download](https://nodejs.org/)
2. **VS Code** (v1.85 or higher)
3. **Python 3.11+** with effilocal package installed

## Setup

1. Install dependencies:
   ```bash
   cd extension
   npm install
   ```

2. Build the extension:
   ```bash
   npm run compile
   ```

3. Launch the extension in development mode:
   - Press `F5` in VS Code (from the `extension/` directory)
   - Or run: `npm run watch` and then press `F5`

## Usage

### Analyzing a Document

1. Open a `.docx` file in VS Code
2. Click the book icon (📖) in the editor toolbar
3. Or use Command Palette: `Effi: Show Contract Analysis`

### Features

- **Document Info**: View metadata, block count, sections, attachments
- **Outline View**: Navigate document structure (coming soon)
- **Schedules**: View attachments and annexes (coming soon)
- **Jump to Clause**: Click clause to navigate in Word (coming soon)

## Configuration

Open VS Code settings and search for "Effi Contract Viewer":

- `effiContractViewer.pythonPath`: Path to Python interpreter (default: `.venv/Scripts/python.exe`)
- `effiContractViewer.mcpServerCommand`: Command to start MCP server
- `effiContractViewer.autoAnalyze`: Auto-analyze .docx files on open
- `effiContractViewer.showNumberingMetadata`: Show detailed numbering info

## Development

### Project Structure

```
extension/
├── src/
│   ├── extension.ts          # Extension entry point
│   └── webview/
│       ├── main.js            # Webview logic
│       └── style.css          # Webview styling
├── dist/                      # Compiled output
├── package.json               # Extension manifest
├── tsconfig.json              # TypeScript config
└── esbuild.js                 # Build configuration
```

### Commands

- `npm run compile` - Compile TypeScript
- `npm run watch` - Watch mode for development
- `npm run lint` - Run ESLint
- `npm run package` - Package for production

### Testing

1. Press `F5` to launch Extension Development Host
2. Open a `.docx` file from `EL_Projects/`
3. Click the book icon or run `Effi: Show Contract Analysis`
4. Verify the webview opens and displays document info

## Integration with Analysis Pipeline

The extension expects analyzed documents in this structure:

```
EL_Projects/
└── <Project Name>/
    ├── drafts/
    │   └── current_drafts/
    │       └── document.docx
    └── analysis/                # Created by analysis pipeline
        ├── manifest.json
        ├── index.json
        ├── blocks.jsonl
        ├── sections.json
        ├── relationships.json
        └── styles.json
```

To analyze a document:
```bash
python -m effilocal.cli analyze "path/to/document.docx" --doc-id <uuid> --out "path/to/analysis"
```

Or use the extension command: `Effi: Analyze Document` (coming soon - will integrate with MCP server)

## Next Steps

- [ ] Integrate artifact loader for outline display
- [ ] Add clause navigation tree view
- [ ] Implement MCP server communication for live analysis
- [ ] Add search/filter functionality
- [ ] Show clause relationships and continuations
- [ ] Highlight changed clauses (EditHistory integration)

## Troubleshooting

### Extension doesn't activate
- Check VS Code version (need 1.85+)
- Run `npm run compile` to build
- Check Output panel: "Extension Host"

### Webview shows "No analysis found"
- Ensure document has been analyzed
- Check analysis directory exists at expected location
- Verify `manifest.json` and `index.json` exist

### TypeScript errors
- Run `npm install` to ensure dependencies are installed
- Check `tsconfig.json` for correct paths
