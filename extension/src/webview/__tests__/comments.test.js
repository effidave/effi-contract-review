/**
 * CommentPanel UI Tests
 * 
 * Sprint 3, Phase 1: Comment Display & Basic Interaction
 * 
 * These tests verify the CommentPanel component functionality:
 * - Rendering a flat list of comments
 * - Displaying comment metadata (author, date, status)
 * - Click-to-scroll to referenced text
 * - Resolve/unresolve action triggering
 * - Comment-block highlighting
 * 
 * TDD Approach: These tests are written to FAIL initially.
 * Implement comments.js to make them pass.
 */

// Mock DOM environment for Node.js testing
// In browser/webview, this would use actual DOM
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
                // Clear children when setting innerHTML
                if (val === '') {
                    this.children = [];
                }
            },
            _textContent: '',
            get textContent() {
                // If we have a direct text value, return it
                if (this._textContent) return this._textContent;
                // Otherwise, gather text from children
                let text = '';
                for (const child of this.children) {
                    text += child.textContent || '';
                }
                return text;
            },
            set textContent(val) {
                this._textContent = val;
                // Clear children when setting text content directly
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
                // Simple selector support for testing
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
                if (name.startsWith('data-')) {
                    this.dataset[name.slice(5)] = value;
                }
                this[name] = value;
            },
            getAttribute(name) {
                if (name.startsWith('data-')) {
                    return this.dataset[name.slice(5)];
                }
                return this[name];
            }
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
                // Convert kebab-case to camelCase for dataset access
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

// Test data
const sampleComments = [
    {
        id: 'comment_1',
        comment_id: '0',  // actual w:id from XML
        author: 'John Smith',
        date: '2024-01-15T10:30:00Z',
        text: 'Please review this clause carefully.',
        status: 'active',
        is_resolved: false,
        para_id: '05C9333F',
        reference_text: 'The Supplier shall provide...'
    },
    {
        id: 'comment_2',
        comment_id: '1',  // actual w:id from XML
        author: 'Jane Doe',
        date: '2024-01-16T14:45:00Z',
        text: 'This has been addressed.',
        status: 'resolved',
        is_resolved: true,
        para_id: '1A2B3C4D',
        reference_text: 'Payment terms shall be...'
    },
    {
        id: 'comment_3',
        comment_id: '2',  // actual w:id from XML
        author: 'Bob Wilson',
        date: '2024-01-17T09:15:00Z',
        text: 'Need legal review on this section.',
        status: 'active',
        is_resolved: false,
        para_id: null,
        reference_text: null
    }
];

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
        console.log('\nCommentPanel UI Tests\n' + '='.repeat(50));
        
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
    throws(fn, msg) {
        let threw = false;
        try { fn(); } catch (e) { threw = true; }
        if (!threw) throw new Error(msg || 'Expected function to throw');
    }
};

// Import the CommentPanel (will fail until implemented)
let CommentPanel;
let commentsModule;
try {
    // In browser, this would be loaded via script tag
    // For Node.js testing, we need to require it
    commentsModule = require('../comments.js');
    CommentPanel = commentsModule.CommentPanel;
} catch (e) {
    // Module not found - expected for TDD
    CommentPanel = null;
}

// Helper to create panel with mock document
const createPanelWithMockDOM = (options = {}) => {
    const doc = createMockDOM();
    // Inject mock document into global scope
    global.document = doc;
    
    const container = doc.createElement('div');
    const panel = new CommentPanel(container, options);
    return { doc, container, panel };
};

// ============================================================================
// TEST DEFINITIONS
// ============================================================================

const runner = new TestRunner();

