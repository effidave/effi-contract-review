import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { exec, spawn } from 'child_process';
import { promisify } from 'util';
import { ProjectProvider } from './projectProvider';
import { PlanProvider, TaskUpdateOptions } from './models/planProvider';
import type { TaskStatus, WorkPlanJSON } from './models/workplan';
import { EffiChatParticipant } from './chatParticipant';

const execAsync = promisify(exec);

let webviewPanel: vscode.WebviewPanel | undefined;
let planWebviewPanel: vscode.WebviewPanel | undefined;
let currentDocumentPath: string | undefined;
let currentProjectPath: string | undefined;
let planProvider: PlanProvider | undefined;
let currentBlocks: any[] | undefined;  // Blocks currently displayed in Contract Analysis

export function activate(context: vscode.ExtensionContext) {
    console.log('Effi Contract Viewer is now active');

    // Register chat participant for @effi
    const effiChat = new EffiChatParticipant(
        () => currentDocumentPath,
        undefined,  // No test loader
        () => currentBlocks  // Provide access to loaded blocks
    );
    const chatParticipant = vscode.chat.createChatParticipant(
        'effi-contract-viewer.effi',
        effiChat.getHandler()
    );
    chatParticipant.iconPath = vscode.Uri.joinPath(context.extensionUri, 'icon.png');
    context.subscriptions.push(chatParticipant);

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

    // Register command to refresh view (re-analyzes document and reloads)
    const refreshCommand = vscode.commands.registerCommand(
        'effi-contract-viewer.refreshView',
        async () => {
            if (!currentDocumentPath) {
                vscode.window.showWarningMessage('No document loaded to refresh');
                return;
            }
            if (webviewPanel) {
                await reanalyzeAndRefresh(currentDocumentPath);
            }
        }
    );

    // Register Project Provider
    const workspaceRoot = vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0 
        ? vscode.workspace.workspaceFolders[0].uri.fsPath 
        : undefined;
    const projectProvider = new ProjectProvider(workspaceRoot);
    vscode.window.registerTreeDataProvider('effiProjects', projectProvider);

    // Register command to analyze and load
    const analyzeAndLoadCommand = vscode.commands.registerCommand(
        'effi-contract-viewer.analyzeAndLoad',
        async (fileUri: vscode.Uri) => {
            await analyzeAndLoadDocument(context, fileUri.fsPath);
        }
    );

    // Register command to save document (blocks matched via native w14:paraId)
    const saveDocumentCommand = vscode.commands.registerCommand(
        'effi-contract-viewer.saveDocument',
        async () => {
            if (!currentDocumentPath) {
                vscode.window.showWarningMessage('No document loaded');
                return;
            }
            await saveDocument(currentDocumentPath);
        }
    );

    // Register command to create checkpoint
    const saveCheckpointCommand = vscode.commands.registerCommand(
        'effi-contract-viewer.saveCheckpoint',
        async () => {
            if (!currentDocumentPath) {
                vscode.window.showWarningMessage('No document loaded');
                return;
            }
            const note = await vscode.window.showInputBox({
                prompt: 'Enter checkpoint note (optional)',
                placeHolder: 'e.g., Completed liability section review'
            });
            await saveCheckpoint(currentDocumentPath, note || '');
        }
    );

    // Register command to show version history
    const showHistoryCommand = vscode.commands.registerCommand(
        'effi-contract-viewer.showHistory',
        async () => {
            if (!currentDocumentPath) {
                vscode.window.showWarningMessage('No document loaded');
                return;
            }
            await showVersionHistory(currentDocumentPath);
        }
    );

    // Register command to show Plan webview
    const showPlanCommand = vscode.commands.registerCommand(
        'effi-contract-viewer.showPlan',
        () => showPlanWebview(context)
    );

    context.subscriptions.push(
        showWebviewCommand, 
        analyzeCommand, 
        refreshCommand, 
        loadAnalysisCommand, 
        analyzeAndLoadCommand,
        saveDocumentCommand,
        saveCheckpointCommand,
        showHistoryCommand,
        showPlanCommand
    );

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
    if (planWebviewPanel) {
        planWebviewPanel.dispose();
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
                        await sendClausesToChat(message.clauseIds, message.query, message.clauseTexts);
                        break;
                    case 'ready':
                        console.log('Webview ready');
                        // Send initial data if available
                        if (currentDocumentPath) {
                            loadAnalysisData(currentDocumentPath);
                        }
                        break;
                    case 'saveNote':
                        await saveNote(message.blockId, message.paraIdx, message.text);
                        break;
                    case 'saveBlocks':
                        // Sprint 2: Save edited blocks to document
                        await saveBlocksToDocument(message.blocks, message.documentPath, webviewPanel);
                        break;
                    // Sprint 3: Comment management
                    case 'getComments':
                        await getComments(message.documentPath, webviewPanel);
                        break;
                    case 'resolveComment':
                        await resolveComment(message.documentPath, message.paraId, webviewPanel);
                        break;
                    case 'unresolveComment':
                        await unresolveComment(message.documentPath, message.paraId, webviewPanel);
                        break;
                    // Sprint 3 Phase 2: Track Changes (Revisions)
                    case 'getRevisions':
                        await getRevisions(message.documentPath, webviewPanel);
                        break;
                    case 'acceptRevision':
                        await acceptRevision(message.documentPath, message.revisionId, webviewPanel);
                        break;
                    case 'rejectRevision':
                        await rejectRevision(message.documentPath, message.revisionId, webviewPanel);
                        break;
                    case 'acceptAllRevisions':
                        await acceptAllRevisions(message.documentPath, webviewPanel);
                        break;
                    case 'rejectAllRevisions':
                        await rejectAllRevisions(message.documentPath, webviewPanel);
                        break;
                    case 'showPlan':
                        showPlanWebview(context);
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

/**
 * Show the Plan WebviewPanel (separate from Contract Analysis)
 */
function showPlanWebview(context: vscode.ExtensionContext) {
    // Use the same column as Contract Analysis so they appear as tabs in the same group
    const columnToShowIn = webviewPanel 
        ? webviewPanel.viewColumn || vscode.ViewColumn.One
        : (vscode.window.activeTextEditor?.viewColumn || vscode.ViewColumn.One);

    if (planWebviewPanel) {
        // If panel exists, reveal it
        planWebviewPanel.reveal(columnToShowIn);
    } else {
        // Create new panel
        planWebviewPanel = vscode.window.createWebviewPanel(
            'effiPlanViewer',
            'Work Plan',
            columnToShowIn,
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
        planWebviewPanel.webview.html = getPlanWebviewContent(context, planWebviewPanel.webview);

        // Handle messages from webview
        planWebviewPanel.webview.onDidReceiveMessage(
            async (message) => {
                switch (message.command) {
                    case 'ready':
                        console.log('Plan webview ready');
                        // Send project path and plan data if available
                        if (currentProjectPath) {
                            await handleGetPlan(currentProjectPath, planWebviewPanel);
                        }
                        break;
                    case 'getPlan':
                        await handleGetPlan(message.projectPath, planWebviewPanel);
                        break;
                    case 'savePlan':
                        await handleSavePlan(message.projectPath, message.plan, planWebviewPanel);
                        break;
                    case 'addTask':
                        await handleAddTask(message.projectPath, message.title, message.description, message.options, planWebviewPanel);
                        break;
                    case 'updateTask':
                        await handleUpdateTask(message.projectPath, message.taskId, message.updates, planWebviewPanel);
                        break;
                    case 'deleteTask':
                        await handleDeleteTask(message.projectPath, message.taskId, planWebviewPanel);
                        break;
                    case 'moveTask':
                        await handleMoveTask(message.projectPath, message.taskId, message.newOrdinal, planWebviewPanel);
                        break;
                    case 'logEdit':
                        await handleLogEdit(message.projectPath, message.taskId, message.toolName, message.request, message.response, planWebviewPanel);
                        break;
                }
            },
            undefined,
            context.subscriptions
        );

        // Handle panel disposal
        planWebviewPanel.onDidDispose(
            () => {
                planWebviewPanel = undefined;
                vscode.commands.executeCommand('setContext', 'effiPlanViewerActive', false);
            },
            null,
            context.subscriptions
        );

        vscode.commands.executeCommand('setContext', 'effiPlanViewerActive', true);
    }
}

async function analyzeDocument(documentPath: string) {
    currentDocumentPath = documentPath;
    currentProjectPath = getProjectDir(documentPath);
    
    if (!fs.existsSync(documentPath)) {
        vscode.window.showErrorMessage(`Document not found: ${documentPath}`);
        return;
    }

    vscode.window.showInformationMessage(`Analyzing: ${path.basename(documentPath)}`);

    // TODO: Call Python MCP server to analyze document
    // For now, just try to load existing analysis
    await loadAnalysisData(documentPath);
}

/**
 * Re-analyze the document and refresh the webview.
 * This is called when the user presses Ctrl+L to see changes made by MCP tools.
 */
async function reanalyzeAndRefresh(documentPath: string) {
    // Calculate output directory: project/analysis/<filename_no_ext>
    const analysisDir = getAnalysisDir(documentPath);
    
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: `Refreshing ${path.basename(documentPath)}...`,
        cancellable: false
    }, async (progress) => {
        try {
            const workspaceRoot = path.join(__dirname, '..', '..');
            const pythonCmd = getPythonPath(workspaceRoot);
            
            // Re-analyze using the existing doc-id from manifest if available
            let docId = '123e4567-e89b-12d3-a456-426614174000';
            const manifestPath = path.join(analysisDir, 'manifest.json');
            if (fs.existsSync(manifestPath)) {
                try {
                    const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
                    if (manifest.doc_id) {
                        docId = manifest.doc_id;
                    }
                } catch (e) {
                    // Use default doc-id
                }
            }
            
            const cmd = `cd "${workspaceRoot}" && "${pythonCmd}" -m effilocal.cli analyze "${documentPath}" --doc-id "${docId}" --out "${analysisDir}"`;
            
            await execAsync(cmd);
            
            // Load the updated analysis
            await loadAnalysisData(documentPath);
            
        } catch (error) {
            vscode.window.showErrorMessage(`Refresh failed: ${error}`);
        }
    });
}

async function analyzeAndLoadDocument(context: vscode.ExtensionContext, documentPath: string) {
    currentDocumentPath = documentPath;
    
    // Calculate output directory: project/analysis/<filename_no_ext>
    const docDir = path.dirname(documentPath); // drafts/current_drafts
    const draftsDir = path.dirname(docDir); // drafts
    const projectDir = path.dirname(draftsDir); // ProjectName
    const filenameNoExt = path.basename(documentPath, '.docx');
    const analysisDir = path.join(projectDir, 'analysis', filenameNoExt);
    
    vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: `Analyzing ${path.basename(documentPath)}...`,
        cancellable: false
    }, async (progress) => {
        try {
            const workspaceRoot = path.join(__dirname, '..', '..');
            const pythonCmd = getPythonPath(workspaceRoot);
            
            // Generate a random UUID for doc-id (simple version)
            const docId = '123e4567-e89b-12d3-a456-426614174000'; 
            
            const cmd = `cd "${workspaceRoot}" && "${pythonCmd}" -m effilocal.cli analyze "${documentPath}" --doc-id "${docId}" --out "${analysisDir}"`;
            
            await execAsync(cmd);
            
            // Load analysis
            // Note: loadAnalysisFromDirectory expects projectPath (documentPath) as second arg now
            await loadAnalysisFromDirectory(analysisDir, documentPath); 
            
            // Show webview
            showContractWebview(context);
            
        } catch (error) {
            vscode.window.showErrorMessage(`Analysis failed: ${error}`);
        }
    });
}

