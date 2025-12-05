/**
 * Editor Track Changes Tests
 * 
 * Sprint 3, Phase 2: Track Changes Display & Accept/Reject
 * 
 * These tests verify the BlockEditor component functionality for track changes:
 * - Rendering insertions with <ins> tags and green underline styling
 * - Rendering deletions with <del> tags and red strikethrough styling
 * - Tooltip display with author and date information
 * - Toolbar Accept All / Reject All button behavior
 * 
 * TDD Approach: These tests are written to FAIL initially.
 * Implementation should make them pass.
 */

// Mock DOM environment for Node.js testing
const createMockDOM = () => {
    const elements = new Map();
    let idCounter = 0;
    
    const createElement = (tag) => {
        const id = `mock-${++idCounter}`;
        const element = {
            tagName: tag.toUpperCase(),
            id: '',
            className: '',
            classList: {
                _classes: new Set(),
                add(...classes) { classes.forEach(c => this._classes.add(c)); },
                remove(...classes) { classes.forEach(c => this._classes.delete(c)); },
                contains(c) { return this._classes.has(c); },
                toggle(c) { this._classes.has(c) ? this._classes.delete(c) : this._classes.add(c); }
            },
            _innerHTML: '',
            get innerHTML() {
                return this._innerHTML;
            },
            set innerHTML(val) {
                this._innerHTML = val;
                if (val === '') {
                    this.children = [];
                }
            },
            _textContent: '',
            get textContent() {
                if (this._textContent) return this._textContent;
                let text = '';
                for (const child of this.children) {
                    text += child.textContent || '';
                }
                return text;
            },
            set textContent(val) {
                this._textContent = val;
                this.children = [];
            },
            style: {},
            dataset: {},
            children: [],
            parentElement: null,
            _eventListeners: {},
            appendChild(child) {
                child.parentElement = this;
                this.children.push(child);
                return child;
            },
            removeChild(child) {
                const idx = this.children.indexOf(child);
                if (idx >= 0) {
                    this.children.splice(idx, 1);
                    child.parentElement = null;
                }
                return child;
            },
            addEventListener(event, handler) {
                if (!this._eventListeners[event]) this._eventListeners[event] = [];
                this._eventListeners[event].push(handler);
            },
            removeEventListener(event, handler) {
                if (this._eventListeners[event]) {
                    const idx = this._eventListeners[event].indexOf(handler);
                    if (idx >= 0) this._eventListeners[event].splice(idx, 1);
                }
            },
            dispatchEvent(event) {
                const handlers = this._eventListeners[event.type] || [];
                handlers.forEach(h => h(event));
            },
            click() {
                this.dispatchEvent({ type: 'click', target: this, stopPropagation: () => {} });
            },
            querySelector(selector) {
                for (const child of this.children) {
                    if (matchesSelector(child, selector)) return child;
                    const found = child.querySelector ? child.querySelector(selector) : null;
                    if (found) return found;
                }
                return null;
            },
            querySelectorAll(selector) {
                const results = [];
                const search = (el) => {
                    if (matchesSelector(el, selector)) results.push(el);
                    (el.children || []).forEach(search);
                };
                this.children.forEach(search);
                return results;
            },
            scrollIntoView() {
                this._scrolledIntoView = true;
            },
            setAttribute(name, value) {
                if (name === 'title') {
                    this.title = value;
                } else if (name.startsWith('data-')) {
                    this.dataset[name.slice(5)] = value;
                }
                this[name] = value;
            },
            getAttribute(name) {
                if (name === 'title') {
                    return this.title;
                } else if (name.startsWith('data-')) {
                    return this.dataset[name.slice(5)];
                }
                return this[name];
            },
            title: ''
        };
        elements.set(id, element);
        return element;
    };
    
    const matchesSelector = (el, selector) => {
        if (selector.startsWith('.')) {
            return el.classList.contains(selector.slice(1));
        }
        if (selector.startsWith('#')) {
            return el.id === selector.slice(1);
        }
        if (selector.startsWith('[data-')) {
            const match = selector.match(/\[data-([^=]+)="([^"]+)"\]/);
            if (match) {
                const key = match[1].replace(/-([a-z])/g, (g) => g[1].toUpperCase());
                return el.dataset[key] === match[2];
            }
        }
        return el.tagName === selector.toUpperCase();
    };
    
    return {
        createElement,
        getElementById(id) {
            for (const el of elements.values()) {
                if (el.id === id) return el;
            }
            return null;
        },
        body: createElement('body')
    };
};

