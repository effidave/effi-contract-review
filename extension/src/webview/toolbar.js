/**
 * Toolbar - Editor toolbar component
 * 
 * Provides formatting buttons, undo/redo, and save functionality
 */

// @ts-check

class Toolbar {
    /**
     * @param {HTMLElement} container - Container element for toolbar
     * @param {BlockEditor} editor - The editor instance
     * @param {Object} options - Toolbar options
     */
    constructor(container, editor, options = {}) {
        this.container = container;
        this.editor = editor;
        this.options = {
            onSave: options.onSave || (() => {}),
            ...options
        };
        
        this.saveStatus = 'saved'; // 'saved', 'unsaved', 'saving'
    }
    
    /**
     * Render the toolbar
     */
    render() {
        this.container.innerHTML = `
            <div class="editor-toolbar">
                <div class="toolbar-group format-group">
                    <button class="toolbar-btn" id="bold-btn" title="Bold (Ctrl+B)" data-format="bold">
                        <strong>B</strong>
                    </button>
                    <button class="toolbar-btn" id="italic-btn" title="Italic (Ctrl+I)" data-format="italic">
                        <em>I</em>
                    </button>
                    <button class="toolbar-btn" id="underline-btn" title="Underline (Ctrl+U)" data-format="underline">
                        <u>U</u>
                    </button>
                </div>
                <div class="toolbar-separator"></div>
                <div class="toolbar-group history-group">
                    <button class="toolbar-btn" id="undo-btn" title="Undo (Ctrl+Z)">
                        ↶
                    </button>
                    <button class="toolbar-btn" id="redo-btn" title="Redo (Ctrl+Y)">
                        ↷
                    </button>
                </div>
                <div class="toolbar-separator"></div>
                <div class="toolbar-group save-group">
                    <button class="toolbar-btn save-btn" id="save-btn" title="Save (Ctrl+S)">
                        💾 Save
                    </button>
                    <span class="save-status" id="save-status">Saved ✓</span>
                </div>
            </div>
        `;
        
        this._setupEventListeners();
    }
    
    /**
     * Set up button event listeners
     */
    _setupEventListeners() {
        // Format buttons
        ['bold', 'italic', 'underline'].forEach(format => {
            const btn = this.container.querySelector(`[data-format="${format}"]`);
            if (btn) {
                btn.addEventListener('click', () => {
                    this.editor.applyFormat(format);
                    this._updateFormatButtons();
                });
            }
        });
        
        // Undo/Redo
        const undoBtn = this.container.querySelector('#undo-btn');
        const redoBtn = this.container.querySelector('#redo-btn');
        
        if (undoBtn) {
            undoBtn.addEventListener('click', () => this.editor.undo());
        }
        if (redoBtn) {
            redoBtn.addEventListener('click', () => this.editor.redo());
        }
        
        // Save
        const saveBtn = this.container.querySelector('#save-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.options.onSave());
        }
    }
    
    /**
     * Update format button states based on current selection
     */
    _updateFormatButtons() {
        // TODO: Check selection and highlight active formats
    }
    
    /**
     * Update save status display
     * @param {'saved' | 'unsaved' | 'saving' | 'error'} status 
     * @param {string} [message] - Optional message
     */
    setSaveStatus(status, message) {
        this.saveStatus = status;
        const statusEl = this.container.querySelector('#save-status');
        const saveBtn = this.container.querySelector('#save-btn');
        
        if (!statusEl) return;
        
        switch (status) {
            case 'saved':
                statusEl.textContent = message || 'Saved ✓';
                statusEl.className = 'save-status status-saved';
                if (saveBtn) saveBtn.disabled = false;
                break;
            case 'unsaved':
                statusEl.textContent = message || 'Unsaved changes';
                statusEl.className = 'save-status status-unsaved';
                if (saveBtn) saveBtn.disabled = false;
                break;
            case 'saving':
                statusEl.textContent = message || 'Saving...';
                statusEl.className = 'save-status status-saving';
                if (saveBtn) saveBtn.disabled = true;
                break;
            case 'error':
                statusEl.textContent = message || 'Save failed';
                statusEl.className = 'save-status status-error';
                if (saveBtn) saveBtn.disabled = false;
                break;
        }
    }
}

// Export for use in main.js
window.Toolbar = Toolbar;
