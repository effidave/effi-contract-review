// @ts-check
/// <reference types="vscode-webview" />

// Get VS Code API
// @ts-ignore - acquireVsCodeApi is injected by VS Code
const vscode = acquireVsCodeApi();

let currentData = null;

// Handle messages from extension
window.addEventListener('message', event => {
    const message = event.data;
    
    switch (message.command) {
        case 'updateData':
            currentData = message.data;
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
    
    // Render outline (will load separately via artifact loader)
    renderOutlinePlaceholder(data);
    
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

function renderOutlinePlaceholder(data) {
    const outlineEl = document.getElementById('outline');
    if (!outlineEl) return;
    
    const outline = data.outline || [];
    
    if (outline.length === 0) {
        outlineEl.innerHTML = `
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

    outlineEl.innerHTML = `
        <div class="outline-list">
            ${html}
        </div>
        <div class="chat-query-box">
            <div class="selection-info">
                <span id="selection-count">0 clauses selected</span>
                <button id="clear-selection" class="secondary-button">Clear</button>
            </div>
            <textarea id="chat-query" placeholder="Ask a question about the selected clauses..."></textarea>
            <button id="send-to-chat" class="primary-button">Send to Chat</button>
        </div>
        <div class="outline-count">
            ${outline.length} items
        </div>
    `;

    // Add event listeners
    document.querySelectorAll('.clause-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            const id = e.target.dataset.id;
            if (e.target.checked) {
                selectedClauses.add(id);
            } else {
                selectedClauses.delete(id);
            }
            updateSelectionCount();
        });
    });

    document.getElementById('clear-selection')?.addEventListener('click', () => {
        selectedClauses.clear();
        document.querySelectorAll('.clause-checkbox').forEach(cb => cb.checked = false);
        updateSelectionCount();
    });

    document.getElementById('send-to-chat')?.addEventListener('click', () => {
        sendToChat();
    });

    updateSelectionCount();
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

    // Send message to extension
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
