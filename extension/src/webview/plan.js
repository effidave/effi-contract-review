/**
 * PlanPanel Component
 * 
 * Step 4: Plan WebviewPanel UI
 * 
 * A UI component that displays work plan tasks in a sidebar panel.
 * Features:
 * - Task list with ordinals, titles, descriptions, statuses
 * - Task CRUD operations (add, update, delete)
 * - Task status changes (pending, in_progress, completed, blocked)
 * - Task reordering via move operations
 * - Edit log display for tasks
 * - Filter by status
 * - Progress summary with completion percentage
 */

/**
 * Status labels for display
 */
const STATUS_LABELS = {
    pending: 'Pending',
    in_progress: 'In Progress',
    completed: 'Completed',
    blocked: 'Blocked'
};

/**
 * Allowed HTML tags for markdown sanitization.
 * Only these tags will be kept; all others are stripped.
 */
const ALLOWED_TAGS = [
    'p', 'br',
    'strong', 'b', 'em', 'i', 'u',
    'code', 'pre',
    'ul', 'ol', 'li',
    'a',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote',
    'hr'
];

/**
 * Allowed attributes per tag for markdown sanitization.
 * Only these attributes on these tags will be kept.
 */
const ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    '*': [] // No global attributes allowed
};

/**
 * Patterns for dangerous attribute values (e.g., javascript: URLs)
 */
const DANGEROUS_URL_PATTERNS = [
    /^javascript:/i,
    /^data:/i,
    /^vbscript:/i
];

/**
 * Sanitize HTML from markdown output to prevent XSS attacks.
 * Allows only safe tags and attributes; strips everything else.
 * 
 * @param {string} html - The HTML string to sanitize
 * @returns {string} Sanitized HTML string
 */
function sanitizeMarkdownHtml(html) {
    // Handle null/undefined/empty
    if (!html) return '';
    if (typeof html !== 'string') return '';
    
    // Create a temporary container to parse the HTML
    // Use DOMParser for Node.js compatibility, or create element in browser
    let doc;
    if (typeof DOMParser !== 'undefined') {
        const parser = new DOMParser();
        doc = parser.parseFromString(`<div>${html}</div>`, 'text/html');
    } else if (typeof document !== 'undefined') {
        doc = document.implementation.createHTMLDocument('');
        doc.body.innerHTML = `<div>${html}</div>`;
    } else {
        // Node.js test environment - use simple regex-based sanitization
        return sanitizeHtmlRegex(html);
    }
    
    const container = doc.body.firstChild || doc.body;
    sanitizeNode(container);
    
    return container.innerHTML;
}

/**
 * Recursively sanitize a DOM node and its children.
 * @param {Node} node - The DOM node to sanitize
 */
function sanitizeNode(node) {
    // Process children in reverse order (so we can remove nodes safely)
    const children = Array.from(node.childNodes);
    for (let i = children.length - 1; i >= 0; i--) {
        const child = children[i];
        
        if (child.nodeType === 1) { // Element node
            const tagName = child.tagName.toLowerCase();
            
            if (!ALLOWED_TAGS.includes(tagName)) {
                // Tag not allowed - unwrap children (keep text content)
                while (child.firstChild) {
                    node.insertBefore(child.firstChild, child);
                }
                node.removeChild(child);
            } else {
                // Tag allowed - sanitize attributes
                sanitizeAttributes(child, tagName);
                // Recursively sanitize children
                sanitizeNode(child);
            }
        }
        // Text nodes (nodeType 3) are always kept as-is
    }
}

/**
 * Sanitize attributes on an element.
 * @param {Element} element - The element to sanitize
 * @param {string} tagName - The lowercase tag name
 */
function sanitizeAttributes(element, tagName) {
    const allowedForTag = ALLOWED_ATTRIBUTES[tagName] || [];
    const allowedGlobal = ALLOWED_ATTRIBUTES['*'] || [];
    const allowed = [...allowedForTag, ...allowedGlobal];
    
    // Get all attribute names
    const attrNames = Array.from(element.attributes).map(a => a.name);
    
    for (const attrName of attrNames) {
        // Remove event handlers (on*)
        if (attrName.startsWith('on')) {
            element.removeAttribute(attrName);
            continue;
        }
        
        // Check if attribute is allowed
        if (!allowed.includes(attrName)) {
            element.removeAttribute(attrName);
            continue;
        }
        
        // For href, check for dangerous URL schemes
        if (attrName === 'href') {
            const value = element.getAttribute(attrName);
            if (isDangerousUrl(value)) {
                element.removeAttribute(attrName);
            }
        }
    }
}

/**
 * Check if a URL is dangerous (javascript:, data:, etc.)
 * @param {string} url - The URL to check
 * @returns {boolean} True if the URL is dangerous
 */
function isDangerousUrl(url) {
    if (!url) return false;
    const trimmed = url.trim();
    return DANGEROUS_URL_PATTERNS.some(pattern => pattern.test(trimmed));
}

/**
 * Regex-based HTML sanitization for Node.js test environment.
 * This is a fallback when DOMParser is not available.
 * @param {string} html - The HTML to sanitize
 * @returns {string} Sanitized HTML
 */
