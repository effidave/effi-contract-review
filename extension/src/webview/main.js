// @ts-check
/// <reference types="vscode-webview" />

// Get VS Code API
// @ts-ignore - acquireVsCodeApi is injected by VS Code
const vscode = acquireVsCodeApi();

let currentData = null;
let allBlocks = []; // Store all blocks from blocks.jsonl
let relationshipsMap = new Map(); // Map of block_id -> relationship data
let notesMap = new Map(); // Map of block_id -> note text
let activeTab = 'outline'; // Track active tab

// Editor components (Sprint 2)
let blockEditor = null;
let toolbar = null;
let shortcutManager = null;
let isEditMode = false; // Toggle between view and edit mode

// Handle messages from extension
window.addEventListener('message', event => {
    const message = event.data;
    
    switch (message.command) {
        case 'updateData':
            currentData = message.data;
            allBlocks = message.data.blocks || [];
            // Build relationships map
            relationshipsMap.clear();
            if (message.data.relationships && message.data.relationships.relationships) {
                message.data.relationships.relationships.forEach(rel => {
                    relationshipsMap.set(rel.block_id, rel);
                });
            }
            // Build notes map
            notesMap.clear();
            if (message.data.notes) {
                Object.entries(message.data.notes).forEach(([id, text]) => {
                    notesMap.set(id, text);
                });
            }
            renderData(message.data);
            break;
        case 'noAnalysis':
            showMessage(message.message);
            break;
        case 'refresh':
            if (currentData) {
                renderData(currentData);
            }
            break;
        case 'saveComplete':
            // Handle save completion from extension
            if (toolbar) {
                toolbar.setSaveStatus('saved', message.message || 'Saved ✓');
            }
            break;
        case 'saveError':
            // Handle save error from extension
            if (toolbar) {
                toolbar.setSaveStatus('error', message.message || 'Save failed');
            }
            break;
    }
});

function setupChatControls() {
    const clearBtn = document.getElementById('clear-selection');
    const sendBtn = document.getElementById('send-to-chat');
    
    if (clearBtn) {
        clearBtn.onclick = () => {
            selectedClauses.clear();
            document.querySelectorAll('.clause-checkbox').forEach(cb => cb.checked = false);
            updateSelectionCount();
        };
    }
    
    if (sendBtn) {
        sendBtn.onclick = () => {
            sendToChat();
        };
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Set up event listeners
    document.getElementById('refresh-btn')?.addEventListener('click', () => {
        vscode.postMessage({ command: 'ready' });
    });
    
    // Notify extension that webview is ready
    vscode.postMessage({ command: 'ready' });
});

function showMessage(message) {
    const loadingEl = document.getElementById('loading');
    const dataViewEl = document.getElementById('data-view');
    
    if (loadingEl) loadingEl.style.display = 'block';
    if (dataViewEl) dataViewEl.style.display = 'none';
    
    if (loadingEl) {
        loadingEl.innerHTML = `<p>${escapeHtml(message)}</p>`;
    }
}

function renderData(data) {
    const loadingEl = document.getElementById('loading');
    const dataViewEl = document.getElementById('data-view');
    
    if (loadingEl) loadingEl.style.display = 'none';
    if (dataViewEl) dataViewEl.style.display = 'block';
    
    // Render document info
    renderDocumentInfo(data);
    
    // Set up tabs
    setupTabs();
    
    // Render both views
    renderOutlineView(data);
    renderFullTextView(data);
    
    // Set up chat controls
    setupChatControls();
    
    // Render schedules
    renderSchedulesPlaceholder(data);
}

function renderDocumentInfo(data) {
    const docInfoEl = document.getElementById('doc-info');
    if (!docInfoEl) return;
    
    const { manifest, index, documentPath } = data;
    
    const html = `
        <div class="info-grid">
            <div class="info-item">
                <span class="label">Document:</span>
                <span class="value">${escapeHtml(getFileName(documentPath))}</span>
            </div>
            <div class="info-item">
                <span class="label">Blocks:</span>
                <span class="value">${index.block_count || 0}</span>
            </div>
            <div class="info-item">
                <span class="label">Sections:</span>
                <span class="value">${index.section_count || 0}</span>
            </div>
            <div class="info-item">
                <span class="label">Attachments:</span>
                <span class="value">${index.attachment_count || 0}</span>
            </div>
            <div class="info-item">
                <span class="label">Analyzed:</span>
                <span class="value">${manifest.timestamp ? new Date(manifest.timestamp).toLocaleString() : 'Unknown'}</span>
            </div>
        </div>
    `;
    
    docInfoEl.innerHTML = html;
}

const selectedClauses = new Set();