// Mock vscode API
const createMockVSCode = () => {
    const messages = [];
    return {
        postMessage(msg) {
            messages.push(msg);
        },
        getMessages() {
            return messages;
        },
        clearMessages() {
            messages.length = 0;
        }
    };
};

// Test data - blocks with revision runs
const sampleBlocksWithRevisions = [
    {
        id: 'block-001',
        type: 'paragraph',
        text: 'This is normal text with an insertion.',
        runs: [
            { start: 0, end: 20, formats: [] },
            { start: 20, end: 35, formats: ['insert'], author: 'John Smith', date: '2024-01-15T10:30:00Z' },
            { start: 35, end: 39, formats: [] }
        ]
    },
    {
        id: 'block-002',
        type: 'paragraph',
        text: 'Text with a deletion here.',
        runs: [
            { start: 0, end: 12, formats: [] },
            { start: 12, end: 20, formats: ['delete'], author: 'Jane Doe', date: '2024-01-16T14:45:00Z' },
            { start: 20, end: 26, formats: [] }
        ]
    },
    {
        id: 'block-003',
        type: 'paragraph',
        text: 'Bold inserted text here.',
        runs: [
            { start: 0, end: 5, formats: ['bold'] },
            { start: 5, end: 18, formats: ['insert', 'bold'], author: 'Bob Wilson', date: '2024-01-17T09:15:00Z' },
            { start: 18, end: 24, formats: [] }
        ]
    },
    {
        id: 'block-004',
        type: 'paragraph',
        text: 'Multiple revisions in one block.',
        runs: [
            { start: 0, end: 9, formats: ['insert'], author: 'John Smith', date: '2024-01-18T11:00:00Z' },
            { start: 9, end: 20, formats: [] },
            { start: 20, end: 32, formats: ['delete'], author: 'Jane Doe', date: '2024-01-18T12:00:00Z' }
        ]
    }
];

const blockWithNoRevisions = {
    id: 'block-plain',
    type: 'paragraph',
    text: 'Plain text without any revisions.',
    runs: [
        { start: 0, end: 33, formats: [] }
    ]
};

const blockWithNoRuns = {
    id: 'block-no-runs',
    type: 'paragraph',
    text: 'Text with no runs array.'
};

// Test Suite
class TestRunner {
    constructor() {
        this.tests = [];
        this.passed = 0;
        this.failed = 0;
        this.skipped = 0;
    }
    
    describe(name, fn) {
        console.log(`\n  ${name}`);
        fn();
    }
    
    it(name, fn) {
        this.tests.push({ name, fn });
    }
    
    skip(name, fn) {
        this.tests.push({ name, fn, skip: true });
    }
    
    async run() {
        console.log('\nEditor Track Changes Tests\n' + '='.repeat(50));
        
        for (const test of this.tests) {
            if (test.skip) {
                console.log(`  ⏭ SKIP: ${test.name}`);
                this.skipped++;
                continue;
            }
            
            try {
                await test.fn();
                console.log(`  ✓ PASS: ${test.name}`);
                this.passed++;
            } catch (error) {
                console.log(`  ✗ FAIL: ${test.name}`);
                console.log(`    Error: ${error.message}`);
                this.failed++;
            }
        }
        
        console.log('\n' + '='.repeat(50));
        console.log(`Results: ${this.passed} passed, ${this.failed} failed, ${this.skipped} skipped`);
        console.log('='.repeat(50));
        
        return { passed: this.passed, failed: this.failed, skipped: this.skipped };
    }
}