function sanitizeHtmlRegex(html) {
    if (!html) return '';
    
    let result = html;
    
    // Remove script, style, iframe, object, embed, form tags and their contents
    const dangerousTags = ['script', 'style', 'iframe', 'object', 'embed', 'form', 'input', 'img'];
    for (const tag of dangerousTags) {
        // Remove opening and closing tags with content
        result = result.replace(new RegExp(`<${tag}[^>]*>[\\s\\S]*?</${tag}>`, 'gi'), '');
        // Remove self-closing tags
        result = result.replace(new RegExp(`<${tag}[^>]*/?>`, 'gi'), '');
    }
    
    // Remove event handlers from remaining tags
    result = result.replace(/\s+on\w+\s*=\s*["'][^"']*["']/gi, '');
    result = result.replace(/\s+on\w+\s*=\s*[^\s>]+/gi, '');
    
    // Remove javascript: and data: URLs from href
    result = result.replace(/href\s*=\s*["']javascript:[^"']*["']/gi, '');
    result = result.replace(/href\s*=\s*["']data:[^"']*["']/gi, '');
    
    // Remove disallowed tags but keep their text content
    const disallowedTags = ['div', 'span', 'table', 'tr', 'td', 'th', 'tbody', 'thead', 'tfoot'];
    for (const tag of disallowedTags) {
        result = result.replace(new RegExp(`</?${tag}[^>]*>`, 'gi'), '');
    }
    
    return result;
}

/**
 * Render markdown text to sanitized HTML.
 * Uses the marked library (must be loaded globally as window.marked).
 * 
 * @param {string} markdown - The markdown text to render
 * @returns {string} Sanitized HTML string
 */
function renderMarkdown(markdown) {
    // Handle null/undefined/empty
    if (!markdown) return '';
    if (typeof markdown !== 'string') return '';
    
    // Check if marked is available
    const markedLib = typeof window !== 'undefined' ? window.marked : 
                      typeof marked !== 'undefined' ? marked : null;
    
    // Debug logging
    console.log('[renderMarkdown] window.marked available:', !!markedLib);
    console.log('[renderMarkdown] input length:', markdown.length);
    
    if (!markedLib) {
        // Fallback: escape HTML and return as-is
        console.warn('marked library not available, returning plain text');
        return escapeHtml(markdown);
    }
    
    try {
        // Parse markdown to HTML
        const html = markedLib.parse(markdown);
        console.log('[renderMarkdown] output length:', html.length);
        // Sanitize the output
        return sanitizeMarkdownHtml(html);
    } catch (err) {
        console.error('Error rendering markdown:', err);
        return escapeHtml(markdown);
    }
}

/**
 * Escape HTML special characters for safe display.
 * @param {string} text - The text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = typeof document !== 'undefined' ? 
                document.createElement('div') : 
                { textContent: '', innerHTML: '' };
    div.textContent = text;
    return div.innerHTML || text.replace(/[&<>"']/g, char => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    })[char]);
}

/**
 * PlanPanel class - manages the work plan UI
 */
class PlanPanel {
    /**
     * Create a PlanPanel
     * @param {HTMLElement} container - The container element to render into
     * @param {Object} options - Configuration options
     * @param {Object} options.vscode - VS Code API object for postMessage
     * @param {string} options.projectPath - Path to the project
     * @param {Function} options.onTaskSelect - Called when a task is selected
     * @param {Function} options.onAddTask - Called when add task is clicked
     * @param {Function} options.onUpdateTask - Called when a task is updated
     * @param {Function} options.onDeleteTask - Called when a task is deleted
     * @param {Function} options.onMoveTask - Called when a task is moved
     * @param {boolean} options.confirmDelete - Whether to confirm before delete (default: true)
     */
    constructor(container, options = {}) {
        this.container = container;
        this.options = options;
        this.vscode = options.vscode;
        this.projectPath = options.projectPath || '';
        this.confirmDelete = options.confirmDelete !== false;
        
        this.tasks = [];
        this.edits = [];
        this.editsByTaskId = new Map();
        this.filter = 'all';
        this.selectedTaskId = null;
        this.expandedTaskIds = new Set();
        this.expandedEditIds = new Set();
        this.expandedDescriptions = new Set(); // Track which task descriptions are expanded
        
        // DOM elements
        this.panelElement = null;
        this.headerElement = null;
        this.listElement = null;
        this.progressElement = null;
        this.addFormElement = null;
        
        this._render();
    }
    
    /**
     * Set the project path
     * @param {string} projectPath - Path to the project
     */
    setProjectPath(projectPath) {
        this.projectPath = projectPath;
    }
    
    /**
     * Set the tasks to display
     * @param {Array} tasks - Array of task objects
     */
    setTasks(tasks) {
        this.tasks = (tasks || []).slice();
        
        // Sort by ordinal
        this.tasks.sort((a, b) => a.ordinal - b.ordinal);
        
        // Check if selected task still exists
        if (this.selectedTaskId) {
            const stillExists = this.tasks.some(t => t.id === this.selectedTaskId);
            if (!stillExists) {
                this.selectedTaskId = null;
            }
        }
        
        this._renderTasks();
        this._renderProgress();
        
        // Re-apply selection if task still exists
        if (this.selectedTaskId) {
            this._applySelection(this.selectedTaskId);
        }
    }
    
    /**
     * Set the edits to display
     * @param {Array} edits - Array of edit objects
     */
    setEdits(edits) {
        this.edits = edits || [];
        
        // Build map of edits by task ID
        this.editsByTaskId.clear();
        for (const edit of this.edits) {
            if (!this.editsByTaskId.has(edit.taskId)) {
                this.editsByTaskId.set(edit.taskId, []);
            }
            this.editsByTaskId.get(edit.taskId).push(edit);
        }
        
        // Re-render if we have tasks
        if (this.tasks.length > 0) {
            this._renderTasks();
        }
    }
    
    /**
     * Set the filter for displaying tasks
     * @param {string} filter - 'all', 'pending', 'in_progress', 'completed', or 'blocked'
     */
    setFilter(filter) {
        this.filter = filter;
        this._updateFilterButtons();
        this._applyFilter();
    }
    
