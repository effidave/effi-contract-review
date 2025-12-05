// @ts-check
/// <reference types="vscode-webview" />

// Get VS Code API
// @ts-ignore - acquireVsCodeApi is injected by VS Code
const vscode = acquireVsCodeApi();

let currentData = null;
let allBlocks = []; // Store all blocks from blocks.jsonl
let relationshipsMap = new Map(); // Map of block_id -> relationship data
let relationshipDepthCache = new Map();

// Editor components (Sprint 2)
let blockEditor = null;
let toolbar = null;
let shortcutManager = null;
let isEditMode = false; // Toggle between view and edit mode
let pageBreakBeforeSet = new Set();
let pageBreakAfterSet = new Set();
const PAGE_HEIGHT_PX = 1000; // Automatic page break threshold
let paginationRequestId = null;

// Comment panel (Sprint 3)
let commentPanel = null;
let commentsData = []; // Store comments from the document
let commentParaIds = new Set(); // Set of para_ids that have comments

// Track Changes (Sprint 3 Phase 2)
let revisionsData = []; // Store revisions from the document
let revisionCount = 0; // Total revision count

// Handle messages from extension
window.addEventListener('message', event => {
    const message = event.data;

    switch (message.command) {
        case 'updateData':
            currentData = message.data;
            allBlocks = (message.data.blocks || []).map(block => ({ ...block }));
            // Build relationships map
            relationshipsMap.clear();
            relationshipDepthCache.clear();
            if (message.data.relationships && message.data.relationships.relationships) {
                message.data.relationships.relationships.forEach(rel => {
                    relationshipsMap.set(rel.block_id, rel);
                });
            }
            allBlocks.forEach(block => {
                block.hierarchy_depth = getRelationshipDepth(block.id);
            });
            renderData(message.data);
            
            // Sprint 3: Auto-load comments when document data is received
            if (message.data.documentPath) {
                requestComments();
            }
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
        case 'updateComments':
            // Handle comments data from extension
            commentsData = message.comments || [];
            
            // Build set of para_ids that have comments
            commentParaIds = new Set();
            commentsData.forEach(comment => {
                if (comment.para_id) {
                    commentParaIds.add(comment.para_id);
                }
            });
            
            // Update comment panel
            if (commentPanel) {
                commentPanel.setComments(commentsData);
            }
            
            // Update inline comment indicators in editor
            updateCommentIndicators();
            break;
        case 'commentResolved':
            // Handle comment resolved confirmation
            if (commentPanel) {
                commentPanel.updateCommentStatus(message.commentId, 'resolved');
            }
            break;
        case 'commentUnresolved':
            // Handle comment unresolved confirmation
            if (commentPanel) {
                commentPanel.updateCommentStatus(message.commentId, 'active');
            }
            break;
        case 'commentError':
            // Handle comment operation error
            console.error('Comment operation failed:', message.error);
            showErrorToast(message.error || 'Comment operation failed');
            break;
        
        // Sprint 3 Phase 2: Track Changes (Revisions)
        case 'updateRevisions':
            // Handle revisions data from extension
            revisionsData = message.revisions || [];
            revisionCount = message.totalRevisions || 0;
            
            // Update revision count in UI
            updateRevisionCountDisplay();
            
            // TODO: When blocks are re-analyzed, inject revision info into runs
            console.log(`Received ${revisionCount} revisions`);
            break;
        case 'revisionAccepted':
            console.log('Revision accepted:', message.revisionId);
            break;
        case 'revisionRejected':
            console.log('Revision rejected:', message.revisionId);
            break;
        case 'allRevisionsAccepted':
            console.log(`All ${message.acceptedCount} revisions accepted`);
            break;
        case 'allRevisionsRejected':
            console.log(`All ${message.rejectedCount} revisions rejected`);
            break;
        case 'revisionError':
            console.error('Revision operation failed:', message.error);
            showErrorToast(message.error || 'Revision operation failed');
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
    
    // Set up toggle comments button
    document.getElementById('toggle-comments-btn')?.addEventListener('click', () => {
        toggleCommentsPanel();
    });
    
    // Initialize comment panel
    initializeCommentPanel();
    
    // Notify extension that webview is ready
    vscode.postMessage({ command: 'ready' });
});

/**
 * Toggle visibility of the comments panel
 */
function toggleCommentsPanel() {
    const container = document.getElementById('comment-panel-container');
    const toggleBtn = document.getElementById('toggle-comments-btn');
    
    if (!container) return;
    
    const isVisible = container.style.display !== 'none';
    container.style.display = isVisible ? 'none' : 'block';
    
    // Update button appearance
    if (toggleBtn) {
        toggleBtn.classList.toggle('active', !isVisible);
    }
    
    // Request comments if showing and not yet loaded
    if (!isVisible && commentsData.length === 0) {
        requestComments();
    }
}

function showMessage(message) {
    const loadingEl = document.getElementById('loading');
    const dataViewEl = document.getElementById('data-view');
    
    if (loadingEl) loadingEl.style.display = 'block';
    if (dataViewEl) dataViewEl.style.display = 'none';
    
    if (loadingEl) {
        loadingEl.innerHTML = `<p>${escapeHtml(message)}</p>`;
    }
}

/**
 * Show an error toast notification to the user.
 * The toast auto-dismisses after 5 seconds or can be clicked to dismiss.
 */
function showErrorToast(message) {
    // Remove any existing toast
    const existingToast = document.querySelector('.error-toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'error-toast';
    toast.innerHTML = `
        <span class="error-toast-icon">⚠️</span>
        <span class="error-toast-message">${escapeHtml(message)}</span>
        <button class="error-toast-close" title="Dismiss">×</button>
    `;
    
    // Add click handlers
    toast.querySelector('.error-toast-close').onclick = () => toast.remove();
    toast.onclick = (e) => {
        if (e.target.className !== 'error-toast-close') {
            toast.remove();
        }
    };
    
    // Add to document
    document.body.appendChild(toast);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.add('error-toast-fade-out');
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

function renderData(data) {
    const loadingEl = document.getElementById('loading');
    const dataViewEl = document.getElementById('data-view');

    if (loadingEl) loadingEl.style.display = 'none';
    if (dataViewEl) dataViewEl.style.display = 'block';

    // Set document title in header
    const titleEl = document.getElementById('document-title');
    if (titleEl && data.documentPath) {
        titleEl.textContent = getFileName(data.documentPath).replace('.docx', '');
    }

    // Render document view
    renderFullTextView(data);

    // Set up chat controls
    setupChatControls();
}


const selectedClauses = new Set();


function getRelationshipDepth(blockId) {
    if (!blockId) {
        return 0;
    }
    if (relationshipDepthCache.has(blockId)) {
        return relationshipDepthCache.get(blockId);
    }

    const visited = new Set();

    function resolve(id) {
        if (!id) {
            return 0;
        }
        if (relationshipDepthCache.has(id)) {
            return relationshipDepthCache.get(id);
        }
        if (visited.has(id)) {
            relationshipDepthCache.set(id, 0);
            return 0;
        }

        visited.add(id);
        const rel = relationshipsMap.get(id);
        if (!rel || !rel.parent_block_id) {
            relationshipDepthCache.set(id, 0);
            visited.delete(id);
            return 0;
        }

        const depth = resolve(rel.parent_block_id) + 1;
        relationshipDepthCache.set(id, depth);
        visited.delete(id);
        return depth;
    }

    return resolve(blockId);
}

function getBlockDepth(block) {
    if (!block) {
        return 0;
    }
    if (typeof block.hierarchy_depth === 'number') {
        return block.hierarchy_depth;
    }
    const depth = getRelationshipDepth(block.id);
    if (typeof depth === 'number') {
        block.hierarchy_depth = depth;
        return depth;
    }
    return 0;
}

/**
 * Get the visual indent depth for a block.
 * For blocks within an attachment (but not the anchor itself), reduce by 1 level
 * so that level-0 clauses within a Schedule are not indented.
 */
function getVisualDepth(block) {
    let depth = getBlockDepth(block);
    // For blocks within an attachment (but not the anchor itself), reduce indent by 1 level
    if (block.attachment_id && !block.attachment && depth > 0) {
        depth = depth - 1;
    }
    return depth;
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


function renderFullTextView(data) {
    const fullTextContent = document.getElementById('fulltext-content');
    const mainToolbar = document.getElementById('main-toolbar');
    if (!fullTextContent) return;

    if (shortcutManager) {
        shortcutManager.detach();
        shortcutManager = null;
    }

    const blocks = allBlocks;

    if (blocks.length === 0) {
        fullTextContent.innerHTML = `
            <div class="document-page">
                <div class="placeholder">
                    <p>No blocks found</p>
                </div>
            </div>
        `;
        return;
    }

    // Always render the main toolbar with mode toggle
    renderMainToolbar(mainToolbar);

    // Prepare page break metadata sets
    pageBreakBeforeSet = new Set();
    pageBreakAfterSet = new Set();
    blocks.forEach((block, index) => {
        if (block.page_break_before) {
            pageBreakBeforeSet.add(index);
        }
        if (block.page_break_after) {
            pageBreakAfterSet.add(index);
            if (index + 1 < blocks.length) {
                pageBreakBeforeSet.add(index + 1);
            }
        }
    });

    // Always use BlockEditor - toggle readOnly based on mode
    if (window.BlockEditor) {
        renderEditorPages(fullTextContent, blocks, !isEditMode);
    } else {
        // Fallback if BlockEditor not loaded
        const fallbackPages = buildFallbackPages(blocks, pageBreakBeforeSet, pageBreakAfterSet);
        renderViewPages(fullTextContent, fallbackPages);
    }
}

/**
 * Render the main toolbar with formatting tools and mode toggle
 */
function renderMainToolbar(mainToolbar) {
    if (!mainToolbar) return;
    
    mainToolbar.style.display = 'flex';
    mainToolbar.innerHTML = `
        <div id="editor-toolbar-container" class="editor-toolbar"></div>
        <div class="mode-toggle">
            <button class="mode-toggle-btn ${!isEditMode ? 'active' : ''}" data-mode="view" title="View Mode">
                📖 View
            </button>
            <button class="mode-toggle-btn ${isEditMode ? 'active' : ''}" data-mode="edit" title="Edit Mode">
                ✏️ Edit
            </button>
        </div>
    `;
    
    // Set up mode toggle listeners
    mainToolbar.querySelectorAll('.mode-toggle-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const newMode = e.target.dataset.mode === 'edit';
            if (newMode !== isEditMode) {
                isEditMode = newMode;
                // Toggle readOnly on existing editor instead of re-rendering
                if (blockEditor) {
                    blockEditor.setReadOnly(!isEditMode);
                    updateToolbarState(!isEditMode);
                    updateModeToggleButtons(mainToolbar);
                    schedulePagination();
                }
            }
        });
    });
}

/**
 * Update mode toggle button states
 */
function updateModeToggleButtons(mainToolbar) {
    mainToolbar.querySelectorAll('.mode-toggle-btn').forEach(btn => {
        const btnMode = btn.dataset.mode === 'edit';
        btn.classList.toggle('active', btnMode === isEditMode);
    });
}

/**
 * Update toolbar button states based on readOnly mode
 */
function updateToolbarState(readOnly) {
    const toolbarContainer = document.getElementById('editor-toolbar-container');
    if (!toolbarContainer) return;
    
    const buttons = toolbarContainer.querySelectorAll('.toolbar-btn');
    buttons.forEach(btn => {
        btn.disabled = readOnly;
    });
}

/**
 * Render read-only view pages (fallback if BlockEditor not loaded)
 */
function renderViewPages(container, pages) {
    let pagesHtml = pages.map((pageBlocks, pageIndex) => {
        let pageContent = '';
        let i = 0;
        while (i < pageBlocks.length) {
            const block = pageBlocks[i];
            if (block.table) {
                const tableBlocks = [block];
                let j = i + 1;
                while (j < pageBlocks.length && pageBlocks[j].table) {
                    tableBlocks.push(pageBlocks[j]);
                    j++;
                }
                pageContent += renderTable(tableBlocks);
                i = j;
            } else {
                pageContent += renderBlock(block);
                i++;
            }
        }
        return `
            <div class="document-page">
                <div class="block-list">${pageContent}</div>
                <div class="page-number">${pageIndex + 1}</div>
            </div>
        `;
    }).join('');

    container.innerHTML = pagesHtml;

    // Add event listeners for checkboxes
    container.querySelectorAll('.clause-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            handleCheckboxChange(e.target.dataset.id, e.target.checked);
        });
    });
}

