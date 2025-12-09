/**
 * Refresh View Tests
 * 
 * Tests for the effi-contract-viewer.refreshView command and Ctrl+L keybinding.
 * 
 * TDD Approach: These tests are written to FAIL initially.
 * Implement the feature to make them pass.
 */

const path = require('path');
const fs = require('fs');

// Workspace root
const WORKSPACE_ROOT = path.resolve(__dirname, '..', '..', '..');

// Path to package.json
const PACKAGE_JSON_PATH = path.join(WORKSPACE_ROOT, 'extension', 'package.json');

// Path to extension.ts source
const EXTENSION_TS_PATH = path.join(WORKSPACE_ROOT, 'extension', 'src', 'extension.ts');

// ============================================================================
// SECTION 1: Keybinding Tests (package.json)
// ============================================================================

describe('Refresh keybinding (Ctrl+L)', () => {
    let packageJson;
    
    beforeAll(() => {
        const content = fs.readFileSync(PACKAGE_JSON_PATH, 'utf-8');
        packageJson = JSON.parse(content);
    });
    
    test('package.json should have keybindings section', () => {
        expect(packageJson.contributes).toHaveProperty('keybindings');
        expect(Array.isArray(packageJson.contributes.keybindings)).toBe(true);
    });
    
    test('should have Ctrl+L keybinding for refreshView command', () => {
        const keybindings = packageJson.contributes.keybindings;
        
        const refreshKeybinding = keybindings.find(kb => 
            kb.command === 'effi-contract-viewer.refreshView'
        );
        
        expect(refreshKeybinding).toBeDefined();
        expect(refreshKeybinding.key).toBe('ctrl+l');
    });
    
    test('refreshView keybinding should only be active when effiContractViewerActive', () => {
        const keybindings = packageJson.contributes.keybindings;
        
        const refreshKeybinding = keybindings.find(kb => 
            kb.command === 'effi-contract-viewer.refreshView'
        );
        
        expect(refreshKeybinding).toBeDefined();
        expect(refreshKeybinding.when).toBe('effiContractViewerActive');
    });
    
    test('refreshView keybinding should have mac key variant', () => {
        const keybindings = packageJson.contributes.keybindings;
        
        const refreshKeybinding = keybindings.find(kb => 
            kb.command === 'effi-contract-viewer.refreshView'
        );
        
        expect(refreshKeybinding).toBeDefined();
        // Mac should use cmd+l
        expect(refreshKeybinding.mac).toBe('cmd+l');
    });
});

// ============================================================================
// SECTION 2: Extension Code Structure Tests
// ============================================================================

describe('refreshView command implementation', () => {
    let extensionCode;
    
    beforeAll(() => {
        extensionCode = fs.readFileSync(EXTENSION_TS_PATH, 'utf-8');
    });
    
    test('refreshView handler should call reanalyzeAndRefresh', () => {
        // The refreshView command should call reanalyzeAndRefresh to re-analyze the document
        
        // Look for the refreshCommand registration pattern
        const refreshCommandPattern = /registerCommand\s*\(\s*['"]effi-contract-viewer\.refreshView['"][\s\S]*?\}\s*\)/;
        const refreshCommandMatch = extensionCode.match(refreshCommandPattern);
        
        expect(refreshCommandMatch).not.toBeNull();
        
        // The handler should reference reanalyzeAndRefresh
        const handlerCode = refreshCommandMatch[0];
        expect(handlerCode).toContain('reanalyzeAndRefresh');
    });
    
    test('refreshView handler should check for currentDocumentPath', () => {
        // The handler should guard against undefined currentDocumentPath
        
        const refreshCommandPattern = /registerCommand\s*\(\s*['"]effi-contract-viewer\.refreshView['"][\s\S]*?\}\s*\)/;
        const refreshCommandMatch = extensionCode.match(refreshCommandPattern);
        
        expect(refreshCommandMatch).not.toBeNull();
        
        const handlerCode = refreshCommandMatch[0];
        // Should check if currentDocumentPath exists before calling reanalyzeAndRefresh
        expect(handlerCode).toContain('currentDocumentPath');
    });
    
    test('refreshView handler should NOT just postMessage refresh', () => {
        // The old implementation only posted a 'refresh' message to re-render cached data
        // The new implementation should actually re-analyze and reload from disk
        
        const refreshCommandPattern = /registerCommand\s*\(\s*['"]effi-contract-viewer\.refreshView['"][\s\S]*?\}\s*\)/;
        const refreshCommandMatch = extensionCode.match(refreshCommandPattern);
        
        expect(refreshCommandMatch).not.toBeNull();
        
        const handlerCode = refreshCommandMatch[0];
        
        // The handler should contain reanalyzeAndRefresh call
        const hasReanalyze = handlerCode.includes('reanalyzeAndRefresh');
        
        // This test passes if reanalyzeAndRefresh is present
        expect(hasReanalyze).toBe(true);
    });
    
    test('refreshView should be async to await reanalyzeAndRefresh', () => {
        // reanalyzeAndRefresh is async, so the handler should be async too
        
        const refreshCommandPattern = /registerCommand\s*\(\s*['"]effi-contract-viewer\.refreshView['"][\s\S]*?\}\s*\)/;
        const refreshCommandMatch = extensionCode.match(refreshCommandPattern);
        
        expect(refreshCommandMatch).not.toBeNull();
        
        const handlerCode = refreshCommandMatch[0];
        
        // Handler should be async or await the reanalyzeAndRefresh call
        const isAsync = handlerCode.includes('async') || handlerCode.includes('await');
        expect(isAsync).toBe(true);
    });
    
    test('refreshView should show warning if no document is loaded', () => {
        // When currentDocumentPath is undefined, should show a warning
        
        const refreshCommandPattern = /registerCommand\s*\(\s*['"]effi-contract-viewer\.refreshView['"][\s\S]*?\}\s*\)/;
        const refreshCommandMatch = extensionCode.match(refreshCommandPattern);
        
        expect(refreshCommandMatch).not.toBeNull();
        
        const handlerCode = refreshCommandMatch[0];
        
        // Should show warning message when no document
        const hasWarningCheck = handlerCode.includes('showWarningMessage') || 
                               handlerCode.includes('showInformationMessage') ||
                               handlerCode.includes('return');
        expect(hasWarningCheck).toBe(true);
    });
    
    test('reanalyzeAndRefresh function should exist', () => {
        // The reanalyzeAndRefresh function should be defined
        expect(extensionCode).toContain('async function reanalyzeAndRefresh');
    });
    
    test('reanalyzeAndRefresh should call effilocal.cli analyze', () => {
        // The function should invoke the Python CLI to re-analyze
        expect(extensionCode).toContain('effilocal.cli analyze');
    });
    
    test('reanalyzeAndRefresh should show progress notification', () => {
        // Should show progress while re-analyzing
        expect(extensionCode).toContain('Refreshing');
    });
});

// ============================================================================
// SECTION 3: Command Registration Tests
// ============================================================================

describe('Command registration in package.json', () => {
    let packageJson;
    
    beforeAll(() => {
        const content = fs.readFileSync(PACKAGE_JSON_PATH, 'utf-8');
        packageJson = JSON.parse(content);
    });
    
    test('refreshView command should be registered', () => {
        const commands = packageJson.contributes.commands;
        
        const refreshCommand = commands.find(cmd => 
            cmd.command === 'effi-contract-viewer.refreshView'
        );
        
        expect(refreshCommand).toBeDefined();
        expect(refreshCommand.title).toBe('Effi: Refresh View');
    });
});