const assert = {
    ok(value, msg) {
        if (!value) throw new Error(msg || `Expected truthy but got ${value}`);
    },
    equal(actual, expected, msg) {
        if (actual !== expected) {
            throw new Error(msg || `Expected ${expected} but got ${actual}`);
        }
    },
    deepEqual(actual, expected, msg) {
        if (JSON.stringify(actual) !== JSON.stringify(expected)) {
            throw new Error(msg || `Objects not equal:\nActual: ${JSON.stringify(actual)}\nExpected: ${JSON.stringify(expected)}`);
        }
    },
    includes(str, substr, msg) {
        if (!str || !str.includes(substr)) {
            throw new Error(msg || `Expected "${str}" to include "${substr}"`);
        }
    },
    notIncludes(str, substr, msg) {
        if (str && str.includes(substr)) {
            throw new Error(msg || `Expected "${str}" to NOT include "${substr}"`);
        }
    },
    throws(fn, msg) {
        let threw = false;
        try { fn(); } catch (e) { threw = true; }
        if (!threw) throw new Error(msg || 'Expected function to throw');
    }
};

// Import the BlockEditor (will fail until implemented/exposed properly)
let BlockEditor;
let editorModule;
try {
    editorModule = require('../editor.js');
    BlockEditor = editorModule.BlockEditor;
} catch (e) {
    // Module not found - expected for TDD
    BlockEditor = null;
}

// Helper to create a minimal BlockEditor mock that uses _renderFormattedText
const createEditorWithBlock = (block, options = {}) => {
    const doc = createMockDOM();
    global.document = doc;
    
    // Create a minimal object to test _renderFormattedText
    // This mimics what BlockEditor does internally
    const editor = {
        _escapeHtml(str) {
            return str
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;');
        },
        _buildRevisionTitle(run, action) {
            if (!BlockEditor) throw new Error('BlockEditor not implemented');
            return BlockEditor.prototype._buildRevisionTitle.call(this, run, action);
        },
        _formatRevisionDate(dateStr) {
            if (!BlockEditor) throw new Error('BlockEditor not implemented');
            return BlockEditor.prototype._formatRevisionDate.call(this, dateStr);
        },
        _renderFormattedText(block) {
            if (!BlockEditor) throw new Error('BlockEditor not implemented');
            return BlockEditor.prototype._renderFormattedText.call(this, block);
        }
    };
    
    return { doc, editor, block };
};

// ============================================================================
// TEST DEFINITIONS
// ============================================================================

const runner = new TestRunner();

// ----------------------------------------------------------------------------
// Insertion Rendering Tests
// ----------------------------------------------------------------------------
runner.describe('Insertion Rendering', () => {
    
    runner.it('should wrap inserted text in <ins> tag', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const { editor } = createEditorWithBlock(sampleBlocksWithRevisions[0]);
        
        const html = editor._renderFormattedText(sampleBlocksWithRevisions[0]);
        
        assert.includes(html, '<ins', 'Should contain <ins> tag for inserted text');
        assert.includes(html, '</ins>', 'Should have closing </ins> tag');
    });
    
    runner.it('should apply revision-insert class to inserted text', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const { editor } = createEditorWithBlock(sampleBlocksWithRevisions[0]);
        
        const html = editor._renderFormattedText(sampleBlocksWithRevisions[0]);
        
        assert.includes(html, 'class="revision-insert"', 'Should have revision-insert class');
    });
    
    runner.it('should include author in title attribute for insertions', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const { editor } = createEditorWithBlock(sampleBlocksWithRevisions[0]);
        
        const html = editor._renderFormattedText(sampleBlocksWithRevisions[0]);
        
        assert.includes(html, 'title="', 'Should have title attribute');
        assert.includes(html, 'John Smith', 'Title should include author name');
    });
    
    runner.it('should include action type in title attribute for insertions', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const { editor } = createEditorWithBlock(sampleBlocksWithRevisions[0]);
        
        const html = editor._renderFormattedText(sampleBlocksWithRevisions[0]);
        
        assert.includes(html, 'Inserted', 'Title should indicate "Inserted"');
    });
    
    runner.it('should include date in title attribute when available', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const { editor } = createEditorWithBlock(sampleBlocksWithRevisions[0]);
        
        const html = editor._renderFormattedText(sampleBlocksWithRevisions[0]);
        
        // Date should be formatted, checking for year is a good indicator
        assert.includes(html, '2024', 'Title should include the year from the date');
    });
    
});

