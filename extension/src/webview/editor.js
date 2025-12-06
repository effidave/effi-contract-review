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
 * @property {string} [text] - Text content (for normal/insert runs)
 * @property {string} [deleted_text] - Deleted text content (for delete runs)
 * @property {string[]} formats - Array of format names ('bold', 'italic', 'underline', 'insert', 'delete')
 * @property {string} [author] - Author of revision (for insert/delete runs)
 * @property {string} [date] - Date of revision (for insert/delete runs)
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
     * Supports both text-based runs (new model) and position-based runs (legacy)
     * @param {Block[]} blocks 
     * @returns {Block[]}
     */
    _normalizeBlocks(blocks) {
        return blocks.map(block => ({
            ...block,
            runs: block.runs || [{ text: block.text || '', formats: [] }]
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
        let depth = typeof block.hierarchy_depth === 'number' ? block.hierarchy_depth : 0;
        // For blocks within an attachment (but not the anchor itself), reduce indent by 1 level
        // so that level-0 clauses within a Schedule are not indented
        if (block.attachment_id && !block.attachment && depth > 0) {
            depth = depth - 1;
        }
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

        let depth = typeof firstBlock.hierarchy_depth === 'number' ? firstBlock.hierarchy_depth : 0;
        // For blocks within an attachment (but not the anchor itself), reduce indent by 1 level
        if (firstBlock.attachment_id && !firstBlock.attachment && depth > 0) {
            depth = depth - 1;
        }
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
     * Supports both text-based runs (new model) and position-based runs (legacy)
     * @param {Block} block 
     * @returns {string}
     */
    _renderFormattedText(block) {
        const blockText = block.text || '';
        if (!blockText && !block.runs?.length) return '<br>'; // Empty block needs BR for cursor
        
        const runs = block.runs || [{ text: blockText, formats: [] }];
        
        let html = '';
        runs.forEach(run => {
            // Support both text-based runs (new) and position-based runs (legacy/editor)
            // Delete runs use 'deleted_text', normal/insert runs use 'text'
            // Legacy runs use start/end positions into block.text
            let runText;
            if (run.deleted_text !== undefined) {
                runText = run.deleted_text;
            } else if (run.text !== undefined) {
                runText = run.text;
            } else if (run.start !== undefined && run.end !== undefined) {
                // Legacy position-based runs (from editor operations)
                runText = blockText.substring(run.start, run.end);
            } else {
                runText = '';
            }
            
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
     * Extract runs from contenteditable DOM element
     * Preserves formatting like bold, italic, insert, delete
     * @param {HTMLElement} element - The contenteditable element
     * @param {Array} originalRuns - Original runs for metadata (author, date)
     * @returns {Array} Array of run objects with text and formats
     */
    _extractRunsFromDOM(element, originalRuns = []) {
        const runs = [];
        
        // Build a map of original run text -> metadata for tracking changes
        const originalMetadata = new Map();
        for (const run of originalRuns) {
            const text = run.deleted_text || run.text || '';
            if (text && (run.author || run.date)) {
                originalMetadata.set(text, { author: run.author, date: run.date });
            }
        }
        
        /**
         * Recursively extract runs from a node
         * @param {Node} node 
         * @param {Array} currentFormats - formats inherited from parent
         * @param {Object} metadata - author/date from parent
         */
        const extractNode = (node, currentFormats = [], metadata = {}) => {
            if (node.nodeType === Node.TEXT_NODE) {
                const text = node.textContent;
                if (text) {
                    // Check if original had metadata for this text
                    const origMeta = originalMetadata.get(text) || metadata;
                    const run = { 
                        text, 
                        formats: [...currentFormats]
                    };
                    // For delete runs, use deleted_text
                    if (currentFormats.includes('delete')) {
                        run.deleted_text = text;
                        delete run.text;
                    }
                    // Preserve author/date for track changes
                    if (origMeta.author) run.author = origMeta.author;
                    if (origMeta.date) run.date = origMeta.date;
                    runs.push(run);
                }
                return;
            }
            
            if (node.nodeType !== Node.ELEMENT_NODE) return;
            
            const el = /** @type {HTMLElement} */ (node);
            const tagName = el.tagName.toLowerCase();
            
            // Build formats based on tag
            const newFormats = [...currentFormats];
            const newMetadata = { ...metadata };
            
            if (tagName === 'strong' || tagName === 'b') {
                if (!newFormats.includes('bold')) newFormats.push('bold');
            }
            if (tagName === 'em' || tagName === 'i') {
                if (!newFormats.includes('italic')) newFormats.push('italic');
            }
            if (tagName === 'u') {
                if (!newFormats.includes('underline')) newFormats.push('underline');
            }
            if (tagName === 'ins') {
                if (!newFormats.includes('insert')) newFormats.push('insert');
            }
            if (tagName === 'del') {
                if (!newFormats.includes('delete')) newFormats.push('delete');
            }
            
            // Process children
            for (const child of el.childNodes) {
                extractNode(child, newFormats, newMetadata);
            }
        };
        
        // Process all child nodes
        for (const child of element.childNodes) {
            extractNode(child, [], {});
        }
        
        // Merge adjacent runs with same formats
        return this._mergeAdjacentRuns(runs);
    }
    
    /**
     * Merge adjacent runs with identical formats
     * @param {Array} runs 
     * @returns {Array}
     */
    _mergeAdjacentRuns(runs) {
        if (runs.length === 0) return runs;
        
        const merged = [];
        let current = { ...runs[0] };
        
        for (let i = 1; i < runs.length; i++) {
            const run = runs[i];
            const sameFormats = JSON.stringify(current.formats?.sort() || []) === 
                               JSON.stringify(run.formats?.sort() || []);
            const sameAuthor = current.author === run.author;
            const sameDate = current.date === run.date;
            
            if (sameFormats && sameAuthor && sameDate) {
                // Merge text
                if (current.deleted_text !== undefined) {
                    current.deleted_text += run.deleted_text || run.text || '';
                } else {
                    current.text = (current.text || '') + (run.text || run.deleted_text || '');
                }
            } else {
                merged.push(current);
                current = { ...run };
            }
        }
        merged.push(current);
        
        return merged;
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
        
        // Extract runs from DOM, preserving formatting
        const newRuns = this._extractRunsFromDOM(target, block.runs || []);
        
        // Update block text (combined text from all runs, excluding deleted)
        const newText = newRuns
            .filter(r => !r.formats?.includes('delete'))
            .map(r => r.text || '')
            .join('');
        block.text = newText;
        
        // Update runs with extracted structure
        block.runs = newRuns;
        
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
            // Use full offset (including deleted text) for proper splitting
            this._splitBlock(blockIndex, this._getCaretOffsetFull(target));
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
                    const isDelete = activeFormats.includes('delete');
                    // Only add to visible text if not deleted
                    if (!isDelete) {
                        text += nodeText;
                    }
                    const run = {
                        formats: [...activeFormats]
                    };
                    // Use deleted_text for delete runs, text for others
                    if (isDelete) {
                        run.deleted_text = nodeText;
                    } else {
                        run.text = nodeText;
                    }
                    runs.push(run);
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
                if (el.tagName === 'INS') {
                    if (!newFormats.includes('insert')) newFormats.push('insert');
                }
                if (el.tagName === 'DEL') {
                    if (!newFormats.includes('delete')) newFormats.push('delete');
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
     * Merge adjacent runs with identical formats (text-based model)
     * @param {Run[]} runs 
     * @returns {Run[]}
     */
    _mergeRuns(runs) {
        if (runs.length <= 1) return runs;
        
        const merged = [{ ...runs[0] }];
        for (let i = 1; i < runs.length; i++) {
            const prev = merged[merged.length - 1];
            const curr = runs[i];
            
            if (this._formatsEqual(prev.formats, curr.formats)) {
                // Concatenate text for merged runs (handle deleted_text)
                if (prev.deleted_text !== undefined || curr.deleted_text !== undefined) {
                    prev.deleted_text = (prev.deleted_text || '') + (curr.deleted_text || '');
                } else {
                    prev.text = (prev.text || '') + (curr.text || '');
                }
            } else {
                merged.push({ ...curr });
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
     * @param {number} offset - FULL offset including deleted text
     */
    _splitBlock(blockIndex, offset) {
        this._pushUndoState();
        
        const block = this.blocks[blockIndex];
        
        // Split runs at the offset, preserving formatting
        const { beforeRuns, afterRuns } = this._splitRunsAtOffset(block.runs || [], offset);
        
        // Compute text from runs (excluding deleted)
        const beforeText = this._getTextFromRuns(beforeRuns);
        const afterText = this._getTextFromRuns(afterRuns);
        
        // Create new block with text/runs after cursor
        // Generate Word-compatible para_id so save can insert it properly
        const newBlock = {
            id: this._generateId(),
            type: 'paragraph',
            text: afterText,
            runs: afterRuns.length > 0 ? afterRuns : [{ text: afterText, formats: [] }],
            list: block.list ? { ...block.list } : undefined,
            para_id: this._generateParaId(),  // Word-compatible 8-char hex ID
            para_idx: -1, // Negative indicates new block to insert on save
            hierarchy_depth: typeof block.hierarchy_depth === 'number' ? block.hierarchy_depth : 0,
        };
        
        // Truncate current block
        block.text = beforeText;
        block.runs = beforeRuns.length > 0 ? beforeRuns : [{ text: beforeText, formats: [] }];
        
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
     * Split runs at a given text offset, preserving formatting
     * @param {Array} runs - Original runs array
     * @param {number} offset - Character offset to split at (FULL offset including deleted text)
     * @returns {{ beforeRuns: Array, afterRuns: Array }}
     */
    _splitRunsAtOffset(runs, offset) {
        const beforeRuns = [];
        const afterRuns = [];
        let currentOffset = 0;
        let splitDone = false;
        
        for (const run of runs) {
            const isDelete = run.formats?.includes('delete');
            const runText = isDelete ? (run.deleted_text || '') : (run.text || '');
            const runLength = runText.length; // Count ALL text including deleted
            
            if (splitDone) {
                // Already past split point, add to after
                afterRuns.push(this._cloneRun(run));
            } else if (currentOffset + runLength <= offset) {
                // Entire run is before split point
                beforeRuns.push(this._cloneRun(run));
                currentOffset += runLength;
            } else if (currentOffset >= offset) {
                // Entire run is after split point
                afterRuns.push(this._cloneRun(run));
                splitDone = true;
            } else {
                // Split point is within this run
                const splitIndex = offset - currentOffset;
                
                // Before part
                if (splitIndex > 0) {
                    const beforeRun = this._cloneRun(run);
                    if (isDelete) {
                        beforeRun.deleted_text = runText.substring(0, splitIndex);
                    } else {
                        beforeRun.text = runText.substring(0, splitIndex);
                    }
                    beforeRuns.push(beforeRun);
                }
                
                // After part
                if (splitIndex < runText.length) {
                    const afterRun = this._cloneRun(run);
                    if (isDelete) {
                        afterRun.deleted_text = runText.substring(splitIndex);
                    } else {
                        afterRun.text = runText.substring(splitIndex);
                    }
                    afterRuns.push(afterRun);
                }
                
                currentOffset += runLength;
                splitDone = true;
            }
        }
        
        return { beforeRuns, afterRuns };
    }
    
    /**
     * Get visible text from runs (excluding deleted text)
     * @param {Array} runs 
     * @returns {string}
     */
    _getTextFromRuns(runs) {
        return runs
            .filter(r => !r.formats?.includes('delete'))
            .map(r => r.text || '')
            .join('');
    }
    
    /**
     * Clone a run object, preserving all properties
     * @param {Object} run 
     * @returns {Object}
     */
    _cloneRun(run) {
        const cloned = {
            formats: [...(run.formats || [])]
        };
        if (run.text !== undefined) cloned.text = run.text;
        if (run.deleted_text !== undefined) cloned.deleted_text = run.deleted_text;
        if (run.author !== undefined) cloned.author = run.author;
        if (run.date !== undefined) cloned.date = run.date;
        return cloned;
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
        
        // Get cursor position using full offset (including deleted text) for accurate positioning
        const prevRuns = prevBlock.runs || [{ text: prevBlock.text || '', formats: [] }];
        const currRuns = currBlock.runs || [{ text: currBlock.text || '', formats: [] }];
        
        // Calculate merge point offset (full offset including deleted text)
        const prevFullLength = prevRuns.reduce((sum, r) => {
            const text = r.deleted_text || r.text || '';
            return sum + text.length;
        }, 0);
        
        // Concatenate runs from both blocks
        prevBlock.runs = [...prevRuns, ...currRuns];
        
        // Update text (visible text only, excluding deleted)
        prevBlock.text = this._getTextFromRuns(prevBlock.runs);
        
        // Remove current block
        this.blocks.splice(blockIndex, 1);
        
        // Remove from DOM
        const currEl = this.container.querySelector(`[data-block-id="${currBlock.id}"]`).parentElement;
        currEl.remove();
        
        // Re-render previous block
        this._reRenderBlock(blockIndex - 1);
        
        // Update indices
        this._updateBlockIndices();
        
        // Set cursor at merge point (using visible offset for caret positioning)
        const prevLength = this._getTextFromRuns(prevRuns).length;
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
        
        const currRuns = currBlock.runs || [{ text: currBlock.text || '', formats: [] }];
        const nextRuns = nextBlock.runs || [{ text: nextBlock.text || '', formats: [] }];
        
        // Remember cursor position (visible text length)
        const currLength = this._getTextFromRuns(currRuns).length;
        
        // Concatenate runs from both blocks
        currBlock.runs = [...currRuns, ...nextRuns];
        
        // Update text (visible text only, excluding deleted)
        currBlock.text = this._getTextFromRuns(currBlock.runs);
        
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
     * Get caret offset within element (excluding deleted text)
     * @param {HTMLElement} element 
     * @returns {number}
     */
    _getCaretOffset(element) {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) return 0;
        
        const range = selection.getRangeAt(0);
        
        // Walk through text nodes, counting only non-deleted text
        let offset = 0;
        const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null);
        
        let node = walker.nextNode();
        while (node) {
            // Check if this text node is inside a <del> element
            const isDeleted = this._isInsideDeletedElement(node);
            
            if (node === range.endContainer) {
                // Caret is in this node
                if (!isDeleted) {
                    offset += range.endOffset;
                }
                break;
            } else if (range.endContainer.contains && range.endContainer.contains(node)) {
                // range.endContainer is an element containing this text node
                if (!isDeleted) {
                    offset += node.textContent.length;
                }
            } else if (this._nodeIsBeforeCaret(node, range)) {
                // This node is before the caret
                if (!isDeleted) {
                    offset += node.textContent.length;
                }
            }
            
            node = walker.nextNode();
        }
        
        return offset;
    }
    
    /**
     * Check if a node is inside a <del> element
     * @param {Node} node 
     * @returns {boolean}
     */
    _isInsideDeletedElement(node) {
        let parent = node.parentElement;
        while (parent) {
            if (parent.tagName === 'DEL') return true;
            if (parent.classList?.contains('editor-block-text')) break;
            parent = parent.parentElement;
        }
        return false;
    }
    
    /**
     * Check if a node is before the caret position
     * @param {Node} node 
     * @param {Range} range 
     * @returns {boolean}
     */
    _nodeIsBeforeCaret(node, range) {
        const nodeRange = document.createRange();
        nodeRange.selectNode(node);
        return nodeRange.compareBoundaryPoints(Range.END_TO_START, range) < 0;
    }
    
    /**
     * Get caret offset including ALL text (including deleted)
     * Used for splitting blocks where we need to preserve deleted text position
     * @param {HTMLElement} element 
     * @returns {number}
     */
    _getCaretOffsetFull(element) {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) return 0;
        
        const range = selection.getRangeAt(0);
        const preCaretRange = range.cloneRange();
        preCaretRange.selectNodeContents(element);
        preCaretRange.setEnd(range.endContainer, range.endOffset);
        
        return preCaretRange.toString().length;
    }
    
    /**
     * Set caret position within element (offset excludes deleted text)
     * @param {HTMLElement} element 
     * @param {number} offset 
     */
    _setCaretPosition(element, offset) {
        const range = document.createRange();
        const selection = window.getSelection();
        
        // Find the text node and offset (skipping deleted text)
        let currentOffset = 0;
        const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null);
        
        let node = walker.nextNode();
        while (node) {
            // Skip text inside <del> elements
            if (this._isInsideDeletedElement(node)) {
                node = walker.nextNode();
                continue;
            }
            
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
     * Generate a Word-compatible w14:paraId (8-char uppercase hex)
     * Checks for collisions against existing blocks' para_id values.
     * @param {number} maxAttempts - Maximum collision avoidance attempts
     * @returns {string} - 8-character uppercase hex string
     */
    _generateParaId(maxAttempts = 100) {
        // Collect existing para_ids for collision checking
        const existingIds = new Set();
        for (const block of this.blocks) {
            if (block.para_id) {
                existingIds.add(block.para_id.toUpperCase());
            }
        }
        
        for (let i = 0; i < maxAttempts; i++) {
            // Generate 8 random hex characters (4 bytes)
            const bytes = new Uint8Array(4);
            crypto.getRandomValues(bytes);
            const paraId = Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('').toUpperCase();
            
            if (!existingIds.has(paraId)) {
                return paraId;
            }
        }
        
        // Fallback: timestamp-based ID (should never happen in practice)
        const fallback = Date.now().toString(16).slice(-8).toUpperCase().padStart(8, '0');
        return fallback;
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
