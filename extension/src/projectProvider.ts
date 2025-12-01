import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

export class ProjectProvider implements vscode.TreeDataProvider<ProjectItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<ProjectItem | undefined | null | void> = new vscode.EventEmitter<ProjectItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<ProjectItem | undefined | null | void> = this._onDidChangeTreeData.event;

    constructor(private workspaceRoot: string | undefined) {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: ProjectItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: ProjectItem): Thenable<ProjectItem[]> {
        if (!this.workspaceRoot) {
            return Promise.resolve([]);
        }

        if (element) {
            // If it's a project, return .docx files in drafts/current_drafts
            if (element.contextValue === 'project') {
                // Use the path from the element, not constructed from workspaceRoot
                const draftsPath = path.join(element.fsPath, 'drafts', 'current_drafts');
                
                if (fs.existsSync(draftsPath)) {
                    const files = fs.readdirSync(draftsPath).filter(f => f.endsWith('.docx') && !f.startsWith('~$'));
                    return Promise.resolve(files.map(f => new ProjectItem(
                        f,
                        vscode.TreeItemCollapsibleState.None,
                        'file',
                        path.join(draftsPath, f),
                        {
                            command: 'effi-contract-viewer.analyzeAndLoad',
                            title: 'Analyze and Load',
                            arguments: [vscode.Uri.file(path.join(draftsPath, f))]
                        }
                    )));
                }
                return Promise.resolve([]);
            }
        } else {
            // Root level - try to find projects
            
            // Strategy 0: Workspace IS EL_Projects
            if (path.basename(this.workspaceRoot) === 'EL_Projects') {
                return this.getProjectsInDirectory(this.workspaceRoot);
            }

            // Strategy 1: Workspace contains EL_Projects (e.g. opened 'effi-contract-review')
            const elProjectsPath = path.join(this.workspaceRoot, 'EL_Projects');
            if (fs.existsSync(elProjectsPath)) {
                return this.getProjectsInDirectory(elProjectsPath);
            }

            // Strategy 2: Workspace IS a project inside EL_Projects (e.g. opened 'Test Project')
            // Check if parent is EL_Projects
            const parentDir = path.dirname(this.workspaceRoot);
            if (path.basename(parentDir) === 'EL_Projects') {
                return this.getProjectsInDirectory(parentDir);
            }

            // Strategy 3: Workspace IS a standalone project (has drafts folder)
            const draftsPath = path.join(this.workspaceRoot, 'drafts');
            if (fs.existsSync(draftsPath)) {
                const projectName = path.basename(this.workspaceRoot);
                return Promise.resolve([new ProjectItem(
                    projectName,
                    vscode.TreeItemCollapsibleState.Collapsed,
                    'project',
                    this.workspaceRoot
                )]);
            }

            return Promise.resolve([]);
        }
        return Promise.resolve([]);
    }

    private getProjectsInDirectory(directoryPath: string): Promise<ProjectItem[]> {
        const projects = fs.readdirSync(directoryPath).filter(f => {
            return !f.startsWith('.') && fs.statSync(path.join(directoryPath, f)).isDirectory();
        });
        return Promise.resolve(projects.map(p => new ProjectItem(
            p,
            vscode.TreeItemCollapsibleState.Collapsed,
            'project',
            path.join(directoryPath, p)
        )));
    }
}

class ProjectItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly contextValue: string,
        public readonly fsPath: string,
        public readonly command?: vscode.Command
    ) {
        super(label, collapsibleState);
        this.tooltip = `${this.label}`;
        this.description = contextValue === 'file' ? 'Document' : 'Project';
        
        if (contextValue === 'project') {
            this.iconPath = new vscode.ThemeIcon('folder');
        } else {
            this.iconPath = new vscode.ThemeIcon('file-text');
        }
    }
}