function getPythonPath(workspaceRoot: string): string {
    // Check for .venv in workspace root
    const venvPath = process.platform === 'win32' 
        ? path.join(workspaceRoot, '.venv', 'Scripts', 'python.exe')
        : path.join(workspaceRoot, '.venv', 'bin', 'python');
        
    if (fs.existsSync(venvPath)) {
        return venvPath;
    }
    
    // Fallback to system python
    return process.platform === 'win32' ? 'python' : 'python3';
}

async function loadAnalysisFromDirectory(analysisDir: string, projectPathOrDocPath: string) {
    if (!fs.existsSync(analysisDir)) {
        webviewPanel?.webview.postMessage({
            command: 'noAnalysis',
            message: 'No analysis found in workspace.'
        });
        return;
    }

    // Determine document path
    let documentPath = '';
    if (fs.existsSync(projectPathOrDocPath) && fs.statSync(projectPathOrDocPath).isFile() && projectPathOrDocPath.endsWith('.docx')) {
        documentPath = projectPathOrDocPath;
    } else {
        // It's a project directory, try to find the file
        const projectPath = projectPathOrDocPath;
        
        // Strategy 1: Check drafts/current_drafts
        const draftsDir = path.join(projectPath, 'drafts', 'current_drafts');
        if (fs.existsSync(draftsDir)) {
            const files = fs.readdirSync(draftsDir).filter(f => f.endsWith('.docx') && !f.startsWith('~$'));
            if (files.length > 0) {
                documentPath = path.join(draftsDir, files[0]);
            }
        }

        // Strategy 2: Check root if not found
        if (!documentPath) {
            const files = fs.readdirSync(projectPath).filter(f => f.endsWith('.docx') && !f.startsWith('~$'));
            if (files.length > 0) {
                documentPath = path.join(projectPath, files[0]);
            }
        }
    }

    if (documentPath) {
        currentDocumentPath = documentPath;
        console.log(`Found document: ${documentPath}`);
    } else {
        console.warn('No .docx file found in project');
        vscode.window.showWarningMessage('Could not find associated .docx file. Note saving may not work.');
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
        const workspaceRoot = path.join(__dirname, '..', '..');
        const pythonCmd = getPythonPath(workspaceRoot);

        // Load notes from comments using Python script
        let notes = {};
        if (documentPath) {
            try {
                const scriptPath = path.join(__dirname, '..', 'scripts', 'manage_notes.py');
                
                // Call: manage_notes.py get_notes <filename> <analysis_dir>
                const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" "get_notes" "${documentPath}" "${analysisDir}"`);
                const result = JSON.parse(stdout);
                
                if (result.success) {
                    notes = result.notes;
                    console.log(`Loaded notes for ${Object.keys(notes).length} blocks`);
                } else {
                    console.error('Failed to load notes:', result.error);
                }
            } catch (error) {
                console.error('Error executing manage_notes.py:', error);
            }
        }

        // Load outline data using Python script
        let outline = [];
        try {
            // __dirname is dist/ after compilation, so go up one level to reach scripts/
            const scriptPath = path.join(__dirname, '..', 'scripts', 'get_outline.py');
            const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" "${analysisDir}"`);
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
        let blocks: any[] = [];
        const blocksPath = path.join(analysisDir, 'blocks.jsonl');
        if (fs.existsSync(blocksPath)) {
            try {
                const blocksContent = fs.readFileSync(blocksPath, 'utf-8');
                blocks = blocksContent.trim().split('\n')
                    .filter(line => line.trim())
                    .map(line => JSON.parse(line));
                console.log(`Loaded ${blocks.length} blocks from blocks.jsonl`);
                // Store blocks for chat participant access
                currentBlocks = blocks;
            } catch (error) {
                console.error('Error loading blocks.jsonl:', error);
            }
        }

        // Load relationships.json for hierarchy
        let relationships: any = {};
        const relationshipsPath = path.join(analysisDir, 'relationships.json');
        if (fs.existsSync(relationshipsPath)) {
            try {
                relationships = JSON.parse(fs.readFileSync(relationshipsPath, 'utf-8'));
                console.log(`Loaded ${relationships.relationships?.length || 0} relationships`);
            } catch (error) {
                console.error('Error loading relationships.json:', error);
            }
        }

        webviewPanel?.webview.postMessage({
            command: 'updateData',
            data: {
                manifest,
                index,
                analysisDir,
                documentPath: documentPath || projectPathOrDocPath,
                outline,
                blocks,
                relationships,
                notes
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
    //        -> EL_Projects/<project>/analysis/<filename_no_ext>/
    
    const analysisDir = getAnalysisDir(documentPath);

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
        const workspaceRoot = path.join(__dirname, '..', '..');
        const pythonCmd = getPythonPath(workspaceRoot);

        // Load notes from comments using Python script (live from document)
        let notes = {};
        try {
            const scriptPath = path.join(__dirname, '..', 'scripts', 'manage_notes.py');
            
            const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" "get_notes" "${documentPath}" "${analysisDir}"`);
            const result = JSON.parse(stdout);
            
            if (result.success) {
                notes = result.notes;
                console.log(`Loaded notes for ${Object.keys(notes).length} blocks`);
            } else {
                console.error('Failed to load notes:', result.error);
            }
        } catch (error) {
            console.error('Error executing manage_notes.py:', error);
        }

        // Load outline data using Python script
        let outline = [];
        try {
            const scriptPath = path.join(__dirname, '..', 'scripts', 'get_outline.py');
            const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" "${analysisDir}"`);
            const outlineResult = JSON.parse(stdout);
            if (outlineResult.success) {
                outline = outlineResult.outline;
                console.log(`Loaded ${outline.length} outline items`);
            } else {
                console.error('Failed to load outline:', outlineResult.error);
            }
        } catch (error) {
            console.error('Error executing get_outline.py:', error);
        }

        // Load blocks.jsonl for full text view
        let blocks: any[] = [];
        const blocksPath = path.join(analysisDir, 'blocks.jsonl');
        if (fs.existsSync(blocksPath)) {
            try {
                const blocksContent = fs.readFileSync(blocksPath, 'utf-8');
                blocks = blocksContent.trim().split('\n')
                    .filter(line => line.trim())
                    .map(line => JSON.parse(line));
                console.log(`Loaded ${blocks.length} blocks from blocks.jsonl`);
                // Store blocks for chat participant access
                currentBlocks = blocks;
            } catch (error) {
                console.error('Error loading blocks.jsonl:', error);
            }
        }

        // Load relationships.json for hierarchy
        let relationships: any = {};
        const relationshipsPath = path.join(analysisDir, 'relationships.json');
        if (fs.existsSync(relationshipsPath)) {
            try {
                relationships = JSON.parse(fs.readFileSync(relationshipsPath, 'utf-8'));
                console.log(`Loaded ${relationships.relationships?.length || 0} relationships`);
            } catch (error) {
                console.error('Error loading relationships.json:', error);
            }
        }

        webviewPanel?.webview.postMessage({
            command: 'updateData',
            data: {
                manifest,
                index,
                analysisDir,
                documentPath,
                outline,
                blocks,
                relationships,
                notes
            }
        });

        vscode.window.showInformationMessage('Analysis loaded successfully');
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to load analysis: ${error}`);
    }
}

async function saveNote(blockId: string, paraIdx: string, text: string) {
    if (!currentDocumentPath) return;
    
    try {
        const scriptPath = path.join(__dirname, '..', 'scripts', 'manage_notes.py');
        const workspaceRoot = path.join(__dirname, '..', '..');
        const pythonCmd = getPythonPath(workspaceRoot);
        
        // Call: manage_notes.py save_note <filename> <para_idx> <text>
        // Use spawn to handle potentially long text safely
        const proc = spawn(pythonCmd, [scriptPath, 'save_note', currentDocumentPath, paraIdx, text], {
            cwd: workspaceRoot,
            shell: false
        });
        
        let stdout = '';
        let stderr = '';
        
        proc.stdout.on('data', (data) => { stdout += data.toString(); });
        proc.stderr.on('data', (data) => { stderr += data.toString(); });
        
        proc.on('close', (code) => {
            if (code !== 0) {
                console.error(`manage_notes.py failed: ${stderr}`);
                vscode.window.showErrorMessage(`Failed to save note: ${stderr}`);
            } else {
                try {
                    const result = JSON.parse(stdout);
                    if (!result.success) {
                        vscode.window.showErrorMessage(`Failed to save note: ${result.error}`);
                    }
                } catch (e) {
                    console.error('Failed to parse output:', stdout);
                }
            }
        });
        
    } catch (error) {
        console.error('Error saving note:', error);
        vscode.window.showErrorMessage(`Failed to save note: ${error}`);
    }
}

function jumpToClause(paraId: string) {
    // TODO: Implement jumping to clause in Word document
    // This will require interacting with the Word document
    vscode.window.showInformationMessage(`Jump to clause: ${paraId}`);
}

async function sendClausesToChat(paraIds: string[], query: string, clauseTexts?: any[]) {
    try {
        // Use para IDs for context
        const clauseContext = paraIds.map(id => `- ${id}`).join('\n');
        const fullPrompt = `Context - Selected clauses from contract (Paragraph IDs):\n${clauseContext}\n\nQuestion: ${query}`;

        // Copy to clipboard and open chat
        await vscode.env.clipboard.writeText(fullPrompt);
        
        vscode.window.showInformationMessage(
            `✓ Copied ${paraIds.length} clause${paraIds.length !== 1 ? 's' : ''} + question to clipboard`,
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
    
    // Sprint 2: Editor scripts
    const editorPath = path.join(context.extensionPath, 'src', 'webview', 'editor.js');
    const toolbarPath = path.join(context.extensionPath, 'src', 'webview', 'toolbar.js');
    const shortcutsPath = path.join(context.extensionPath, 'src', 'webview', 'shortcuts.js');
    
    // Sprint 3: Comment panel
    const commentsPath = path.join(context.extensionPath, 'src', 'webview', 'comments.js');

    const scriptUri = webview.asWebviewUri(vscode.Uri.file(scriptPath));
    const styleUri = webview.asWebviewUri(vscode.Uri.file(stylePath));
    const editorUri = webview.asWebviewUri(vscode.Uri.file(editorPath));
    const toolbarUri = webview.asWebviewUri(vscode.Uri.file(toolbarPath));
    const shortcutsUri = webview.asWebviewUri(vscode.Uri.file(shortcutsPath));
    const commentsUri = webview.asWebviewUri(vscode.Uri.file(commentsPath));

    // Use CSP nonce for security
    const nonce = getNonce();

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="${styleUri}" rel="stylesheet">
    <title>Document</title>
</head>
<body>
    <div id="app">
        <div class="header">
            <h1 id="document-title">Document</h1>
            <div class="toolbar">
                <button id="show-plan-btn" class="plan-toggle-btn" title="Open Work Plan">
                    <span class="plan-icon">📋</span>
                    <span class="plan-label">Plan</span>
                </button>
                <button id="toggle-comments-btn" class="comments-toggle-btn" title="Toggle Comments Panel">
                    <span class="comments-icon">💬</span>
                    <span class="comments-label">Comments</span>
                </button>
                <button id="refresh-btn" class="icon-button" title="Refresh">↻</button>
            </div>
        </div>

        <!-- Toolbar - Outside document like Google Docs -->
        <div id="main-toolbar" class="main-toolbar" style="display: none;"></div>

        <div class="content">
            <div id="loading" class="message">
                <p>No document loaded</p>
                <p class="hint">Open a .docx file and click the book icon to analyze</p>
            </div>

            <div id="data-view" style="display: none;">
                <div class="document-with-panels">
                    <div class="pages-container">
                        <div id="fulltext-content" class="tab-content"></div>
                    </div>
                    <div id="comment-panel-container" class="side-panel" style="display: none;"></div>
                </div>
            </div>
        </div>

        <div class="chat-query-box-fixed">
            <div class="selection-info">
                <span id="selection-count">0 clauses selected</span>
                <button id="clear-selection" class="secondary-button">Clear</button>
            </div>
            <textarea id="chat-query" placeholder="Ask a question about the selected clauses..."></textarea>
            <button id="send-to-chat" class="primary-button">Ask Copilot</button>
        </div>
    </div>
    
    <!-- Sprint 2: Load editor scripts before main.js -->
    <script nonce="${nonce}" src="${editorUri}"></script>
    <script nonce="${nonce}" src="${toolbarUri}"></script>
    <script nonce="${nonce}" src="${shortcutsUri}"></script>
    <!-- Sprint 3: Comment panel -->
    <script nonce="${nonce}" src="${commentsUri}"></script>
    <script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
}

/**
 * Get HTML content for the Plan WebviewPanel
 */
function getPlanWebviewContent(context: vscode.ExtensionContext, webview: vscode.Webview): string {
    const stylePath = path.join(context.extensionPath, 'src', 'webview', 'style.css');
    const planPath = path.join(context.extensionPath, 'src', 'webview', 'plan.js');
    const planMainPath = path.join(context.extensionPath, 'src', 'webview', 'planMain.js');

    const styleUri = webview.asWebviewUri(vscode.Uri.file(stylePath));
    const planUri = webview.asWebviewUri(vscode.Uri.file(planPath));
    const planMainUri = webview.asWebviewUri(vscode.Uri.file(planMainPath));

    // Use CSP nonce for security
    const nonce = getNonce();

    // Include project path in the page for initialization
    const projectPathEscaped = currentProjectPath ? currentProjectPath.replace(/\\/g, '\\\\').replace(/'/g, "\\'") : '';

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="${styleUri}" rel="stylesheet">
    <title>Work Plan</title>
</head>
<body class="plan-webview">
    <div id="plan-app">
        <div id="plan-container"></div>
    </div>
    
    <script nonce="${nonce}">
        window.initialProjectPath = '${projectPathEscaped}';
    </script>
    <script nonce="${nonce}" src="${planUri}"></script>
    <script nonce="${nonce}" src="${planMainUri}"></script>
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

function getAnalysisDir(documentPath: string): string {
    // Determine analysis directory based on document path
    // Expected: EL_Projects/<project>/drafts/current_drafts/<file>.docx
    //        -> EL_Projects/<project>/analysis/<filename_no_ext>/
    const docDir = path.dirname(documentPath);
    const draftsDir = path.dirname(docDir);
    const projectDir = path.dirname(draftsDir);
    const filenameNoExt = path.basename(documentPath, '.docx');
    return path.join(projectDir, 'analysis', filenameNoExt);
}

/**
 * Get the project directory from a document path
 * Expected: EL_Projects/<project>/drafts/current_drafts/<file>.docx
 *        -> EL_Projects/<project>/
 */
function getProjectDir(documentPath: string): string {
    const docDir = path.dirname(documentPath);
    const draftsDir = path.dirname(docDir);
    const projectDir = path.dirname(draftsDir);
    return projectDir;
}

async function saveDocument(documentPath: string) {
    const analysisDir = getAnalysisDir(documentPath);
    const autoCommit = vscode.workspace.getConfiguration('effiContractViewer').get<boolean>('autoCommit', true);
    
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Saving document...',
        cancellable: false
    }, async (progress) => {
        try {
            const workspaceRoot = path.join(__dirname, '..', '..');
            const pythonCmd = getPythonPath(workspaceRoot);
            const scriptPath = path.join(__dirname, '..', 'scripts', 'save_document.py');
            
            const args = ['save', documentPath, analysisDir];
            if (!autoCommit) {
                args.push('--no-commit');
            }
            
            const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" ${args.map(a => `"${a}"`).join(' ')}`);
            const result = JSON.parse(stdout);
            
            if (result.success) {
                let message = `✓ Document saved with ${result.embedded_count} blocks matched via para_id`;
                if (result.commit_hash) {
                    message += ` (committed: ${result.commit_hash.substring(0, 8)})`;
                }
                vscode.window.showInformationMessage(message);
            } else {
                vscode.window.showErrorMessage(`Save failed: ${result.error}`);
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Save failed: ${error}`);
        }
    });
}

async function saveCheckpoint(documentPath: string, note: string) {
    const analysisDir = getAnalysisDir(documentPath);
    
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Creating checkpoint...',
        cancellable: false
    }, async (progress) => {
        try {
            const workspaceRoot = path.join(__dirname, '..', '..');
            const pythonCmd = getPythonPath(workspaceRoot);
            const scriptPath = path.join(__dirname, '..', 'scripts', 'save_document.py');
            
            const args = ['checkpoint', documentPath, analysisDir];
            if (note) {
                args.push('--note', note);
            }
            
            const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" ${args.map(a => `"${a}"`).join(' ')}`);
            const result = JSON.parse(stdout);
            
            if (result.success) {
                let message = `✓ Checkpoint created`;
                if (result.commit_hash) {
                    message += ` (${result.commit_hash.substring(0, 8)})`;
                }
                if (note) {
                    message += `: ${note}`;
                }
                vscode.window.showInformationMessage(message);
            } else {
                vscode.window.showErrorMessage(`Checkpoint failed: ${result.error}`);
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Checkpoint failed: ${error}`);
        }
    });
}

interface CommitInfo {
    hash: string;
    short_hash: string;
    author: string;
    date: string;
    message: string;
}

/**
 * Sprint 2: Save edited blocks to the document via Python script
 */
async function saveBlocksToDocument(blocks: any[], documentPath: string, webviewPanel: vscode.WebviewPanel | undefined) {
    if (!documentPath) {
        const errorMsg = 'No document path provided';
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ command: 'saveError', message: errorMsg });
        }
        vscode.window.showErrorMessage(errorMsg);
        return;
    }
    
    if (!blocks || blocks.length === 0) {
        const errorMsg = 'No blocks to save';
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ command: 'saveError', message: errorMsg });
        }
        return;
    }
    
    try {
        const analysisDir = getAnalysisDir(documentPath);
        const workspaceRoot = path.join(__dirname, '..', '..');
        const pythonCmd = getPythonPath(workspaceRoot);
        const scriptPath = path.join(__dirname, '..', 'scripts', 'save_blocks.py');
        
        // Write blocks to a temp file to pass to Python
        const tempBlocksPath = path.join(analysisDir, '.temp_blocks.json');
        fs.writeFileSync(tempBlocksPath, JSON.stringify(blocks, null, 2));
        
        const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" "${documentPath}" "${tempBlocksPath}"`);
        
        // DEBUG: Keep temp file for inspection
        // if (fs.existsSync(tempBlocksPath)) {
        //     fs.unlinkSync(tempBlocksPath);
        // }
        
        const result = JSON.parse(stdout);
        
        if (result.success) {
            const message = `✓ Saved ${result.block_count} block(s) to document`;
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ command: 'saveComplete', message });
            }
            vscode.window.showInformationMessage(message);
            
            // Reload analysis data to reflect changes
            if (currentDocumentPath) {
                await loadAnalysisData(currentDocumentPath);
            }
        } else {
            // Note: Old "No embedded UUIDs" error handling removed - we now use native w14:paraId
            const errorMsg = `Save failed: ${result.error}`;
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ command: 'saveError', message: errorMsg });
            }
            vscode.window.showErrorMessage(errorMsg);
        }
    } catch (error) {
        const errorMsg = `Save failed: ${error}`;
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ command: 'saveError', message: errorMsg });
        }
        vscode.window.showErrorMessage(errorMsg);
    }
}

