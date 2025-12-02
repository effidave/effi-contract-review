/**
 * BlockEditor - WYSIWYG editor for contract documents
 * 
 * This is the core editor component that handles:
 * - Block-based contentEditable editing
 * - Undo/Redo stack
 * - Formatting (bold, italic, underline)
 * - Dirty state tracking
 */

// @ts-check

/**
 * @typedef {Object} Run
 * @property {number} start - Start offset in text
 * @property {number} end - End offset in text
 * @property {string[]} formats - Array of format names ('bold', 'italic', 'underline')
 */

/**
 * @typedef {Object} Block
 * @property {string} id - Block UUID
 * @property {string} text - Plain text content
 * @property {Run[]} [runs] - Formatted runs (optional, defaults to single unformatted run)
 * @property {string} [type] - Block type (paragraph, heading, list_item)
 * @property {Object} [list] - List metadata (ordinal, level, etc.)
 * @property {number} [para_idx] - Paragraph index in document
 */

/**
 * @typedef {Object} EditorState
 * @property {Block[]} blocks - All blocks in document
 * @property {number} cursorBlockIndex - Index of block with cursor
 * @property {number} cursorOffset - Character offset within block
 */

class BlockEditor {
    /**
     * @param {HTMLElement} container - Container element for editor
     * @param {Block[]} blocks - Initial blocks from analysis
     * @param {Object} options - Editor options
     */
    constructor(container, blocks, options = {}) {
        this.container = container;
        this.blocks = this._normalizeBlocks(blocks);
        this.options = {
            onDirtyChange: options.onDirtyChange || (() => {}),
            onSave: options.onSave || (() => {}),
            showCheckboxes: options.showCheckboxes || false,
            selectedClauses: options.selectedClauses || new Set(),
            onCheckboxChange: options.onCheckboxChange || (() => {}),
            readOnly: options.readOnly || false,
            ...options
        };
        
        /** @type {EditorState[]} */
        this.undoStack = [];
        /** @type {EditorState[]} */
        this.redoStack = [];
        
        this.isDirty = false;
        this.dirtyBlockIds = new Set();
        
        // Selection tracking
        this.currentSelection = null;
        
        // Bind methods
        this._handleInput = this._handleInput.bind(this);
        this._handleKeydown = this._handleKeydown.bind(this);
        this._handleSelectionChange = this._handleSelectionChange.bind(this);
        this._handlePaste = this._handlePaste.bind(this);
    }
    
    /**
     * Normalize blocks to ensure consistent structure
     * @param {Block[]} blocks 
     * @returns {Block[]}
     */
    _normalizeBlocks(blocks) {
        return blocks.map(block => ({
            ...block,
            runs: block.runs || [{ start: 0, end: (block.text || '').length, formats: [] }]
        }));
    }
    
    /**
     * Initialize and render the editor
     */
    render() {
        this.container.innerHTML = '';
        this.container.className = 'block-editor';
        
        // Create editor content area
        const editorContent = document.createElement('div');
        editorContent.className = 'editor-content';
        
        this.blocks.forEach((block, index) => {
            const blockEl = this._renderBlock(block, index);
            editorContent.appendChild(blockEl);
        });
        
        this.container.appendChild(editorContent);
        this.editorContent = editorContent;
        
        // Set up event listeners
        this._setupEventListeners();
    }
    
