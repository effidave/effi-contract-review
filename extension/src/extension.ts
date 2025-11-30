import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { exec, spawn } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

let webviewPanel: vscode.WebviewPanel | undefined;
let currentDocumentPath: string | undefined;

export function activate(context: vscode.ExtensionContext) {
    console.log('Effi Contract Viewer is now active');

    // Register command to show webview
    const showWebviewCommand = vscode.commands.registerCommand(
        'effi-contract-viewer.showWebview',
        () => showContractWebview(context)
    );

    // Register command to load analysis from current workspace
    const loadAnalysisCommand = vscode.commands.registerCommand(
        'effi-contract-viewer.loadAnalysis',
        async () => {
            if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
                vscode.window.showWarningMessage('No workspace folder open');
                return;
            }
            const workspaceRoot = vscode.workspace.workspaceFolders[0].uri.fsPath;
            const analysisDir = path.join(workspaceRoot, 'analysis');
            
            if (fs.existsSync(analysisDir)) {
                await loadAnalysisFromDirectory(analysisDir, workspaceRoot);
            } else {
                vscode.window.showWarningMessage('No analysis directory found in workspace');
            }
        }
    );

    // Register command to analyze document
    const analyzeCommand = vscode.commands.registerCommand(
        'effi-contract-viewer.analyzeDocument',
        async () => {
            const editor = vscode.window.activeTextEditor;
            if (editor && editor.document.uri.scheme === 'file') {
                await analyzeDocument(editor.document.uri.fsPath);
            } else {
                vscode.window.showWarningMessage('No active document to analyze');
            }
        }
    );

    // Register command to refresh view
    const refreshCommand = vscode.commands.registerCommand(
        'effi-contract-viewer.refreshView',
        () => {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ command: 'refresh' });
            }
        }
    );

    context.subscriptions.push(showWebviewCommand, analyzeCommand, refreshCommand, loadAnalysisCommand);

    // Auto-analyze on .docx file open if configured
    const autoAnalyze = vscode.workspace.getConfiguration('effiContractViewer').get<boolean>('autoAnalyze');
    if (autoAnalyze) {
        vscode.workspace.onDidOpenTextDocument((doc) => {
            if (doc.uri.fsPath.endsWith('.docx')) {
                analyzeDocument(doc.uri.fsPath);
            }
        });
    }
}

export function deactivate() {
    if (webviewPanel) {
        webviewPanel.dispose();
    }
}

function showContractWebview(context: vscode.ExtensionContext) {
    const columnToShowIn = vscode.window.activeTextEditor
        ? vscode.window.activeTextEditor.viewColumn
        : undefined;

    if (webviewPanel) {
        // If panel exists, reveal it
        webviewPanel.reveal(columnToShowIn);
    } else {
        // Create new panel
        webviewPanel = vscode.window.createWebviewPanel(
            'effiContractViewer',
            'Contract Analysis',
            vscode.ViewColumn.Beside,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.file(path.join(context.extensionPath, 'dist')),
                    vscode.Uri.file(path.join(context.extensionPath, 'src', 'webview'))
                ]
            }
        );

        // Set HTML content
        webviewPanel.webview.html = getWebviewContent(context, webviewPanel.webview);

        // Handle messages from webview
        webviewPanel.webview.onDidReceiveMessage(
            async (message) => {
                switch (message.command) {
                    case 'analyze':
                        await analyzeDocument(message.documentPath);
                        break;
                    case 'jumpToClause':
                        jumpToClause(message.paraId);
                        break;
                    case 'sendToChat':
                        await sendClausesToChat(message.clauseIds, message.query);
                        break;
                    case 'ready':
                        console.log('Webview ready');
                        // Send initial data if available
                        if (currentDocumentPath) {
                            loadAnalysisData(currentDocumentPath);
                        }
                        break;
                }
            },
            undefined,
            context.subscriptions
        );

        // Handle panel disposal
        webviewPanel.onDidDispose(
            () => {
                webviewPanel = undefined;
                vscode.commands.executeCommand('setContext', 'effiContractViewerActive', false);
            },
            null,
            context.subscriptions
        );

        vscode.commands.executeCommand('setContext', 'effiContractViewerActive', true);
    }
}

async function analyzeDocument(documentPath: string) {
    currentDocumentPath = documentPath;
    
    if (!fs.existsSync(documentPath)) {
        vscode.window.showErrorMessage(`Document not found: ${documentPath}`);
        return;
    }

    vscode.window.showInformationMessage(`Analyzing: ${path.basename(documentPath)}`);

    // TODO: Call Python MCP server to analyze document
    // For now, just try to load existing analysis
    await loadAnalysisData(documentPath);
}