/**
 * Render pages with BlockEditor (used for both view and edit modes)
 * @param {HTMLElement} container 
 * @param {Array} pages 
 * @param {Array} blocks 
 * @param {boolean} readOnly - true for view mode, false for edit mode
 */
function renderEditorPages(container, blocks, readOnly) {
    container.innerHTML = '<div id="editor-pages-host" class="editor-pages-host"></div>';

    const pagesHost = document.getElementById('editor-pages-host');
    if (!pagesHost) return;

    const toolbarContainer = document.getElementById('editor-toolbar-container');

    // Initialize BlockEditor with checkbox support and readOnly option
    blockEditor = new window.BlockEditor(pagesHost, blocks, {
        onChange: () => {
            if (toolbar) {
                toolbar.setSaveStatus('unsaved');
            }
            schedulePagination();
        },
        showCheckboxes: true,
        selectedClauses: selectedClauses,
        onCheckboxChange: handleCheckboxChange,
        readOnly: readOnly
    });
    blockEditor.render();

    // Initialize Toolbar in main toolbar area (always shown, disabled in view mode)
    if (toolbarContainer && window.Toolbar) {
        toolbar = new window.Toolbar(toolbarContainer, blockEditor, {
            onSave: saveEdits
        });
        toolbar.render();
        updateToolbarState(readOnly);
    }

    // Initialize ShortcutManager (only in edit mode)
    if (!readOnly && window.ShortcutManager) {
        shortcutManager = new window.ShortcutManager(blockEditor, {
            onSave: saveEdits
        });
        shortcutManager.attach(pagesHost);
    }

    // Apply pagination after layout to respect explicit and automatic page breaks
    schedulePagination();
}