    /**
     * Select a task by ID
     * @param {string} taskId - The ID of the task to select
     */
    selectTask(taskId) {
        // Clear previous selection
        this.clearSelection();
        
        this.selectedTaskId = taskId;
        this._applySelection(taskId);
    }
    
    /**
     * Clear the current selection
     */
    clearSelection() {
        if (this.listElement) {
            const prevSelected = this.listElement.querySelector('.task-selected');
            if (prevSelected) {
                prevSelected.classList.remove('task-selected');
            }
        }
        this.selectedTaskId = null;
    }
    
    /**
     * Request plan data from extension
     */
    requestPlan() {
        if (this.vscode) {
            this.vscode.postMessage({
                command: 'getPlan',
                projectPath: this.projectPath
            });
        }
    }
    
    /**
     * Show the add task form
     */
    showAddTaskForm() {
        if (this.addFormElement) {
            this.addFormElement.style.display = 'block';
        } else {
            this._createAddForm();
        }
        
        if (this.options.onAddTask) {
            this.options.onAddTask();
        }
    }
    
    /**
     * Hide the add task form
     */
    hideAddTaskForm() {
        if (this.addFormElement) {
            this.addFormElement.style.display = 'none';
        }
    }
    
    /**
     * Submit the add task form
     */
    submitAddTask() {
        const titleInput = this.container.querySelector('.task-title-input');
        const descInput = this.container.querySelector('.task-description-input');
        
        const title = titleInput ? (titleInput._textContent || titleInput.textContent || titleInput.value || '') : '';
        const description = descInput ? (descInput._textContent || descInput.textContent || descInput.value || '') : '';
        
        if (this.vscode) {
            this.vscode.postMessage({
                command: 'addTask',
                projectPath: this.projectPath,
                title,
                description
            });
        }
        
        this.hideAddTaskForm();
    }
    
    /**
     * Refresh the plan from disk (reload any changes made by LLM)
     */
    refreshPlan() {
        if (this.vscode && this.projectPath) {
            this.vscode.postMessage({
                command: 'getPlan',
                projectPath: this.projectPath
            });
        }
    }
    
    /**
     * Change a task's status
     * @param {string} taskId - The task ID
     * @param {string} status - The new status
     */
    changeTaskStatus(taskId, status) {
        if (this.options.onUpdateTask) {
            this.options.onUpdateTask(taskId, { status });
        }
        
        if (this.vscode) {
            this.vscode.postMessage({
                command: 'updateTask',
                projectPath: this.projectPath,
                taskId,
                updates: { status }
            });
        }
    }
    