async function loadAnalysisFromDirectory(analysisDir: string, projectPath: string) {
    if (!fs.existsSync(analysisDir)) {
        webviewPanel?.webview.postMessage({
            command: 'noAnalysis',
            message: 'No analysis found in workspace.'
        });
        return;
    }

    // Check for required artifacts
    const manifestPath = path.join(analysisDir, 'manifest.json');
    const indexPath = path.join(analysisDir, 'index.json');

    if (!fs.existsSync(manifestPath) || !fs.existsSync(indexPath)) {
        webviewPanel?.webview.postMessage({
            command: 'noAnalysis',
            message: 'Analysis artifacts incomplete.'
        });
        return;
    }

    try {
        const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
        const index = JSON.parse(fs.readFileSync(indexPath, 'utf-8'));

        // Load outline data using Python script
        let outline = [];
        try {
            // __dirname is dist/ after compilation, so go up one level to reach scripts/
            const scriptPath = path.join(__dirname, '..', 'scripts', 'get_outline.py');
            // Python needs to run from the workspace root to import effilocal
            const workspaceRoot = path.join(__dirname, '..', '..');
            const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
            const { stdout } = await execAsync(`cd "${workspaceRoot}" && ${pythonCmd} "${scriptPath}" "${analysisDir}"`);
            const outlineResult = JSON.parse(stdout);
            if (outlineResult.success) {
                outline = outlineResult.outline;
                console.log(`Loaded ${outline.length} outline items`);
            } else {
                console.error('Failed to load outline:', outlineResult.error);
            }
        } catch (error) {
            console.error('Error executing Python script:', error);
            console.error('Script path would be:', path.join(__dirname, '..', 'scripts', 'get_outline.py'));
            console.error('Analysis dir:', analysisDir);
        }

        // Load blocks.jsonl for full text view
        let blocks = [];
        const blocksPath = path.join(analysisDir, 'blocks.jsonl');
        if (fs.existsSync(blocksPath)) {
            try {
                const blocksContent = fs.readFileSync(blocksPath, 'utf-8');
                blocks = blocksContent.trim().split('\\n')
                    .filter(line => line.trim())
                    .map(line => JSON.parse(line));
                console.log(`Loaded ${blocks.length} blocks from blocks.jsonl`);
            } catch (error) {
                console.error('Error loading blocks.jsonl:', error);
            }
        }

        webviewPanel?.webview.postMessage({
            command: 'updateData',
            data: {
                manifest,
                index,
                analysisDir,
                documentPath: projectPath,
                outline,
                blocks
            }
        });

        vscode.window.showInformationMessage('Analysis loaded successfully');
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to load analysis: ${error}`);
    }
}

async function loadAnalysisData(documentPath: string) {
    // Determine analysis directory based on document path
    // Expected: EL_Projects/<project>/drafts/current_drafts/<file>.docx
    //        -> EL_Projects/<project>/analysis/
    
    const docDir = path.dirname(documentPath);
    const projectDir = path.dirname(path.dirname(docDir)); // Go up two levels
    const analysisDir = path.join(projectDir, 'analysis');

    if (!fs.existsSync(analysisDir)) {
        webviewPanel?.webview.postMessage({
            command: 'noAnalysis',
            message: 'No analysis found. Run "Effi: Analyze Document" first.'
        });
        return;
    }

    // Check for required artifacts
    const manifestPath = path.join(analysisDir, 'manifest.json');
    const indexPath = path.join(analysisDir, 'index.json');

    if (!fs.existsSync(manifestPath) || !fs.existsSync(indexPath)) {
        webviewPanel?.webview.postMessage({
            command: 'noAnalysis',
            message: 'Analysis artifacts incomplete.'
        });
        return;
    }

    try {
        const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
        const index = JSON.parse(fs.readFileSync(indexPath, 'utf-8'));

        // Load blocks.jsonl for full text view
        let blocks = [];
        const blocksPath = path.join(analysisDir, 'blocks.jsonl');
        if (fs.existsSync(blocksPath)) {
            try {
                const blocksContent = fs.readFileSync(blocksPath, 'utf-8');
                blocks = blocksContent.trim().split('\\n')
                    .filter(line => line.trim())
                    .map(line => JSON.parse(line));
                console.log(`Loaded ${blocks.length} blocks from blocks.jsonl`);
            } catch (error) {
                console.error('Error loading blocks.jsonl:', error);
            }
        }

        webviewPanel?.webview.postMessage({
            command: 'updateData',
            data: {
                manifest,
                index,
                analysisDir,
                documentPath,
                blocks
            }
        });

        vscode.window.showInformationMessage('Analysis loaded successfully');
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to load analysis: ${error}`);
    }
}

