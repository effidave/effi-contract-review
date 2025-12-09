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
    documents?: LegalDocumentJSON[];
}

export interface LegalDocumentData {
    id?: string;
    filename: string;
    displayName?: string;
    addedDate?: Date;
}

export interface LegalDocumentJSON {
    id: string;
    filename: string;
    displayName: string;
    addedDate: string;
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
    // Normalize line endings to \n
    const normalized = content.replace(/\r\n/g, '\n');
    const match = normalized.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
    if (!match) {
        console.log('parseYAMLFrontmatter: No frontmatter match found');
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
 * Handles multi-line string values (folded style)
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
    
    // Track multi-line value building
    let lastPropertyKey = '';
    let lastPropertyIndent = 0;
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // Skip empty lines
        if (line.trim() === '') continue;
        
        // Check if this is a continuation line (more indented than the property)
        const lineIndent = line.match(/^(\s*)/)?.[1].length || 0;
        if (lastPropertyKey && lineIndent > lastPropertyIndent && inObject) {
            // This is a continuation of the previous value
            const continuation = line.trim();
            if (currentObject[lastPropertyKey] !== undefined) {
                const existing = currentObject[lastPropertyKey];
                if (typeof existing === 'string') {
                    currentObject[lastPropertyKey] = existing + ' ' + continuation;
                }
            }
            continue;
        }
        
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
            lastPropertyKey = '';
            continue;
        }
        
        // Array item start (handles both "- key: value" and "  - key: value")
        const arrayItemMatch = line.match(/^([ ]{0,2})- (\w+): (.*)$/);
        if (arrayItemMatch && inArray) {
            // Save previous object if exists
            if (Object.keys(currentObject).length > 0) {
                currentArray.push(currentObject);
            }
            currentObject = {};
            inObject = true;
            inNestedArray = false;
            
            const key = arrayItemMatch[2];
            const value = parseYAMLValue(arrayItemMatch[3].trim());
            currentObject[key] = value;
            lastPropertyKey = key;
            lastPropertyIndent = (arrayItemMatch[1].length || 0) + 2; // "- " adds 2
            continue;
        }
        
        // Nested array start (handles "  key:" or "    key:")
        const nestedArrayStartMatch = line.match(/^[ ]{2,4}(\w+):$/);
        if (nestedArrayStartMatch && inObject) {
            nestedArrayKey = nestedArrayStartMatch[1];
            nestedArray = [];
            inNestedArray = true;
            lastPropertyKey = '';
            continue;
        }
        
        // Nested array item (handles "    - value" or "      - value")
        const nestedArrayItemMatch = line.match(/^[ ]{4,6}- (.*)$/);
        if (nestedArrayItemMatch && inNestedArray) {
            nestedArray.push(parseYAMLValue(nestedArrayItemMatch[1].trim()) as string);
            continue;
        }
        