/**
 * Sprint 3: Get all comments from a document
 */
async function getComments(documentPath: string, webviewPanel: vscode.WebviewPanel | undefined) {
    console.log('DEBUG getComments: documentPath=', documentPath);
    if (!documentPath || !fs.existsSync(documentPath)) {
        console.log('DEBUG getComments: file not found or empty path');
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ 
                command: 'commentError', 
                error: 'Document path not provided or file not found' 
            });
        }
        return;
    }
    
    try {
        const workspaceRoot = path.join(__dirname, '..', '..');
        const pythonCmd = getPythonPath(workspaceRoot);
        const scriptPath = path.join(__dirname, '..', 'scripts', 'manage_comments.py');
        
        console.log('DEBUG getComments: calling script', scriptPath);
        const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" get_comments "${documentPath}"`);
        const result = JSON.parse(stdout);
        console.log('DEBUG getComments: result.success=', result.success, 'count=', result.comments?.length);
        
        if (result.success) {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ 
                    command: 'updateComments', 
                    comments: result.comments,
                    totalComments: result.total_comments
                });
            }
        } else {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ 
                    command: 'commentError', 
                    error: result.error 
                });
            }
        }
    } catch (error) {
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ 
                command: 'commentError', 
                error: `Failed to get comments: ${error}` 
            });
        }
    }
}