function setupTabs() {
    const outlineTab = document.getElementById('outline-tab');
    const fullTextTab = document.getElementById('fulltext-tab');
    const outlineContent = document.getElementById('outline-content');
    const fullTextContent = document.getElementById('fulltext-content');
    
    if (!outlineTab || !fullTextTab) return;
    
    outlineTab.addEventListener('click', () => {
        activeTab = 'outline';
        outlineTab.classList.add('active');
        fullTextTab.classList.remove('active');
        if (outlineContent) outlineContent.style.display = 'block';
        if (fullTextContent) fullTextContent.style.display = 'none';
    });
    
    fullTextTab.addEventListener('click', () => {
        activeTab = 'fulltext';
        fullTextTab.classList.add('active');
        outlineTab.classList.remove('active');
        if (outlineContent) outlineContent.style.display = 'none';
        if (fullTextContent) fullTextContent.style.display = 'block';
    });
}

function handleCheckboxChange(id, checked) {
    // Check if this is a table checkbox
    const checkbox = document.querySelector(`.clause-checkbox[data-id="${id}"][data-table-ids]`);
    
    if (checkbox) {
        const tableIds = checkbox.dataset.tableIds.split(',');
        tableIds.forEach(tid => {
            if (checked) {
                selectedClauses.add(tid);
            } else {
                selectedClauses.delete(tid);
            }
        });
    } else {
        if (checked) {
            selectedClauses.add(id);
            // Auto-check all descendants
            checkAllDescendants(id, true);
        } else {
            selectedClauses.delete(id);
            // Auto-uncheck all descendants
            checkAllDescendants(id, false);
        }
    }
    
    // Sync checkbox state across both views
    document.querySelectorAll(`.clause-checkbox[data-id="${id}"]`).forEach(cb => {
        cb.checked = checked;
    });
    
    updateSelectionCount();
}

function checkAllDescendants(blockId, checked) {
    const rel = relationshipsMap.get(blockId);
    if (!rel || !rel.child_block_ids) return;
    
    // Recursively check/uncheck all children
    rel.child_block_ids.forEach(childId => {
        if (checked) {
            selectedClauses.add(childId);
        } else {
            selectedClauses.delete(childId);
        }
        
        // Update checkboxes in DOM
        document.querySelectorAll(`.clause-checkbox[data-id="${childId}"]`).forEach(cb => {
            cb.checked = checked;
        });
        
        // Recurse to grandchildren
        checkAllDescendants(childId, checked);
    });
}

function renderOutlineView(data) {
    const outlineContent = document.getElementById('outline-content');
    if (!outlineContent) return;
    
    const outline = data.outline || [];
    
    if (outline.length === 0) {
        outlineContent.innerHTML = `
            <div class="placeholder">
                <p>📋 No outline items found</p>
                <p class="hint">Analysis directory: ${escapeHtml(data.analysisDir)}</p>
            </div>
        `;
        return;
    }

    // Render hierarchical outline with checkboxes
    const html = outline.map(item => {
        // Level 0 gets no indent, level 1+ indents to align numbering with level 0 text
        // Checkbox (20px) + gap (8px) + ordinal (50px) = 78px base offset
        const baseOffset = 78;
        const indent = item.level > 0 ? baseOffset + ((item.level - 1) * 20) : 0;
        const typeClass = item.type === 'heading' ? 'outline-heading' : 'outline-clause';
        const isSelected = selectedClauses.has(item.id);
        return `
            <div class="outline-item ${typeClass}" style="padding-left: ${indent}px;" data-id="${item.id}">
                <input type="checkbox" class="clause-checkbox" data-id="${item.id}" ${isSelected ? 'checked' : ''}>
                <span class="ordinal">${item.ordinal}</span>
                <span class="text">${escapeHtml(item.text)}</span>
            </div>
        `;
    }).join('');

    outlineContent.innerHTML = `
        <div class="outline-list">
            ${html}
        </div>
        <div class="outline-count">
            ${outline.length} items
        </div>
    `;

    // Add event listeners
    outlineContent.querySelectorAll('.clause-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            handleCheckboxChange(e.target.dataset.id, e.target.checked);
        });
    });
}