    /**
     * Start editing a task's title
     * @param {string} taskId - The task ID
     */
    startEditTitle(taskId) {
        const taskEl = this.listElement.querySelector(`[data-task-id="${taskId}"]`);
        if (!taskEl) return;
        
        const titleEl = taskEl.querySelector('.task-title');
        if (!titleEl) return;
        
        // Don't allow multiple edits at once
        if (taskEl.querySelector('.task-title-edit')) return;
        
        const originalTitle = titleEl.textContent;
        
        // Create edit input
        const editInput = this._createElement('input', 'task-title-edit');
        editInput.type = 'text';
        editInput.value = originalTitle;
        
        // Save on Enter, cancel on Escape
        editInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const newTitle = editInput.value.trim();
                if (newTitle && newTitle !== originalTitle) {
                    this.submitTitleEdit(taskId, newTitle);
                }
                this._finishEditTitle(taskEl, titleEl, editInput, newTitle || originalTitle);
            } else if (e.key === 'Escape') {
                this._finishEditTitle(taskEl, titleEl, editInput, originalTitle);
            }
        });
        
        // Save on blur (click outside)
        editInput.addEventListener('blur', () => {
            const newTitle = editInput.value.trim();
            if (newTitle && newTitle !== originalTitle) {
                this.submitTitleEdit(taskId, newTitle);
            }
            this._finishEditTitle(taskEl, titleEl, editInput, newTitle || originalTitle);
        });
        
        titleEl.style.display = 'none';
        titleEl.parentElement.insertBefore(editInput, titleEl);
        editInput.focus();
        editInput.select();
    }
    
    /**
     * Finish editing a title - restore display
     * @param {HTMLElement} taskEl - The task element
     * @param {HTMLElement} titleEl - The title element
     * @param {HTMLElement} editInput - The edit input
     * @param {string} finalTitle - The final title value
     */
    _finishEditTitle(taskEl, titleEl, editInput, finalTitle) {
        titleEl.textContent = finalTitle;
        titleEl.style.display = '';
        if (editInput.parentElement) {
            editInput.remove();
        }
    }
    
    /**
     * Start editing a task's description
     * @param {string} taskId - The task ID
     */
    startEditDescription(taskId) {
        const taskEl = this.listElement.querySelector(`[data-task-id="${taskId}"]`);
        if (!taskEl) return;
        
        const descEl = taskEl.querySelector('.task-description');
        const contentEl = taskEl.querySelector('.task-content');
        if (!contentEl) return;
        
        // Don't allow multiple edits at once
        if (taskEl.querySelector('.task-description-edit')) return;
        
        const task = this.tasks.find(t => t.id === taskId);
        const originalDesc = task ? task.description : (descEl ? descEl.textContent : '');
        
        // Create edit textarea
        const editTextarea = this._createElement('textarea', 'task-description-edit');
        editTextarea.value = originalDesc;
        editTextarea.rows = 3;
        editTextarea.placeholder = 'Enter description...';
        
        // Save on Ctrl+Enter, cancel on Escape
        editTextarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                const newDesc = editTextarea.value.trim();
                if (newDesc !== originalDesc) {
                    this.submitDescriptionEdit(taskId, newDesc);
                }
                this._finishEditDescription(taskEl, descEl, contentEl, editTextarea, newDesc);
            } else if (e.key === 'Escape') {
                this._finishEditDescription(taskEl, descEl, contentEl, editTextarea, originalDesc);
            }
        });
        
        // Save on blur (click outside)
        editTextarea.addEventListener('blur', () => {
            const newDesc = editTextarea.value.trim();
            if (newDesc !== originalDesc) {
                this.submitDescriptionEdit(taskId, newDesc);
            }
            this._finishEditDescription(taskEl, descEl, contentEl, editTextarea, newDesc);
        });
        
        if (descEl) {
            descEl.style.display = 'none';
            contentEl.insertBefore(editTextarea, descEl);
        } else {
            contentEl.appendChild(editTextarea);
        }
        editTextarea.focus();
    }
    
    /**
     * Finish editing a description - restore display
     */
    _finishEditDescription(taskEl, descEl, contentEl, editTextarea, finalDesc) {
        if (descEl) {
            descEl.textContent = finalDesc;
            descEl.style.display = '';
        } else if (finalDesc) {
            // Create new description element if it didn't exist
            const newDescEl = this._createElement('p', 'task-description');
            newDescEl.textContent = finalDesc;
            newDescEl.addEventListener('dblclick', () => {
                const taskId = taskEl.getAttribute('data-task-id');
                this.startEditDescription(taskId);
            });
            const titleEl = contentEl.querySelector('.task-title');
            if (titleEl && titleEl.nextSibling) {
                contentEl.insertBefore(newDescEl, titleEl.nextSibling);
            } else {
                contentEl.appendChild(newDescEl);
            }
        }
        if (editTextarea.parentElement) {
            editTextarea.remove();
        }
    }
    
    /**
     * Submit a description edit
     * @param {string} taskId - The task ID
     * @param {string} newDescription - The new description
     */
    submitDescriptionEdit(taskId, newDescription) {
        // Update local state
        const task = this.tasks.find(t => t.id === taskId);
        if (task) {
            task.description = newDescription;
        }
        
        if (this.vscode) {
            this.vscode.postMessage({
                command: 'updateTask',
                projectPath: this.projectPath,
                taskId,
                updates: { description: newDescription }
            });
        }
    }
    
    /**
     * Submit a title edit
     * @param {string} taskId - The task ID
     * @param {string} newTitle - The new title
     */
    submitTitleEdit(taskId, newTitle) {
        // Update local state
        const task = this.tasks.find(t => t.id === taskId);
        if (task) {
            task.title = newTitle;
        }
        
        if (this.vscode) {
            this.vscode.postMessage({
                command: 'updateTask',
                projectPath: this.projectPath,
                taskId,
                updates: { title: newTitle }
            });
        }
    }
    
    /**
     * Delete a task
     * @param {string} taskId - The task ID
     */
    deleteTask(taskId) {
        if (this.options.onDeleteTask) {
            this.options.onDeleteTask(taskId);
        }
        
        if (this.vscode) {
            this.vscode.postMessage({
                command: 'deleteTask',
                projectPath: this.projectPath,
                taskId
            });
        }
    }
    
    /**
     * Move a task to a new ordinal
     * @param {string} taskId - The task ID
     * @param {number} newOrdinal - The new 0-based ordinal
     */
    moveTask(taskId, newOrdinal) {
        if (this.options.onMoveTask) {
            this.options.onMoveTask(taskId, newOrdinal);
        }
        
        if (this.vscode) {
            this.vscode.postMessage({
                command: 'moveTask',
                projectPath: this.projectPath,
                taskId,
                newOrdinal
            });
        }
    }
    
    /**
     * Expand a task to show its edits
     * @param {string} taskId - The task ID
     */
    expandTask(taskId) {
        this.expandedTaskIds.add(taskId);
        this._renderTaskEdits(taskId);
    }
    
    /**
     * Collapse a task to hide its edits
     * @param {string} taskId - The task ID
     */
    collapseTask(taskId) {
        this.expandedTaskIds.delete(taskId);
        
        const taskEl = this.listElement.querySelector(`[data-task-id="${taskId}"]`);
        if (!taskEl) return;
        
        const editList = taskEl.querySelector('.task-edit-list');
        if (editList) {
            editList.style.display = 'none';
        }
    }
    
    /**
     * Toggle task expansion
     * @param {string} taskId - The task ID
     */
    toggleTask(taskId) {
        if (this.expandedTaskIds.has(taskId)) {
            this.collapseTask(taskId);
        } else {
            this.expandTask(taskId);
        }
    }
    
    /**
     * Toggle task description expansion (collapsed/expanded view)
     * @param {string} taskId - The task ID
     */
    toggleDescriptionExpansion(taskId) {
        const taskEl = this.listElement.querySelector(`[data-task-id="${taskId}"]`);
        if (!taskEl) return;
        
        const descEl = taskEl.querySelector('.task-description');
        if (!descEl) return;
        
        if (this.expandedDescriptions.has(taskId)) {
            this.expandedDescriptions.delete(taskId);
            descEl.classList.remove('expanded');
        } else {
            this.expandedDescriptions.add(taskId);
            descEl.classList.add('expanded');
        }
    }
    
    /**
     * Expand an edit to show details
     * @param {string} editId - The edit ID
     */
    expandEdit(editId) {
        this.expandedEditIds.add(editId);
        
        const editEl = this.listElement.querySelector(`[data-edit-id="${editId}"]`);
        if (!editEl) return;
        
        const detailsEl = editEl.querySelector('.edit-details');
        if (detailsEl) {
            detailsEl.style.display = 'block';
        } else {
            this._renderEditDetails(editId, editEl);
        }
    }
    
    /**
     * Handle keyboard events
     * @param {KeyboardEvent} event - The keyboard event
     */
    handleKeyDown(event) {
        const { key } = event;
        
        if (!this.selectedTaskId && this.tasks.length > 0) {
            // Select first task if none selected
            if (key === 'ArrowDown' || key === 'ArrowUp') {
                this.selectTask(this.tasks[0].id);
                event.preventDefault();
                return;
            }
        }
        
        if (!this.selectedTaskId) return;
        
        const currentIndex = this.tasks.findIndex(t => t.id === this.selectedTaskId);
        if (currentIndex === -1) return;
        
        switch (key) {
            case 'ArrowDown':
                event.preventDefault();
                if (currentIndex < this.tasks.length - 1) {
                    this.selectTask(this.tasks[currentIndex + 1].id);
                }
                break;
            case 'ArrowUp':
                event.preventDefault();
                if (currentIndex > 0) {
                    this.selectTask(this.tasks[currentIndex - 1].id);
                }
                break;
            case 'Enter':
                event.preventDefault();
                this.toggleTask(this.selectedTaskId);
                break;
            case 'Delete':
                event.preventDefault();
                if (!this.confirmDelete) {
                    this.deleteTask(this.selectedTaskId);
                }
                break;
        }
    }
    
    /**
     * Handle messages from the extension
     * @param {Object} message - The message object
     */
    handleMessage(message) {
        console.log('PlanPanel.handleMessage:', message.command, message);
        switch (message.command) {
            case 'planData':
                console.log('PlanPanel: Received planData, tasks:', message.plan?.tasks?.length);
                if (message.plan && message.plan.tasks) {
                    this.setTasks(message.plan.tasks);
                }
                break;
            case 'taskAdded':
                if (message.task) {
                    this.tasks.push(message.task);
                    this.tasks.sort((a, b) => a.ordinal - b.ordinal);
                    this._renderTasks();
                    this._renderProgress();
                }
                break;
            case 'taskUpdated':
                // Just re-request fresh data or update from cache
                break;
            case 'taskDeleted':
                this.tasks = this.tasks.filter(t => t.id !== message.taskId);
                // Re-render
                this._renderTasks();
                this._renderProgress();
                break;
            case 'taskMoved':
                // Update local state to reflect move
                const movedTask = this.tasks.find(t => t.id === message.taskId);
                if (movedTask) {
                    // Simple approach: update ordinal and re-sort
                    const oldOrdinal = movedTask.ordinal;
                    const newOrdinal = message.newOrdinal;
                    
                    // Shift other tasks
                    for (const task of this.tasks) {
                        if (task.id === message.taskId) {
                            task.ordinal = newOrdinal;
                        } else if (oldOrdinal > newOrdinal) {
                            // Moving up - shift others down
                            if (task.ordinal >= newOrdinal && task.ordinal < oldOrdinal) {
                                task.ordinal++;
                            }
                        } else {
                            // Moving down - shift others up
                            if (task.ordinal > oldOrdinal && task.ordinal <= newOrdinal) {
                                task.ordinal--;
                            }
                        }
                    }
                    
                    this.tasks.sort((a, b) => a.ordinal - b.ordinal);
                    this._renderTasks();
                }
                break;
            case 'editLogged':
                if (message.edit) {
                    this.edits.push(message.edit);
                    
                    // Update editsByTaskId
                    if (!this.editsByTaskId.has(message.taskId)) {
                        this.editsByTaskId.set(message.taskId, []);
                    }
                    this.editsByTaskId.get(message.taskId).push(message.edit);
                    
                    // Update the task's editIds if we have it
                    const task = this.tasks.find(t => t.id === message.taskId);
                    if (task) {
                        task.editIds = task.editIds || [];
                        task.editIds.push(message.edit.id);
                    }
                    
                    this._renderTasks();
                }
                break;
            case 'planError':
                this._showError(message.error);
                break;
        }
    }
    
    // ========================================================================
    // Private Methods
    // ========================================================================
    
    /**
     * Initial render of the panel structure
     */
    _render() {
        // Create panel element
        this.panelElement = this._createElement('div', 'plan-panel');
        this.container.appendChild(this.panelElement);
        
        // Header
        this._renderHeader();
        
        // Progress summary
        this._renderProgress();
        
        // Task list
        this.listElement = this._createElement('div', 'plan-task-list');
        this.panelElement.appendChild(this.listElement);
        
        // Empty state
        this._renderEmptyState();
    }
    
    /**
     * Render the header with add button and filters
     */
    _renderHeader() {
        this.headerElement = this._createElement('div', 'plan-header');
        this.panelElement.appendChild(this.headerElement);
        
        // Title
        const title = this._createElement('h2', 'plan-title');
        title.textContent = 'Work Plan';
        this.headerElement.appendChild(title);
        
        // Button container
        const buttonContainer = this._createElement('div', 'plan-header-buttons');
        this.headerElement.appendChild(buttonContainer);
        
        // Refresh button
        const refreshBtn = this._createElement('button', 'plan-refresh-btn');
        refreshBtn.textContent = '↻';
        refreshBtn.title = 'Refresh plan from disk';
        refreshBtn.addEventListener('click', () => this.refreshPlan());
        buttonContainer.appendChild(refreshBtn);
        
        // Add button
        const addBtn = this._createElement('button', 'plan-add-task-btn');
        addBtn.textContent = '+ Add Task';
        addBtn.addEventListener('click', () => this.showAddTaskForm());
        buttonContainer.appendChild(addBtn);
        
        // Filter controls
        this._renderFilterControls();
    }
    
    /**
     * Render filter controls
     */
    _renderFilterControls() {
        const filters = this._createElement('div', 'plan-filter-controls');
        this.headerElement.appendChild(filters);
        
        const filterOptions = ['all', 'pending', 'in_progress', 'completed', 'blocked'];
        
        for (const filterValue of filterOptions) {
            const btn = this._createElement('button', `filter-${filterValue}`);
            btn.classList.add('filter-btn');
            if (filterValue === this.filter) {
                btn.classList.add('filter-active');
            }
            btn.textContent = filterValue === 'all' ? 'All' : STATUS_LABELS[filterValue] || filterValue;
            btn.addEventListener('click', () => this.setFilter(filterValue));
            filters.appendChild(btn);
        }
    }
    
    /**
     * Render the progress summary
     */
    _renderProgress() {
        if (this.progressElement) {
            this.progressElement.parentElement.removeChild(this.progressElement);
        }
        
        this.progressElement = this._createElement('div', 'plan-progress-summary');
        
        const completedCount = this.tasks.filter(t => t.status === 'completed').length;
        const totalCount = this.tasks.length;
        const percentage = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;
        
        // Summary text
        const summaryText = this._createElement('span', 'progress-text');
        summaryText.textContent = `${completedCount}/${totalCount} completed`;
        this.progressElement.appendChild(summaryText);
        
        // Progress bar container
        const barContainer = this._createElement('div', 'progress-bar-container');
        this.progressElement.appendChild(barContainer);
        
        // Progress bar fill
        const bar = this._createElement('div', 'plan-progress-bar');
        bar.style.width = `${percentage}%`;
        barContainer.appendChild(bar);
        
        // Insert after header
        if (this.headerElement && this.headerElement.nextSibling) {
            this.panelElement.insertBefore(this.progressElement, this.headerElement.nextSibling);
        } else {
            this.panelElement.appendChild(this.progressElement);
        }
    }
    
    /**
     * Render the task list
     */
    _renderTasks() {
        if (!this.listElement) return;
        
        // Clear existing
        this.listElement.innerHTML = '';
        
        if (this.tasks.length === 0) {
            this._renderEmptyState();
            return;
        }
        
        for (let i = 0; i < this.tasks.length; i++) {
            const task = this.tasks[i];
            const taskEl = this._renderTask(task, i);
            this.listElement.appendChild(taskEl);
        }
        
        this._applyFilter();
    }
    
    /**
     * Render a single task
     * @param {Object} task - The task object
     * @param {number} index - The task index
     * @returns {HTMLElement} The task element
     */
    _renderTask(task, index) {
        const taskEl = this._createElement('div', 'plan-task-item');
        taskEl.dataset.taskId = task.id;
        taskEl.setAttribute('data-task-id', task.id);
        
        // Add status class
        if (task.status === 'completed') {
            taskEl.classList.add('task-completed');
        }
        
        // Track expanded state for this task's description
        const isExpanded = this.expandedDescriptions && this.expandedDescriptions.has(task.id);
        
        // Click handler for toggling description expansion
        taskEl.addEventListener('click', (e) => {
            // Ignore clicks on buttons
            if (e.target.classList.contains('task-delete-btn') ||
                e.target.classList.contains('task-complete-btn') ||
                e.target.classList.contains('task-move-up') ||
                e.target.classList.contains('task-move-down') ||
                e.target.classList.contains('task-expand-btn')) {
                return;
            }
            
            // Toggle description expansion
            this.toggleDescriptionExpansion(task.id);
            
            // Also select the task
            this.selectTask(task.id);
            if (this.options.onTaskSelect) {
                this.options.onTaskSelect(task.id);
            }
        });
        
        // Ordinal
        const ordinalEl = this._createElement('span', 'task-ordinal');
        ordinalEl.textContent = String(task.ordinal);
        taskEl.appendChild(ordinalEl);
        
        // Content container
        const contentEl = this._createElement('div', 'task-content');
        taskEl.appendChild(contentEl);
        
        // Title
        const titleEl = this._createElement('span', 'task-title');
        titleEl.textContent = task.title;
        titleEl.title = 'Double-click to edit title';
        titleEl.addEventListener('dblclick', () => this.startEditTitle(task.id));
        contentEl.appendChild(titleEl);
        
        // Description
        const descEl = this._createElement('p', 'task-description');
        if (isExpanded) {
            descEl.classList.add('expanded');
        }
        if (task.description) {
            // Render markdown to sanitized HTML
            descEl.innerHTML = renderMarkdown(task.description);
        } else {
            descEl.textContent = '(Click to add description)';
            descEl.classList.add('task-description-placeholder');
        }
        descEl.title = 'Double-click to edit description (Ctrl+Enter to save)';
        descEl.addEventListener('dblclick', () => this.startEditDescription(task.id));
        contentEl.appendChild(descEl);
        
        // Status badge
        const statusEl = this._createElement('span', 'task-status');
        statusEl.classList.add(`status-${task.status}`);
        statusEl.textContent = STATUS_LABELS[task.status] || task.status;
        taskEl.appendChild(statusEl);
        
        // Edit count badge
        const editCount = task.editIds ? task.editIds.length : 0;
        if (editCount > 0) {
            const editBadge = this._createElement('span', 'task-edit-count');
            editBadge.textContent = String(editCount);
            taskEl.appendChild(editBadge);
            
            // Expand button
            const expandBtn = this._createElement('button', 'task-expand-btn');
            expandBtn.textContent = this.expandedTaskIds.has(task.id) ? '▼' : '▶';
            expandBtn.addEventListener('click', () => this.toggleTask(task.id));
            taskEl.appendChild(expandBtn);
        }
        
        // Actions container
        const actionsEl = this._createElement('div', 'task-actions');
        taskEl.appendChild(actionsEl);
        
        // Complete button
        const completeBtn = this._createElement('button', 'task-complete-btn');
        completeBtn.textContent = task.status === 'completed' ? '↩' : '✓';
        completeBtn.title = task.status === 'completed' ? 'Mark as pending' : 'Mark as completed';
        completeBtn.addEventListener('click', () => {
            const newStatus = task.status === 'completed' ? 'pending' : 'completed';
            this.changeTaskStatus(task.id, newStatus);
        });
        actionsEl.appendChild(completeBtn);
        
        // Move up button
        const moveUpBtn = this._createElement('button', 'task-move-up');
        moveUpBtn.textContent = '↑';
        moveUpBtn.title = 'Move up';
        if (index === 0) {
            moveUpBtn.disabled = true;
        } else {
            moveUpBtn.addEventListener('click', () => this.moveTask(task.id, task.ordinal - 1));
        }
        actionsEl.appendChild(moveUpBtn);
        
        // Move down button
        const moveDownBtn = this._createElement('button', 'task-move-down');
        moveDownBtn.textContent = '↓';
        moveDownBtn.title = 'Move down';
        if (index === this.tasks.length - 1) {
            moveDownBtn.disabled = true;
        } else {
            moveDownBtn.addEventListener('click', () => this.moveTask(task.id, task.ordinal + 1));
        }
        actionsEl.appendChild(moveDownBtn);
        
        // Delete button
        const deleteBtn = this._createElement('button', 'task-delete-btn');
        deleteBtn.textContent = '×';
        deleteBtn.title = 'Delete task';
        deleteBtn.addEventListener('click', () => {
            if (this.confirmDelete) {
                this._showDeleteConfirm(task.id);
            } else {
                this.deleteTask(task.id);
            }
        });
        actionsEl.appendChild(deleteBtn);
        
        // Render edits if expanded
        if (this.expandedTaskIds.has(task.id)) {
            const editList = this._renderEditList(task.id);
            taskEl.appendChild(editList);
        }
        
        return taskEl;
    }
    
    /**
     * Render the edit list for a task
     * @param {string} taskId - The task ID
     * @returns {HTMLElement} The edit list element
     */
    _renderEditList(taskId) {
        const editList = this._createElement('div', 'task-edit-list');
        
        const taskEdits = this.editsByTaskId.get(taskId) || [];
        
        for (const edit of taskEdits) {
            const editEl = this._renderEdit(edit);
            editList.appendChild(editEl);
        }
        
        return editList;
    }
    
    /**
     * Render the edit list for a task (after expansion)
     * @param {string} taskId - The task ID
     */
    _renderTaskEdits(taskId) {
        const taskEl = this.listElement.querySelector(`[data-task-id="${taskId}"]`);
        if (!taskEl) return;
        
        // Remove existing edit list if any
        const existingList = taskEl.querySelector('.task-edit-list');
        if (existingList) {
            existingList.style.display = 'block';
            return;
        }
        
        // Create new edit list
        const editList = this._renderEditList(taskId);
        taskEl.appendChild(editList);
    }
    
    /**
     * Render a single edit
     * @param {Object} edit - The edit object
     * @returns {HTMLElement} The edit element
     */
    _renderEdit(edit) {
        const editEl = this._createElement('div', 'edit-item');
        editEl.dataset.editId = edit.id;
        editEl.setAttribute('data-edit-id', edit.id);
        
        // Tool name (strip mcp_effi-local_ prefix)
        const toolNameEl = this._createElement('span', 'edit-tool-name');
        const displayName = edit.toolName.replace(/^mcp_effi-local_/, '');
        toolNameEl.textContent = displayName;
        editEl.appendChild(toolNameEl);
        
        // Timestamp
        if (edit.timestamp) {
            const timestampEl = this._createElement('span', 'edit-timestamp');
            const date = new Date(edit.timestamp);
            timestampEl.textContent = date.toLocaleTimeString();
            editEl.appendChild(timestampEl);
        }
        
        // Details toggle
        const detailsToggle = this._createElement('button', 'edit-details-toggle');
        detailsToggle.textContent = 'Details';
        detailsToggle.addEventListener('click', () => this.expandEdit(edit.id));
        editEl.appendChild(detailsToggle);
        
        // Details (hidden by default)
        if (this.expandedEditIds.has(edit.id)) {
            this._renderEditDetails(edit.id, editEl);
        }
        
        return editEl;
    }
    
    /**
     * Render edit details
     * @param {string} editId - The edit ID
     * @param {HTMLElement} editEl - The edit element
     */
    _renderEditDetails(editId, editEl) {
        const edit = this.edits.find(e => e.id === editId);
        if (!edit) return;
        
        const detailsEl = this._createElement('div', 'edit-details');
        detailsEl.style.display = 'block';
        
        // Request
        const requestEl = this._createElement('pre', 'edit-request');
        requestEl.textContent = JSON.stringify(edit.request, null, 2);
        detailsEl.appendChild(requestEl);
        
        // Response
        const responseEl = this._createElement('pre', 'edit-response');
        responseEl.textContent = JSON.stringify(edit.response, null, 2);
        detailsEl.appendChild(responseEl);
        
        editEl.appendChild(detailsEl);
    }
    
    /**
     * Render empty state
     */
    _renderEmptyState() {
        const emptyState = this._createElement('div', 'plan-empty-state');
        emptyState.textContent = 'No tasks in the work plan. Click "+ Add Task" to create one.';
        this.listElement.appendChild(emptyState);
    }
    
    /**
     * Create the add task form
     */
    _createAddForm() {
        this.addFormElement = this._createElement('div', 'plan-add-task-form');
        
        // Title input
        const titleLabel = this._createElement('label');
        titleLabel.textContent = 'Title:';
        this.addFormElement.appendChild(titleLabel);
        
        const titleInput = this._createElement('input', 'task-title-input');
        titleInput.type = 'text';
        titleInput.placeholder = 'Task title';
        this.addFormElement.appendChild(titleInput);
        
        // Description input
        const descLabel = this._createElement('label');
        descLabel.textContent = 'Description:';
        this.addFormElement.appendChild(descLabel);
        
        const descInput = this._createElement('textarea', 'task-description-input');
        descInput.placeholder = 'Task description';
        this.addFormElement.appendChild(descInput);
        
        // Position select
        const posLabel = this._createElement('label');
        posLabel.textContent = 'Position:';
        this.addFormElement.appendChild(posLabel);
        
        const posSelect = this._createElement('select', 'task-position-select');
        const endOption = this._createElement('option');
        endOption.value = 'end';
        endOption.textContent = 'At end';
        posSelect.appendChild(endOption);
        
        const startOption = this._createElement('option');
        startOption.value = 'start';
        startOption.textContent = 'At start';
        posSelect.appendChild(startOption);
        this.addFormElement.appendChild(posSelect);
        
        // Submit button
        const submitBtn = this._createElement('button', 'task-submit-btn');
        submitBtn.textContent = 'Add Task';
        submitBtn.addEventListener('click', () => this.submitAddTask());
        this.addFormElement.appendChild(submitBtn);
        
        // Cancel button
        const cancelBtn = this._createElement('button', 'task-cancel-btn');
        cancelBtn.textContent = 'Cancel';
        cancelBtn.addEventListener('click', () => this.hideAddTaskForm());
        this.addFormElement.appendChild(cancelBtn);
        
        // Insert after header
        if (this.headerElement && this.headerElement.nextSibling) {
            this.panelElement.insertBefore(this.addFormElement, this.headerElement.nextSibling);
        } else {
            this.panelElement.appendChild(this.addFormElement);
        }
    }
    
    /**
     * Show delete confirmation
     * @param {string} taskId - The task ID
     */
    _showDeleteConfirm(taskId) {
        const taskEl = this.listElement.querySelector(`[data-task-id="${taskId}"]`);
        if (!taskEl) return;
        
        const confirmEl = this._createElement('div', 'task-delete-confirm');
        confirmEl.textContent = 'Delete this task? ';
        
        const yesBtn = this._createElement('button');
        yesBtn.textContent = 'Yes';
        yesBtn.addEventListener('click', () => {
            this.deleteTask(taskId);
            confirmEl.parentElement.removeChild(confirmEl);
        });
        confirmEl.appendChild(yesBtn);
        
        const noBtn = this._createElement('button');
        noBtn.textContent = 'No';
        noBtn.addEventListener('click', () => {
            confirmEl.parentElement.removeChild(confirmEl);
        });
        confirmEl.appendChild(noBtn);
        
        taskEl.appendChild(confirmEl);
    }
    
    /**
     * Show error message
     * @param {string} message - The error message
     */
    _showError(message) {
        const errorEl = this._createElement('div', 'plan-error');
        errorEl.textContent = message;
        
        // Insert at top of panel
        if (this.headerElement && this.headerElement.nextSibling) {
            this.panelElement.insertBefore(errorEl, this.headerElement.nextSibling);
        } else {
            this.panelElement.appendChild(errorEl);
        }
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorEl.parentElement) {
                errorEl.parentElement.removeChild(errorEl);
            }
        }, 5000);
    }
    
    /**
     * Apply selection styling
     * @param {string} taskId - The task ID
     */
    _applySelection(taskId) {
        if (!this.listElement) return;
        
        const taskEl = this.listElement.querySelector(`[data-task-id="${taskId}"]`);
        if (taskEl) {
            taskEl.classList.add('task-selected');
        }
    }
    
    /**
     * Apply filter to task list
     */
    _applyFilter() {
        if (!this.listElement) return;
        
        const taskElements = this.listElement.querySelectorAll('.plan-task-item');
        
        for (const taskEl of taskElements) {
            const taskId = taskEl.getAttribute('data-task-id');
            const task = this.tasks.find(t => t.id === taskId);
            
            if (!task) continue;
            
            if (this.filter === 'all' || task.status === this.filter) {
                taskEl.classList.remove('hidden');
            } else {
                taskEl.classList.add('hidden');
            }
        }
    }
    
    /**
     * Update filter button styling
     */
    _updateFilterButtons() {
        if (!this.headerElement) return;
        
        const filterBtns = this.headerElement.querySelectorAll('.filter-btn');
        for (const btn of filterBtns) {
            btn.classList.remove('filter-active');
            if (btn.classList.contains(`filter-${this.filter}`)) {
                btn.classList.add('filter-active');
            }
        }
    }
    
    /**
     * Helper to create an element
     * @param {string} tag - The element tag
     * @param {string} className - The class name
     * @returns {HTMLElement} The created element
     */
    _createElement(tag, className) {
        // Use document if available (browser), otherwise use mock
        const doc = typeof document !== 'undefined' ? document : global.document;
        const el = doc.createElement(tag);
        if (className) {
            el.classList.add(className);
        }
        return el;
    }
}

// Export for both Node.js (testing) and browser
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        PlanPanel,
        sanitizeMarkdownHtml,
        renderMarkdown,
        ALLOWED_TAGS,
        ALLOWED_ATTRIBUTES
    };
}

// Also expose to window for browser/webview use
if (typeof window !== 'undefined') {
    window.PlanPanel = PlanPanel;
    window.sanitizeMarkdownHtml = sanitizeMarkdownHtml;
    window.renderMarkdown = renderMarkdown;
}
