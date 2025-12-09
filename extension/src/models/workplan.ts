/**
 * WorkPlan, WorkTask, and Edit Classes
 * 
 * Object-oriented structure for managing work plans in the Effi Contract Viewer.
 * 
 * - Edit: Records MCP tool calls with request/response
 * - WorkTask: Individual task with title, description, status, edits
 * - WorkPlan: Manages collection of WorkTasks with ordering and persistence
 */

import * as crypto from 'crypto';

// ============================================================================
// Types
// ============================================================================

export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'blocked';

export interface EditData {
    id?: string;
    taskId: string;
    toolName: string;
    request: Record<string, unknown>;
    response: Record<string, unknown>;
    timestamp?: Date;
}

export interface EditJSON {
    id: string;
    taskId: string;
    toolName: string;
    request: Record<string, unknown>;
    response: Record<string, unknown>;
    timestamp: string;
}

export interface WorkTaskData {
    id?: string;
    title: string;
    description: string;
    status?: TaskStatus;
    ordinal?: number;
    creationDate?: Date;
    completionDate?: Date | null;
    editIds?: string[];
}

export interface WorkTaskJSON {
    id: string;
    title: string;
    description: string;
    status: TaskStatus;
    ordinal: number;
    creationDate: string;
    completionDate: string | null;
    editIds: string[];
}

export interface WorkPlanJSON {
    tasks: WorkTaskJSON[];
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Generate an 8-character hex hash ID
 */
function generateId(): string {
    const bytes = crypto.randomBytes(4);
    return bytes.toString('hex');
}

/**
 * Parse YAML frontmatter from markdown content
 */
function parseYAMLFrontmatter(content: string): { frontmatter: Record<string, unknown>; body: string } {
    const match = content.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
    if (!match) {
        return { frontmatter: {}, body: content };
    }
    
    const yamlContent = match[1];
    const body = match[2];
    
    // Simple YAML parser for our specific structure
    const frontmatter = parseSimpleYAML(yamlContent);
    
    return { frontmatter, body };
}

/**
 * Simple YAML parser for our specific task structure
 */
function parseSimpleYAML(yaml: string): Record<string, unknown> {
    const result: Record<string, unknown> = {};
    const lines = yaml.split('\n');
    
    let currentKey = '';
    let currentArray: Record<string, unknown>[] = [];
    let currentObject: Record<string, unknown> = {};
    let inArray = false;
    let inObject = false;
    let inNestedArray = false;
    let nestedArrayKey = '';
    let nestedArray: string[] = [];
    
    for (const line of lines) {
        // Skip empty lines
        if (line.trim() === '') continue;
        
        // Top-level key with array indicator
        const topLevelArrayMatch = line.match(/^(\w+):$/);
        if (topLevelArrayMatch) {
            // Save previous array if exists
            if (inArray && currentKey) {
                if (Object.keys(currentObject).length > 0) {
                    currentArray.push(currentObject);
                }
                result[currentKey] = currentArray;
            }
            currentKey = topLevelArrayMatch[1];
            currentArray = [];
            currentObject = {};
            inArray = true;
            inObject = false;
            continue;
        }
        
        // Array item start
        const arrayItemMatch = line.match(/^  - (\w+): (.*)$/);
        if (arrayItemMatch && inArray) {
            // Save previous object if exists
            if (Object.keys(currentObject).length > 0) {
                currentArray.push(currentObject);
            }
            currentObject = {};
            inObject = true;
            inNestedArray = false;
            
            const key = arrayItemMatch[1];
            const value = parseYAMLValue(arrayItemMatch[2].trim());
            currentObject[key] = value;
            continue;
        }
        
        // Nested array start
        const nestedArrayStartMatch = line.match(/^    (\w+):$/);
        if (nestedArrayStartMatch && inObject) {
            nestedArrayKey = nestedArrayStartMatch[1];
            nestedArray = [];
            inNestedArray = true;
            continue;
        }
        
        // Nested array item
        const nestedArrayItemMatch = line.match(/^      - (.*)$/);
        if (nestedArrayItemMatch && inNestedArray) {
            nestedArray.push(parseYAMLValue(nestedArrayItemMatch[1].trim()) as string);
            continue;
        }
        
        // Object property continuation
        const objectPropMatch = line.match(/^    (\w+): (.*)$/);
        if (objectPropMatch && inObject) {
            // Save nested array if we were building one
            if (inNestedArray && nestedArrayKey) {
                currentObject[nestedArrayKey] = nestedArray;
                inNestedArray = false;
                nestedArrayKey = '';
                nestedArray = [];
            }
            
            const key = objectPropMatch[1];
            const value = parseYAMLValue(objectPropMatch[2].trim());
            currentObject[key] = value;
            continue;
        }
    }
    
    // Save final object and array
    if (inNestedArray && nestedArrayKey) {
        currentObject[nestedArrayKey] = nestedArray;
    }
    if (Object.keys(currentObject).length > 0) {
        currentArray.push(currentObject);
    }
    if (currentKey && currentArray.length > 0) {
        result[currentKey] = currentArray;
    }
    
    return result;
}

/**
 * Parse a YAML value string to appropriate type
 */
function parseYAMLValue(value: string): string | number | boolean | null | string[] {
    // Handle quoted strings
    if ((value.startsWith("'") && value.endsWith("'")) || 
        (value.startsWith('"') && value.endsWith('"'))) {
        return value.slice(1, -1);
    }
    
    // Handle null
    if (value === 'null' || value === '~') {
        return null;
    }
    
    // Handle boolean
    if (value === 'true') return true;
    if (value === 'false') return false;
    
    // Handle empty array
    if (value === '[]') return [];
    
    // Handle numbers
    if (/^-?\d+$/.test(value)) {
        return parseInt(value, 10);
    }
    if (/^-?\d+\.\d+$/.test(value)) {
        return parseFloat(value);
    }
    
    return value;
}

/**
 * Convert value to YAML string representation
 */
function toYAMLValue(value: unknown): string {
    if (value === null) return 'null';
    if (typeof value === 'boolean') return value.toString();
    if (typeof value === 'number') return value.toString();
    if (typeof value === 'string') {
        // Quote strings that could be interpreted as other types
        if (value === 'null' || value === 'true' || value === 'false' || 
            /^-?\d+(\.\d+)?$/.test(value) || value.includes(':') || value.includes('#')) {
            return `'${value}'`;
        }
        return value;
    }
    if (Array.isArray(value) && value.length === 0) return '[]';
    return String(value);
}

// ============================================================================
// Edit Class
// ============================================================================

/**
 * Records an MCP tool call with request and response details
 */
export class Edit {
    public readonly id: string;
    public readonly taskId: string;
    public readonly toolName: string;
    public readonly request: Record<string, unknown>;
    public readonly response: Record<string, unknown>;
    public readonly timestamp: Date;