/**
 * Sprint 3: Resolve a comment in a document
 * @param paraId - The w14:paraId of the comment's internal paragraph
 */
async function resolveComment(documentPath: string, paraId: string, webviewPanel: vscode.WebviewPanel | undefined) {
    if (!documentPath || !fs.existsSync(documentPath)) {
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ 
                command: 'commentError', 
                error: 'Document path not provided or file not found',
                paraId 
            });
        }
        return;
    }
    
    try {
        const workspaceRoot = path.join(__dirname, '..', '..');
        const pythonCmd = getPythonPath(workspaceRoot);
        const scriptPath = path.join(__dirname, '..', 'scripts', 'manage_comments.py');
        
        const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" resolve_comment "${documentPath}" "${paraId}"`);
        const result = JSON.parse(stdout);
        
        if (result.success) {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ 
                    command: 'commentResolved', 
                    paraId,
                    success: true
                });
            }
            // Refresh comments list
            await getComments(documentPath, webviewPanel);
        } else {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ 
                    command: 'commentError', 
                    error: result.error,
                    paraId 
                });
            }
        }
    } catch (error) {
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ 
                command: 'commentError', 
                error: `Failed to resolve comment: ${error}`,
                paraId 
            });
        }
    }
}

/**
 * Sprint 3: Unresolve a comment in a document
 * @param paraId - The w14:paraId of the comment's internal paragraph
 */
