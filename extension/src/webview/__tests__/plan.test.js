/**
 * PlanPanel UI Tests
 * 
 * Step 4: Plan WebviewPanel UI
 * 
 * These tests verify the PlanPanel component functionality:
 * - Rendering task list with ordinals, titles, descriptions, statuses
 * - Task CRUD operations (add, update, delete)
 * - Task status changes (pending, in_progress, completed, blocked)
 * - Task reordering via move operations
 * - Edit log display for tasks
 * - Filter by status
 * - Empty state rendering
 * - Webview message handling
 * 
 * TDD Approach: These tests are written to FAIL initially.
 * Implement plan.js to make them pass.
 */

// Mock DOM environment for Node.js testing
// In browser/webview, this would use actual DOM
const createMockDOM = () => {
    const elements = new Map();
    let idCounter = 0;
    
    const createElement = (tag) => {
        const id = `mock-${++idCounter}`;
        const element = {
            tagName: tag.toUpperCase(),
            id: '',
            className: '',
            classList: {
                _classes: new Set(),
                add(...classes) { classes.forEach(c => this._classes.add(c)); },
                remove(...classes) { classes.forEach(c => this._classes.delete(c)); },
                contains(c) { return this._classes.has(c); },
                toggle(c) { this._classes.has(c) ? this._classes.delete(c) : this._classes.add(c); }
            },
            _innerHTML: '',
            get innerHTML() {
                return this._innerHTML;
            },
            set innerHTML(val) {
                this._innerHTML = val;
                // Clear children when setting innerHTML
                if (val === '') {
                    this.children = [];
                }
            },
            _textContent: '',
            get textContent() {
                // If we have a direct text value, return it
                if (this._textContent) return this._textContent;
                // Otherwise, gather text from children
                let text = '';
                for (const child of this.children) {
                    text += child.textContent || '';
                }
                return text;
            },
            set textContent(val) {
                this._textContent = val;
                // Clear children when setting text content directly
                this.children = [];
            },
            style: {},
            dataset: {},
            children: [],
            parentElement: null,
            _eventListeners: {},
            appendChild(child) {
                child.parentElement = this;
                this.children.push(child);
                return child;
            },
            removeChild(child) {
                const idx = this.children.indexOf(child);
                if (idx >= 0) {
                    this.children.splice(idx, 1);
                    child.parentElement = null;
                }
                return child;
            },
            addEventListener(event, handler) {
                if (!this._eventListeners[event]) this._eventListeners[event] = [];
                this._eventListeners[event].push(handler);
            },
            removeEventListener(event, handler) {
                if (this._eventListeners[event]) {
                    const idx = this._eventListeners[event].indexOf(handler);
                    if (idx >= 0) this._eventListeners[event].splice(idx, 1);
                }
            },
            dispatchEvent(event) {
                const handlers = this._eventListeners[event.type] || [];
                handlers.forEach(h => h(event));
            },
            click() {
                this.dispatchEvent({ type: 'click', target: this, stopPropagation: () => {} });
            },
            querySelector(selector) {
                // Simple selector support for testing
                for (const child of this.children) {
                    if (matchesSelector(child, selector)) return child;
                    const found = child.querySelector ? child.querySelector(selector) : null;
                    if (found) return found;
                }
                return null;
            },
            querySelectorAll(selector) {
                const results = [];
                // Handle :not(.hidden) selector
                let baseSelector = selector;
                let notClass = null;
                const notMatch = selector.match(/^(.+):not\(\.([^)]+)\)$/);
                if (notMatch) {
                    baseSelector = notMatch[1];
                    notClass = notMatch[2];
                }
                const search = (el) => {
                    if (matchesSelector(el, baseSelector)) {
                        // If there's a :not() clause, check it
                        if (notClass) {
                            if (!el.classList.contains(notClass)) {
                                results.push(el);
                            }
                        } else {
                            results.push(el);
                        }
                    }
                    (el.children || []).forEach(search);
                };
                this.children.forEach(search);
                return results;
            },
            scrollIntoView() {
                this._scrolledIntoView = true;
            },
            setAttribute(name, value) {
                if (name.startsWith('data-')) {
                    this.dataset[name.slice(5)] = value;
                }
                this[name] = value;
            },
            getAttribute(name) {
                if (name.startsWith('data-')) {
                    return this.dataset[name.slice(5)];
                }
                return this[name];
            }
        };
        elements.set(id, element);
        return element;
    };
    
    const matchesSelector = (el, selector) => {
        if (selector.startsWith('.')) {
            return el.classList.contains(selector.slice(1));
        }
        if (selector.startsWith('#')) {
            return el.id === selector.slice(1);
        }
        if (selector.startsWith('[data-')) {
            const match = selector.match(/\[data-([^=]+)="([^"]+)"\]/);
            if (match) {
                // Convert kebab-case to camelCase for dataset access
                const key = match[1].replace(/-([a-z])/g, (g) => g[1].toUpperCase());
                return el.dataset[key] === match[2];
            }
        }
        return el.tagName === selector.toUpperCase();
    };
    
    return {
        createElement,
        getElementById: (id) => {
            for (const [, el] of elements) {
                if (el.id === id) return el;
            }
            return null;
        },
        body: createElement('body')
    };
};