    constructor(data: EditData) {
        this.id = data.id || generateId();
        this.taskId = data.taskId;
        this.toolName = data.toolName;
        this.request = data.request;
        this.response = data.response;
        this.timestamp = data.timestamp || new Date();
    }

    /**
     * Serialize to JSON object
     */
    toJSON(): EditJSON {
        return {
            id: this.id,
            taskId: this.taskId,
            toolName: this.toolName,
            request: this.request,
            response: this.response,
            timestamp: this.timestamp.toISOString()
        };
    }

    /**
     * Deserialize from JSON object
     */
    static fromJSON(json: EditJSON): Edit {
        return new Edit({
            id: json.id,
            taskId: json.taskId,
            toolName: json.toolName,
            request: json.request,
            response: json.response,
            timestamp: new Date(json.timestamp)
        });
    }

    /**
     * Serialize to JSONL format (single line)
     */
    toJSONL(): string {
        return JSON.stringify(this.toJSON());
    }
}

// ============================================================================
// WorkTask Class
// ============================================================================

/**
 * Represents a single task in the work plan
 */
export class WorkTask {
    public readonly id: string;
    public title: string;
    public description: string;
    public status: TaskStatus;
    public ordinal: number;
    public readonly creationDate: Date;
    public completionDate: Date | null;
    public editIds: string[];

    constructor(data: WorkTaskData) {
        this.id = data.id || generateId();
        this.title = data.title;
        this.description = data.description;
        this.status = data.status || 'pending';
        this.ordinal = data.ordinal || 0;
        this.creationDate = data.creationDate || new Date();
        this.completionDate = data.completionDate || null;
        this.editIds = data.editIds || [];
    }

    /**
     * Start working on this task
     */
    start(): void {
        this.status = 'in_progress';
    }

