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
        
        for (let index = 0; index < this.blocks.length; ) {
            const block = this.blocks[index];
            if (block.table && block.table.table_id) {
                const { element, count } = this._renderTableGroup(block.table.table_id, index);
                editorContent.appendChild(element);
                index += count;
            } else {
                const blockEl = this._renderBlock(block, index);
                editorContent.appendChild(blockEl);
                index += 1;
            }
        }
        
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
        wrapper.dataset.blockIndexStart = String(index);
        wrapper.dataset.blockIndexEnd = String(index);
        
        // Add para_id for comment linkage (Sprint 3)
        if (block.para_id) {
            wrapper.dataset.paraId = block.para_id;
        }

        // Text indentation based on hierarchy depth (no checkbox indent)
        const listMeta = block.list || {};
        const depth = typeof block.hierarchy_depth === 'number' ? block.hierarchy_depth : 0;
        const textIndent = depth > 0 ? (depth * 45) : 0;

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
     * Render a contiguous group of table cell blocks as a single table wrapper
     * @param {string} tableId
     * @param {number} startIndex
     * @returns {{ element: HTMLElement, count: number }}
     */
    _renderTableGroup(tableId, startIndex) {
        const tableBlocks = [];
        let index = startIndex;
        while (index < this.blocks.length) {
            const candidate = this.blocks[index];
            if (!candidate.table || candidate.table.table_id !== tableId) {
                break;
            }
            tableBlocks.push({ block: candidate, index });
            index += 1;
        }

        const firstBlock = tableBlocks[0].block;
        const wrapper = document.createElement('div');
        wrapper.className = 'editor-block-wrapper editor-table-wrapper';
        wrapper.dataset.tableId = tableId;
        wrapper.dataset.blockId = firstBlock.id;
        wrapper.dataset.blockIndex = String(startIndex);
        wrapper.dataset.blockIndexStart = String(startIndex);
        wrapper.dataset.blockIndexEnd = String(startIndex + tableBlocks.length - 1);
        
        // Add para_id for comment linkage (Sprint 3)
        if (firstBlock.para_id) {
            wrapper.dataset.paraId = firstBlock.para_id;
        }

        if (this.options.showCheckboxes) {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'clause-checkbox editor-checkbox';
            checkbox.dataset.id = firstBlock.id;
            checkbox.dataset.tableIds = tableBlocks.map(tb => tb.block.id).join(',');
            checkbox.checked = this.options.selectedClauses.has(firstBlock.id);
            checkbox.addEventListener('change', (e) => {
                this.options.onCheckboxChange(firstBlock.id, e.target.checked);
            });
            wrapper.appendChild(checkbox);
        }

        const depth = typeof firstBlock.hierarchy_depth === 'number' ? firstBlock.hierarchy_depth : 0;
        const indent = depth > 0 ? (depth * 45) : 0;

        const contentEl = document.createElement('div');
        contentEl.className = 'editor-table-container';
        contentEl.style.paddingLeft = `${indent}px`;

        const tableEl = document.createElement('table');
        tableEl.className = 'block-table';

        const toNumber = (value) => {
            if (typeof value === 'number') {
                return value;
            }
            if (typeof value === 'string' && value.trim() !== '') {
                const parsed = parseInt(value, 10);
                if (Number.isFinite(parsed)) {
                    return parsed;
                }
            }
            return Number.NaN;
        };

        const spanValue = (raw) => {
            const parsed = toNumber(raw);
            if (!Number.isNaN(parsed) && parsed > 0) {
                return parsed;
            }
            return 1;
        };

        const rowNextCol = new Map();
        const normalizedCells = tableBlocks.map(tb => {
            const { block } = tb;
            const tableInfo = block.table || {};
            const rawRow = toNumber(tableInfo.row);
            const row = !Number.isNaN(rawRow) ? rawRow : (rowNextCol.size > 0 ? Math.max(...rowNextCol.keys()) : 0);
            const rawCol = toNumber(tableInfo.col);
            const hasExplicitCol = !Number.isNaN(rawCol);
            const rowSpan = spanValue(tableInfo.row_span);
            const colSpan = spanValue(tableInfo.col_span);

            const nextCol = rowNextCol.get(row) ?? 0;
            let col = nextCol;
            if (hasExplicitCol) {
                col = rawCol;
                if (col + colSpan > nextCol) {
                    rowNextCol.set(row, col + colSpan);
                }
            } else {
                rowNextCol.set(row, nextCol + colSpan);
            }

            return {
                block,
                index: tb.index,
                row,
                col,
                rowSpan,
                colSpan
            };
        });

        const sortedCells = normalizedCells.slice().sort((a, b) => {
            if (a.row !== b.row) {
                return a.row - b.row;
            }
            return a.col - b.col;
        });

        const maxRow = Math.max(...sortedCells.map(cell => cell.row + cell.rowSpan), 1);
        const maxCol = Math.max(...sortedCells.map(cell => cell.col + cell.colSpan), 1);
        const rowCount = Math.max(Math.ceil(maxRow), 1);
        const colCount = Math.max(Math.ceil(maxCol), 1);

        const cellMap = new Map();
        sortedCells.forEach(cell => {
            cellMap.set(`${cell.row}:${cell.col}`, cell);
        });

        const spanTracker = Array.from({ length: rowCount }, () => Array(colCount).fill(false));

        for (let row = 0; row < rowCount; row++) {
            const rowEl = document.createElement('tr');
            for (let col = 0; col < colCount; col++) {
                if (spanTracker[row][col]) {
                    continue;
                }

                const key = `${row}:${col}`;
                const cellData = cellMap.get(key);
                const td = document.createElement('td');

                if (cellData) {
                    const { block, rowSpan, colSpan } = cellData;
                    if (rowSpan > 1) {
                        td.rowSpan = rowSpan;
                    }
                    if (colSpan > 1) {
                        td.colSpan = colSpan;
                    }

                    const cellEl = this._renderTableCell(block, cellData.index);
                    cellEl.dataset.row = String(cellData.row);
                    cellEl.dataset.col = String(cellData.col);
                    cellEl.dataset.rowSpan = String(rowSpan);
                    cellEl.dataset.colSpan = String(colSpan);
                    td.appendChild(cellEl);

                    for (let r = row; r < row + rowSpan; r++) {
                        for (let c = col; c < col + colSpan; c++) {
                            if (r < rowCount && c < colCount) {
                                spanTracker[r][c] = true;
                            }
                        }
                    }
                } else {
                    td.className = 'empty-table-cell';
                    td.innerHTML = '&nbsp;';
                    spanTracker[row][col] = true;
                }

                rowEl.appendChild(td);
            }
            tableEl.appendChild(rowEl);
        }

        contentEl.appendChild(tableEl);
        wrapper.appendChild(contentEl);

        return { element: wrapper, count: tableBlocks.length };
    }

    /**
     * Render a single table cell within a table group
     * @param {Block} block
     * @param {number} index
     * @returns {HTMLElement}
     */
    _renderTableCell(block, index) {
        const cellWrapper = document.createElement('div');
        cellWrapper.className = 'editor-table-cell';
        cellWrapper.dataset.blockId = block.id;
        cellWrapper.dataset.blockIndex = String(index);
        cellWrapper.dataset.blockIndexStart = String(index);
        cellWrapper.dataset.blockIndexEnd = String(index);

        const textEl = document.createElement('div');
        textEl.className = 'editor-block-text';
        textEl.dataset.blockId = block.id;
        textEl.contentEditable = this.options.readOnly ? 'false' : 'true';
        textEl.spellcheck = !this.options.readOnly;
        textEl.innerHTML = this._renderFormattedText(block);

        cellWrapper.appendChild(textEl);
        return cellWrapper;
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
                
                // Track changes formatting
                if (run.formats.includes('insert')) {
                    // Build title attribute for hover info
                    const title = this._buildRevisionTitle(run, 'Inserted');
                    escapedText = `<ins class="revision-insert" title="${title}">${escapedText}</ins>`;
                }
                if (run.formats.includes('delete')) {
                    const title = this._buildRevisionTitle(run, 'Deleted');
                    escapedText = `<del class="revision-delete" title="${title}">${escapedText}</del>`;
                }
            }
            
            html += escapedText;
        });
        
        return html || '<br>';
    }

    /**
     * Build title attribute for revision hover tooltip
     * @param {Object} run - The run object with revision info
     * @param {string} action - 'Inserted' or 'Deleted'
     * @returns {string}
     */
    _buildRevisionTitle(run, action) {
        const author = run.author || 'Unknown';
        const date = run.date ? this._formatRevisionDate(run.date) : '';
        return this._escapeHtml(`${action} by ${author}${date ? ' on ' + date : ''}`);
    }

    /**
     * Format revision date for display
     * @param {string} dateStr - ISO date string
     * @returns {string}
     */
    _formatRevisionDate(dateStr) {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString(undefined, { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateStr;
        }
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
        const block = this.blocks[blockIndex];
        if (block && block.table) {
            return;
        }
        
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
            para_idx: -1, // New block, will be assigned on save
            hierarchy_depth: typeof block.hierarchy_depth === 'number' ? block.hierarchy_depth : 0,
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
        if (block.table && block.table.table_id) {
            const tableWrapper = this.container.querySelector(`.editor-table-wrapper[data-table-id="${block.table.table_id}"]`);
            if (!tableWrapper) {
                return;
            }
            const { element } = this._renderTableGroup(block.table.table_id, Number(tableWrapper.dataset.blockIndexStart || 0));
            tableWrapper.replaceWith(element);
            return;
        }

        const textEl = this.container.querySelector(`.editor-block-text[data-block-id="${block.id}"]`);
        const oldWrapper = textEl ? textEl.closest('.editor-block-wrapper') : null;
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
    
    // ========================================================================
    // Sprint 3: Comment Integration Methods
    // ========================================================================
    
    /**
     * Scroll to a block by its para_id
     * @param {string} paraId - The paragraph ID
     * @returns {boolean} - Whether the block was found and scrolled to
     */
    scrollToBlock(paraId) {
        if (!paraId) return false;
        
        const blockEl = this.container.querySelector(`[data-para-id="${paraId}"]`);
        if (blockEl) {
            blockEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return true;
        }
        return false;
    }
    
    /**
     * Highlight a block by its para_id
     * @param {string} paraId - The paragraph ID (null to clear highlights)
     */
    highlightBlock(paraId) {
        // Remove existing highlights
        this.container.querySelectorAll('.comment-highlight').forEach(el => {
            el.classList.remove('comment-highlight');
        });
        
        if (!paraId) return;
        
        const blockEl = this.container.querySelector(`[data-para-id="${paraId}"]`);
        if (blockEl) {
            blockEl.classList.add('comment-highlight');
        }
    }
    
    /**
     * Get all para_ids that have blocks in the document
     * @returns {Set<string>} - Set of para_ids
     */
    getBlockParaIds() {
        const paraIds = new Set();
        this.blocks.forEach(block => {
            if (block.para_id) {
                paraIds.add(block.para_id);
            }
        });
        return paraIds;
    }
    
    /**
     * Check which para_ids from a list exist in the document
     * @param {Array<string>} paraIds - Array of para_ids to check
     * @returns {Set<string>} - Set of para_ids that exist in the document
     */
    getMatchingParaIds(paraIds) {
        const docParaIds = this.getBlockParaIds();
        return new Set(paraIds.filter(id => docParaIds.has(id)));
    }
}

// Export for use in main.js (browser)
if (typeof window !== 'undefined') {
    window.BlockEditor = BlockEditor;
}

// Export for use in Node.js (testing)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { BlockEditor };
}