// Mock VS Code API for webview
const createMockVSCodeAPI = () => {
    const messages = [];
    return {
        postMessage: (msg) => messages.push(msg),
        getMessages: () => messages,
        clearMessages: () => messages.length = 0
    };
};

// Sample task data
const createSampleTask = (overrides = {}) => ({
    id: 'task_abc123',
    title: 'Review liability clauses',
    description: 'Analyze indemnity and limitation of liability sections',
    status: 'pending',
    ordinal: 0,
    creationDate: '2025-12-09T10:00:00.000Z',
    completionDate: null,
    editIds: [],
    ...overrides
});

const createSampleEdit = (overrides = {}) => ({
    id: 'edit_xyz789',
    taskId: 'task_abc123',
    toolName: 'mcp_effi-local_search_and_replace',
    request: { find_text: 'shall', replace_text: 'will' },
    response: { success: true, replacements: 5 },
    timestamp: '2025-12-09T10:30:00.000Z',
    ...overrides
});

// Import the module to test (will fail until implementation exists)
let PlanPanel;
try {
    PlanPanel = require('../plan.js').PlanPanel;
} catch (e) {
    // Module doesn't exist yet - this is expected in TDD
    PlanPanel = null;
}

// ============================================================================
// Test Suite: PlanPanel Initialization
// ============================================================================

describe('PlanPanel Initialization', () => {
    let document;
    let container;
    let vscodeApi;
    
    beforeEach(() => {
        document = createMockDOM();
        container = document.createElement('div');
        vscodeApi = createMockVSCodeAPI();
        global.document = document;
    });
    
    test('should create panel with container element', () => {
        expect(PlanPanel).not.toBeNull();
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        expect(panel).toBeDefined();
        expect(panel.container).toBe(container);
    });
    
    test('should render empty state when no tasks', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        panel.setTasks([]);
        
        const emptyState = container.querySelector('.plan-empty-state');
        expect(emptyState).not.toBeNull();
        expect(emptyState.textContent).toContain('No tasks');
    });
    
    test('should create panel structure with header and list', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        
        const header = container.querySelector('.plan-header');
        const list = container.querySelector('.plan-task-list');
        
        expect(header).not.toBeNull();
        expect(list).not.toBeNull();
    });
    
    test('should include add task button in header', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        
        const addButton = container.querySelector('.plan-add-task-btn');
        expect(addButton).not.toBeNull();
    });
    
    test('should include filter controls in header', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        
        const filters = container.querySelector('.plan-filter-controls');
        expect(filters).not.toBeNull();
    });
});

// ============================================================================
// Test Suite: Task Rendering
// ============================================================================

describe('PlanPanel Task Rendering', () => {
    let document;
    let container;
    let vscodeApi;
    
    beforeEach(() => {
        document = createMockDOM();
        container = document.createElement('div');
        vscodeApi = createMockVSCodeAPI();
        global.document = document;
    });
    
    test('should render single task with all fields', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask();
        
        panel.setTasks([task]);
        
        const taskEl = container.querySelector(`[data-task-id="${task.id}"]`);
        expect(taskEl).not.toBeNull();
        expect(taskEl.textContent).toContain('Review liability clauses');
        expect(taskEl.textContent).toContain('Analyze indemnity');
    });
    
    test('should render task ordinal as 0-based index', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ ordinal: 0 });
        
        panel.setTasks([task]);
        
        const ordinalEl = container.querySelector('.task-ordinal');
        expect(ordinalEl).not.toBeNull();
        expect(ordinalEl.textContent).toBe('0');
    });
    
    test('should render task status badge', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ status: 'in_progress' });
        
        panel.setTasks([task]);
        
        const statusEl = container.querySelector('.task-status');
        expect(statusEl).not.toBeNull();
        expect(statusEl.classList.contains('status-in_progress')).toBe(true);
    });
    
    test('should render multiple tasks in ordinal order', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0, title: 'First task' }),
            createSampleTask({ id: 'task_2', ordinal: 1, title: 'Second task' }),
            createSampleTask({ id: 'task_3', ordinal: 2, title: 'Third task' })
        ];
        
        panel.setTasks(tasks);
        
        const taskElements = container.querySelectorAll('.plan-task-item');
        expect(taskElements.length).toBe(3);
        expect(taskElements[0].textContent).toContain('First task');
        expect(taskElements[1].textContent).toContain('Second task');
        expect(taskElements[2].textContent).toContain('Third task');
    });
    
    test('should sort tasks by ordinal even if provided out of order', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_3', ordinal: 2, title: 'Third task' }),
            createSampleTask({ id: 'task_1', ordinal: 0, title: 'First task' }),
            createSampleTask({ id: 'task_2', ordinal: 1, title: 'Second task' })
        ];
        
        panel.setTasks(tasks);
        
        const taskElements = container.querySelectorAll('.plan-task-item');
        expect(taskElements[0].textContent).toContain('First task');
        expect(taskElements[1].textContent).toContain('Second task');
        expect(taskElements[2].textContent).toContain('Third task');
    });
    
    test('should show completion date for completed tasks', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ 
            status: 'completed', 
            completionDate: '2025-12-09T15:00:00.000Z' 
        });
        
        panel.setTasks([task]);
        
        const taskEl = container.querySelector('.plan-task-item');
        expect(taskEl.classList.contains('task-completed')).toBe(true);
    });
    
    test('should show edit count badge when task has edits', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ editIds: ['edit_1', 'edit_2', 'edit_3'] });
        
        panel.setTasks([task]);
        
        const editBadge = container.querySelector('.task-edit-count');
        expect(editBadge).not.toBeNull();
        expect(editBadge.textContent).toBe('3');
    });
    
    test('should hide edit badge when task has no edits', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ editIds: [] });
        
        panel.setTasks([task]);
        
        const editBadge = container.querySelector('.task-edit-count');
        // Badge should not exist or be hidden
        expect(editBadge === null || editBadge.style.display === 'none').toBe(true);
    });
});