async function unresolveComment(documentPath: string, paraId: string, webviewPanel: vscode.WebviewPanel | undefined) {
    if (!documentPath || !fs.existsSync(documentPath)) {
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ 
                command: 'commentError', 
                error: 'Document path not provided or file not found',
                paraId 
            });
        }
        return;
    }
    
    try {
        const workspaceRoot = path.join(__dirname, '..', '..');
        const pythonCmd = getPythonPath(workspaceRoot);
        const scriptPath = path.join(__dirname, '..', 'scripts', 'manage_comments.py');
        
        const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" unresolve_comment "${documentPath}" "${paraId}"`);
        const result = JSON.parse(stdout);
        
        if (result.success) {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ 
                    command: 'commentUnresolved', 
                    paraId,
                    success: true
                });
            }
            // Refresh comments list
            await getComments(documentPath, webviewPanel);
        } else {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ 
                    command: 'commentError', 
                    error: result.error,
                    paraId 
                });
            }
        }
    } catch (error) {
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ 
                command: 'commentError', 
                error: `Failed to unresolve comment: ${error}`,
                paraId 
            });
        }
    }
}

/**
 * Sprint 3 Phase 2: Get all revisions (track changes) from a document
 */
async function getRevisions(documentPath: string, webviewPanel: vscode.WebviewPanel | undefined) {
    if (!documentPath || !fs.existsSync(documentPath)) {
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ 
                command: 'revisionError', 
                error: 'Document path not provided or file not found'
            });
        }
        return;
    }
    
    try {
        const workspaceRoot = path.join(__dirname, '..', '..');
        const pythonCmd = getPythonPath(workspaceRoot);
        const scriptPath = path.join(__dirname, '..', 'scripts', 'manage_revisions.py');
        
        const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" get_revisions "${documentPath}"`);
        const result = JSON.parse(stdout);
        
        if (result.success) {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ 
                    command: 'updateRevisions', 
                    revisions: result.revisions,
                    totalRevisions: result.total_revisions
                });
            }
        } else {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ 
                    command: 'revisionError', 
                    error: result.error 
                });
            }
        }
    } catch (error) {
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ 
                command: 'revisionError', 
                error: `Failed to get revisions: ${error}`
            });
        }
    }
}

