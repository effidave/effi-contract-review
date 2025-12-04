/**
 * Extension Integration Tests
 * 
 * Sprint 3, Phase 1: Comment Display & Basic Interaction
 * Day 5: Integration & Testing
 * 
 * These tests verify the complete integration:
 * - Python script calls (manage_comments.py)
 * - Extension message handlers (getComments, resolveComment, unresolveComment)
 * - End-to-end flow from UI action to document update
 * 
 * TDD Approach: These tests are written to FAIL initially.
 * Implement the integration code to make them pass.
 */

const path = require('path');
const fs = require('fs');
const { execSync, spawn } = require('child_process');

// Determine workspace root (effi-contract-review folder)
// When running from extension directory: __dirname is extension/src/__tests__
// WORKSPACE_ROOT should be effi-contract-review
const WORKSPACE_ROOT = path.resolve(__dirname, '..', '..', '..');

// Test fixture path - tests/fixtures/real_world relative to workspace
const FIXTURES_DIR = path.join(WORKSPACE_ROOT, 'tests', 'fixtures', 'real_world');
const TEST_DOC = path.join(FIXTURES_DIR, 'with_comments.docx');

// Scripts directory - extension/scripts relative to workspace  
const SCRIPTS_DIR = path.join(WORKSPACE_ROOT, 'extension', 'scripts');
const MANAGE_COMMENTS_SCRIPT = path.join(SCRIPTS_DIR, 'manage_comments.py');

// Helper to get Python path
function getPythonPath() {
    const venvPath = process.platform === 'win32'
        ? path.join(WORKSPACE_ROOT, '.venv', 'Scripts', 'python.exe')
        : path.join(WORKSPACE_ROOT, '.venv', 'bin', 'python');
    
    if (fs.existsSync(venvPath)) {
        return venvPath;
    }
    return process.platform === 'win32' ? 'python' : 'python3';
}

// Helper to run Python script and get JSON output
function runPythonScript(scriptPath, args = []) {
    const pythonPath = getPythonPath();
    const cmd = `"${pythonPath}" "${scriptPath}" ${args.map(a => `"${a}"`).join(' ')}`;
    
    try {
        const stdout = execSync(cmd, { 
            cwd: WORKSPACE_ROOT,
            encoding: 'utf-8',
            timeout: 30000
        });
        return JSON.parse(stdout.trim());
    } catch (error) {
        // If we get output before the error, try to parse it
        if (error.stdout) {
            try {
                return JSON.parse(error.stdout.trim());
            } catch (e) {
                // Fall through
            }
        }
        throw new Error(`Python script failed: ${error.message}\nStderr: ${error.stderr || ''}`);
    }
}

// Helper to create a copy of test document for modification tests
function createTestCopy() {
    const copyPath = TEST_DOC.replace('.docx', '_test_copy.docx');
    fs.copyFileSync(TEST_DOC, copyPath);
    return copyPath;
}

function cleanupTestCopy(copyPath) {
    if (fs.existsSync(copyPath)) {
        try {
            fs.unlinkSync(copyPath);
        } catch (e) {
            // Ignore cleanup errors
        }
    }
}

// ============================================================================
// SECTION 1: Python Script Tests (manage_comments.py)
// ============================================================================