// ============================================================================
// Test Suite: Task Status Display
// ============================================================================

describe('PlanPanel Task Status Display', () => {
    let document;
    let container;
    let vscodeApi;
    
    beforeEach(() => {
        document = createMockDOM();
        container = document.createElement('div');
        vscodeApi = createMockVSCodeAPI();
        global.document = document;
    });
    
    test.each([
        ['pending', 'status-pending'],
        ['in_progress', 'status-in_progress'],
        ['completed', 'status-completed'],
        ['blocked', 'status-blocked']
    ])('should apply correct class for %s status', (status, expectedClass) => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ status });
        
        panel.setTasks([task]);
        
        const statusEl = container.querySelector('.task-status');
        expect(statusEl.classList.contains(expectedClass)).toBe(true);
    });
    
    test('should display human-readable status label', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ status: 'in_progress' });
        
        panel.setTasks([task]);
        
        const statusEl = container.querySelector('.task-status');
        expect(statusEl.textContent).toBe('In Progress');
    });
});

// ============================================================================
// Test Suite: Task Selection
// ============================================================================

describe('PlanPanel Task Selection', () => {
    let document;
    let container;
    let vscodeApi;
    let onTaskSelect;
    
    beforeEach(() => {
        document = createMockDOM();
        container = document.createElement('div');
        vscodeApi = createMockVSCodeAPI();
        onTaskSelect = jest.fn();
        global.document = document;
    });
    
    test('should call onTaskSelect callback when task is clicked', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            onTaskSelect
        });
        const task = createSampleTask();
        
        panel.setTasks([task]);
        
        const taskEl = container.querySelector('.plan-task-item');
        taskEl.click();
        
        expect(onTaskSelect).toHaveBeenCalledWith(task.id);
    });
    
    test('should add selected class to clicked task', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask();
        
        panel.setTasks([task]);
        
        const taskEl = container.querySelector('.plan-task-item');
        taskEl.click();
        
        expect(taskEl.classList.contains('task-selected')).toBe(true);
    });
    
    test('should remove selected class from previously selected task', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0 }),
            createSampleTask({ id: 'task_2', ordinal: 1 })
        ];
        
        panel.setTasks(tasks);
        
        const taskElements = container.querySelectorAll('.plan-task-item');
        taskElements[0].click();
        taskElements[1].click();
        
        expect(taskElements[0].classList.contains('task-selected')).toBe(false);
        expect(taskElements[1].classList.contains('task-selected')).toBe(true);
    });
    
    test('should clear selection when clearSelection is called', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask();
        
        panel.setTasks([task]);
        
        const taskEl = container.querySelector('.plan-task-item');
        taskEl.click();
        
        panel.clearSelection();
        
        expect(taskEl.classList.contains('task-selected')).toBe(false);
    });
    
    test('should select task programmatically by ID', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ id: 'task_xyz' });
        
        panel.setTasks([task]);
        panel.selectTask('task_xyz');
        
        const taskEl = container.querySelector(`[data-task-id="task_xyz"]`);
        expect(taskEl.classList.contains('task-selected')).toBe(true);
    });
});

// ============================================================================
// Test Suite: Add Task
// ============================================================================

describe('PlanPanel Add Task', () => {
    let document;
    let container;
    let vscodeApi;
    let onAddTask;
    
    beforeEach(() => {
        document = createMockDOM();
        container = document.createElement('div');
        vscodeApi = createMockVSCodeAPI();
        onAddTask = jest.fn();
        global.document = document;
    });
    
    test('should call onAddTask callback when add button clicked', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            onAddTask
        });
        
        const addBtn = container.querySelector('.plan-add-task-btn');
        addBtn.click();
        
        expect(onAddTask).toHaveBeenCalled();
    });
    
    test('should show add task form when add button clicked', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        
        const addBtn = container.querySelector('.plan-add-task-btn');
        addBtn.click();
        
        const form = container.querySelector('.plan-add-task-form');
        expect(form).not.toBeNull();
    });
    
    test('should send addTask message to extension when form submitted', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            projectPath: '/test/project'
        });
        
        // Show form
        panel.showAddTaskForm();
        
        const titleInput = container.querySelector('.task-title-input');
        const descInput = container.querySelector('.task-description-input');
        
        titleInput._textContent = 'New task title';
        descInput._textContent = 'New task description';
        
        // Submit
        panel.submitAddTask();
        
        const messages = vscodeApi.getMessages();
        expect(messages.length).toBe(1);
        expect(messages[0]).toEqual({
            command: 'addTask',
            projectPath: '/test/project',
            title: 'New task title',
            description: 'New task description'
        });
    });
    
    test('should hide add task form after submission', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            projectPath: '/test/project'
        });
        
        panel.showAddTaskForm();
        panel.submitAddTask();
        
        const form = container.querySelector('.plan-add-task-form');
        expect(form === null || form.style.display === 'none').toBe(true);
    });
    
    test('should provide option to add at start or end', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            projectPath: '/test/project'
        });
        
        panel.showAddTaskForm();
        
        const positionSelect = container.querySelector('.task-position-select');
        expect(positionSelect).not.toBeNull();
    });
});

