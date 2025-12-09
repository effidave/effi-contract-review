/**
 * PlanStorage - Persistence Layer for WorkPlan
 * 
 * Handles reading and writing:
 * - [project]/plans/current/plan.md - YAML frontmatter + markdown
 * - [project]/plans/current/plan.meta.json - Fast-load JSON state
 * - [project]/logs/edits.jsonl - Append-only edit log
 */

import * as fs from 'fs';
import * as path from 'path';
import { WorkPlan, Edit } from './workplan';

// ============================================================================
// PlanStorage Class
// ============================================================================

/**
 * Handles persistence of WorkPlan and Edit data to the filesystem
 */
export class PlanStorage {
    private readonly projectDir: string;
    private readonly plansDir: string;
    private readonly logsDir: string;

    constructor(projectDir: string) {
        this.projectDir = projectDir;
        this.plansDir = path.join(projectDir, 'plans', 'current');
        this.logsDir = path.join(projectDir, 'logs');
    }

    // ========================================================================
    // File Path Getters
    // ========================================================================

    /**
     * Path to the plan.md file
     */
    get planFilePath(): string {
        return path.join(this.plansDir, 'plan.md');
    }

    /**
     * Path to the plan.meta.json file
     */
    get planMetaFilePath(): string {
        return path.join(this.plansDir, 'plan.meta.json');
    }

    /**
     * Path to the edits.jsonl file
     */
    get editsFilePath(): string {
        return path.join(this.logsDir, 'edits.jsonl');
    }

    // ========================================================================
    // Directory Management
    // ========================================================================

    /**
     * Ensure all required directories exist
     */
    async ensureDirectories(): Promise<void> {
        await fs.promises.mkdir(this.plansDir, { recursive: true });
        await fs.promises.mkdir(this.logsDir, { recursive: true });
    }

    /**
     * Ensure the plan.md file exists, creating a blank one if not
     */
    async ensurePlanFile(): Promise<void> {
        await this.ensureDirectories();
        
        if (!fs.existsSync(this.planFilePath)) {
            const emptyPlan = new WorkPlan();
            const content = emptyPlan.toPlanFile();
            await fs.promises.writeFile(this.planFilePath, content, 'utf-8');
        }
    }

    // ========================================================================
    // Plan File (plan.md) Operations
    // ========================================================================

    /**
     * Save WorkPlan to plan.md
     */
    async savePlan(plan: WorkPlan): Promise<void> {
        await this.ensureDirectories();
        const content = plan.toPlanFile();
        await fs.promises.writeFile(this.planFilePath, content, 'utf-8');
    }

    /**
     * Load WorkPlan from plan.md
     * Returns null if file doesn't exist
     */
    async loadPlan(): Promise<WorkPlan | null> {
        if (!fs.existsSync(this.planFilePath)) {
            return null;
        }

        try {
            const content = await fs.promises.readFile(this.planFilePath, 'utf-8');
            if (!content.trim()) {
                return new WorkPlan();
            }
            return WorkPlan.fromPlanFile(content);
        } catch (error) {
            // Handle corrupted files gracefully
            console.error('Error loading plan.md:', error);
            return new WorkPlan();
        }
    }

    // ========================================================================
    // Meta File (plan.meta.json) Operations
    // ========================================================================

    /**
     * Save WorkPlan to plan.meta.json for fast loading
     */
    async savePlanMeta(plan: WorkPlan): Promise<void> {
        await this.ensureDirectories();
        const json = JSON.stringify(plan.toJSON(), null, 2);
        await fs.promises.writeFile(this.planMetaFilePath, json, 'utf-8');
    }

    /**
     * Load WorkPlan from plan.meta.json
     * Returns null if file doesn't exist or is corrupted
     */
    async loadPlanMeta(): Promise<WorkPlan | null> {
        if (!fs.existsSync(this.planMetaFilePath)) {
            return null;
        }

        try {
            const content = await fs.promises.readFile(this.planMetaFilePath, 'utf-8');
            const json = JSON.parse(content);
            return WorkPlan.fromJSON(json);
        } catch (error) {
            // Handle corrupted files gracefully
            console.error('Error loading plan.meta.json:', error);
            return null;
        }
    }

    // ========================================================================
    // Edit Log (edits.jsonl) Operations
    // ========================================================================

