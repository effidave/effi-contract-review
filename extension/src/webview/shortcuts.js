/**
 * Keyboard Shortcuts - Handles keyboard shortcuts for the editor
 * 
 * Shortcuts:
 * - Ctrl+B: Bold
 * - Ctrl+I: Italic
 * - Ctrl+U: Underline
 * - Ctrl+S: Save
 * - Ctrl+Z: Undo
 * - Ctrl+Y: Redo
 */

// @ts-check

class ShortcutManager {
    /**
     * @param {BlockEditor} editor - The editor instance
     * @param {Object} handlers - Callback handlers
     */
    constructor(editor, handlers = {}) {
        this.editor = editor;
        this.handlers = {
            onSave: handlers.onSave || (() => {}),
            ...handlers
        };
        
        this._boundHandler = this._handleKeydown.bind(this);
    }
    
    /**
     * Attach keyboard event listeners
     * @param {HTMLElement} target - Element to attach listeners to
     */
    attach(target) {
        this.target = target;
        target.addEventListener('keydown', this._boundHandler);
    }
    
    /**
     * Detach keyboard event listeners
     */
    detach() {
        if (this.target) {
            this.target.removeEventListener('keydown', this._boundHandler);
            this.target = null;
        }
    }
    
    /**
     * Handle keydown events
     * @param {KeyboardEvent} e 
     */
    _handleKeydown(e) {
        // Only handle Ctrl/Cmd shortcuts
        if (!e.ctrlKey && !e.metaKey) {
            return;
        }
        
        const key = e.key.toLowerCase();
        
        switch (key) {
            case 'b':
                // Bold
                e.preventDefault();
                this.editor.applyFormat('bold');
                break;
                
            case 'i':
                // Italic
                e.preventDefault();
                this.editor.applyFormat('italic');
                break;
                
            case 'u':
                // Underline
                e.preventDefault();
                this.editor.applyFormat('underline');
                break;
                
            case 's':
                // Save
                e.preventDefault();
                this.handlers.onSave();
                break;
                
            case 'z':
                // Undo/Redo
                e.preventDefault();
                if (e.shiftKey) {
                    this.editor.redo();
                } else {
                    this.editor.undo();
                }
                break;
                
            case 'y':
                // Redo
                e.preventDefault();
                this.editor.redo();
                break;
        }
    }
}

// Export for use in main.js
window.ShortcutManager = ShortcutManager;