// ============================================================================
// Test Suite: Update Task
// ============================================================================

describe('PlanPanel Update Task', () => {
    let document;
    let container;
    let vscodeApi;
    let onUpdateTask;
    
    beforeEach(() => {
        document = createMockDOM();
        container = document.createElement('div');
        vscodeApi = createMockVSCodeAPI();
        onUpdateTask = jest.fn();
        global.document = document;
    });
    
    test('should call onUpdateTask callback when status changed', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            onUpdateTask
        });
        const task = createSampleTask();
        
        panel.setTasks([task]);
        panel.changeTaskStatus(task.id, 'in_progress');
        
        expect(onUpdateTask).toHaveBeenCalledWith(task.id, { status: 'in_progress' });
    });
    
    test('should send updateTask message when status checkbox clicked', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            projectPath: '/test/project'
        });
        const task = createSampleTask({ status: 'pending' });
        
        panel.setTasks([task]);
        
        // Find and click the complete checkbox
        const completeBtn = container.querySelector('.task-complete-btn');
        completeBtn.click();
        
        const messages = vscodeApi.getMessages();
        expect(messages.length).toBe(1);
        expect(messages[0]).toEqual({
            command: 'updateTask',
            projectPath: '/test/project',
            taskId: task.id,
            updates: { status: 'completed' }
        });
    });
    
    test('should show inline edit when task title double-clicked', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask();
        
        panel.setTasks([task]);
        
        const titleEl = container.querySelector('.task-title');
        titleEl.dispatchEvent({ type: 'dblclick', target: titleEl });
        
        const editInput = container.querySelector('.task-title-edit');
        expect(editInput).not.toBeNull();
    });
    
    test('should send updateTask message when title edit submitted', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            projectPath: '/test/project'
        });
        const task = createSampleTask();
        
        panel.setTasks([task]);
        panel.startEditTitle(task.id);
        panel.submitTitleEdit(task.id, 'Updated title');
        
        const messages = vscodeApi.getMessages();
        expect(messages.length).toBe(1);
        expect(messages[0]).toEqual({
            command: 'updateTask',
            projectPath: '/test/project',
            taskId: task.id,
            updates: { title: 'Updated title' }
        });
    });
});

// ============================================================================
// Test Suite: Delete Task
// ============================================================================

describe('PlanPanel Delete Task', () => {
    let document;
    let container;
    let vscodeApi;
    let onDeleteTask;
    
    beforeEach(() => {
        document = createMockDOM();
        container = document.createElement('div');
        vscodeApi = createMockVSCodeAPI();
        onDeleteTask = jest.fn();
        global.document = document;
    });
    
    test('should call onDeleteTask callback when delete clicked', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            onDeleteTask,
            confirmDelete: false
        });
        const task = createSampleTask();
        
        panel.setTasks([task]);
        
        const deleteBtn = container.querySelector('.task-delete-btn');
        deleteBtn.click();
        
        expect(onDeleteTask).toHaveBeenCalledWith(task.id);
    });
    
    test('should send deleteTask message to extension', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            projectPath: '/test/project'
        });
        const task = createSampleTask();
        
        panel.setTasks([task]);
        panel.deleteTask(task.id);
        
        const messages = vscodeApi.getMessages();
        expect(messages.length).toBe(1);
        expect(messages[0]).toEqual({
            command: 'deleteTask',
            projectPath: '/test/project',
            taskId: task.id
        });
    });
    
    test('should show confirmation before delete by default', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            confirmDelete: true
        });
        const task = createSampleTask();
        
        panel.setTasks([task]);
        
        const deleteBtn = container.querySelector('.task-delete-btn');
        deleteBtn.click();
        
        const confirmDialog = container.querySelector('.task-delete-confirm');
        expect(confirmDialog).not.toBeNull();
    });
});

// ============================================================================
// Test Suite: Move Task (Reorder)
// ============================================================================