/**
 * Sprint 3 Phase 2: Accept a revision in a document
 */
async function acceptRevision(documentPath: string, revisionId: string, webviewPanel: vscode.WebviewPanel | undefined) {
    if (!documentPath || !fs.existsSync(documentPath)) {
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ 
                command: 'revisionError', 
                error: 'Document path not provided or file not found',
                revisionId 
            });
        }
        return;
    }
    
    try {
        const workspaceRoot = path.join(__dirname, '..', '..');
        const pythonCmd = getPythonPath(workspaceRoot);
        const scriptPath = path.join(__dirname, '..', 'scripts', 'manage_revisions.py');
        
        const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" accept_revision "${documentPath}" "${revisionId}"`);
        const result = JSON.parse(stdout);
        
        if (result.success) {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ 
                    command: 'revisionAccepted', 
                    revisionId,
                    success: true
                });
            }
            // Refresh revisions list
            await getRevisions(documentPath, webviewPanel);
        } else {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ 
                    command: 'revisionError', 
                    error: result.error,
                    revisionId 
                });
            }
        }
    } catch (error) {
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ 
                command: 'revisionError', 
                error: `Failed to accept revision: ${error}`,
                revisionId 
            });
        }
    }
}

/**
 * Sprint 3 Phase 2: Reject a revision in a document
 */
async function rejectRevision(documentPath: string, revisionId: string, webviewPanel: vscode.WebviewPanel | undefined) {
    if (!documentPath || !fs.existsSync(documentPath)) {
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ 
                command: 'revisionError', 
                error: 'Document path not provided or file not found',
                revisionId 
            });
        }
        return;
    }
    
    try {
        const workspaceRoot = path.join(__dirname, '..', '..');
        const pythonCmd = getPythonPath(workspaceRoot);
        const scriptPath = path.join(__dirname, '..', 'scripts', 'manage_revisions.py');
        
        const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" reject_revision "${documentPath}" "${revisionId}"`);
        const result = JSON.parse(stdout);
        
        if (result.success) {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ 
                    command: 'revisionRejected', 
                    revisionId,
                    success: true
                });
            }
            // Refresh revisions list
            await getRevisions(documentPath, webviewPanel);
        } else {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ 
                    command: 'revisionError', 
                    error: result.error,
                    revisionId 
                });
            }
        }
    } catch (error) {
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ 
                command: 'revisionError', 
                error: `Failed to reject revision: ${error}`,
                revisionId 
            });
        }
    }
}

/**
 * Sprint 3 Phase 2: Accept all revisions in a document
 */