function renderFullTextView(data) {
    const fullTextContent = document.getElementById('fulltext-content');
    if (!fullTextContent) return;
    
    const blocks = allBlocks; // Show ALL blocks
    
    if (blocks.length === 0) {
        fullTextContent.innerHTML = `
            <div class="placeholder">
                <p>📋 No blocks found</p>
            </div>
        `;
        return;
    }

    // Check if we're in edit mode
    if (isEditMode && window.BlockEditor && window.Toolbar && window.ShortcutManager) {
        renderEditableFullTextView(fullTextContent, blocks);
        return;
    }

    // Read-only view (original implementation)
    let html = '';
    let i = 0;
    while (i < blocks.length) {
        const block = blocks[i];
        
        // Check if this is a table cell
        if (block.table) {
            // Collect all consecutive table blocks
            const tableBlocks = [block];
            let j = i + 1;
            while (j < blocks.length && blocks[j].table) {
                tableBlocks.push(blocks[j]);
                j++;
            }
            
            // Render table
            html += renderTable(tableBlocks);
            i = j;
        } else {
            // Render normal block
            html += renderBlock(block);
            i++;
        }
    }

    fullTextContent.innerHTML = `
        <div class="fulltext-controls">
            <button id="edit-toggle" class="edit-toggle-btn" title="Switch to Edit Mode">✏️ Edit Mode</button>
        </div>
        <div class="block-list">
            ${html}
        </div>
        <div class="block-count">
            ${blocks.length} blocks
        </div>
    `;

    // Add edit toggle listener
    document.getElementById('edit-toggle')?.addEventListener('click', toggleEditMode);

    // Add event listeners
    fullTextContent.querySelectorAll('.clause-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            handleCheckboxChange(e.target.dataset.id, e.target.checked);
        });
    });

    // Add event listeners for note boxes
    fullTextContent.querySelectorAll('.note-box').forEach(textarea => {
        textarea.addEventListener('change', (e) => {
            const blockId = e.target.dataset.id;
            const paraIdx = e.target.dataset.paraIdx;
            const text = e.target.value;
            notesMap.set(blockId, text);
            vscode.postMessage({
                command: 'saveNote',
                blockId: blockId,
                paraIdx: paraIdx,
                text: text
            });
        });
    });
}

/**
 * Render the editable full text view using BlockEditor
 */
function renderEditableFullTextView(container, blocks) {
    // Create structure for editable view
    container.innerHTML = `
        <div class="fulltext-controls">
            <button id="edit-toggle" class="edit-toggle-btn active" title="Switch to View Mode">📖 View Mode</button>
        </div>
        <div id="editor-toolbar-container" class="editor-toolbar-container"></div>
        <div id="editor-container" class="editor-container"></div>
        <div class="block-count">
            ${blocks.length} blocks (Edit Mode)
        </div>
    `;
    
    // Add edit toggle listener
    document.getElementById('edit-toggle')?.addEventListener('click', toggleEditMode);
    
    const toolbarContainer = document.getElementById('editor-toolbar-container');
    const editorContainer = document.getElementById('editor-container');
    
    if (!toolbarContainer || !editorContainer) return;
    
    // Initialize BlockEditor
    blockEditor = new window.BlockEditor(editorContainer, blocks, {
        onChange: () => {
            if (toolbar) {
                toolbar.setSaveStatus('unsaved');
            }
        }
    });
    blockEditor.render();
    
    // Initialize Toolbar
    toolbar = new window.Toolbar(toolbarContainer, blockEditor, {
        onSave: saveEdits
    });
    toolbar.render();
    
    // Initialize ShortcutManager
    shortcutManager = new window.ShortcutManager(blockEditor, {
        onSave: saveEdits
    });
    shortcutManager.attach(editorContainer);
}

function renderBlock(block) {
    const listMeta = block.list || {};
    const isSelected = selectedClauses.has(block.id);
    const level = listMeta.level || 0;
    
    // Indentation logic
    // Level 0: 0px
    // Level 1: Aligns with Level 0 text (approx 54px)
    // Level 2+: Add 15px per level for clearer nesting
    let indent = 0;
    if (level > 0) {
        indent = 54 + ((level - 1) * 15);
    }
    
    const ordinal = listMeta.ordinal || '';
    const typeLabel = ''; 
    const noteText = notesMap.get(block.id) || '';
    const paraIdx = block.para_idx !== undefined ? block.para_idx : '';
    
    return `
        <div class="block-wrapper" style="padding-left: ${indent}px;" data-id="${block.id}">
            <input type="checkbox" class="clause-checkbox" data-id="${block.id}" ${isSelected ? 'checked' : ''}>
            <div class="block-item">
                <div class="block-header">
                    <span class="block-ordinal">${escapeHtml(ordinal)}${escapeHtml(typeLabel)}</span>
                    <span class="block-text-inline">${escapeHtml(block.text || '')}</span>
                </div>
            </div>
            <textarea class="note-box" data-id="${block.id}" data-para-idx="${paraIdx}" placeholder="Add notes...">${escapeHtml(noteText)}</textarea>
        </div>
    `;
}