// ----------------------------------------------------------------------------
// Rendering Tests
// ----------------------------------------------------------------------------
runner.describe('CommentPanel Rendering', () => {
    
    runner.it('should create panel container with correct class', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container } = createPanelWithMockDOM();
        
        assert.ok(container.querySelector('.comment-panel'), 'Panel container should have .comment-panel class');
    });
    
    runner.it('should render header with title and count', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments(sampleComments);
        
        const header = container.querySelector('.comment-panel-header');
        assert.ok(header, 'Should have header element');
        assert.ok(header.textContent.includes('Comments'), 'Header should show "Comments"');
        assert.ok(header.textContent.includes('3'), 'Header should show count');
    });
    
    runner.it('should render flat list of comments', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments(sampleComments);
        
        const items = container.querySelectorAll('.comment-item');
        assert.equal(items.length, 3, 'Should render 3 comment items');
    });
    
    runner.it('should display comment author', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments([sampleComments[0]]);
        
        const author = container.querySelector('.comment-author');
        assert.ok(author, 'Should have author element');
        assert.ok(author.textContent.includes('John Smith'), 'Should display author name');
    });
    
    runner.it('should display comment date in readable format', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments([sampleComments[0]]);
        
        const date = container.querySelector('.comment-date');
        assert.ok(date, 'Should have date element');
        // Should show something like "Jan 15, 2024" or relative time
        assert.ok(date.textContent.length > 0, 'Date should not be empty');
    });
    
    runner.it('should display comment text content', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments([sampleComments[0]]);
        
        const text = container.querySelector('.comment-text');
        assert.ok(text, 'Should have text element');
        assert.ok(text.textContent.includes('Please review this clause'), 'Should display comment text');
    });
    
    runner.it('should display reference text preview when available', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments([sampleComments[0]]);
        
        const reference = container.querySelector('.comment-reference');
        assert.ok(reference, 'Should have reference element');
        assert.ok(reference.textContent.includes('The Supplier shall'), 'Should display reference text');
    });
    
    runner.it('should not display reference text when para_id is null', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments([sampleComments[2]]); // Comment with null para_id
        
        const reference = container.querySelector('.comment-reference');
        assert.ok(!reference || reference.textContent === '', 'Should not display reference when para_id is null');
    });
    
    runner.it('should show empty state when no comments', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments([]);
        
        const empty = container.querySelector('.comment-panel-empty');
        assert.ok(empty, 'Should show empty state');
        assert.ok(empty.textContent.includes('No comments'), 'Should display no comments message');
    });
    
});

// ----------------------------------------------------------------------------
// Status Display Tests
// ----------------------------------------------------------------------------
runner.describe('Comment Status Display', () => {
    
    runner.it('should show active status indicator for active comments', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments([sampleComments[0]]); // active comment
        
        const item = container.querySelector('.comment-item');
        assert.ok(item.classList.contains('status-active'), 'Active comment should have status-active class');
    });
    
    runner.it('should show resolved status indicator for resolved comments', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments([sampleComments[1]]); // resolved comment
        
        const item = container.querySelector('.comment-item');
        assert.ok(item.classList.contains('status-resolved'), 'Resolved comment should have status-resolved class');
    });
    
    runner.it('should display status badge text', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments([sampleComments[1]]);
        
        const badge = container.querySelector('.comment-status-badge');
        assert.ok(badge, 'Should have status badge');
        assert.ok(badge.textContent.toLowerCase().includes('resolved'), 'Badge should show resolved status');
    });
    
    runner.it('should store comment id in data attribute', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments([sampleComments[0]]);
        
        const item = container.querySelector('.comment-item');
        assert.equal(item.dataset.commentId, 'comment_1', 'Should store comment id in data-comment-id');
    });
    
    runner.it('should store para_id in data attribute when available', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments([sampleComments[0]]);
        
        const item = container.querySelector('.comment-item');
        assert.equal(item.dataset.paraId, '05C9333F', 'Should store para_id in data-para-id');
    });
    
});

