/**
 * MCP Tool Logger
 * 
 * Step 5: LLM/MCP Integration
 * 
 * Provides automatic logging of MCP tool calls as Edit objects.
 * Tracks the active task and associates tool calls with it.
 * 
 * Features:
 * - Active task management (set/clear/get)
 * - Tool call logging to active task
 * - Pending tool call tracking (for async operations)
 * - Event notifications (onEditLogged, onActiveTaskChanged)
 * - Session statistics (edit count, tool usage)
 */

import { PlanProvider } from './planProvider';
import { Edit, WorkTask } from './workplan';

// ============================================================================
// Types
// ============================================================================

/**
 * Result of logging a tool call
 */
export interface LogToolCallResult {
    success: boolean;
    edit?: Edit;
    error?: string;
}

/**
 * Record of a pending or completed tool call
 */
export interface ToolCallRecord {
    id: string;
    toolName: string;
    request: Record<string, unknown>;
    response?: string | Record<string, unknown>;
    startTime: Date;
    endTime?: Date;
    elapsedMs?: number;
    completed: boolean;
}

/**
 * Disposable for removing event listeners
 */
type Disposable = () => void;

/**
 * Event listener for edit logged events
 */
type EditLoggedListener = (edit: Edit) => void;

/**
 * Event listener for active task changed events
 */
type ActiveTaskChangedListener = (taskId: string | null) => void;

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Generate a unique ID for tool call records
 */
