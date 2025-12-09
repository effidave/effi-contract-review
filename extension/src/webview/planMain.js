/**
 * Plan Webview Main Script
 * 
 * Entry point for the Plan WebviewPanel (separate from Contract Analysis).
 * Initializes the PlanPanel component and handles VS Code webview messaging.
 */

// @ts-check
/// <reference types="vscode-webview" />

// Get VS Code API
// @ts-ignore - acquireVsCodeApi is injected by VS Code
const vscode = acquireVsCodeApi();

// Plan panel instance
let planPanel = null;

// Project path (set from initial page data or messages)
let projectPath = window.initialProjectPath || '';

/**
 * Initialize the Plan panel
 */
function initializePlanPanel() {
    const container = document.getElementById('plan-container');
    if (!container) {
        console.error('Plan container not found');
        return;
    }
    
    if (!window.PlanPanel) {
        console.error('PlanPanel class not available');
        return;
    }
    
    // Create the plan panel with event handlers
    planPanel = new window.PlanPanel(container, {
        vscode: vscode,
        projectPath: projectPath,
        onTaskSelect: (taskId) => {
            console.log('Task selected:', taskId);
        }
    });
    
    console.log('Plan panel initialized with projectPath:', projectPath);
}

/**
 * Handle messages from the extension
 */
window.addEventListener('message', event => {
    const message = event.data;

    switch (message.command) {
        case 'setProjectPath':
            // Update project path
            projectPath = message.projectPath;
            if (planPanel) {
                planPanel.setProjectPath(projectPath);
            }
            break;
            
        case 'planData':
            // Handle plan data from extension
            if (planPanel) {
                planPanel.handleMessage(message);
            }
            break;
            
        case 'taskAdded':
        case 'taskUpdated':
        case 'taskDeleted':
        case 'taskMoved':
        case 'editLogged':
        case 'planSaved':
            // Forward plan operation results to panel
            if (planPanel) {
                planPanel.handleMessage(message);
            }
            break;
            
        case 'planError':
            // Handle plan operation error
            console.error('Plan operation failed:', message.error);
            if (planPanel) {
                planPanel.handleMessage(message);
            }
            break;
    }
});

/**
 * Initialize when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize plan panel
    initializePlanPanel();
    
    // Notify extension that webview is ready
    vscode.postMessage({ command: 'ready' });
});
