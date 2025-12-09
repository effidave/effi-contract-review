/**
 * PlanProvider - Manages work plan operations for the VS Code extension
 * 
 * Bridges between PlanStorage (file I/O) and webview communication.
 * Provides high-level operations for plan management with caching and persistence.
 */

import { WorkPlan, WorkTask, Edit, TaskStatus, WorkTaskData, EditData } from './workplan';
import { PlanStorage } from './planStorage';

// ============================================================================
// Types
// ============================================================================

export interface TaskUpdateOptions {
    title?: string;
    description?: string;
    status?: TaskStatus;
}

export interface AddTaskOptions {
    position?: 'start' | 'end';
    ordinal?: number;
}

export interface OperationResult {
    success: boolean;
    error?: string;
}

export interface AddTaskResult extends OperationResult {
    task?: WorkTask;
}

export interface UpdateTaskResult extends OperationResult {
    taskId?: string;
}

export interface DeleteTaskResult extends OperationResult {
    taskId?: string;
}

export interface LogEditResult extends OperationResult {
    edit?: Edit;
    editId?: string;
    taskId?: string;
}

export interface WebviewPlanData {
    tasks: WebviewTaskData[];
}

export interface WebviewTaskData {
    id: string;
    title: string;
    description: string;
    status: TaskStatus;
    ordinal: number;
    creationDate: string;
    completionDate: string | null;
    editIds: string[];
}

// ============================================================================
// PlanProvider Class
// ============================================================================

export class PlanProvider {
    public readonly planStorage: PlanStorage;
    public currentPlan: WorkPlan | null = null;
    private readonly projectPath: string;
    private initialized = false;

    constructor(projectPath: string) {
        if (!projectPath || projectPath.trim() === '') {
            throw new Error('Project path is required');
        }
        this.projectPath = projectPath;
        this.planStorage = new PlanStorage(projectPath);
    }

    /**
     * Initialize the provider - creates necessary directories
     */
    async initialize(): Promise<void> {
        if (this.initialized) {
            return;
        }
        await this.planStorage.ensureDirectories();
        this.initialized = true;
    }

    /**
     * Get the current plan, loading from disk if needed
     */
    async getPlan(): Promise<WorkPlan> {
        if (this.currentPlan) {
            return this.currentPlan;
        }

        try {
            // Try to load plan with edits
            const { plan, edits } = await this.planStorage.loadWithEdits();
            if (plan) {
                // Log the edits into the plan
                for (const edit of edits) {
                    plan.logEdit(edit);
                }
                this.currentPlan = plan;
                return plan;
            }
        } catch (error) {
            // If loading fails, return empty plan
            console.error('Failed to load plan:', error);
        }

        // Create and return empty plan
        this.currentPlan = new WorkPlan();
        return this.currentPlan;
    }

    /**
     * Save the plan to disk
     */
    async savePlan(plan: WorkPlan): Promise<OperationResult> {
        try {
            await this.planStorage.saveAll(plan);
            this.currentPlan = plan;
            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }

    /**
     * Add a new task to the plan
     */
    async addTask(
        title: string,
        description: string,
        options: AddTaskOptions = {}
    ): Promise<AddTaskResult> {
        try {
            if (!this.currentPlan) {
                await this.getPlan();
            }

            const task = new WorkTask({ title, description });

            if (options.position === 'start') {
                this.currentPlan!.addTaskAtStart(task);
            } else if (options.ordinal !== undefined) {
                this.currentPlan!.addTaskAtOrdinal(task, options.ordinal);
            } else {
                this.currentPlan!.addTaskAtEnd(task);
            }

            await this.planStorage.savePlan(this.currentPlan!);

            return { success: true, task };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }

    /**
     * Update an existing task
     */
    async updateTask(
        taskId: string,
        updates: TaskUpdateOptions
    ): Promise<UpdateTaskResult> {
        try {
            if (!this.currentPlan) {
                await this.getPlan();
            }

            const task = this.currentPlan!.getTaskById(taskId);
            if (!task) {
                return { success: false, error: 'Task not found', taskId };
            }

            // Apply updates
            if (updates.title !== undefined) {
                task.title = updates.title;
            }
            if (updates.description !== undefined) {
                task.description = updates.description;
            }
            if (updates.status !== undefined) {
                task.status = updates.status;
                if (updates.status === 'completed' && !task.completionDate) {
                    task.completionDate = new Date();
                }
            }

            await this.planStorage.savePlan(this.currentPlan!);

            return { success: true, taskId };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error),
                taskId
            };
        }
    }

    /**
     * Delete a task from the plan
     */
    async deleteTask(taskId: string): Promise<DeleteTaskResult> {
        try {
            if (!this.currentPlan) {
                await this.getPlan();
            }

            const removed = this.currentPlan!.removeTask(taskId);
            if (!removed) {
                return { success: false, error: 'Task not found', taskId };
            }

            await this.planStorage.savePlan(this.currentPlan!);

            return { success: true, taskId };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error),
                taskId
            };
        }
    }

    /**
     * Move a task to a new position
     */
    async moveTask(taskId: string, newOrdinal: number): Promise<OperationResult> {
        try {
            if (!this.currentPlan) {
                await this.getPlan();
            }

            const moved = this.currentPlan!.moveTask(taskId, newOrdinal);
            if (!moved) {
                return { success: false, error: 'Task not found' };
            }

            await this.planStorage.savePlan(this.currentPlan!);

            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }

    /**
     * Log an edit (MCP tool call) for a task
     */
    async logEdit(
        taskId: string,
        toolName: string,
        request: Record<string, unknown>,
        response: string | Record<string, unknown>
    ): Promise<LogEditResult> {
        try {
            if (!this.currentPlan) {
                await this.getPlan();
            }

            const task = this.currentPlan!.getTaskById(taskId);
            if (!task) {
                return { success: false, error: 'Task not found', taskId };
            }

            // Create edit with proper response format
            const responseObj = typeof response === 'string' 
                ? { result: response } 
                : response;

            const edit = new Edit({
                taskId,
                toolName,
                request,
                response: responseObj
            });

            // Log edit to plan and add to task
            this.currentPlan!.logEdit(edit);

            // Persist edit to file
            await this.planStorage.appendEdit(edit);
            // Also save plan to update task's editIds
            await this.planStorage.savePlan(this.currentPlan!);

            return {
                success: true,
                edit,
                editId: edit.id,
                taskId
            };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error),
                taskId
            };
        }
    }

    /**
     * Get all edits for a specific task
     */
    async getEditsForTask(taskId: string): Promise<Edit[]> {
        if (!this.currentPlan) {
            await this.getPlan();
        }

        return this.currentPlan!.getEditsForTask(taskId);
    }

    /**
     * Convert current plan to webview-friendly format
     */
    toWebviewData(): WebviewPlanData {
        if (!this.currentPlan) {
            return { tasks: [] };
        }

        const tasks: WebviewTaskData[] = this.currentPlan.tasks.map(task => ({
            id: task.id,
            title: task.title,
            description: task.description,
            status: task.status,
            ordinal: task.ordinal,
            creationDate: task.creationDate.toISOString(),
            completionDate: task.completionDate ? task.completionDate.toISOString() : null,
            editIds: [...task.editIds]
        }));

        return { tasks };
    }
}