function generateRecordId(): string {
    return `tcr_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
}

// ============================================================================
// McpToolLogger Class
// ============================================================================

/**
 * Service for logging MCP tool calls as Edit objects
 */
export class McpToolLogger {
    private provider: PlanProvider;
    private activeTaskId: string | null = null;
    
    // Pending tool calls (for async start/complete pattern)
    private pendingToolCalls: Map<string, ToolCallRecord> = new Map();
    
    // Event listeners
    private editLoggedListeners: Set<EditLoggedListener> = new Set();
    private activeTaskChangedListeners: Set<ActiveTaskChangedListener> = new Set();
    
    // Session statistics
    private sessionEditCount: number = 0;
    private toolUsageStats: Map<string, number> = new Map();
    private recentEdits: Edit[] = [];
    private maxRecentEdits: number = 100;

    constructor(provider: PlanProvider) {
        this.provider = provider;
    }

    // ========================================================================
    // Active Task Management
    // ========================================================================

    /**
     * Get the current active task ID
     */
    getActiveTaskId(): string | null {
        return this.activeTaskId;
    }

    /**
     * Check if there is an active task
     */
    hasActiveTask(): boolean {
        return this.activeTaskId !== null;
    }

    /**
     * Set the active task by ID
     */
    setActiveTask(taskId: string): void {
        const previousId = this.activeTaskId;
        this.activeTaskId = taskId;
        
        if (previousId !== taskId) {
            this.emitActiveTaskChanged(taskId);
        }
    }

    /**
     * Clear the active task
     */
    clearActiveTask(): void {
        if (this.activeTaskId !== null) {
            this.activeTaskId = null;
            this.emitActiveTaskChanged(null);
        }
    }

    /**
     * Get the active task object
     */
    async getActiveTask(): Promise<WorkTask | null> {
        if (!this.activeTaskId) {
            return null;
        }

        try {
            if (!this.provider.currentPlan) {
                await this.provider.getPlan();
            }

            const task = this.provider.currentPlan?.getTaskById(this.activeTaskId);
            return task || null;
        } catch {
            return null;
        }
    }

    /**
     * Handle task status change - auto-set/clear active task
     */
    onTaskStatusChanged(taskId: string, newStatus: string): void {
        if (newStatus === 'in_progress') {
            // Auto-set as active task
            this.setActiveTask(taskId);
        } else if (this.activeTaskId === taskId) {
            // Clear if this was the active task
            this.clearActiveTask();
        }
    }

    // ========================================================================
    // Tool Call Logging
    // ========================================================================

    /**
     * Log a tool call to the active task
     */
    async logToolCall(
        toolName: string,
        request: Record<string, unknown>,
        response: string | Record<string, unknown>
    ): Promise<LogToolCallResult> {
        // Validate tool name
        if (!toolName || toolName.trim() === '') {
            return {
                success: false,
                error: 'Tool name is required'
            };
        }

        // Check for active task
        if (!this.activeTaskId) {
            return {
                success: false,
                error: 'No active task. Start a task before logging tool calls.'
            };
        }

        try {
            // Use provider to log the edit
            const result = await this.provider.logEdit(
                this.activeTaskId,
                toolName,
                request,
                response
            );

            if (result.success && result.edit) {
                // Update session stats
                this.sessionEditCount++;
                this.toolUsageStats.set(
                    toolName,
                    (this.toolUsageStats.get(toolName) || 0) + 1
                );
                
                // Add to recent edits
                this.recentEdits.unshift(result.edit);
                if (this.recentEdits.length > this.maxRecentEdits) {
                    this.recentEdits.pop();
                }

                // Emit event
                this.emitEditLogged(result.edit);

                return {
                    success: true,
                    edit: result.edit
                };
            } else {
                return {
                    success: false,
                    error: result.error || 'Task not found'
                };
            }
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }

    // ========================================================================
    // Tool Call Records (Async Start/Complete Pattern)
    // ========================================================================

    /**
     * Record the start of a tool call (for async operations)
     */
    recordToolCallStart(
        toolName: string,
        request: Record<string, unknown>
    ): ToolCallRecord {
        const record: ToolCallRecord = {
            id: generateRecordId(),
            toolName,
            request,
            startTime: new Date(),
            completed: false
        };

        this.pendingToolCalls.set(record.id, record);
        return record;
    }

    /**
     * Complete a pending tool call and log it
     */
    async completeToolCall(
        recordId: string,
        response: string | Record<string, unknown>
    ): Promise<LogToolCallResult> {
        const record = this.pendingToolCalls.get(recordId);
        
        if (!record) {
            return {
                success: false,
                error: `Tool call record not found: ${recordId}`
            };
        }

        // Update record
        record.response = response;
        record.endTime = new Date();
        record.elapsedMs = record.endTime.getTime() - record.startTime.getTime();
        record.completed = true;

        // Remove from pending
        this.pendingToolCalls.delete(recordId);

        // Log the tool call
        return this.logToolCall(record.toolName, record.request, response);
    }

    /**
     * Get a tool call record by ID
     */
    getToolCallRecord(recordId: string): ToolCallRecord | undefined {
        return this.pendingToolCalls.get(recordId);
    }

    /**
     * Get all pending (incomplete) tool calls
     */
    getPendingToolCalls(): ToolCallRecord[] {
        return Array.from(this.pendingToolCalls.values()).filter(r => !r.completed);
    }

    // ========================================================================
    // Event Notifications
    // ========================================================================

    /**
     * Register a listener for edit logged events
     */
    onEditLogged(listener: EditLoggedListener): Disposable {
        this.editLoggedListeners.add(listener);
        return () => {
            this.editLoggedListeners.delete(listener);
        };
    }

    /**
     * Register a listener for active task changed events
     */
    onActiveTaskChanged(listener: ActiveTaskChangedListener): Disposable {
        this.activeTaskChangedListeners.add(listener);
        return () => {
            this.activeTaskChangedListeners.delete(listener);
        };
    }

    private emitEditLogged(edit: Edit): void {
        for (const listener of this.editLoggedListeners) {
            try {
                listener(edit);
            } catch {
                // Ignore listener errors
            }
        }
    }

    private emitActiveTaskChanged(taskId: string | null): void {
        for (const listener of this.activeTaskChangedListeners) {
            try {
                listener(taskId);
            } catch {
                // Ignore listener errors
            }
        }
    }

    // ========================================================================
    // Statistics and History
    // ========================================================================

    /**
     * Get the total number of edits logged in this session
     */
    getSessionEditCount(): number {
        return this.sessionEditCount;
    }

    /**
     * Get tool usage statistics (tool name -> count)
     */
    getToolUsageStats(): Record<string, number> {
        const stats: Record<string, number> = {};
        for (const [toolName, count] of this.toolUsageStats) {
            stats[toolName] = count;
        }
        return stats;
    }

    /**
     * Get recent edits (most recent first)
     */
    getRecentEdits(limit?: number): Edit[] {
        if (limit !== undefined) {
            return this.recentEdits.slice(0, limit);
        }
        return [...this.recentEdits];
    }

    /**
     * Reset session statistics
     */
    resetSessionStats(): void {
        this.sessionEditCount = 0;
        this.toolUsageStats.clear();
        this.recentEdits = [];
    }
}