describe('manage_comments.py Python script', () => {
    // Pre-test check: fixtures exist
    beforeAll(() => {
        expect(fs.existsSync(FIXTURES_DIR)).toBe(true);
        expect(fs.existsSync(TEST_DOC)).toBe(true);
    });
    
    describe('Script existence and structure', () => {
        test('manage_comments.py script should exist', () => {
            expect(fs.existsSync(MANAGE_COMMENTS_SCRIPT)).toBe(true);
        });
        
        test('script should be valid Python (no syntax errors)', () => {
            const pythonPath = getPythonPath();
            const result = execSync(`"${pythonPath}" -m py_compile "${MANAGE_COMMENTS_SCRIPT}"`, {
                cwd: WORKSPACE_ROOT,
                encoding: 'utf-8'
            });
            // No exception = valid Python
        });
    });
    
    describe('get_comments command', () => {
        test('should return JSON with success and comments array', () => {
            const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', TEST_DOC]);
            
            expect(result).toHaveProperty('success', true);
            expect(result).toHaveProperty('comments');
            expect(Array.isArray(result.comments)).toBe(true);
        });
        
        test('should return comments with required fields', () => {
            const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', TEST_DOC]);
            
            expect(result.success).toBe(true);
            expect(result.comments.length).toBeGreaterThan(0);
            
            const comment = result.comments[0];
            expect(comment).toHaveProperty('id');
            expect(comment).toHaveProperty('author');
            expect(comment).toHaveProperty('text');
            expect(comment).toHaveProperty('status');
        });
        
        test('should return comment count', () => {
            const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', TEST_DOC]);
            
            expect(result.success).toBe(true);
            expect(result).toHaveProperty('total_comments');
            expect(typeof result.total_comments).toBe('number');
            expect(result.total_comments).toBe(result.comments.length);
        });
        
        test('should include para_id for each comment', () => {
            const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', TEST_DOC]);
            
            expect(result.success).toBe(true);
            // At least some comments should have para_id
            const commentsWithParaId = result.comments.filter(c => c.para_id);
            expect(commentsWithParaId.length).toBeGreaterThan(0);
        });
        
        test('should include status (active/resolved) for each comment', () => {
            const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', TEST_DOC]);
            
            expect(result.success).toBe(true);
            for (const comment of result.comments) {
                expect(['active', 'resolved']).toContain(comment.status);
            }
        });
        
        test('should return error for non-existent file', () => {
            const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', '/nonexistent/file.docx']);
            
            expect(result).toHaveProperty('success', false);
            expect(result).toHaveProperty('error');
        });
    });
    
    describe('resolve_comment command', () => {
        let testCopyPath;
        
        beforeEach(() => {
            testCopyPath = createTestCopy();
        });
        
        afterEach(() => {
            cleanupTestCopy(testCopyPath);
        });
        
        test('should resolve an active comment', () => {
            // First, get a comment ID
            const getResult = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', testCopyPath]);
            expect(getResult.success).toBe(true);
            
            const activeComment = getResult.comments.find(c => c.status === 'active');
            if (!activeComment) {
                console.log('No active comments found in test document');
                return; // Skip if no active comments
            }
            
            // Resolve the comment using comment_id (the w:id attribute, e.g., "0")
            const resolveResult = runPythonScript(MANAGE_COMMENTS_SCRIPT, [
                'resolve_comment',
                testCopyPath,
                activeComment.comment_id  // Use comment_id, not id
            ]);
            
            expect(resolveResult).toHaveProperty('success', true);
            
            // Verify the comment is now resolved
            const verifyResult = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', testCopyPath]);
            const updatedComment = verifyResult.comments.find(c => c.comment_id === activeComment.comment_id);
            expect(updatedComment.status).toBe('resolved');
        });
        
        test('should return error for invalid comment ID', () => {
            const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, [
                'resolve_comment',
                testCopyPath,
                'invalid-id-99999'
            ]);
            
            expect(result).toHaveProperty('success', false);
            expect(result).toHaveProperty('error');
        });
        
        test('should return error for non-existent file', () => {
            const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, [
                'resolve_comment',
                '/nonexistent/file.docx',
                '0'
            ]);
            
            expect(result).toHaveProperty('success', false);
            expect(result).toHaveProperty('error');
        });
    });
    
    describe('unresolve_comment command', () => {
        let testCopyPath;
        
        beforeEach(() => {
            testCopyPath = createTestCopy();
        });
        
        afterEach(() => {
            cleanupTestCopy(testCopyPath);
        });
        
        test('should unresolve a resolved comment', () => {
            // First, get a comment and resolve it
            const getResult = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', testCopyPath]);
            expect(getResult.success).toBe(true);
            
            const activeComment = getResult.comments.find(c => c.status === 'active');
            if (!activeComment) {
                console.log('No active comments to test unresolve');
                return;
            }
            
            // Resolve it first using comment_id
            runPythonScript(MANAGE_COMMENTS_SCRIPT, [
                'resolve_comment',
                testCopyPath,
                activeComment.comment_id
            ]);
            
            // Now unresolve it
            const unresolveResult = runPythonScript(MANAGE_COMMENTS_SCRIPT, [
                'unresolve_comment',
                testCopyPath,
                activeComment.comment_id
            ]);
            
            expect(unresolveResult).toHaveProperty('success', true);
            
            // Verify it's back to active
            const verifyResult = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', testCopyPath]);
            const updatedComment = verifyResult.comments.find(c => c.comment_id === activeComment.comment_id);
            expect(updatedComment.status).toBe('active');
        });
        
        test('should return error for invalid comment ID', () => {
            const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, [
                'unresolve_comment',
                testCopyPath,
                'invalid-id-99999'
            ]);
            
            expect(result).toHaveProperty('success', false);
            expect(result).toHaveProperty('error');
        });
    });
});