// ----------------------------------------------------------------------------
// Interaction Tests
// ----------------------------------------------------------------------------
runner.describe('CommentPanel Interactions', () => {
    
    runner.it('should call onCommentClick callback when comment is clicked', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        let clickedId = null;
        const { container, panel } = createPanelWithMockDOM({
            onCommentClick: (comment) => { clickedId = comment.id; }
        });
        panel.setComments([sampleComments[0]]);
        
        const item = container.querySelector('.comment-item');
        item.click();
        
        assert.equal(clickedId, 'comment_1', 'Should call onCommentClick with comment id');
    });
    
    runner.it('should trigger scrollToBlock when comment with para_id is clicked', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        let scrolledToParaId = null;
        const { container, panel } = createPanelWithMockDOM({
            onScrollToBlock: (paraId) => { scrolledToParaId = paraId; }
        });
        panel.setComments([sampleComments[0]]);
        
        const item = container.querySelector('.comment-item');
        item.click();
        
        assert.equal(scrolledToParaId, '05C9333F', 'Should call onScrollToBlock with para_id');
    });
    
    runner.it('should not trigger scrollToBlock when comment has no para_id', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        let scrollCalled = false;
        const { container, panel } = createPanelWithMockDOM({
            onScrollToBlock: () => { scrollCalled = true; }
        });
        panel.setComments([sampleComments[2]]); // null para_id
        
        const item = container.querySelector('.comment-item');
        item.click();
        
        assert.ok(!scrollCalled, 'Should not call onScrollToBlock when para_id is null');
    });
    
    runner.it('should show resolve action button for active comments', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments([sampleComments[0]]);
        
        const resolveBtn = container.querySelector('.comment-action-resolve');
        assert.ok(resolveBtn, 'Active comment should have resolve button');
    });
    
    runner.it('should show unresolve action button for resolved comments', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments([sampleComments[1]]);
        
        const unresolveBtn = container.querySelector('.comment-action-unresolve');
        assert.ok(unresolveBtn, 'Resolved comment should have unresolve button');
    });
    
    runner.it('should call onResolve callback when resolve button clicked', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        let resolvedParaId = null;
        const { container, panel } = createPanelWithMockDOM({
            onResolve: (paraId) => { resolvedParaId = paraId; }
        });
        panel.setComments([sampleComments[0]]);
        
        const resolveBtn = container.querySelector('.comment-action-resolve');
        resolveBtn.click();
        
        assert.equal(resolvedParaId, '05C9333F', 'Should call onResolve with para_id');
    });
    
    runner.it('should call onUnresolve callback when unresolve button clicked', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        let unresolvedParaId = null;
        const { container, panel } = createPanelWithMockDOM({
            onUnresolve: (paraId) => { unresolvedParaId = paraId; }
        });
        panel.setComments([sampleComments[1]]);
        
        const unresolveBtn = container.querySelector('.comment-action-unresolve');
        unresolveBtn.click();
        
        assert.equal(unresolvedParaId, '1A2B3C4D', 'Should call onUnresolve with para_id');
    });
    
    runner.it('should prevent event bubbling when action button clicked', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        let itemClicked = false;
        let resolveClicked = false;
        const { container, panel } = createPanelWithMockDOM({
            onCommentClick: () => { itemClicked = true; },
            onResolve: () => { resolveClicked = true; }
        });
        panel.setComments([sampleComments[0]]);
        
        const resolveBtn = container.querySelector('.comment-action-resolve');
        resolveBtn.click();
        
        assert.ok(resolveClicked, 'onResolve should be called');
        assert.ok(!itemClicked, 'onCommentClick should not be called when action button clicked');
    });
    
});

// ----------------------------------------------------------------------------
// Highlighting Tests
// ----------------------------------------------------------------------------
runner.describe('Comment-Block Highlighting', () => {
    
    runner.it('should add highlight class when comment is selected', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments(sampleComments);
        
        panel.selectComment('comment_1');
        
        const item = container.querySelector('[data-comment-id="comment_1"]');
        assert.ok(item.classList.contains('comment-selected'), 'Selected comment should have highlight class');
    });
    
    runner.it('should remove highlight from previously selected comment', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments(sampleComments);
        
        panel.selectComment('comment_1');
        panel.selectComment('comment_2');
        
        const item0 = container.querySelector('[data-comment-id="comment_1"]');
        const item1 = container.querySelector('[data-comment-id="comment_2"]');
        assert.ok(!item0.classList.contains('comment-selected'), 'First comment should not be selected');
        assert.ok(item1.classList.contains('comment-selected'), 'Second comment should be selected');
    });
    
    runner.it('should call onHighlightBlock when comment is selected', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        let highlightedParaId = null;
        const { container, panel } = createPanelWithMockDOM({
            onHighlightBlock: (paraId) => { highlightedParaId = paraId; }
        });
        panel.setComments([sampleComments[0]]);
        
        panel.selectComment('comment_1');
        
        assert.equal(highlightedParaId, '05C9333F', 'Should call onHighlightBlock with para_id');
    });
    
    runner.it('should clear block highlight when comment is deselected', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        let highlightCleared = false;
        const { container, panel } = createPanelWithMockDOM({
            onHighlightBlock: (paraId) => { highlightCleared = paraId === null; }
        });
        panel.setComments([sampleComments[0]]);
        
        panel.selectComment('comment_1');
        panel.clearSelection();
        
        assert.ok(highlightCleared, 'Should call onHighlightBlock with null to clear highlight');
    });
    
    runner.it('should scroll selected comment into view', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments(sampleComments);
        
        panel.selectComment('comment_1');
        
        const item = container.querySelector('[data-comment-id="comment_1"]');
        assert.ok(item._scrolledIntoView, 'Selected comment should be scrolled into view');
    });
    
});