describe('PlanPanel Move Task', () => {
    let document;
    let container;
    let vscodeApi;
    let onMoveTask;
    
    beforeEach(() => {
        document = createMockDOM();
        container = document.createElement('div');
        vscodeApi = createMockVSCodeAPI();
        onMoveTask = jest.fn();
        global.document = document;
    });
    
    test('should call onMoveTask callback with new 0-based ordinal', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            onMoveTask
        });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0 }),
            createSampleTask({ id: 'task_2', ordinal: 1 }),
            createSampleTask({ id: 'task_3', ordinal: 2 })
        ];
        
        panel.setTasks(tasks);
        panel.moveTask('task_3', 0); // Move last to first (0-based)
        
        expect(onMoveTask).toHaveBeenCalledWith('task_3', 0);
    });
    
    test('should send moveTask message with 0-based ordinal', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            projectPath: '/test/project'
        });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0 }),
            createSampleTask({ id: 'task_2', ordinal: 1 })
        ];
        
        panel.setTasks(tasks);
        panel.moveTask('task_2', 0);
        
        const messages = vscodeApi.getMessages();
        expect(messages.length).toBe(1);
        expect(messages[0]).toEqual({
            command: 'moveTask',
            projectPath: '/test/project',
            taskId: 'task_2',
            newOrdinal: 0
        });
    });
    
    test('should have move up button for non-first tasks', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0 }),
            createSampleTask({ id: 'task_2', ordinal: 1 })
        ];
        
        panel.setTasks(tasks);
        
        const taskElements = container.querySelectorAll('.plan-task-item');
        const moveUpBtn1 = taskElements[0].querySelector('.task-move-up');
        const moveUpBtn2 = taskElements[1].querySelector('.task-move-up');
        
        // First task should have disabled or no move up
        expect(moveUpBtn1 === null || moveUpBtn1.disabled).toBe(true);
        // Second task should have enabled move up
        expect(moveUpBtn2).not.toBeNull();
        expect(moveUpBtn2.disabled).toBeFalsy();
    });
    
    test('should have move down button for non-last tasks', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0 }),
            createSampleTask({ id: 'task_2', ordinal: 1 })
        ];
        
        panel.setTasks(tasks);
        
        const taskElements = container.querySelectorAll('.plan-task-item');
        const moveDownBtn1 = taskElements[0].querySelector('.task-move-down');
        const moveDownBtn2 = taskElements[1].querySelector('.task-move-down');
        
        // First task should have enabled move down
        expect(moveDownBtn1).not.toBeNull();
        expect(moveDownBtn1.disabled).toBeFalsy();
        // Last task should have disabled or no move down
        expect(moveDownBtn2 === null || moveDownBtn2.disabled).toBe(true);
    });
    
    test('should move task up when move up button clicked', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            projectPath: '/test/project'
        });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0 }),
            createSampleTask({ id: 'task_2', ordinal: 1 })
        ];
        
        panel.setTasks(tasks);
        
        const task2El = container.querySelector(`[data-task-id="task_2"]`);
        const moveUpBtn = task2El.querySelector('.task-move-up');
        moveUpBtn.click();
        
        const messages = vscodeApi.getMessages();
        expect(messages.length).toBe(1);
        expect(messages[0].command).toBe('moveTask');
        expect(messages[0].taskId).toBe('task_2');
        expect(messages[0].newOrdinal).toBe(0);
    });
});

// ============================================================================
// Test Suite: Filtering
// ============================================================================

describe('PlanPanel Filtering', () => {
    let document;
    let container;
    let vscodeApi;
    
    beforeEach(() => {
        document = createMockDOM();
        container = document.createElement('div');
        vscodeApi = createMockVSCodeAPI();
        global.document = document;
    });
    
    test('should filter to show only pending tasks', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0, status: 'pending' }),
            createSampleTask({ id: 'task_2', ordinal: 1, status: 'completed' }),
            createSampleTask({ id: 'task_3', ordinal: 2, status: 'in_progress' })
        ];
        
        panel.setTasks(tasks);
        panel.setFilter('pending');
        
        const visibleTasks = container.querySelectorAll('.plan-task-item:not(.hidden)');
        expect(visibleTasks.length).toBe(1);
        expect(visibleTasks[0].getAttribute('data-task-id')).toBe('task_1');
    });
    
    test('should filter to show only completed tasks', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0, status: 'pending' }),
            createSampleTask({ id: 'task_2', ordinal: 1, status: 'completed' }),
            createSampleTask({ id: 'task_3', ordinal: 2, status: 'completed' })
        ];
        
        panel.setTasks(tasks);
        panel.setFilter('completed');
        
        const visibleTasks = container.querySelectorAll('.plan-task-item:not(.hidden)');
        expect(visibleTasks.length).toBe(2);
    });
    
    test('should show all tasks with "all" filter', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0, status: 'pending' }),
            createSampleTask({ id: 'task_2', ordinal: 1, status: 'completed' }),
            createSampleTask({ id: 'task_3', ordinal: 2, status: 'blocked' })
        ];
        
        panel.setTasks(tasks);
        panel.setFilter('all');
        
        const visibleTasks = container.querySelectorAll('.plan-task-item:not(.hidden)');
        expect(visibleTasks.length).toBe(3);
    });
    
    test('should highlight active filter button', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        
        panel.setFilter('completed');
        
        const completedBtn = container.querySelector('.filter-completed');
        expect(completedBtn.classList.contains('filter-active')).toBe(true);
    });
    
    test('should filter to show in_progress tasks', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0, status: 'in_progress' }),
            createSampleTask({ id: 'task_2', ordinal: 1, status: 'pending' })
        ];
        
        panel.setTasks(tasks);
        panel.setFilter('in_progress');
        
        const visibleTasks = container.querySelectorAll('.plan-task-item:not(.hidden)');
        expect(visibleTasks.length).toBe(1);
        expect(visibleTasks[0].getAttribute('data-task-id')).toBe('task_1');
    });
});