        // Object property continuation (handles "  key: value" or "    key: value")
        const objectPropMatch = line.match(/^([ ]{2,4})(\w+): (.*)$/);
        if (objectPropMatch && inObject) {
            // Save nested array if we were building one
            if (inNestedArray && nestedArrayKey) {
                currentObject[nestedArrayKey] = nestedArray;
                inNestedArray = false;
                nestedArrayKey = '';
                nestedArray = [];
            }
            
            const key = objectPropMatch[2];
            const value = parseYAMLValue(objectPropMatch[3].trim());
            currentObject[key] = value;
            lastPropertyKey = key;
            lastPropertyIndent = objectPropMatch[1].length;
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

/**
 * Extract the filename from a path (handles both Windows and Unix paths)
 */
function extractFilenameFromPath(filepath: string): string {
    // Normalize to forward slashes
    const normalized = filepath.replace(/\\/g, '/');
    const parts = normalized.split('/');
    return parts[parts.length - 1] || filepath;
}

/**
 * Normalize a file path for comparison (lowercase, forward slashes)
 */
function normalizePathForComparison(filepath: string): string {
    return filepath.replace(/\\/g, '/').toLowerCase();
}

// ============================================================================
// LegalDocument Class
// ============================================================================

/**
 * Represents a legal document that a WorkPlan relates to.
 * Lightweight reference with tracking information.
 */
export class LegalDocument {
    public readonly id: string;
    public readonly filename: string;
    public displayName: string;
    public readonly addedDate: Date;

    constructor(data: LegalDocumentData) {
        this.id = data.id || generateId();
        this.filename = data.filename;
        this.displayName = data.displayName || extractFilenameFromPath(data.filename);
        this.addedDate = data.addedDate || new Date();
    }

    /**
     * Check if this document matches a given filename (case-insensitive, path-normalized)
     */
    matchesFilename(filename: string): boolean {
        return normalizePathForComparison(this.filename) === normalizePathForComparison(filename);
    }

    /**
     * Serialize to JSON object
     */
    toJSON(): LegalDocumentJSON {
        return {
            id: this.id,
            filename: this.filename,
            displayName: this.displayName,
            addedDate: this.addedDate.toISOString()
        };
    }

    /**
     * Deserialize from JSON object
     */
    static fromJSON(json: LegalDocumentJSON): LegalDocument {
        return new LegalDocument({
            id: json.id,
            filename: json.filename,
            displayName: json.displayName,
            addedDate: new Date(json.addedDate)
        });
    }

    /**
     * Serialize to YAML-friendly object
     */
    toYAML(): Record<string, unknown> {
        return {
            id: this.id,
            filename: this.filename,
            displayName: this.displayName,
            addedDate: this.addedDate.toISOString()
        };
    }
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
    public documents: LegalDocument[];
    private _edits: Edit[];

    constructor(tasks: WorkTask[] = [], documents: LegalDocument[] = []) {
        this.tasks = [...tasks];
        this.documents = [...documents];
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
     * Get the number of documents
     */
    getDocumentCount(): number {
        return this.documents.length;
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

    // ========================================================================
    // Document Management
    // ========================================================================

    /**
     * Add a document to the plan (no duplicates by filename)
     */
    addDocument(doc: LegalDocument): void {
        if (!this.hasDocument(doc.filename)) {
            this.documents.push(doc);
        }
    }

    /**
     * Remove a document by ID
     */
    removeDocument(id: string): boolean {
        const index = this.documents.findIndex(d => d.id === id);
        if (index === -1) {
            return false;
        }
        this.documents.splice(index, 1);
        return true;
    }

    /**
     * Get a document by ID
     */
    getDocumentById(id: string): LegalDocument | undefined {
        return this.documents.find(d => d.id === id);
    }

    /**
     * Get a document by filename
     */
    getDocumentByFilename(filename: string): LegalDocument | undefined {
        return this.documents.find(d => d.matchesFilename(filename));
    }

    /**
     * Check if a document with the given filename exists
     */
    hasDocument(filename: string): boolean {
        return this.documents.some(d => d.matchesFilename(filename));
    }

    /**
     * Get all edits that affect a specific document
     */
    getEditsForDocument(filename: string): Edit[] {
        return this._edits.filter(e => {
            const editFilename = e.request.filename as string | undefined;
            if (!editFilename) return false;
            // Normalize for comparison
            return editFilename.replace(/\\/g, '/').toLowerCase() === 
                   filename.replace(/\\/g, '/').toLowerCase();
        });
    }

    /**
     * Get all edits that affect any of the plan's documents
     */
    getDocumentEdits(): Edit[] {
        if (this.documents.length === 0) {
            return [];
        }
        return this._edits.filter(e => {
            const editFilename = e.request.filename as string | undefined;
            if (!editFilename) return false;
            return this.hasDocument(editFilename);
        });
    }

    // ========================================================================
    // Edit Management
    // ========================================================================

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
            tasks: this.tasks.map(t => t.toJSON()),
            documents: this.documents.map(d => d.toJSON())
        };
    }

    /**
     * Deserialize from JSON object
     */
    static fromJSON(json: WorkPlanJSON): WorkPlan {
        const tasks = json.tasks.map(t => WorkTask.fromJSON(t));
        const documents = (json.documents || []).map(d => LegalDocument.fromJSON(d));
        return new WorkPlan(tasks, documents);
    }

    /**
     * Generate YAML frontmatter string
     */
    toYAMLFrontmatter(): string {
        const lines: string[] = ['---'];
        
        // Documents section
        if (this.documents.length > 0) {
            lines.push('documents:');
            for (const doc of this.documents) {
                lines.push(`  - id: ${toYAMLValue(doc.id)}`);
                lines.push(`    filename: ${toYAMLValue(doc.filename)}`);
                lines.push(`    displayName: ${toYAMLValue(doc.displayName)}`);
                lines.push(`    addedDate: '${doc.addedDate.toISOString()}'`);
            }
        }
        
        // Tasks section
        lines.push('tasks:');
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
        
        // Parse documents
        const documents: LegalDocument[] = [];
        if (frontmatter.documents && Array.isArray(frontmatter.documents)) {
            for (const d of frontmatter.documents as Record<string, unknown>[]) {
                documents.push(new LegalDocument({
                    id: d.id as string,
                    filename: d.filename as string,
                    displayName: d.displayName as string,
                    addedDate: new Date(d.addedDate as string)
                }));
            }
        }
        
        // Parse tasks
        if (!frontmatter.tasks || !Array.isArray(frontmatter.tasks)) {
            return new WorkPlan([], documents);
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
        
        return new WorkPlan(tasks, documents);
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