function renderTable(blocks) {
    // Find dimensions
    let maxRow = 0;
    let maxCol = 0;
    blocks.forEach(b => {
        if (b.table.row > maxRow) maxRow = b.table.row;
        if (b.table.col > maxCol) maxCol = b.table.col;
    });
    
    // Create grid
    const grid = Array(maxRow + 1).fill().map(() => Array(maxCol + 1).fill(null));
    blocks.forEach(b => {
        grid[b.table.row][b.table.col] = b;
    });
    
    // Generate table HTML
    let tableHtml = '<table class="block-table">';
    for (let r = 0; r <= maxRow; r++) {
        tableHtml += '<tr>';
        for (let c = 0; c <= maxCol; c++) {
            const cellBlock = grid[r][c];
            tableHtml += `<td>${cellBlock ? escapeHtml(cellBlock.text || '') : ''}</td>`;
        }
        tableHtml += '</tr>';
    }
    tableHtml += '</table>';
    
    // Use the first block's ID for the checkbox, but store all IDs
    const firstBlock = blocks[0];
    const allIds = blocks.map(b => b.id).join(',');
    const isSelected = selectedClauses.has(firstBlock.id);
    
    // Indentation (use first block's level)
    const listMeta = firstBlock.list || {};
    const level = listMeta.level || 0;
    let indent = 0;
    if (level > 0) {
        indent = 54 + ((level - 1) * 15);
    }

    const noteText = notesMap.get(firstBlock.id) || '';
    const paraIdx = firstBlock.para_idx !== undefined ? firstBlock.para_idx : '';
    
    return `
        <div class="block-wrapper" style="padding-left: ${indent}px;" data-id="${firstBlock.id}">
            <input type="checkbox" class="clause-checkbox" data-id="${firstBlock.id}" data-table-ids="${allIds}" ${isSelected ? 'checked' : ''}>
            <div class="block-item">
                ${tableHtml}
            </div>
            <textarea class="note-box" data-id="${firstBlock.id}" data-para-idx="${paraIdx}" placeholder="Add notes...">${escapeHtml(noteText)}</textarea>
        </div>
    `;
}

function updateSelectionCount() {
    const countEl = document.getElementById('selection-count');
    if (countEl) {
        const count = selectedClauses.size;
        countEl.textContent = `${count} clause${count !== 1 ? 's' : ''} selected`;
    }
}

function sendToChat() {
    const query = document.getElementById('chat-query')?.value.trim();
    if (!query) {
        alert('Please enter a question');
        return;
    }
    if (selectedClauses.size === 0) {
        alert('Please select at least one clause');
        return;
    }

    // Map selected block IDs to para_ids
    const selectedParaIds = [];
    selectedClauses.forEach(blockId => {
        const block = allBlocks.find(b => b.id === blockId);
        if (block && block.para_id) {
            selectedParaIds.push(block.para_id);
        }
    });

    if (selectedParaIds.length === 0) {
        alert('Selected clauses do not have paragraph IDs (para_id).');
        return;
    }

    // Send message to extension with para IDs
    vscode.postMessage({
        command: 'sendToChat',
        clauseIds: selectedParaIds,
        query: query
    });
}

/**
 * Save edited blocks to the document
 */
function saveEdits() {
    if (!blockEditor) {
        console.error('No editor instance');
        return;
    }
    
    const dirtyBlocks = blockEditor.getDirtyBlocks();
    
    if (dirtyBlocks.length === 0) {
        if (toolbar) {
            toolbar.setSaveStatus('saved', 'No changes to save');
        }
        return;
    }
    
    if (toolbar) {
        toolbar.setSaveStatus('saving');
    }
    
    // Send dirty blocks to extension for saving
    vscode.postMessage({
        command: 'saveBlocks',
        blocks: dirtyBlocks,
        documentPath: currentData?.documentPath || ''
    });
}

/**
 * Toggle between view mode and edit mode
 */
function toggleEditMode() {
    isEditMode = !isEditMode;
    
    const editToggle = document.getElementById('edit-toggle');
    if (editToggle) {
        editToggle.textContent = isEditMode ? '📖 View Mode' : '✏️ Edit Mode';
        editToggle.classList.toggle('active', isEditMode);
    }
    
    if (currentData) {
        renderFullTextView(currentData);
    }
}

function renderSchedulesPlaceholder(data) {
    const schedulesEl = document.getElementById('schedules');
    if (!schedulesEl) return;
    
    schedulesEl.innerHTML = `
        <div class="placeholder">
            <p>📎 ${data.index.attachment_count || 0} attachments found</p>
        </div>
    `;
}

function getFileName(path) {
    return path.split(/[/\\]/).pop() || path;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
