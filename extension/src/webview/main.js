// @ts-check
/// <reference types="vscode-webview" />

// Get VS Code API
// @ts-ignore - acquireVsCodeApi is injected by VS Code
const vscode = acquireVsCodeApi();

let currentData = null;
let allBlocks = []; // Store all blocks from blocks.jsonl
let activeTab = 'outline'; // Track active tab

// Handle messages from extension
window.addEventListener('message', event => {
    const message = event.data;
    
    switch (message.command) {
        case 'updateData':
            currentData = message.data;
            allBlocks = message.data.blocks || [];
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
    if (checked) {
        selectedClauses.add(id);
    } else {
        selectedClauses.delete(id);
    }
    
    // Sync checkbox state across both views
    document.querySelectorAll(`.clause-checkbox[data-id="${id}"]`).forEach(cb => {
        cb.checked = checked;
    });
    
    updateSelectionCount();
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
        const indent = (item.level || 0) * 20;
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
    
    const blocks = allBlocks.filter(block => {
        const listMeta = block.list || {};
        return listMeta.ordinal; // Only show blocks with ordinals
    });
    
    if (blocks.length === 0) {
        fullTextContent.innerHTML = `
            <div class="placeholder">
                <p>📋 No blocks found</p>
            </div>
        `;
        return;
    }

    // Render blocks with full text
    const html = blocks.map(block => {
        const listMeta = block.list || {};
        const isSelected = selectedClauses.has(block.id);
        const level = listMeta.level || 0;
        return `
            <div class="block-item" data-id="${block.id}">
                <div class="block-header">
                    <input type="checkbox" class="clause-checkbox" data-id="${block.id}" ${isSelected ? 'checked' : ''}>
                    <span class="block-ordinal">${escapeHtml(listMeta.ordinal || '')}</span>
                    <span class="block-meta">Level ${level}</span>
                </div>
                <div class="block-text">${escapeHtml(block.text || '')}</div>
            </div>
        `;
    }).join('');

    fullTextContent.innerHTML = `
        <div class="block-list">
            ${html}
        </div>
        <div class="block-count">
            ${blocks.length} blocks
        </div>
    `;

    // Add event listeners
    fullTextContent.querySelectorAll('.clause-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            handleCheckboxChange(e.target.dataset.id, e.target.checked);
        });
    });
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

    // Send message to extension with clause IDs
    // The extension will fetch full text from blocks.jsonl
    vscode.postMessage({
        command: 'sendToChat',
        clauseIds: Array.from(selectedClauses),
        query: query
    });
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