// ----------------------------------------------------------------------------
// Deletion Rendering Tests
// ----------------------------------------------------------------------------
runner.describe('Deletion Rendering', () => {
    
    runner.it('should wrap deleted text in <del> tag', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const { editor } = createEditorWithBlock(sampleBlocksWithRevisions[1]);
        
        const html = editor._renderFormattedText(sampleBlocksWithRevisions[1]);
        
        assert.includes(html, '<del', 'Should contain <del> tag for deleted text');
        assert.includes(html, '</del>', 'Should have closing </del> tag');
    });
    
    runner.it('should apply revision-delete class to deleted text', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const { editor } = createEditorWithBlock(sampleBlocksWithRevisions[1]);
        
        const html = editor._renderFormattedText(sampleBlocksWithRevisions[1]);
        
        assert.includes(html, 'class="revision-delete"', 'Should have revision-delete class');
    });
    
    runner.it('should include author in title attribute for deletions', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const { editor } = createEditorWithBlock(sampleBlocksWithRevisions[1]);
        
        const html = editor._renderFormattedText(sampleBlocksWithRevisions[1]);
        
        assert.includes(html, 'Jane Doe', 'Title should include author name');
    });
    
    runner.it('should include action type in title attribute for deletions', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const { editor } = createEditorWithBlock(sampleBlocksWithRevisions[1]);
        
        const html = editor._renderFormattedText(sampleBlocksWithRevisions[1]);
        
        assert.includes(html, 'Deleted', 'Title should indicate "Deleted"');
    });
    
});

// ----------------------------------------------------------------------------
// Combined Formatting Tests
// ----------------------------------------------------------------------------
runner.describe('Combined Formatting', () => {
    
    runner.it('should handle bold + insert combined formatting', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const { editor } = createEditorWithBlock(sampleBlocksWithRevisions[2]);
        
        const html = editor._renderFormattedText(sampleBlocksWithRevisions[2]);
        
        // Should have both <strong> and <ins> tags
        assert.includes(html, '<strong>', 'Should have bold formatting');
        assert.includes(html, '<ins', 'Should have insert tag');
    });
    
    runner.it('should handle multiple revisions in one block', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const { editor } = createEditorWithBlock(sampleBlocksWithRevisions[3]);
        
        const html = editor._renderFormattedText(sampleBlocksWithRevisions[3]);
        
        assert.includes(html, '<ins', 'Should have insert tag');
        assert.includes(html, '<del', 'Should have delete tag');
    });
    
});

// ----------------------------------------------------------------------------
// Edge Cases
// ----------------------------------------------------------------------------
runner.describe('Edge Cases', () => {
    
    runner.it('should handle blocks with no revisions', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const { editor } = createEditorWithBlock(blockWithNoRevisions);
        
        const html = editor._renderFormattedText(blockWithNoRevisions);
        
        assert.notIncludes(html, '<ins', 'Should not have insert tag');
        assert.notIncludes(html, '<del', 'Should not have delete tag');
        assert.includes(html, 'Plain text', 'Should contain the text');
    });
    
    runner.it('should handle blocks with no runs array', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const { editor } = createEditorWithBlock(blockWithNoRuns);
        
        const html = editor._renderFormattedText(blockWithNoRuns);
        
        assert.includes(html, 'Text with no runs array', 'Should render text correctly');
        assert.notIncludes(html, '<ins', 'Should not have insert tag');
        assert.notIncludes(html, '<del', 'Should not have delete tag');
    });
    
    runner.it('should escape HTML in inserted text', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const block = {
            id: 'block-html',
            type: 'paragraph',
            text: 'Text with <script>alert("xss")</script>',
            runs: [
                { start: 0, end: 10, formats: [] },
                { start: 10, end: 38, formats: ['insert'], author: 'Test', date: '2024-01-01T00:00:00Z' }
            ]
        };
        const { editor } = createEditorWithBlock(block);
        
        const html = editor._renderFormattedText(block);
        
        assert.notIncludes(html, '<script>', 'Should escape script tags');
        assert.includes(html, '&lt;script&gt;', 'Should have escaped script tag');
    });
    
    runner.it('should handle run with missing author', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const block = {
            id: 'block-no-author',
            type: 'paragraph',
            text: 'Inserted without author.',
            runs: [
                { start: 0, end: 24, formats: ['insert'], date: '2024-01-01T00:00:00Z' }
            ]
        };
        const { editor } = createEditorWithBlock(block);
        
        const html = editor._renderFormattedText(block);
        
        assert.includes(html, 'Unknown', 'Should show "Unknown" for missing author');
    });
    
    runner.it('should handle run with missing date', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const block = {
            id: 'block-no-date',
            type: 'paragraph',
            text: 'Inserted without date.',
            runs: [
                { start: 0, end: 22, formats: ['insert'], author: 'Test Author' }
            ]
        };
        const { editor } = createEditorWithBlock(block);
        
        const html = editor._renderFormattedText(block);
        
        assert.includes(html, 'Test Author', 'Should include author');
        // Should not crash when date is missing
    });
    
    runner.it('should handle empty text block', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const block = {
            id: 'block-empty',
            type: 'paragraph',
            text: '',
            runs: []
        };
        const { editor } = createEditorWithBlock(block);
        
        const html = editor._renderFormattedText(block);
        
        assert.includes(html, '<br>', 'Should return <br> for empty block');
    });
    
});