    /**
     * Render a single block
     * @param {Block} block 
     * @param {number} index 
     * @returns {HTMLElement}
     */
    _renderBlock(block, index) {
        const wrapper = document.createElement('div');
        wrapper.className = 'editor-block-wrapper';
        wrapper.dataset.blockId = block.id;
        wrapper.dataset.blockIndex = String(index);

        // Text indentation based on level (no checkbox indent)
        const listMeta = block.list || {};
        const level = listMeta.level || 0;
        const textIndent = level > 0 ? (level * 45) : 0;

        // Add checkbox if enabled
        if (this.options.showCheckboxes) {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'clause-checkbox editor-checkbox';
            checkbox.dataset.id = block.id;
            checkbox.checked = this.options.selectedClauses.has(block.id);
            checkbox.addEventListener('change', (e) => {
                this.options.onCheckboxChange(block.id, e.target.checked);
            });
            wrapper.appendChild(checkbox);
        }

        // Content container with indentation
        const contentEl = document.createElement('div');
        contentEl.className = 'editor-block-content';
        contentEl.style.paddingLeft = `${textIndent}px`;

        // Ordinal/number
        const ordinal = listMeta.ordinal || '';
        if (ordinal) {
            const ordinalEl = document.createElement('span');
            ordinalEl.className = 'editor-ordinal';
            ordinalEl.textContent = ordinal;
            contentEl.appendChild(ordinalEl);
        }

        // Text content (editable based on readOnly option)
        const textEl = document.createElement('div');
        textEl.className = 'editor-block-text';
        textEl.contentEditable = this.options.readOnly ? 'false' : 'true';
        textEl.dataset.blockId = block.id;
        textEl.spellcheck = !this.options.readOnly;

        // Render formatted content
        textEl.innerHTML = this._renderFormattedText(block);

        // Apply heading styles
        if (block.type === 'heading') {
            textEl.classList.add('editor-heading');
            const headingLevel = block.level || 1;
            textEl.classList.add(`editor-heading-${Math.min(headingLevel, 4)}`);
        }

        contentEl.appendChild(textEl);
        wrapper.appendChild(contentEl);

        return wrapper;
    }
    
    /**
     * Render block text with formatting spans
     * @param {Block} block 
     * @returns {string}
     */
    _renderFormattedText(block) {
        const text = block.text || '';
        if (!text) return '<br>'; // Empty block needs BR for cursor
        
        const runs = block.runs || [{ start: 0, end: text.length, formats: [] }];
        
        let html = '';
        runs.forEach(run => {
            const runText = text.substring(run.start, run.end);
            if (!runText) return;
            
            let escapedText = this._escapeHtml(runText);
            
            // Apply formatting
            if (run.formats && run.formats.length > 0) {
                if (run.formats.includes('bold')) {
                    escapedText = `<strong>${escapedText}</strong>`;
                }
                if (run.formats.includes('italic')) {
                    escapedText = `<em>${escapedText}</em>`;
                }
                if (run.formats.includes('underline')) {
                    escapedText = `<u>${escapedText}</u>`;
                }
            }
            
            html += escapedText;
        });
        
        return html || '<br>';
    }
    
    /**
     * Set up all event listeners
     */
    _setupEventListeners() {
        // Skip edit-related listeners in readOnly mode
        if (this.options.readOnly) return;
        
        // Input events on contenteditable elements
        this.container.addEventListener('input', this._handleInput);
        
        // Keydown for special keys
        this.container.addEventListener('keydown', this._handleKeydown);
        
        // Selection change
        document.addEventListener('selectionchange', this._handleSelectionChange);
        
        // Paste handling
        this.container.addEventListener('paste', this._handlePaste);
    }
    
    /**
     * Set read-only mode without re-rendering
     * @param {boolean} readOnly
     */
    setReadOnly(readOnly) {
        this.options.readOnly = readOnly;
        
        // Update all contenteditable elements
        const textElements = this.container.querySelectorAll('.editor-block-text');
        textElements.forEach(el => {
            el.contentEditable = readOnly ? 'false' : 'true';
            el.spellcheck = !readOnly;
        });
        
        // Add/remove event listeners
        if (readOnly) {
            this.container.removeEventListener('input', this._handleInput);
            this.container.removeEventListener('keydown', this._handleKeydown);
            document.removeEventListener('selectionchange', this._handleSelectionChange);
            this.container.removeEventListener('paste', this._handlePaste);
        } else {
            this.container.addEventListener('input', this._handleInput);
            this.container.addEventListener('keydown', this._handleKeydown);
            document.addEventListener('selectionchange', this._handleSelectionChange);
            this.container.addEventListener('paste', this._handlePaste);
        }
    }
    