function schedulePagination() {
    if (!blockEditor || !blockEditor.container) {
        return;
    }
    if (paginationRequestId !== null) {
        cancelAnimationFrame(paginationRequestId);
    }
    paginationRequestId = requestAnimationFrame(() => {
        paginationRequestId = null;
        paginateEditorContent(blockEditor.container, pageBreakBeforeSet, pageBreakAfterSet);
        
        // Sprint 3: Re-add comment indicators after pagination
        updateCommentIndicators();
    });
}

function paginateEditorContent(pagesHost, breakBeforeSet, breakAfterSet) {
    if (!pagesHost) return;

    const blockElements = Array.from(pagesHost.querySelectorAll('.editor-block-wrapper'));
    if (blockElements.length === 0) return;

    const blockHeights = blockElements.map(el => {
        const rect = el.getBoundingClientRect();
        return rect && rect.height ? rect.height : el.offsetHeight || 0;
    });

    // Remove existing content but keep block elements in memory
    blockElements.forEach(el => el.remove());
    pagesHost.innerHTML = '';

    let currentPage = createDocumentPage();
    pagesHost.appendChild(currentPage);
    let currentContent = currentPage.querySelector('.editor-page-content');
    let currentHeight = 0;
    let pendingBreakAfter = false;

    blockElements.forEach((blockEl, index) => {
        const blockHeight = blockHeights[index] || 0;
        const rawStart = blockEl.dataset.blockIndexStart ? parseInt(blockEl.dataset.blockIndexStart, 10) : (blockEl.dataset.blockIndex ? parseInt(blockEl.dataset.blockIndex, 10) : index);
        const startIndex = Number.isNaN(rawStart) ? index : rawStart;
        const rawEnd = blockEl.dataset.blockIndexEnd ? parseInt(blockEl.dataset.blockIndexEnd, 10) : startIndex;
        const endIndex = Number.isNaN(rawEnd) ? startIndex : rawEnd;
        
        // Respect explicit Word page breaks AND use height-based automatic breaks
        const hasBreakBefore = breakBeforeSet.has(startIndex) && currentContent.childElementCount > 0;
        const exceedsHeight = (currentHeight + blockHeight) > PAGE_HEIGHT_PX && currentContent.childElementCount > 0;

        if (hasBreakBefore || exceedsHeight || pendingBreakAfter) {
            currentPage = createDocumentPage();
            pagesHost.appendChild(currentPage);
            currentContent = currentPage.querySelector('.editor-page-content');
            currentHeight = 0;
            pendingBreakAfter = false;
        }

        currentContent.appendChild(blockEl);
        currentHeight += blockHeight;

        if (breakAfterSet.has(endIndex)) {
            pendingBreakAfter = true;
        }
    });

    updatePageNumbers(pagesHost);
}