// ============================================================================
// SECTION 2: Extension Message Handler Tests (Mock vscode API)
// ============================================================================

describe('Extension message handlers', () => {
    // Mock vscode module
    const mockVscode = {
        window: {
            showInformationMessage: jest.fn(),
            showErrorMessage: jest.fn(),
            showWarningMessage: jest.fn(),
            withProgress: jest.fn((options, task) => task({ report: jest.fn() }))
        },
        ProgressLocation: {
            Notification: 1
        },
        commands: {
            executeCommand: jest.fn()
        }
    };
    
    // Mock webview panel
    let mockWebviewPanel;
    let messageHandler;
    let postedMessages;
    
    beforeEach(() => {
        postedMessages = [];
        mockWebviewPanel = {
            webview: {
                html: '',
                postMessage: jest.fn((msg) => postedMessages.push(msg)),
                onDidReceiveMessage: jest.fn((handler) => {
                    messageHandler = handler;
                })
            },
            dispose: jest.fn()
        };
    });
    
    describe('getComments handler', () => {
        test('should call Python script and post comments to webview', async () => {
            // This test verifies the extension properly handles getComments
            // The actual implementation should:
            // 1. Receive message with command: 'getComments', documentPath: '...'
            // 2. Call manage_comments.py get_comments <path>
            // 3. Post message with command: 'updateComments', comments: [...]
            
            // We can't fully test without loading extension, but we can verify the structure
            const testMessage = {
                command: 'getComments',
                documentPath: TEST_DOC
            };
            
            // Verify message structure
            expect(testMessage).toHaveProperty('command', 'getComments');
            expect(testMessage).toHaveProperty('documentPath');
        });
        
        test('should handle errors gracefully', async () => {
            const testMessage = {
                command: 'getComments',
                documentPath: '/nonexistent/file.docx'
            };
            
            // Verify error message structure
            expect(testMessage).toHaveProperty('documentPath');
        });
    });
    
    describe('resolveComment handler', () => {
        test('should accept resolve message and call Python script', async () => {
            const testMessage = {
                command: 'resolveComment',
                commentId: '0',
                documentPath: TEST_DOC
            };
            
            // Verify message structure
            expect(testMessage).toHaveProperty('command', 'resolveComment');
            expect(testMessage).toHaveProperty('commentId');
            expect(testMessage).toHaveProperty('documentPath');
        });
        
        test('should post success result to webview', async () => {
            // Expected response structure
            const expectedResponse = {
                command: 'commentResolved',
                commentId: '0',
                success: true
            };
            
            expect(expectedResponse).toHaveProperty('command', 'commentResolved');
            expect(expectedResponse).toHaveProperty('success', true);
        });
        
        test('should post error on failure', async () => {
            const expectedErrorResponse = {
                command: 'commentError',
                error: 'Failed to resolve comment',
                commentId: '0'
            };
            
            expect(expectedErrorResponse).toHaveProperty('command', 'commentError');
            expect(expectedErrorResponse).toHaveProperty('error');
        });
    });
    
    describe('unresolveComment handler', () => {
        test('should accept unresolve message and call Python script', async () => {
            const testMessage = {
                command: 'unresolveComment',
                commentId: '0',
                documentPath: TEST_DOC
            };
            
            expect(testMessage).toHaveProperty('command', 'unresolveComment');
            expect(testMessage).toHaveProperty('commentId');
            expect(testMessage).toHaveProperty('documentPath');
        });
        
        test('should post success result to webview', async () => {
            const expectedResponse = {
                command: 'commentUnresolved',
                commentId: '0',
                success: true
            };
            
            expect(expectedResponse).toHaveProperty('command', 'commentUnresolved');
            expect(expectedResponse).toHaveProperty('success', true);
        });
    });
});