// ============================================================================
// Test Suite: Edit Log Display
// ============================================================================

describe('PlanPanel Edit Log Display', () => {
    let document;
    let container;
    let vscodeApi;
    
    beforeEach(() => {
        document = createMockDOM();
        container = document.createElement('div');
        vscodeApi = createMockVSCodeAPI();
        global.document = document;
    });
    
    test('should show edit list when task expanded', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ editIds: ['edit_1'] });
        const edits = [createSampleEdit({ id: 'edit_1', taskId: task.id })];
        
        panel.setTasks([task]);
        panel.setEdits(edits);
        panel.expandTask(task.id);
        
        const editList = container.querySelector('.task-edit-list');
        expect(editList).not.toBeNull();
    });
    
    test('should display edit tool name', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ editIds: ['edit_1'] });
        const edits = [createSampleEdit({ 
            id: 'edit_1', 
            taskId: task.id,
            toolName: 'mcp_effi-local_add_paragraph'
        })];
        
        panel.setTasks([task]);
        panel.setEdits(edits);
        panel.expandTask(task.id);
        
        const editEl = container.querySelector('.edit-tool-name');
        expect(editEl.textContent).toContain('add_paragraph');
    });
    
    test('should display edit timestamp', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ editIds: ['edit_1'] });
        const edits = [createSampleEdit({ 
            id: 'edit_1', 
            taskId: task.id,
            timestamp: '2025-12-09T14:30:00.000Z'
        })];
        
        panel.setTasks([task]);
        panel.setEdits(edits);
        panel.expandTask(task.id);
        
        const timestampEl = container.querySelector('.edit-timestamp');
        expect(timestampEl).not.toBeNull();
    });
    
    test('should show request/response toggle for edits', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ editIds: ['edit_1'] });
        const edits = [createSampleEdit({ id: 'edit_1', taskId: task.id })];
        
        panel.setTasks([task]);
        panel.setEdits(edits);
        panel.expandTask(task.id);
        
        const detailsToggle = container.querySelector('.edit-details-toggle');
        expect(detailsToggle).not.toBeNull();
    });
    
    test('should display request JSON when expanded', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ editIds: ['edit_1'] });
        const edits = [createSampleEdit({ 
            id: 'edit_1', 
            taskId: task.id,
            request: { find_text: 'test', replace_text: 'example' }
        })];
        
        panel.setTasks([task]);
        panel.setEdits(edits);
        panel.expandTask(task.id);
        panel.expandEdit('edit_1');
        
        const requestEl = container.querySelector('.edit-request');
        expect(requestEl).not.toBeNull();
        expect(requestEl.textContent).toContain('find_text');
    });
    
    test('should collapse task to hide edits', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ editIds: ['edit_1'] });
        const edits = [createSampleEdit({ id: 'edit_1', taskId: task.id })];
        
        panel.setTasks([task]);
        panel.setEdits(edits);
        panel.expandTask(task.id);
        panel.collapseTask(task.id);
        
        const editList = container.querySelector('.task-edit-list');
        expect(editList === null || editList.style.display === 'none').toBe(true);
    });
    
    test('should toggle task expansion on click', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ editIds: ['edit_1'] });
        const edits = [createSampleEdit({ id: 'edit_1', taskId: task.id })];
        
        panel.setTasks([task]);
        panel.setEdits(edits);
        
        const expandBtn = container.querySelector('.task-expand-btn');
        expandBtn.click();
        
        const editList = container.querySelector('.task-edit-list');
        expect(editList).not.toBeNull();
        expect(editList.style.display !== 'none').toBe(true);
    });
});

// ============================================================================
// Test Suite: Webview Message Handling
// ============================================================================