// ----------------------------------------------------------------------------
// Filter Tests
// ----------------------------------------------------------------------------
runner.describe('Comment Filtering', () => {
    
    runner.it('should filter to show only active comments', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments(sampleComments);
        
        panel.setFilter('active');
        
        const items = container.querySelectorAll('.comment-item');
        assert.equal(items.length, 2, 'Should show only 2 active comments');
    });
    
    runner.it('should filter to show only resolved comments', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments(sampleComments);
        
        panel.setFilter('resolved');
        
        const items = container.querySelectorAll('.comment-item');
        assert.equal(items.length, 1, 'Should show only 1 resolved comment');
    });
    
    runner.it('should show all comments when filter is "all"', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments(sampleComments);
        
        panel.setFilter('resolved');
        panel.setFilter('all');
        
        const items = container.querySelectorAll('.comment-item');
        assert.equal(items.length, 3, 'Should show all 3 comments');
    });
    
    runner.it('should display filter buttons in header', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments(sampleComments);
        
        const filterAll = container.querySelector('.filter-btn-all');
        const filterActive = container.querySelector('.filter-btn-active');
        const filterResolved = container.querySelector('.filter-btn-resolved');
        
        assert.ok(filterAll, 'Should have All filter button');
        assert.ok(filterActive, 'Should have Active filter button');
        assert.ok(filterResolved, 'Should have Resolved filter button');
    });
    
    runner.it('should highlight active filter button', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments(sampleComments);
        
        panel.setFilter('active');
        
        const filterActive = container.querySelector('.filter-btn-active');
        assert.ok(filterActive.classList.contains('active'), 'Active filter button should have active class');
    });
    
});

// ----------------------------------------------------------------------------
// Update Tests
// ----------------------------------------------------------------------------
runner.describe('Comment Updates', () => {
    
    runner.it('should update comment status after resolve', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments([{...sampleComments[0]}]);
        
        panel.updateCommentStatus('comment_1', 'resolved');
        
        const item = container.querySelector('.comment-item');
        assert.ok(item.classList.contains('status-resolved'), 'Comment should show as resolved');
    });
    
    runner.it('should update comment status after unresolve', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments([{...sampleComments[1]}]);
        
        panel.updateCommentStatus('comment_2', 'active');
        
        const item = container.querySelector('.comment-item');
        assert.ok(item.classList.contains('status-active'), 'Comment should show as active');
    });
    
    runner.it('should refresh panel when setComments called again', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        
        panel.setComments([sampleComments[0]]);
        let items = container.querySelectorAll('.comment-item');
        assert.equal(items.length, 1, 'Should have 1 comment initially');
        
        panel.setComments(sampleComments);
        items = container.querySelectorAll('.comment-item');
        assert.equal(items.length, 3, 'Should have 3 comments after update');
    });
    
    runner.it('should maintain selection after refresh if comment still exists', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        const { container, panel } = createPanelWithMockDOM();
        panel.setComments(sampleComments);
        
        panel.selectComment('comment_1');
        panel.setComments(sampleComments); // refresh
        
        const item = container.querySelector('[data-comment-id="comment_1"]');
        assert.ok(item.classList.contains('comment-selected'), 'Selection should be maintained after refresh');
    });
    
    runner.it('should clear selection if selected comment no longer exists', () => {
        if (!CommentPanel) throw new Error('CommentPanel not implemented');
        let highlightCleared = false;
        const { container, panel } = createPanelWithMockDOM({
            onHighlightBlock: (paraId) => { if (paraId === null) highlightCleared = true; }
        });
        panel.setComments(sampleComments);
        panel.selectComment('comment_1');
        
        // Refresh with comments not including id 'comment_1'
        panel.setComments([sampleComments[1], sampleComments[2]]);
        
        assert.ok(highlightCleared, 'Should clear highlight when selected comment is removed');
    });
    
});

// Run tests
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { runner, CommentPanel, sampleComments, createMockDOM, createMockVSCode };
}

// Auto-run when executed directly
if (typeof require !== 'undefined' && require.main === module) {
    runner.run().then(results => {
        process.exit(results.failed > 0 ? 1 : 0);
    });
}