    /**
     * Mark task as completed
     */
    complete(): void {
        this.status = 'completed';
        this.completionDate = new Date();
    }

    /**
     * Mark task as blocked
     */
    block(): void {
        this.status = 'blocked';
    }

    /**
     * Reset task to pending
     */
    reset(): void {
        this.status = 'pending';
        this.completionDate = null;
    }

    /**
     * Check if task is open (not completed)
     */
    isOpen(): boolean {
        return this.status !== 'completed';
    }

    /**
     * Add an edit ID to this task
     */
    addEditId(editId: string): void {
        if (!this.editIds.includes(editId)) {
            this.editIds.push(editId);
        }
    }

    /**
     * Serialize to JSON object
     */
    toJSON(): WorkTaskJSON {
        return {
            id: this.id,
            title: this.title,
            description: this.description,
            status: this.status,
            ordinal: this.ordinal,
            creationDate: this.creationDate.toISOString(),
            completionDate: this.completionDate ? this.completionDate.toISOString() : null,
            editIds: [...this.editIds]
        };
    }

    /**
     * Deserialize from JSON object
     */
    static fromJSON(json: WorkTaskJSON): WorkTask {
        return new WorkTask({
            id: json.id,
            title: json.title,
            description: json.description,
            status: json.status,
            ordinal: json.ordinal,
            creationDate: new Date(json.creationDate),
            completionDate: json.completionDate ? new Date(json.completionDate) : null,
            editIds: [...json.editIds]
        });
    }

    /**
     * Serialize to YAML-friendly object
     */
    toYAML(): Record<string, unknown> {
        return {
            id: this.id,
            title: this.title,
            description: this.description,
            status: this.status,
            ordinal: this.ordinal,
            creationDate: this.creationDate.toISOString(),
            completionDate: this.completionDate ? this.completionDate.toISOString() : null,
            editIds: [...this.editIds]
        };
    }
}

// ============================================================================
// WorkPlan Class
// ============================================================================

/**
 * Manages a collection of WorkTasks with ordering and persistence
 */
export class WorkPlan {
    public tasks: WorkTask[];
    private _edits: Edit[];

    constructor(tasks: WorkTask[] = []) {
        this.tasks = [...tasks];
        this._edits = [];
        this.renumberTasks();
    }

    /**
     * Get all edits
     */
    get edits(): Edit[] {
        return [...this._edits];
    }

    /**
     * Get the number of tasks
     */
    getTaskCount(): number {
        return this.tasks.length;
    }

    /**
     * Renumber all tasks based on their position in the array
     */
    private renumberTasks(): void {
        this.tasks.forEach((task, index) => {
            task.ordinal = index;
        });
    }

    /**
     * Add a task at the end of the list
     */
    addTaskAtEnd(task: WorkTask): void {
        task.ordinal = this.tasks.length;
        this.tasks.push(task);
    }

    /**
     * Add a task at the start of the list
     */
    addTaskAtStart(task: WorkTask): void {
        this.tasks.unshift(task);
        this.renumberTasks();
    }

    /**
     * Add a task at a specific ordinal position (0-based)
     * ordinal 0 = first position, ordinal 1 = second position, etc.
     */
    addTaskAtOrdinal(task: WorkTask, ordinal: number): void {
        // Clamp ordinal to valid range (0-based)
        const insertIndex = Math.min(Math.max(0, ordinal), this.tasks.length);
        this.tasks.splice(insertIndex, 0, task);
        this.renumberTasks();
    }

    /**
     * Remove a task by ID
     */
    removeTask(id: string): boolean {
        const index = this.tasks.findIndex(t => t.id === id);
        if (index === -1) {
            return false;
        }
        this.tasks.splice(index, 1);
        this.renumberTasks();
        return true;
    }

    /**
     * Move a task to a new ordinal position (0-based)
     * ordinal 0 = first position, ordinal 1 = second position, etc.
     */
    moveTask(id: string, newOrdinal: number): boolean {
        const currentIndex = this.tasks.findIndex(t => t.id === id);
        if (currentIndex === -1) {
            return false;
        }
        
        const [task] = this.tasks.splice(currentIndex, 1);
        // Clamp ordinal to valid range (0-based)
        const insertIndex = Math.min(Math.max(0, newOrdinal), this.tasks.length);
        this.tasks.splice(insertIndex, 0, task);
        this.renumberTasks();
        return true;
    }