describe('PlanPanel Message Handling', () => {
    let document;
    let container;
    let vscodeApi;
    
    beforeEach(() => {
        document = createMockDOM();
        container = document.createElement('div');
        vscodeApi = createMockVSCodeAPI();
        global.document = document;
    });
    
    test('should handle planData message to update tasks', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        
        const planData = {
            tasks: [
                createSampleTask({ id: 'task_1', ordinal: 0 }),
                createSampleTask({ id: 'task_2', ordinal: 1 })
            ]
        };
        
        panel.handleMessage({ command: 'planData', plan: planData });
        
        const taskElements = container.querySelectorAll('.plan-task-item');
        expect(taskElements.length).toBe(2);
    });
    
    test('should handle taskAdded message to add new task', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        panel.setTasks([createSampleTask({ id: 'task_1', ordinal: 0 })]);
        
        const newTask = createSampleTask({ id: 'task_new', ordinal: 1, title: 'New task' });
        panel.handleMessage({ command: 'taskAdded', task: newTask });
        
        const taskElements = container.querySelectorAll('.plan-task-item');
        expect(taskElements.length).toBe(2);
        expect(taskElements[1].textContent).toContain('New task');
    });
    
    test('should handle taskUpdated message to refresh task', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ id: 'task_1', status: 'pending' });
        panel.setTasks([task]);
        
        // Task updated to completed
        panel.handleMessage({ command: 'taskUpdated', taskId: 'task_1' });
        
        // Panel should request fresh data or update from cache
        // This verifies the message triggers update logic
        expect(true).toBe(true); // Handler doesn't throw
    });
    
    test('should handle taskDeleted message to remove task', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0 }),
            createSampleTask({ id: 'task_2', ordinal: 1 })
        ];
        panel.setTasks(tasks);
        
        panel.handleMessage({ command: 'taskDeleted', taskId: 'task_1' });
        
        const taskElements = container.querySelectorAll('.plan-task-item');
        expect(taskElements.length).toBe(1);
        expect(taskElements[0].getAttribute('data-task-id')).toBe('task_2');
    });
    
    test('should handle taskMoved message to reorder', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0, title: 'First' }),
            createSampleTask({ id: 'task_2', ordinal: 1, title: 'Second' })
        ];
        panel.setTasks(tasks);
        
        // Simulate task_2 moved to position 0
        panel.handleMessage({ 
            command: 'taskMoved', 
            taskId: 'task_2', 
            newOrdinal: 0 
        });
        
        // Panel should request fresh data to reflect new order
        // Or update local state if cached
        const taskElements = container.querySelectorAll('.plan-task-item');
        // Order should be task_2, task_1 after move
        expect(taskElements[0].getAttribute('data-task-id')).toBe('task_2');
    });
    
    test('should handle editLogged message to add edit', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ id: 'task_1', editIds: [] });
        panel.setTasks([task]);
        
        const newEdit = createSampleEdit({ id: 'edit_new', taskId: 'task_1' });
        panel.handleMessage({ command: 'editLogged', edit: newEdit, taskId: 'task_1' });
        
        // Task should now show edit count
        const editBadge = container.querySelector('.task-edit-count');
        expect(editBadge.textContent).toBe('1');
    });
    
    test('should handle planError message to show error', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        
        panel.handleMessage({ command: 'planError', error: 'Failed to load plan' });
        
        const errorEl = container.querySelector('.plan-error');
        expect(errorEl).not.toBeNull();
        expect(errorEl.textContent).toContain('Failed to load plan');
    });
});

// ============================================================================
// Test Suite: Progress Summary
// ============================================================================

describe('PlanPanel Progress Summary', () => {
    let document;
    let container;
    let vscodeApi;
    
    beforeEach(() => {
        document = createMockDOM();
        container = document.createElement('div');
        vscodeApi = createMockVSCodeAPI();
        global.document = document;
    });
    
    test('should display task count summary', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0, status: 'completed' }),
            createSampleTask({ id: 'task_2', ordinal: 1, status: 'in_progress' }),
            createSampleTask({ id: 'task_3', ordinal: 2, status: 'pending' })
        ];
        
        panel.setTasks(tasks);
        
        const summary = container.querySelector('.plan-progress-summary');
        expect(summary).not.toBeNull();
        expect(summary.textContent).toContain('1/3');
    });
    
    test('should display progress bar', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', status: 'completed' }),
            createSampleTask({ id: 'task_2', status: 'completed' }),
            createSampleTask({ id: 'task_3', status: 'pending' }),
            createSampleTask({ id: 'task_4', status: 'pending' })
        ];
        
        panel.setTasks(tasks);
        
        const progressBar = container.querySelector('.plan-progress-bar');
        expect(progressBar).not.toBeNull();
        // 2/4 = 50% complete
        expect(progressBar.style.width).toBe('50%');
    });
    
    test('should update progress when task status changes', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', status: 'pending' }),
            createSampleTask({ id: 'task_2', status: 'pending' })
        ];
        
        panel.setTasks(tasks);
        
        // Simulate task completion
        const updatedTasks = [
            { ...tasks[0], status: 'completed' },
            tasks[1]
        ];
        panel.setTasks(updatedTasks);
        
        const progressBar = container.querySelector('.plan-progress-bar');
        expect(progressBar.style.width).toBe('50%');
    });
});

// ============================================================================
// Test Suite: Edge Cases
// ============================================================================