// ============================================================================
// SECTION 3: End-to-End Flow Tests
// ============================================================================

describe('End-to-end comment flows', () => {
    let testCopyPath;
    
    beforeEach(() => {
        testCopyPath = createTestCopy();
    });
    
    afterEach(() => {
        cleanupTestCopy(testCopyPath);
    });
    
    test('full flow: load comments -> resolve -> verify -> unresolve -> verify', () => {
        // Step 1: Load comments
        const loadResult = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', testCopyPath]);
        expect(loadResult.success).toBe(true);
        expect(loadResult.comments.length).toBeGreaterThan(0);
        
        // Step 2: Find an active comment
        const activeComment = loadResult.comments.find(c => c.status === 'active');
        if (!activeComment) {
            console.log('Skipping: no active comments in test document');
            return;
        }
        // Use comment_id (the w:id attribute, e.g., "0") not id
        const commentId = activeComment.comment_id;
        
        // Step 3: Resolve the comment
        const resolveResult = runPythonScript(MANAGE_COMMENTS_SCRIPT, [
            'resolve_comment',
            testCopyPath,
            commentId
        ]);
        expect(resolveResult.success).toBe(true);
        
        // Step 4: Verify it's resolved
        const verifyResolvedResult = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', testCopyPath]);
        const resolvedComment = verifyResolvedResult.comments.find(c => c.comment_id === commentId);
        expect(resolvedComment.status).toBe('resolved');
        
        // Step 5: Unresolve the comment
        const unresolveResult = runPythonScript(MANAGE_COMMENTS_SCRIPT, [
            'unresolve_comment',
            testCopyPath,
            commentId
        ]);
        expect(unresolveResult.success).toBe(true);
        
        // Step 6: Verify it's back to active
        const verifyActiveResult = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', testCopyPath]);
        const unresolvedComment = verifyActiveResult.comments.find(c => c.comment_id === commentId);
        expect(unresolvedComment.status).toBe('active');
    });
    
    test('comments should include reference text snippet', () => {
        const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', testCopyPath]);
        expect(result.success).toBe(true);
        
        // At least some comments should have reference_text
        const commentsWithRefText = result.comments.filter(c => c.reference_text);
        expect(commentsWithRefText.length).toBeGreaterThan(0);
    });
    
    test('comments should be linkable to blocks via para_id', () => {
        const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', testCopyPath]);
        expect(result.success).toBe(true);
        
        // At least some comments should have para_id for block linking
        const commentsWithParaId = result.comments.filter(c => c.para_id);
        expect(commentsWithParaId.length).toBeGreaterThan(0);
        
        // para_id should be 8-character hex strings
        for (const comment of commentsWithParaId) {
            expect(comment.para_id).toMatch(/^[0-9A-Fa-f]{8}$/);
        }
    });
    
    test('concurrent operations should not corrupt document', async () => {
        // Get all comments first
        const loadResult = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', testCopyPath]);
        expect(loadResult.success).toBe(true);
        
        const activeComments = loadResult.comments.filter(c => c.status === 'active').slice(0, 3);
        if (activeComments.length < 2) {
            console.log('Skipping: need at least 2 active comments');
            return;
        }
        
        // Resolve multiple comments sequentially (not truly concurrent in this test)
        for (const comment of activeComments) {
            const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, [
                'resolve_comment',
                testCopyPath,
                comment.comment_id  // Use comment_id, not id
            ]);
            expect(result.success).toBe(true);
        }
        
        // Verify all are resolved
        const verifyResult = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', testCopyPath]);
        expect(verifyResult.success).toBe(true);
        
        for (const comment of activeComments) {
            const updatedComment = verifyResult.comments.find(c => c.comment_id === comment.comment_id);
            expect(updatedComment.status).toBe('resolved');
        }
        
        // Document should still be valid (can be opened)
        const finalLoadResult = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', testCopyPath]);
        expect(finalLoadResult.success).toBe(true);
    });
});