async function acceptAllRevisions(documentPath: string, webviewPanel: vscode.WebviewPanel | undefined) {
    if (!documentPath || !fs.existsSync(documentPath)) {
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ 
                command: 'revisionError', 
                error: 'Document path not provided or file not found'
            });
        }
        return;
    }
    
    try {
        const workspaceRoot = path.join(__dirname, '..', '..');
        const pythonCmd = getPythonPath(workspaceRoot);
        const scriptPath = path.join(__dirname, '..', 'scripts', 'manage_revisions.py');
        
        const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" accept_all "${documentPath}"`);
        const result = JSON.parse(stdout);
        
        if (result.success) {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ 
                    command: 'allRevisionsAccepted', 
                    acceptedCount: result.accepted_count,
                    success: true
                });
            }
            // Refresh revisions list (should now be empty)
            await getRevisions(documentPath, webviewPanel);
            vscode.window.showInformationMessage(`Accepted ${result.accepted_count} revisions`);
        } else {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ 
                    command: 'revisionError', 
                    error: result.error 
                });
            }
        }
    } catch (error) {
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ 
                command: 'revisionError', 
                error: `Failed to accept all revisions: ${error}`
            });
        }
    }
}

/**
 * Sprint 3 Phase 2: Reject all revisions in a document
 */
async function rejectAllRevisions(documentPath: string, webviewPanel: vscode.WebviewPanel | undefined) {
    if (!documentPath || !fs.existsSync(documentPath)) {
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ 
                command: 'revisionError', 
                error: 'Document path not provided or file not found'
            });
        }
        return;
    }
    
    try {
        const workspaceRoot = path.join(__dirname, '..', '..');
        const pythonCmd = getPythonPath(workspaceRoot);
        const scriptPath = path.join(__dirname, '..', 'scripts', 'manage_revisions.py');
        
        const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" reject_all "${documentPath}"`);
        const result = JSON.parse(stdout);
        
        if (result.success) {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ 
                    command: 'allRevisionsRejected', 
                    rejectedCount: result.rejected_count,
                    success: true
                });
            }
            // Refresh revisions list (should now be empty)
            await getRevisions(documentPath, webviewPanel);
            vscode.window.showInformationMessage(`Rejected ${result.rejected_count} revisions`);
        } else {
            if (webviewPanel) {
                webviewPanel.webview.postMessage({ 
                    command: 'revisionError', 
                    error: result.error 
                });
            }
        }
    } catch (error) {
        if (webviewPanel) {
            webviewPanel.webview.postMessage({ 
                command: 'revisionError', 
                error: `Failed to reject all revisions: ${error}`
            });
        }
    }
}

// ============================================================================
// Plan Tab Handlers
// ============================================================================

/**
 * Get or create PlanProvider for a project path
 */
function getOrCreatePlanProvider(projectPath: string): PlanProvider {
    if (!planProvider || planProvider['projectPath'] !== projectPath) {
        planProvider = new PlanProvider(projectPath);
    }
    return planProvider;
}

/**
 * Handle getPlan message - load plan and send to webview
 */
async function handleGetPlan(projectPath: string, webviewPanel: vscode.WebviewPanel | undefined) {
    if (!projectPath) {
        webviewPanel?.webview.postMessage({
            command: 'planError',
            error: 'Project path is required'
        });
        return;
    }

    try {
        const provider = getOrCreatePlanProvider(projectPath);
        await provider.initialize();
        const plan = await provider.getPlan();
        const data = provider.toWebviewData();

        webviewPanel?.webview.postMessage({
            command: 'planData',
            plan: data
        });
    } catch (error) {
        webviewPanel?.webview.postMessage({
            command: 'planError',
            error: `Failed to load plan: ${error}`
        });
    }
}

/**
 * Handle savePlan message - save plan to disk
 */
async function handleSavePlan(projectPath: string, planData: unknown, webviewPanel: vscode.WebviewPanel | undefined) {
    if (!projectPath) {
        webviewPanel?.webview.postMessage({
            command: 'planError',
            error: 'Project path is required'
        });
        return;
    }

    try {
        const provider = getOrCreatePlanProvider(projectPath);
        await provider.initialize();
        
        // Import WorkPlan to reconstruct from data
        const { WorkPlan } = await import('./models/workplan.js');
        const plan = WorkPlan.fromJSON(planData as WorkPlanJSON);
        
        const result = await provider.savePlan(plan);
        
        if (result.success) {
            webviewPanel?.webview.postMessage({
                command: 'planSaved',
                success: true
            });
        } else {
            webviewPanel?.webview.postMessage({
                command: 'planError',
                error: result.error
            });
        }
    } catch (error) {
        webviewPanel?.webview.postMessage({
            command: 'planError',
            error: `Failed to save plan: ${error}`
        });
    }
}

/**
 * Handle addTask message - add a new task to the plan
 */
async function handleAddTask(
    projectPath: string,
    title: string,
    description: string,
    options: { position?: 'start' | 'end'; ordinal?: number } | undefined,
    webviewPanel: vscode.WebviewPanel | undefined
) {
    if (!projectPath) {
        webviewPanel?.webview.postMessage({
            command: 'planError',
            error: 'Project path is required'
        });
        return;
    }

    try {
        const provider = getOrCreatePlanProvider(projectPath);
        await provider.initialize();
        
        const result = await provider.addTask(title, description, options);
        
        if (result.success && result.task) {
            webviewPanel?.webview.postMessage({
                command: 'taskAdded',
                task: result.task.toJSON(),
                success: true
            });
        } else {
            webviewPanel?.webview.postMessage({
                command: 'planError',
                error: result.error || 'Failed to add task'
            });
        }
    } catch (error) {
        webviewPanel?.webview.postMessage({
            command: 'planError',
            error: `Failed to add task: ${error}`
        });
    }
}

/**
 * Handle updateTask message - update an existing task
 */
async function handleUpdateTask(
    projectPath: string,
    taskId: string,
    updates: { title?: string; description?: string; status?: string },
    webviewPanel: vscode.WebviewPanel | undefined
) {
    if (!projectPath) {
        webviewPanel?.webview.postMessage({
            command: 'planError',
            error: 'Project path is required'
        });
        return;
    }

    try {
        const provider = getOrCreatePlanProvider(projectPath);
        await provider.initialize();
        
        // Cast status to TaskStatus if provided
        const typedUpdates: TaskUpdateOptions = {
            ...updates,
            status: updates.status as TaskStatus | undefined
        };
        
        const result = await provider.updateTask(taskId, typedUpdates);
        
        if (result.success) {
            webviewPanel?.webview.postMessage({
                command: 'taskUpdated',
                taskId,
                success: true
            });
        } else {
            webviewPanel?.webview.postMessage({
                command: 'planError',
                error: result.error
            });
        }
    } catch (error) {
        webviewPanel?.webview.postMessage({
            command: 'planError',
            error: `Failed to update task: ${error}`
        });
    }
}