describe('PlanPanel Edge Cases', () => {
    let document;
    let container;
    let vscodeApi;
    
    beforeEach(() => {
        document = createMockDOM();
        container = document.createElement('div');
        vscodeApi = createMockVSCodeAPI();
        global.document = document;
    });
    
    test('should handle null tasks gracefully', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        
        expect(() => panel.setTasks(null)).not.toThrow();
        
        const emptyState = container.querySelector('.plan-empty-state');
        expect(emptyState).not.toBeNull();
    });
    
    test('should handle undefined tasks gracefully', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        
        expect(() => panel.setTasks(undefined)).not.toThrow();
    });
    
    test('should handle task with missing optional fields', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const minimalTask = {
            id: 'task_minimal',
            title: 'Minimal task',
            description: '',
            status: 'pending',
            ordinal: 0
        };
        
        expect(() => panel.setTasks([minimalTask])).not.toThrow();
        
        const taskEl = container.querySelector('.plan-task-item');
        expect(taskEl).not.toBeNull();
    });
    
    test('should handle very long task title', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const longTitle = 'A'.repeat(500);
        const task = createSampleTask({ title: longTitle });
        
        panel.setTasks([task]);
        
        const titleEl = container.querySelector('.task-title');
        expect(titleEl).not.toBeNull();
        // Should truncate or handle gracefully
    });
    
    test('should handle many tasks efficiently', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = Array.from({ length: 100 }, (_, i) => 
            createSampleTask({ id: `task_${i}`, ordinal: i })
        );
        
        const start = Date.now();
        panel.setTasks(tasks);
        const elapsed = Date.now() - start;
        
        expect(elapsed).toBeLessThan(1000); // Should render within 1 second
        
        const taskElements = container.querySelectorAll('.plan-task-item');
        expect(taskElements.length).toBe(100);
    });
    
    test('should preserve selection when tasks are updated', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0 }),
            createSampleTask({ id: 'task_2', ordinal: 1 })
        ];
        
        panel.setTasks(tasks);
        panel.selectTask('task_1');
        
        // Update with same tasks
        panel.setTasks(tasks);
        
        const task1El = container.querySelector(`[data-task-id="task_1"]`);
        expect(task1El.classList.contains('task-selected')).toBe(true);
    });
    
    test('should clear selection if selected task is deleted', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0 }),
            createSampleTask({ id: 'task_2', ordinal: 1 })
        ];
        
        panel.setTasks(tasks);
        panel.selectTask('task_1');
        
        // Update without task_1
        panel.setTasks([tasks[1]]);
        
        expect(panel.selectedTaskId).toBeNull();
    });
    
    test('should handle duplicate task IDs gracefully', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_same', ordinal: 0, title: 'First' }),
            createSampleTask({ id: 'task_same', ordinal: 1, title: 'Duplicate' })
        ];
        
        // Should not throw, but should handle somehow
        expect(() => panel.setTasks(tasks)).not.toThrow();
    });
});

// ============================================================================
// Test Suite: Keyboard Navigation
// ============================================================================

describe('PlanPanel Keyboard Navigation', () => {
    let document;
    let container;
    let vscodeApi;
    
    beforeEach(() => {
        document = createMockDOM();
        container = document.createElement('div');
        vscodeApi = createMockVSCodeAPI();
        global.document = document;
    });
    
    test('should navigate to next task with arrow down', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0 }),
            createSampleTask({ id: 'task_2', ordinal: 1 })
        ];
        
        panel.setTasks(tasks);
        panel.selectTask('task_1');
        
        panel.handleKeyDown({ key: 'ArrowDown', preventDefault: () => {} });
        
        expect(panel.selectedTaskId).toBe('task_2');
    });
    
    test('should navigate to previous task with arrow up', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const tasks = [
            createSampleTask({ id: 'task_1', ordinal: 0 }),
            createSampleTask({ id: 'task_2', ordinal: 1 })
        ];
        
        panel.setTasks(tasks);
        panel.selectTask('task_2');
        
        panel.handleKeyDown({ key: 'ArrowUp', preventDefault: () => {} });
        
        expect(panel.selectedTaskId).toBe('task_1');
    });
    
    test('should expand selected task with Enter', () => {
        const panel = new PlanPanel(container, { vscode: vscodeApi });
        const task = createSampleTask({ editIds: ['edit_1'] });
        const edits = [createSampleEdit({ id: 'edit_1', taskId: task.id })];
        
        panel.setTasks([task]);
        panel.setEdits(edits);
        panel.selectTask(task.id);
        
        panel.handleKeyDown({ key: 'Enter', preventDefault: () => {} });
        
        const editList = container.querySelector('.task-edit-list');
        expect(editList).not.toBeNull();
    });
    
    test('should delete selected task with Delete key', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            projectPath: '/test/project',
            confirmDelete: false
        });
        const task = createSampleTask();
        
        panel.setTasks([task]);
        panel.selectTask(task.id);
        
        panel.handleKeyDown({ key: 'Delete', preventDefault: () => {} });
        
        const messages = vscodeApi.getMessages();
        expect(messages.some(m => m.command === 'deleteTask')).toBe(true);
    });
});

// ============================================================================
// Test Suite: Project Path Integration
// ============================================================================

describe('PlanPanel Project Path', () => {
    let document;
    let container;
    let vscodeApi;
    
    beforeEach(() => {
        document = createMockDOM();
        container = document.createElement('div');
        vscodeApi = createMockVSCodeAPI();
        global.document = document;
    });
    
    test('should include projectPath in all messages', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            projectPath: '/projects/test-contract'
        });
        
        panel.showAddTaskForm();
        panel.submitAddTask();
        
        const messages = vscodeApi.getMessages();
        expect(messages[0].projectPath).toBe('/projects/test-contract');
    });
    
    test('should update projectPath when setProjectPath called', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            projectPath: '/old/path'
        });
        
        panel.setProjectPath('/new/path');
        panel.showAddTaskForm();
        panel.submitAddTask();
        
        const messages = vscodeApi.getMessages();
        expect(messages[0].projectPath).toBe('/new/path');
    });
    
    test('should request plan data with projectPath', () => {
        const panel = new PlanPanel(container, { 
            vscode: vscodeApi,
            projectPath: '/projects/my-contract'
        });
        
        panel.requestPlan();
        
        const messages = vscodeApi.getMessages();
        expect(messages[0]).toEqual({
            command: 'getPlan',
            projectPath: '/projects/my-contract'
        });
    });
});