function jumpToClause(paraId: string) {
    // TODO: Implement jumping to clause in Word document
    // This will require interacting with the Word document
    vscode.window.showInformationMessage(`Jump to clause: ${paraId}`);
}

async function sendClausesToChat(clauseIds: string[], query: string) {
    try {
        // Get clause details using Python script
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
        if (!workspaceRoot) {
            vscode.window.showErrorMessage('No workspace folder open');
            return;
        }

        const analysisDir = path.join(workspaceRoot, 'analysis');
        const scriptPath = path.join(__dirname, '..', 'scripts', 'get_clause_details.py');
        const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
        const workspaceRootForPython = path.join(__dirname, '..', '..');
        
        // Use spawn to pass clause IDs via stdin (avoids shell escaping issues)
        const result = await new Promise<any>((resolve, reject) => {
            const proc = spawn(pythonCmd, [scriptPath, analysisDir], {
                cwd: workspaceRootForPython,
                shell: false
            });
            
            let stdout = '';
            let stderr = '';
            
            proc.stdout.on('data', (data) => { stdout += data.toString(); });
            proc.stderr.on('data', (data) => { stderr += data.toString(); });
            
            proc.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error(`Python script exited with code ${code}: ${stderr}`));
                } else {
                    try {
                        resolve(JSON.parse(stdout));
                    } catch (e) {
                        reject(new Error(`Failed to parse JSON: ${stdout}`));
                    }
                }
            });
            
            // Write clause IDs to stdin
            proc.stdin.write(JSON.stringify(clauseIds));
            proc.stdin.end();
        });
        
        if (!result.success) {
            vscode.window.showErrorMessage(`Failed to get clause details: ${result.error}`);
            return;
        }

        // Format context for chat
        const clauseContext = result.clauses.map((clause: any) => 
            `Clause ${clause.ordinal}: ${clause.text}`
        ).join('\n\n');

        const fullPrompt = `Context - Selected clauses from contract:\n\n${clauseContext}\n\nQuestion: ${query}`;

        // Copy to clipboard and open chat
        await vscode.env.clipboard.writeText(fullPrompt);
        
        vscode.window.showInformationMessage(
            `✓ Copied ${result.clauses.length} clause${result.clauses.length !== 1 ? 's' : ''} + question to clipboard`,
            'Open Chat'
        ).then(action => {
            if (action === 'Open Chat') {
                vscode.commands.executeCommand('workbench.action.chat.open');
            }
        });

    } catch (error) {
        console.error('Error sending to chat:', error);
        vscode.window.showErrorMessage(`Failed to send to chat: ${error}`);
    }
}

function getWebviewContent(context: vscode.ExtensionContext, webview: vscode.Webview): string {
    const htmlPath = path.join(context.extensionPath, 'src', 'webview', 'index.html');
    const scriptPath = path.join(context.extensionPath, 'src', 'webview', 'main.js');
    const stylePath = path.join(context.extensionPath, 'src', 'webview', 'style.css');

    const scriptUri = webview.asWebviewUri(vscode.Uri.file(scriptPath));
    const styleUri = webview.asWebviewUri(vscode.Uri.file(stylePath));

    // Use CSP nonce for security
    const nonce = getNonce();

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="${styleUri}" rel="stylesheet">
    <title>Contract Analysis</title>
</head>
<body>
    <div id="app">
        <div class="header">
            <h1>Contract Analysis</h1>
            <div class="toolbar">
                <button id="refresh-btn" class="icon-button" title="Refresh">
                    <span class="codicon codicon-refresh"></span>
                </button>
            </div>
        </div>
        
        <div class="content">
            <div id="loading" class="message">
                <p>No analysis loaded. Open a .docx file and click the book icon to analyze.</p>
            </div>
            
            <div id="data-view" style="display: none;">
                <div class="section">
                    <h2>Document Info</h2>
                    <div id="doc-info"></div>
                </div>
                
                <div class="section">
                    <div class="tabs">
                        <button id="outline-tab" class="tab-button active">Outline</button>
                        <button id="fulltext-tab" class="tab-button">Full Text</button>
                    </div>
                    
                    <div id="outline-content" class="tab-content"></div>
                    <div id="fulltext-content" class="tab-content" style="display: none;"></div>
                    
                    <div class="chat-query-box">
                        <div class="selection-info">
                            <span id="selection-count">0 clauses selected</span>
                            <button id="clear-selection" class="secondary-button">Clear</button>
                        </div>
                        <textarea id="chat-query" placeholder="Ask a question about the selected clauses..."></textarea>
                        <button id="send-to-chat" class="primary-button">Send to Chat</button>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Schedules</h2>
                    <div id="schedules"></div>
                </div>
            </div>
        </div>
    </div>
    
    <script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
}

function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}