    /**
     * Get a task by ID
     */
    getTaskById(id: string): WorkTask | undefined {
        return this.tasks.find(t => t.id === id);
    }

    /**
     * Get all open tasks (pending, in_progress, blocked)
     */
    getOpenTasks(): WorkTask[] {
        return this.tasks.filter(t => t.isOpen());
    }

    /**
     * Get all completed tasks
     */
    getCompletedTasks(): WorkTask[] {
        return this.tasks.filter(t => t.status === 'completed');
    }

    /**
     * Get tasks by status
     */
    getTasksByStatus(status: TaskStatus): WorkTask[] {
        return this.tasks.filter(t => t.status === status);
    }

    /**
     * Log an edit and associate it with its task
     */
    logEdit(edit: Edit): void {
        this._edits.push(edit);
        const task = this.getTaskById(edit.taskId);
        if (task) {
            task.addEditId(edit.id);
        }
    }

    /**
     * Get all edits for a specific task
     */
    getEditsForTask(taskId: string): Edit[] {
        return this._edits.filter(e => e.taskId === taskId);
    }

    /**
     * Generate JSONL content for all edits
     */
    editsToJSONL(): string {
        return this._edits.map(e => e.toJSONL()).join('\n');
    }

    /**
     * Serialize to JSON object
     */
    toJSON(): WorkPlanJSON {
        return {
            tasks: this.tasks.map(t => t.toJSON())
        };
    }

    /**
     * Deserialize from JSON object
     */
    static fromJSON(json: WorkPlanJSON): WorkPlan {
        const tasks = json.tasks.map(t => WorkTask.fromJSON(t));
        return new WorkPlan(tasks);
    }

    /**
     * Generate YAML frontmatter string
     */
    toYAMLFrontmatter(): string {
        const lines: string[] = ['---', 'tasks:'];
        
        for (const task of this.tasks) {
            lines.push(`  - id: ${toYAMLValue(task.id)}`);
            lines.push(`    title: ${toYAMLValue(task.title)}`);
            lines.push(`    description: ${toYAMLValue(task.description)}`);
            lines.push(`    status: ${toYAMLValue(task.status)}`);
            lines.push(`    ordinal: ${toYAMLValue(task.ordinal)}`);
            lines.push(`    creationDate: '${task.creationDate.toISOString()}'`);
            lines.push(`    completionDate: ${task.completionDate ? `'${task.completionDate.toISOString()}'` : 'null'}`);
            if (task.editIds.length === 0) {
                lines.push(`    editIds: []`);
            } else {
                lines.push(`    editIds:`);
                for (const editId of task.editIds) {
                    lines.push(`      - ${toYAMLValue(editId)}`);
                }
            }
        }
        
        lines.push('---');
        return lines.join('\n');
    }

    /**
     * Parse YAML frontmatter and create WorkPlan
     */
    static fromYAMLFrontmatter(content: string): WorkPlan {
        const { frontmatter } = parseYAMLFrontmatter(content);
        
        if (!frontmatter.tasks || !Array.isArray(frontmatter.tasks)) {
            return new WorkPlan();
        }
        
        const tasks = (frontmatter.tasks as Record<string, unknown>[]).map(t => {
            return new WorkTask({
                id: t.id as string,
                title: t.title as string,
                description: t.description as string,
                status: t.status as TaskStatus,
                ordinal: t.ordinal as number,
                creationDate: new Date(t.creationDate as string),
                completionDate: t.completionDate ? new Date(t.completionDate as string) : null,
                editIds: (t.editIds as string[]) || []
            });
        });
        
        return new WorkPlan(tasks);
    }

    /**
     * Generate human-readable markdown body
     */
    toMarkdown(): string {
        const lines: string[] = ['# Work Plan', ''];
        
        for (const task of this.tasks) {
            lines.push(`## ${task.ordinal + 1}. ${task.title}`);
            lines.push(`Status: ${task.status}`);
            lines.push('');
            lines.push(task.description);
            lines.push('');
        }
        
        return lines.join('\n');
    }

    /**
     * Generate complete plan.md file content (frontmatter + markdown)
     */
    toPlanFile(): string {
        return this.toYAMLFrontmatter() + '\n\n' + this.toMarkdown();
    }

    /**
     * Parse complete plan.md file content
     */
    static fromPlanFile(content: string): WorkPlan {
        return WorkPlan.fromYAMLFrontmatter(content);
    }
}