// ----------------------------------------------------------------------------
// Title Formatting Tests
// ----------------------------------------------------------------------------
runner.describe('Title/Tooltip Formatting', () => {
    
    runner.it('should format date readably in title', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const { editor } = createEditorWithBlock(sampleBlocksWithRevisions[0]);
        
        const title = editor._buildRevisionTitle(
            { author: 'Test', date: '2024-01-15T10:30:00Z' },
            'Inserted'
        );
        
        // Should include month name and day
        assert.includes(title, 'Jan', 'Should format month');
        assert.includes(title, '15', 'Should include day');
    });
    
    runner.it('should escape HTML in title to prevent XSS', () => {
        if (!BlockEditor) throw new Error('BlockEditor not implemented');
        const { editor } = createEditorWithBlock(sampleBlocksWithRevisions[0]);
        
        const title = editor._buildRevisionTitle(
            { author: '<script>alert("xss")</script>', date: '2024-01-15T10:30:00Z' },
            'Inserted'
        );
        
        assert.notIncludes(title, '<script>', 'Should escape script in author');
        assert.includes(title, '&lt;script&gt;', 'Should have escaped script');
    });
    
});

// ----------------------------------------------------------------------------
// Toolbar Button Tests
// ----------------------------------------------------------------------------
runner.describe('Toolbar Accept/Reject All Buttons', () => {
    
    runner.it('should have Accept All button in toolbar when revisions exist', () => {
        // This test requires the main.js integration
        // We'll test that the button element is created
        const doc = createMockDOM();
        global.document = doc;
        const vscode = createMockVSCode();
        global.vscode = vscode;
        
        // For now, skip if not implemented - this requires main.js toolbar setup
        throw new Error('Toolbar button test not implemented');
    });
    
    runner.skip('should have Reject All button in toolbar when revisions exist', () => {
        // Placeholder for toolbar test
    });
    
    runner.skip('should call acceptAllRevisions when Accept All clicked', () => {
        // Placeholder for Accept All action test
    });
    
    runner.skip('should call rejectAllRevisions when Reject All clicked', () => {
        // Placeholder for Reject All action test
    });
    
    runner.skip('should send acceptAllRevisions message to extension', () => {
        // Placeholder for message test
    });
    
    runner.skip('should send rejectAllRevisions message to extension', () => {
        // Placeholder for message test
    });
    
    runner.skip('should update revision count display after Accept All', () => {
        // Placeholder for UI update test
    });
    
    runner.skip('should hide buttons when no revisions', () => {
        // Placeholder for conditional rendering test
    });
    
});

// Run tests
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { runner, BlockEditor, sampleBlocksWithRevisions, createMockDOM, createMockVSCode };
}

// Auto-run when executed directly
if (typeof require !== 'undefined' && require.main === module) {
    runner.run().then(results => {
        process.exit(results.failed > 0 ? 1 : 0);
    });
}