function createDocumentPage() {
    const page = document.createElement('div');
    page.className = 'document-page';

    const content = document.createElement('div');
    content.className = 'editor-page-content';
    page.appendChild(content);

    const pageNumber = document.createElement('div');
    pageNumber.className = 'page-number';
    page.appendChild(pageNumber);

    return page;
}

function updatePageNumbers(pagesHost) {
    const pages = Array.from(pagesHost.querySelectorAll('.document-page'));
    pages.forEach((pageEl, index) => {
        const numberEl = pageEl.querySelector('.page-number');
        if (numberEl) {
            numberEl.textContent = `${index + 1}`;
        }
    });
}

function buildFallbackPages(blocks, breakBeforeSet, breakAfterSet) {
    const pages = [];
    let currentPage = [];
    let currentHeight = 0;
    const averageBlockHeight = 32; // rough estimate when actual layout isn't available

    blocks.forEach((block, index) => {
        // Respect explicit Word page breaks
        if (breakBeforeSet.has(index) && currentPage.length > 0) {
            pages.push(currentPage);
            currentPage = [];
            currentHeight = 0;
        }

        currentPage.push(block);
        currentHeight += averageBlockHeight;

        if (breakAfterSet.has(index)) {
            pages.push(currentPage);
            currentPage = [];
            currentHeight = 0;
            return;
        }

        // Also use height-based automatic breaks
        if (currentHeight >= PAGE_HEIGHT_PX) {
            pages.push(currentPage);
            currentPage = [];
            currentHeight = 0;
        }
    });

    if (currentPage.length > 0) {
        pages.push(currentPage);
    }

    return pages;
}