    /**
     * Check if editor is in read-only mode
     * @returns {boolean}
     */
    isReadOnly() {
        return this.options.readOnly;
    }
    
    /**
     * Handle input events
     * @param {InputEvent} event 
     */
    _handleInput(event) {
        const target = event.target;
        if (!target.classList.contains('editor-block-text')) return;
        
        const blockId = target.dataset.blockId;
        const block = this.blocks.find(b => b.id === blockId);
        if (!block) return;
        
        // Save state for undo before making changes
        this._pushUndoState();
        
        // Update block text (strip HTML for now, preserve formatting later)
        const newText = target.innerText.replace(/\n$/, ''); // Remove trailing newline
        block.text = newText;
        
        // Normalize runs to match new text length
        block.runs = [{ start: 0, end: newText.length, formats: [] }];
        
        // Mark as dirty
        this._markDirty(blockId);
    }
    
    /**
     * Handle keydown events
     * @param {KeyboardEvent} event 
     */
    _handleKeydown(event) {
        const target = event.target;
        if (!target.classList.contains('editor-block-text')) return;
        
        const blockId = target.dataset.blockId;
        const blockIndex = this.blocks.findIndex(b => b.id === blockId);
        
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this._splitBlock(blockIndex, this._getCaretOffset(target));
        } else if (event.key === 'Backspace') {
            const offset = this._getCaretOffset(target);
            if (offset === 0 && blockIndex > 0) {
                event.preventDefault();
                this._mergeWithPrevious(blockIndex);
            }
        } else if (event.key === 'Delete') {
            const block = this.blocks[blockIndex];
            const offset = this._getCaretOffset(target);
            if (offset === (block.text || '').length && blockIndex < this.blocks.length - 1) {
                event.preventDefault();
                this._mergeWithNext(blockIndex);
            }
        }
    }
    
    /**
     * Handle paste events
     * @param {ClipboardEvent} event 
     */
    _handlePaste(event) {
        const target = event.target;
        if (!target.classList.contains('editor-block-text')) return;
        
        event.preventDefault();
        
        // Get plain text only
        const text = event.clipboardData.getData('text/plain');
        
        // Insert at cursor position
        document.execCommand('insertText', false, text);
    }
    
    /**
     * Handle selection change
     */
    _handleSelectionChange() {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) {
            this.currentSelection = null;
            return;
        }
        
        const range = selection.getRangeAt(0);
        const container = range.commonAncestorContainer;
        
        // Find the block element
        let blockEl = container;
        while (blockEl && !blockEl.classList?.contains('editor-block-text')) {
            blockEl = blockEl.parentElement;
        }
        
        if (!blockEl) {
            this.currentSelection = null;
            return;
        }
        
        this.currentSelection = {
            blockId: blockEl.dataset.blockId,
            range: range.cloneRange(),
            isCollapsed: selection.isCollapsed
        };
    }
    
    /**
     * Apply formatting to current selection
     * @param {string} format - 'bold', 'italic', or 'underline'
     */
    applyFormat(format) {
        if (!this.currentSelection || this.currentSelection.isCollapsed) return;
        
        const { blockId, range } = this.currentSelection;
        const block = this.blocks.find(b => b.id === blockId);
        if (!block) return;
        
        // Use execCommand for simple implementation
        // This modifies the DOM directly
        const command = {
            'bold': 'bold',
            'italic': 'italic',
            'underline': 'underline'
        }[format];
        
        if (command) {
            this._pushUndoState();
            document.execCommand(command, false, null);
            this._syncBlockFromDOM(blockId);
            this._markDirty(blockId);
        }
    }
    
    /**
     * Sync block data from DOM after execCommand changes
     * @param {string} blockId 
     */
    _syncBlockFromDOM(blockId) {
        const block = this.blocks.find(b => b.id === blockId);
        if (!block) return;
        
        const blockEl = this.container.querySelector(`[data-block-id="${blockId}"].editor-block-text`);
        if (!blockEl) return;
        
        // Parse DOM to extract text and runs
        const { text, runs } = this._parseFormattedContent(blockEl);
        block.text = text;
        block.runs = runs;
    }
    
    /**
     * Parse formatted content from DOM element
     * @param {HTMLElement} element 
     * @returns {{ text: string, runs: Run[] }}
     */
    _parseFormattedContent(element) {
        let text = '';
        const runs = [];
        
        const processNode = (node, activeFormats = []) => {
            if (node.nodeType === Node.TEXT_NODE) {
                const nodeText = node.textContent || '';
                if (nodeText) {
                    const start = text.length;
                    text += nodeText;
                    runs.push({
                        start,
                        end: text.length,
                        formats: [...activeFormats]
                    });
                }
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                const el = node;
                const newFormats = [...activeFormats];
                
                if (el.tagName === 'STRONG' || el.tagName === 'B') {
                    if (!newFormats.includes('bold')) newFormats.push('bold');
                }
                if (el.tagName === 'EM' || el.tagName === 'I') {
                    if (!newFormats.includes('italic')) newFormats.push('italic');
                }
                if (el.tagName === 'U') {
                    if (!newFormats.includes('underline')) newFormats.push('underline');
                }
                
                for (const child of node.childNodes) {
                    processNode(child, newFormats);
                }
            }
        };
        
        for (const child of element.childNodes) {
            processNode(child, []);
        }
        
        // Merge adjacent runs with same formats
        return { text, runs: this._mergeRuns(runs) };
    }
    
    /**
     * Merge adjacent runs with identical formats
     * @param {Run[]} runs 
     * @returns {Run[]}
     */
    _mergeRuns(runs) {
        if (runs.length <= 1) return runs;
        
        const merged = [runs[0]];
        for (let i = 1; i < runs.length; i++) {
            const prev = merged[merged.length - 1];
            const curr = runs[i];
            
            if (this._formatsEqual(prev.formats, curr.formats)) {
                prev.end = curr.end;
            } else {
                merged.push(curr);
            }
        }
        return merged;
    }
    
    /**
     * Check if two format arrays are equal
     * @param {string[]} a 
     * @param {string[]} b 
     * @returns {boolean}
     */
    _formatsEqual(a, b) {
        if (a.length !== b.length) return false;
        const sortedA = [...a].sort();
        const sortedB = [...b].sort();
        return sortedA.every((v, i) => v === sortedB[i]);
    }
    
    /**
     * Split a block at the given offset
     * @param {number} blockIndex 
     * @param {number} offset 
     */
    _splitBlock(blockIndex, offset) {
        this._pushUndoState();
        
        const block = this.blocks[blockIndex];
        const text = block.text || '';
        
        // Create new block with text after cursor
        const newBlock = {
            id: this._generateId(),
            type: 'paragraph',
            text: text.substring(offset),
            runs: [{ start: 0, end: text.length - offset, formats: [] }],
            list: block.list ? { ...block.list } : undefined,
            para_idx: -1 // New block, will be assigned on save
        };
        
        // Truncate current block
        block.text = text.substring(0, offset);
        block.runs = [{ start: 0, end: offset, formats: [] }];
        
        // Insert new block
        this.blocks.splice(blockIndex + 1, 0, newBlock);
        
        // Re-render
        this._reRenderBlock(blockIndex);
        const newBlockEl = this._renderBlock(newBlock, blockIndex + 1);
        const currentBlockEl = this.container.querySelector(`[data-block-id="${block.id}"]`);
        currentBlockEl.parentElement.insertBefore(newBlockEl, currentBlockEl.nextSibling);
        
        // Update indices
        this._updateBlockIndices();
        
        // Focus new block
        const newTextEl = newBlockEl.querySelector('.editor-block-text');
        if (newTextEl) {
            newTextEl.focus();
            this._setCaretPosition(newTextEl, 0);
        }
        
        this._markDirty(block.id);
        this._markDirty(newBlock.id);
    }
    
    /**
     * Merge block with previous block
     * @param {number} blockIndex 
     */
    _mergeWithPrevious(blockIndex) {
        if (blockIndex <= 0) return;
        
        this._pushUndoState();
        
        const prevBlock = this.blocks[blockIndex - 1];
        const currBlock = this.blocks[blockIndex];
        
        const prevLength = (prevBlock.text || '').length;
        prevBlock.text = (prevBlock.text || '') + (currBlock.text || '');
        prevBlock.runs = [{ start: 0, end: prevBlock.text.length, formats: [] }];
        
        // Remove current block
        this.blocks.splice(blockIndex, 1);
        
        // Remove from DOM
        const currEl = this.container.querySelector(`[data-block-id="${currBlock.id}"]`).parentElement;
        currEl.remove();
        
        // Re-render previous block
        this._reRenderBlock(blockIndex - 1);
        
        // Update indices
        this._updateBlockIndices();
        
        // Set cursor at merge point
        const prevTextEl = this.container.querySelector(`[data-block-id="${prevBlock.id}"].editor-block-text`);
        if (prevTextEl) {
            prevTextEl.focus();
            this._setCaretPosition(prevTextEl, prevLength);
        }
        
        this._markDirty(prevBlock.id);
    }
    
    /**
     * Merge block with next block
     * @param {number} blockIndex 
     */
    _mergeWithNext(blockIndex) {
        if (blockIndex >= this.blocks.length - 1) return;
        
        this._pushUndoState();
        
        const currBlock = this.blocks[blockIndex];
        const nextBlock = this.blocks[blockIndex + 1];
        
        const currLength = (currBlock.text || '').length;
        currBlock.text = (currBlock.text || '') + (nextBlock.text || '');
        currBlock.runs = [{ start: 0, end: currBlock.text.length, formats: [] }];
        
        // Remove next block
        this.blocks.splice(blockIndex + 1, 1);
        
        // Remove from DOM
        const nextEl = this.container.querySelector(`[data-block-id="${nextBlock.id}"]`).parentElement;
        nextEl.remove();
        
        // Re-render current block
        this._reRenderBlock(blockIndex);
        
        // Update indices
        this._updateBlockIndices();
        
        // Keep cursor at original position
        const currTextEl = this.container.querySelector(`[data-block-id="${currBlock.id}"].editor-block-text`);
        if (currTextEl) {
            currTextEl.focus();
            this._setCaretPosition(currTextEl, currLength);
        }
        
        this._markDirty(currBlock.id);
    }
    
    /**
     * Re-render a single block in place
     * @param {number} blockIndex 
     */
    _reRenderBlock(blockIndex) {
        const block = this.blocks[blockIndex];
        const oldWrapper = this.container.querySelector(`[data-block-id="${block.id}"]`)?.parentElement;
        if (!oldWrapper) return;
        
        const newWrapper = this._renderBlock(block, blockIndex);
        oldWrapper.replaceWith(newWrapper);
    }
    
    /**
     * Update block indices in DOM
     */
    _updateBlockIndices() {
        const wrappers = this.container.querySelectorAll('.editor-block-wrapper');
        wrappers.forEach((wrapper, index) => {
            wrapper.dataset.blockIndex = String(index);
        });
    }
    
    /**
     * Push current state to undo stack
     */
    _pushUndoState() {
        const state = this._captureState();
        this.undoStack.push(state);
        
        // Limit undo stack size
        if (this.undoStack.length > 50) {
            this.undoStack.shift();
        }
        
        // Clear redo stack on new change
        this.redoStack = [];
    }
    
    /**
     * Capture current editor state
     * @returns {EditorState}
     */
    _captureState() {
        return {
            blocks: JSON.parse(JSON.stringify(this.blocks)),
            cursorBlockIndex: 0,
            cursorOffset: 0
        };
    }
    
    /**
     * Undo last change
     */
    undo() {
        if (this.undoStack.length === 0) return;
        
        // Save current state to redo stack
        this.redoStack.push(this._captureState());
        
        // Restore previous state
        const state = this.undoStack.pop();
        this.blocks = state.blocks;
        this.render();
        
        // Mark all blocks as potentially dirty
        this.blocks.forEach(b => this.dirtyBlockIds.add(b.id));
        this._updateDirtyState();
    }
    
    /**
     * Redo last undone change
     */
    redo() {
        if (this.redoStack.length === 0) return;
        
        // Save current state to undo stack
        this.undoStack.push(this._captureState());
        
        // Restore redo state
        const state = this.redoStack.pop();
        this.blocks = state.blocks;
        this.render();
        
        // Mark all blocks as potentially dirty
        this.blocks.forEach(b => this.dirtyBlockIds.add(b.id));
        this._updateDirtyState();
    }
    
    /**
     * Mark a block as dirty (has unsaved changes)
     * @param {string} blockId 
     */
    _markDirty(blockId) {
        this.dirtyBlockIds.add(blockId);
        this._updateDirtyState();
    }
    
    /**
     * Update dirty state and notify
     */
    _updateDirtyState() {
        const wasDirty = this.isDirty;
        this.isDirty = this.dirtyBlockIds.size > 0;
        
        if (wasDirty !== this.isDirty) {
            this.options.onDirtyChange(this.isDirty);
        }
    }
    
    /**
     * Get all blocks
     * @returns {Block[]}
     */
    getBlocks() {
        return this.blocks;
    }
    
    /**
     * Get dirty blocks
     * @returns {Block[]}
     */
    getDirtyBlocks() {
        return this.blocks.filter(b => this.dirtyBlockIds.has(b.id));
    }
    
    /**
     * Mark all blocks as clean (after successful save)
     */
    markClean() {
        this.dirtyBlockIds.clear();
        this._updateDirtyState();
    }
    
    /**
     * Get caret offset within element
     * @param {HTMLElement} element 
     * @returns {number}
     */
    _getCaretOffset(element) {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) return 0;
        
        const range = selection.getRangeAt(0);
        const preCaretRange = range.cloneRange();
        preCaretRange.selectNodeContents(element);
        preCaretRange.setEnd(range.endContainer, range.endOffset);
        
        return preCaretRange.toString().length;
    }
    
    /**
     * Set caret position within element
     * @param {HTMLElement} element 
     * @param {number} offset 
     */
    _setCaretPosition(element, offset) {
        const range = document.createRange();
        const selection = window.getSelection();
        
        // Find the text node and offset
        let currentOffset = 0;
        const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null);
        
        let node = walker.nextNode();
        while (node) {
            const nodeLength = node.textContent.length;
            if (currentOffset + nodeLength >= offset) {
                range.setStart(node, offset - currentOffset);
                range.collapse(true);
                break;
            }
            currentOffset += nodeLength;
            node = walker.nextNode();
        }
        
        if (!node) {
            // Offset beyond content, set at end
            range.selectNodeContents(element);
            range.collapse(false);
        }
        
        selection.removeAllRanges();
        selection.addRange(range);
    }
    
    /**
     * Generate a new UUID
     * @returns {string}
     */
    _generateId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    /**
     * Escape HTML special characters
     * @param {string} text 
     * @returns {string}
     */
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Clean up event listeners
     */
    destroy() {
        this.container.removeEventListener('input', this._handleInput);
        this.container.removeEventListener('keydown', this._handleKeydown);
        document.removeEventListener('selectionchange', this._handleSelectionChange);
        this.container.removeEventListener('paste', this._handlePaste);
    }
}

// Export for use in main.js
window.BlockEditor = BlockEditor;