    /**
     * Append an Edit to the edits.jsonl log
     */
    async appendEdit(edit: Edit): Promise<void> {
        await this.ensureDirectories();
        const line = edit.toJSONL() + '\n';
        await fs.promises.appendFile(this.editsFilePath, line, 'utf-8');
    }

    /**
     * Load all edits from edits.jsonl
     * Returns empty array if file doesn't exist
     */
    async loadEdits(): Promise<Edit[]> {
        if (!fs.existsSync(this.editsFilePath)) {
            return [];
        }

        try {
            const content = await fs.promises.readFile(this.editsFilePath, 'utf-8');
            const lines = content.trim().split('\n').filter(line => line.trim());
            
            const edits: Edit[] = [];
            for (const line of lines) {
                try {
                    const json = JSON.parse(line);
                    edits.push(Edit.fromJSON(json));
                } catch (lineError) {
                    // Skip invalid lines
                    console.warn('Skipping invalid edit line:', line);
                }
            }
            return edits;
        } catch (error) {
            console.error('Error loading edits.jsonl:', error);
            return [];
        }
    }

    /**
     * Load edits for a specific task
     */
    async loadEditsForTask(taskId: string): Promise<Edit[]> {
        const allEdits = await this.loadEdits();
        return allEdits.filter(edit => edit.taskId === taskId);
    }

    /**
     * Get specific edits by their IDs, in the order requested
     */
    async getEditsByIds(ids: string[]): Promise<Edit[]> {
        const allEdits = await this.loadEdits();
        const editMap = new Map(allEdits.map(e => [e.id, e]));
        
        // Return in requested order, filtering out missing IDs
        return ids.map(id => editMap.get(id)).filter((e): e is Edit => e !== undefined);
    }

    /**
     * Get all edits from the log (alias for loadEdits for clarity)
     */
    async getAllEdits(): Promise<Edit[]> {
        return this.loadEdits();
    }

    /**
     * Get a single edit by ID
     * Returns null if not found
     */
    async getEditById(id: string): Promise<Edit | null> {
        const allEdits = await this.loadEdits();
        return allEdits.find(e => e.id === id) || null;
    }

    /**
     * Get edits that occurred after a given timestamp
     */
    async getNewEditsSince(cutoff: Date): Promise<Edit[]> {
        const allEdits = await this.loadEdits();
        return allEdits.filter(e => e.timestamp > cutoff);
    }

    /**
     * Get edits that have no task association (taskId is null)
     * These are edits logged by the MCP server that haven't been linked to a task yet
     */
    async getUnassociatedEdits(): Promise<Edit[]> {
        const allEdits = await this.loadEdits();
        return allEdits.filter(e => e.taskId === null || e.taskId === undefined);
    }

    /**
     * Get edits that affected a specific document
     * Matches by filename (case-insensitive, path-normalized)
     */
    async getEditsForDocument(filename: string): Promise<Edit[]> {
        const allEdits = await this.loadEdits();
        const normalizedTarget = this.normalizeFilename(filename);
        
        return allEdits.filter(e => {
            const editFilename = e.request.filename as string | undefined;
            if (!editFilename) return false;
            return this.normalizeFilename(editFilename) === normalizedTarget;
        });
    }

    /**
     * Normalize a filename for comparison (lowercase, forward slashes)
     */
    private normalizeFilename(filename: string): string {
        return filename.replace(/\\/g, '/').toLowerCase();
    }

    // ========================================================================
    // Combined Operations
    // ========================================================================

    /**
     * Save both plan.md and plan.meta.json
     */
    async saveAll(plan: WorkPlan): Promise<void> {
        await Promise.all([
            this.savePlan(plan),
            this.savePlanMeta(plan)
        ]);
    }

    /**
     * Load plan and all associated edits
     */
    async loadWithEdits(): Promise<{ plan: WorkPlan | null; edits: Edit[] }> {
        const [plan, edits] = await Promise.all([
            this.loadPlan(),
            this.loadEdits()
        ]);
        return { plan, edits };
    }

    /**
     * Get existing plan or create a new one
     */
    async getOrCreatePlan(): Promise<WorkPlan> {
        let plan = await this.loadPlan();
        
        if (!plan) {
            plan = new WorkPlan();
            await this.savePlan(plan);
        }
        
        return plan;
    }
}