/**
 * Handle deleteTask message - remove a task from the plan
 */
async function handleDeleteTask(
    projectPath: string,
    taskId: string,
    webviewPanel: vscode.WebviewPanel | undefined
) {
    if (!projectPath) {
        webviewPanel?.webview.postMessage({
            command: 'planError',
            error: 'Project path is required'
        });
        return;
    }

    try {
        const provider = getOrCreatePlanProvider(projectPath);
        await provider.initialize();
        
        const result = await provider.deleteTask(taskId);
        
        if (result.success) {
            webviewPanel?.webview.postMessage({
                command: 'taskDeleted',
                taskId,
                success: true
            });
        } else {
            webviewPanel?.webview.postMessage({
                command: 'planError',
                error: result.error
            });
        }
    } catch (error) {
        webviewPanel?.webview.postMessage({
            command: 'planError',
            error: `Failed to delete task: ${error}`
        });
    }
}

/**
 * Handle moveTask message - reorder a task
 */
async function handleMoveTask(
    projectPath: string,
    taskId: string,
    newOrdinal: number,
    webviewPanel: vscode.WebviewPanel | undefined
) {
    if (!projectPath) {
        webviewPanel?.webview.postMessage({
            command: 'planError',
            error: 'Project path is required'
        });
        return;
    }

    try {
        const provider = getOrCreatePlanProvider(projectPath);
        await provider.initialize();
        
        const result = await provider.moveTask(taskId, newOrdinal);
        
        if (result.success) {
            webviewPanel?.webview.postMessage({
                command: 'taskMoved',
                taskId,
                newOrdinal,
                success: true
            });
        } else {
            webviewPanel?.webview.postMessage({
                command: 'planError',
                error: result.error
            });
        }
    } catch (error) {
        webviewPanel?.webview.postMessage({
            command: 'planError',
            error: `Failed to move task: ${error}`
        });
    }
}

/**
 * Handle logEdit message - log an MCP tool call for a task
 */
async function handleLogEdit(
    projectPath: string,
    taskId: string,
    toolName: string,
    request: Record<string, unknown>,
    response: string | Record<string, unknown>,
    webviewPanel: vscode.WebviewPanel | undefined
) {
    if (!projectPath) {
        webviewPanel?.webview.postMessage({
            command: 'planError',
            error: 'Project path is required'
        });
        return;
    }

    try {
        const provider = getOrCreatePlanProvider(projectPath);
        await provider.initialize();
        
        const result = await provider.logEdit(taskId, toolName, request, response);
        
        if (result.success && result.edit) {
            webviewPanel?.webview.postMessage({
                command: 'editLogged',
                edit: result.edit.toJSON(),
                taskId,
                success: true
            });
        } else {
            webviewPanel?.webview.postMessage({
                command: 'planError',
                error: result.error || 'Failed to log edit'
            });
        }
    } catch (error) {
        webviewPanel?.webview.postMessage({
            command: 'planError',
            error: `Failed to log edit: ${error}`
        });
    }
}

/**
 * DEPRECATED: No longer needed - we use native w14:paraId.
 * 
 * This function is kept for backward compatibility but the underlying
 * script is now a no-op that just reports the number of blocks with para_ids.
 */
async function embedUuidsInDocument(documentPath: string, analysisDir: string): Promise<{success: boolean, count?: number, error?: string}> {
    try {
        const workspaceRoot = path.join(__dirname, '..', '..');
        const pythonCmd = getPythonPath(workspaceRoot);
        const scriptPath = path.join(__dirname, '..', 'scripts', 'embed_uuids.py');
        const blocksPath = path.join(analysisDir, 'blocks.jsonl');
        
        if (!fs.existsSync(blocksPath)) {
            return { success: false, error: 'blocks.jsonl not found' };
        }
        
        const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" "${documentPath}" "${blocksPath}"`);
        const result = JSON.parse(stdout);
        
        if (result.success) {
            return { success: true, count: result.embedded_count };
        } else {
            return { success: false, error: result.error };
        }
    } catch (error) {
        return { success: false, error: String(error) };
    }
}

async function showVersionHistory(documentPath: string) {
    try {
        const workspaceRoot = path.join(__dirname, '..', '..');
        const pythonCmd = getPythonPath(workspaceRoot);
        const scriptPath = path.join(__dirname, '..', 'scripts', 'get_history.py');
        
        const { stdout } = await execAsync(`cd "${workspaceRoot}" && "${pythonCmd}" "${scriptPath}" "${documentPath}"`);
        const result = JSON.parse(stdout);
        
        if (!result.success) {
            vscode.window.showErrorMessage(`Failed to get history: ${result.error}`);
            return;
        }
        
        const commits: CommitInfo[] = result.commits;
        if (commits.length === 0) {
            vscode.window.showInformationMessage('No version history found for this document');
            return;
        }
        
        // Show quick pick with commit history
        const items = commits.map(c => ({
            label: `$(git-commit) ${c.short_hash}`,
            description: c.message,
            detail: `${c.author} • ${new Date(c.date).toLocaleString()}`,
            commit: c
        }));
        
        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select a version to view details',
            title: 'Version History'
        });
        
        if (selected) {
            const action = await vscode.window.showQuickPick([
                { label: '$(eye) View Details', action: 'view' },
                { label: '$(history) Restore This Version', action: 'restore' },
            ], {
                placeHolder: `Commit ${selected.commit.short_hash}: ${selected.commit.message}`
            });
            
            if (action?.action === 'restore') {
                const confirm = await vscode.window.showWarningMessage(
                    `Restore document to version ${selected.commit.short_hash}? A backup will be created.`,
                    'Restore',
                    'Cancel'
                );
                if (confirm === 'Restore') {
                    vscode.window.showInformationMessage('Restore functionality coming soon');
                    // TODO: Implement restore via Python script
                }
            } else if (action?.action === 'view') {
                vscode.window.showInformationMessage(
                    `Commit: ${selected.commit.hash}\nAuthor: ${selected.commit.author}\nDate: ${selected.commit.date}\nMessage: ${selected.commit.message}`
                );
            }
        }
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to get history: ${error}`);
    }
}