function renderBlock(block) {
    const listMeta = block.list || {};
    const isSelected = selectedClauses.has(block.id);
    const depth = getVisualDepth(block);

    // Text indentation based on ancestor depth (for nested relationships)
    let textIndent = depth > 0 ? (depth * 24) : 0;

    const ordinal = listMeta.ordinal || '';

    return `
        <div class="block-row" data-id="${block.id}">
            <input type="checkbox" class="clause-checkbox row-checkbox" data-id="${block.id}" ${isSelected ? 'checked' : ''}>
            <div class="block-content" style="padding-left: ${textIndent}px;">
                <span class="block-ordinal">${escapeHtml(ordinal)}</span>
                <span class="block-text-inline">${escapeHtml(block.text || '')}</span>
            </div>
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
    const depth = getVisualDepth(firstBlock);
    let indent = 0;
    if (depth > 0) {
        indent = 54 + ((depth - 1) * 15);
    }

    return `
        <div class="block-wrapper" style="padding-left: ${indent}px;" data-id="${firstBlock.id}">
            <input type="checkbox" class="clause-checkbox" data-id="${firstBlock.id}" data-table-ids="${allIds}" ${isSelected ? 'checked' : ''}>
            <div class="block-item">
                ${tableHtml}
            </div>
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
    console.log('DEBUG saveEdits: dirtyBlocks count:', dirtyBlocks.length);
    console.log('DEBUG saveEdits: dirtyBlockIds:', Array.from(blockEditor.dirtyBlockIds || []));
    if (dirtyBlocks.length > 0) {
        console.log('DEBUG saveEdits: first dirty block:', JSON.stringify(dirtyBlocks[0]).substring(0, 200));
    }
    
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

function getFileName(path) {
    return path.split(/[/\\]/).pop() || path;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// Comment Panel Functions (Sprint 3)
// ============================================================================

/**
 * Initialize the comment panel
 */
function initializeCommentPanel() {
    const container = document.getElementById('comment-panel-container');
    if (!container || !window.CommentPanel) {
        console.log('CommentPanel not available or container not found');
        return;
    }
    
    // Create the comment panel with event handlers
    commentPanel = new window.CommentPanel(container, {
        onCommentClick: (comment) => {
            console.log('Comment clicked:', comment.id);
        },
        onScrollToBlock: (paraId) => {
            scrollToBlockByParaId(paraId);
        },
        onResolve: (commentId) => {
            resolveComment(commentId);
        },
        onUnresolve: (commentId) => {
            unresolveComment(commentId);
        },
        onHighlightBlock: (paraId) => {
            highlightBlockByParaId(paraId);
        }
    });
    
    // Set initial comments if available
    if (commentsData.length > 0) {
        commentPanel.setComments(commentsData);
    }
}

/**
 * Scroll the document view to a block by its para_id
 */
function scrollToBlockByParaId(paraId) {
    if (!paraId) return;
    
    // Use BlockEditor if available (preferred)
    if (blockEditor && blockEditor.scrollToBlock) {
        if (blockEditor.scrollToBlock(paraId)) {
            return;
        }
    }
    
    // Fallback: Find the block in the document
    const block = allBlocks.find(b => b.para_id === paraId);
    if (!block) {
        console.warn('Block not found for para_id:', paraId);
        return;
    }
    
    // Find the DOM element for this block
    const blockElement = document.querySelector(`[data-para-id="${paraId}"], [data-id="${block.id}"]`);
    if (blockElement) {
        blockElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

/**
 * Highlight a block by its para_id
 */
function highlightBlockByParaId(paraId) {
    // Use BlockEditor if available (preferred)
    if (blockEditor && blockEditor.highlightBlock) {
        blockEditor.highlightBlock(paraId);
        return;
    }
    
    // Fallback: Remove existing highlights
    document.querySelectorAll('.comment-highlight').forEach(el => {
        el.classList.remove('comment-highlight');
    });
    
    if (!paraId) return;
    
    // Find the block in the document
    const block = allBlocks.find(b => b.para_id === paraId);
    if (!block) return;
    
    // Find and highlight the DOM element
    const blockElement = document.querySelector(`[data-para-id="${paraId}"], [data-id="${block.id}"]`);
    if (blockElement) {
        blockElement.classList.add('comment-highlight');
    }
}

/**
 * Send resolve comment request to extension
 * @param {string} paraId - The w14:paraId of the comment's internal paragraph
 */
function resolveComment(paraId) {
    console.log('Resolving comment:', paraId, 'Document:', currentData?.documentPath);
    vscode.postMessage({
        command: 'resolveComment',
        paraId: paraId,
        documentPath: currentData?.documentPath || ''
    });
}

/**
 * Send unresolve comment request to extension
 * @param {string} paraId - The w14:paraId of the comment's internal paragraph
 */
function unresolveComment(paraId) {
    console.log('Unresolving comment:', paraId, 'Document:', currentData?.documentPath);
    vscode.postMessage({
        command: 'unresolveComment',
        paraId: paraId,
        documentPath: currentData?.documentPath || ''
    });
}

/**
 * Request comments from extension
 */
function requestComments() {
    vscode.postMessage({
        command: 'getComments',
        documentPath: currentData?.documentPath || ''
    });
}

/**
 * Update inline comment indicators in the editor
 * Previously showed a 💬 icon next to blocks - now disabled
 * The Comments button in the toolbar provides access to comments
 */
function updateCommentIndicators() {
    // Remove any existing indicators
    document.querySelectorAll('.comment-indicator').forEach(el => el.remove());
    
    // Comment indicators disabled - use the Comments toggle button instead
}

/**
 * Update the revision count display in the UI
 */
function updateRevisionCountDisplay() {
    const countEl = document.getElementById('revision-count');
    if (countEl) {
        countEl.textContent = revisionCount.toString();
        countEl.classList.toggle('has-revisions', revisionCount > 0);
    }
}

/**
 * Request revisions from the extension
 */
function requestRevisions() {
    if (currentData && currentData.documentPath) {
        vscode.postMessage({
            command: 'getRevisions',
            documentPath: currentData.documentPath
        });
    }
}

/**
 * Accept all revisions in the document
 */
function acceptAllRevisions() {
    if (currentData && currentData.documentPath) {
        vscode.postMessage({
            command: 'acceptAllRevisions',
            documentPath: currentData.documentPath
        });
    }
}

/**
 * Reject all revisions in the document
 */
function rejectAllRevisions() {
    if (currentData && currentData.documentPath) {
        vscode.postMessage({
            command: 'rejectAllRevisions',
            documentPath: currentData.documentPath
        });
    }
}