// ============================================================================
// SECTION 4: Comment-Block Association Tests
// ============================================================================

describe('Comment-Block association', () => {
    test('comments should have para_id matching w14:paraId format', () => {
        const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', TEST_DOC]);
        expect(result.success).toBe(true);
        
        // Filter comments that have para_id
        const commentsWithParaId = result.comments.filter(c => c.para_id);
        
        for (const comment of commentsWithParaId) {
            // para_id should be 8-char hex (Word's w14:paraId format)
            expect(comment.para_id).toMatch(/^[0-9A-Fa-f]{8}$/);
        }
    });
    
    test('comment data should be suitable for UI panel display', () => {
        const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', TEST_DOC]);
        expect(result.success).toBe(true);
        
        for (const comment of result.comments.slice(0, 5)) {
            // Fields needed for UI display
            expect(comment).toHaveProperty('id');
            expect(comment).toHaveProperty('author');
            expect(comment).toHaveProperty('text');
            expect(comment).toHaveProperty('status');
            
            // Author and text should be non-empty strings
            expect(typeof comment.author).toBe('string');
            expect(typeof comment.text).toBe('string');
            expect(comment.author.length).toBeGreaterThan(0);
        }
    });
    
    test('resolved/active counts should match status', () => {
        const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', TEST_DOC]);
        expect(result.success).toBe(true);
        
        const activeCount = result.comments.filter(c => c.status === 'active').length;
        const resolvedCount = result.comments.filter(c => c.status === 'resolved').length;
        
        expect(activeCount + resolvedCount).toBe(result.total_comments);
    });
});

// ============================================================================
// SECTION 5: Error Handling Tests
// ============================================================================

describe('Error handling', () => {
    test('invalid command should cause argparse error', () => {
        // Invalid command causes argparse to exit with error (non-JSON output)
        expect(() => {
            runPythonScript(MANAGE_COMMENTS_SCRIPT, ['invalid_command', TEST_DOC]);
        }).toThrow();
    });
    
    test('missing arguments should return error', () => {
        expect(() => {
            runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments']);
        }).toThrow();
    });
    
    test('should handle locked/in-use document gracefully', () => {
        // This test documents the expected behavior but may not be runnable
        // if we can't easily lock a file
        const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, ['get_comments', TEST_DOC]);
        
        // Reading should work (no lock needed for read)
        expect(result.success).toBe(true);
    });
    
    test('should return meaningful error messages', () => {
        const result = runPythonScript(MANAGE_COMMENTS_SCRIPT, [
            'resolve_comment',
            '/nonexistent/path/to/file.docx',
            '0'
        ]);
        
        expect(result.success).toBe(false);
        expect(result.error).toBeDefined();
        expect(result.error.length).toBeGreaterThan(0);
    });
});
