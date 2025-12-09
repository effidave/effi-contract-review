/**
 * MCP Tool Logger Tests
 * 
 * Step 5: LLM/MCP Integration
 * 
 * Tests for:
 * - McpToolLogger service for tracking active tasks and logging edits
 * - Active task context management
 * - Automatic edit logging when tools are called
 * - Integration with PlanProvider
 */

import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import { McpToolLogger, ToolCallRecord } from '../models/mcpToolLogger';
import { PlanProvider } from '../models/planProvider';
import { Edit } from '../models/workplan';

describe('McpToolLogger', () => {
    let tempDir: string;
    let logger: McpToolLogger;
    let provider: PlanProvider;

    beforeEach(async () => {
        // Create temp directory for each test
        tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'mcp-logger-test-'));
        
        // Initialize provider and logger
        provider = new PlanProvider(tempDir);
        await provider.initialize();
        await provider.getPlan();
        
        logger = new McpToolLogger(provider);
    });

    afterEach(() => {
        // Cleanup temp directory
        if (fs.existsSync(tempDir)) {
            fs.rmSync(tempDir, { recursive: true, force: true });
        }
    });

    // ========================================================================
    // Section 1: Active Task Management
    // ========================================================================
    describe('Active Task Management', () => {
        test('should have no active task initially', () => {
            expect(logger.getActiveTaskId()).toBeNull();
            expect(logger.hasActiveTask()).toBe(false);
        });

        test('should set active task by ID', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            
            logger.setActiveTask(task!.id);
            
            expect(logger.getActiveTaskId()).toBe(task!.id);
            expect(logger.hasActiveTask()).toBe(true);
        });

        test('should clear active task', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            logger.clearActiveTask();
            
            expect(logger.getActiveTaskId()).toBeNull();
            expect(logger.hasActiveTask()).toBe(false);
        });

        test('should get active task object', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            const activeTask = await logger.getActiveTask();
            
            expect(activeTask).not.toBeNull();
            expect(activeTask!.id).toBe(task!.id);
            expect(activeTask!.title).toBe('Test Task');
        });

        test('should return null for invalid active task ID', async () => {
            logger.setActiveTask('nonexistent-id');
            
            const activeTask = await logger.getActiveTask();
            
            expect(activeTask).toBeNull();
        });

        test('should auto-set active task when task status changes to in_progress', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            
            // Simulate status change to in_progress
            await provider.updateTask(task!.id, { status: 'in_progress' });
            logger.onTaskStatusChanged(task!.id, 'in_progress');
            
            expect(logger.getActiveTaskId()).toBe(task!.id);
        });

        test('should clear active task when task status changes from in_progress', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            // Simulate status change to completed
            await provider.updateTask(task!.id, { status: 'completed' });
            logger.onTaskStatusChanged(task!.id, 'completed');
            
            expect(logger.getActiveTaskId()).toBeNull();
        });

        test('should not clear active task if different task changes status', async () => {
            const { task: task1 } = await provider.addTask('Task 1', 'Description');
            const { task: task2 } = await provider.addTask('Task 2', 'Description');
            logger.setActiveTask(task1!.id);
            
            // Different task changes status
            logger.onTaskStatusChanged(task2!.id, 'completed');
            
            expect(logger.getActiveTaskId()).toBe(task1!.id);
        });
    });

    // ========================================================================
    // Section 2: Tool Call Logging
    // ========================================================================
    describe('Tool Call Logging', () => {
        test('should log tool call to active task', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            const result = await logger.logToolCall(
                'mcp_effi-local_search_and_replace',
                { filename: 'doc.docx', find_text: 'old', replace_text: 'new' },
                { success: true, replacements: 3 }
            );
            
            expect(result.success).toBe(true);
            expect(result.edit).toBeDefined();
            expect(result.edit!.toolName).toBe('mcp_effi-local_search_and_replace');
            expect(result.edit!.taskId).toBe(task!.id);
        });

        test('should return error when no active task', async () => {
            const result = await logger.logToolCall(
                'mcp_effi-local_add_paragraph',
                { filename: 'doc.docx', text: 'Hello' },
                { success: true }
            );
            
            expect(result.success).toBe(false);
            expect(result.error).toContain('No active task');
        });

        test('should add edit ID to task', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            const { edit } = await logger.logToolCall('tool_name', {}, 'success');
            
            const updatedTask = provider.currentPlan?.getTaskById(task!.id);
            expect(updatedTask?.editIds).toContain(edit!.id);
        });

        test('should persist edit to edits.jsonl', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            await logger.logToolCall('tool_name', { key: 'value' }, 'response');
            
            const editsPath = path.join(tempDir, 'logs', 'edits.jsonl');
            expect(fs.existsSync(editsPath)).toBe(true);
            
            const content = fs.readFileSync(editsPath, 'utf-8');
            expect(content).toContain('tool_name');
            expect(content).toContain('key');
        });

        test('should handle complex request objects', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            const complexRequest = {
                filename: 'contract.docx',
                clauses: [{ id: 1, text: 'clause 1' }, { id: 2, text: 'clause 2' }],
                options: { format: 'markdown', indent: 2 }
            };
            
            const { edit } = await logger.logToolCall('complex_tool', complexRequest, 'success');
            
            expect(edit!.request).toEqual(complexRequest);
        });

        test('should handle string responses', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            const { edit } = await logger.logToolCall('tool', {}, 'Simple string response');
            
            expect(edit!.response).toEqual({ result: 'Simple string response' });
        });

        test('should handle object responses', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            const response = { status: 'ok', count: 5, items: ['a', 'b'] };
            const { edit } = await logger.logToolCall('tool', {}, response);
            
            expect(edit!.response).toEqual(response);
        });
    });

    // ========================================================================
    // Section 3: Tool Call Records (Batch Operations)
    // ========================================================================
    describe('Tool Call Records', () => {
        test('should record pending tool call', () => {
            const record = logger.recordToolCallStart('mcp_tool', { arg: 'value' });
            
            expect(record.id).toBeDefined();
            expect(record.toolName).toBe('mcp_tool');
            expect(record.request).toEqual({ arg: 'value' });
            expect(record.startTime).toBeInstanceOf(Date);
            expect(record.completed).toBe(false);
        });

        test('should complete pending tool call', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            const record = logger.recordToolCallStart('mcp_tool', { arg: 'value' });
            const result = await logger.completeToolCall(record.id, { success: true });
            
            expect(result.success).toBe(true);
            expect(result.edit).toBeDefined();
        });

        test('should include elapsed time in completed record', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            const record = logger.recordToolCallStart('mcp_tool', {});
            
            // Small delay to ensure measurable time
            await new Promise(resolve => setTimeout(resolve, 10));
            
            // Get the record before completion to check it exists
            expect(logger.getToolCallRecord(record.id)).toBeDefined();
            
            const result = await logger.completeToolCall(record.id, 'done');
            
            // After completion, record is removed from pending
            // But the result should be successful
            expect(result.success).toBe(true);
            expect(result.edit).toBeDefined();
        });

        test('should return error for unknown record ID', async () => {
            const result = await logger.completeToolCall('unknown-id', 'response');
            
            expect(result.success).toBe(false);
            expect(result.error).toContain('not found');
        });

        test('should get all pending tool calls', () => {
            logger.recordToolCallStart('tool1', {});
            logger.recordToolCallStart('tool2', {});
            
            const pending = logger.getPendingToolCalls();
            
            expect(pending.length).toBe(2);
        });

        test('should clear completed records from pending', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            const record1 = logger.recordToolCallStart('tool1', {});
            logger.recordToolCallStart('tool2', {});
            
            await logger.completeToolCall(record1.id, 'done');
            
            const pending = logger.getPendingToolCalls();
            expect(pending.length).toBe(1);
            expect(pending[0].toolName).toBe('tool2');
        });
    });

    // ========================================================================
    // Section 4: Event Notifications
    // ========================================================================
    describe('Event Notifications', () => {
        test('should emit event when edit is logged', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            let eventFired = false;
            let eventEdit: Edit | undefined;
            
            logger.onEditLogged((edit) => {
                eventFired = true;
                eventEdit = edit;
            });
            
            await logger.logToolCall('tool_name', {}, 'response');
            
            expect(eventFired).toBe(true);
            expect(eventEdit).toBeDefined();
            expect(eventEdit!.toolName).toBe('tool_name');
        });

        test('should emit event when active task changes', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            
            let eventFired = false;
            let newTaskId: string | null = null;
            
            logger.onActiveTaskChanged((taskId) => {
                eventFired = true;
                newTaskId = taskId;
            });
            
            logger.setActiveTask(task!.id);
            
            expect(eventFired).toBe(true);
            expect(newTaskId).toBe(task!.id);
        });

        test('should emit null when active task is cleared', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            let lastTaskId: string | null = 'initial';
            logger.onActiveTaskChanged((taskId) => {
                lastTaskId = taskId;
            });
            
            logger.clearActiveTask();
            
            expect(lastTaskId).toBeNull();
        });

        test('should allow multiple event listeners', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            let count = 0;
            logger.onEditLogged(() => count++);
            logger.onEditLogged(() => count++);
            
            await logger.logToolCall('tool', {}, 'response');
            
            expect(count).toBe(2);
        });

        test('should remove event listener when disposed', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            let count = 0;
            const dispose = logger.onEditLogged(() => count++);
            
            await logger.logToolCall('tool1', {}, 'response');
            dispose();
            await logger.logToolCall('tool2', {}, 'response');
            
            expect(count).toBe(1);
        });
    });

    // ========================================================================
    // Section 5: Statistics and History
    // ========================================================================
    describe('Statistics and History', () => {
        test('should track total edits logged in session', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            await logger.logToolCall('tool1', {}, 'r1');
            await logger.logToolCall('tool2', {}, 'r2');
            await logger.logToolCall('tool3', {}, 'r3');
            
            expect(logger.getSessionEditCount()).toBe(3);
        });

        test('should track edits by tool name', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            await logger.logToolCall('search_replace', {}, 'r1');
            await logger.logToolCall('add_paragraph', {}, 'r2');
            await logger.logToolCall('search_replace', {}, 'r3');
            
            const stats = logger.getToolUsageStats();
            
            expect(stats['search_replace']).toBe(2);
            expect(stats['add_paragraph']).toBe(1);
        });

        test('should get recent edits', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            await logger.logToolCall('tool1', {}, 'r1');
            await logger.logToolCall('tool2', {}, 'r2');
            await logger.logToolCall('tool3', {}, 'r3');
            
            const recent = logger.getRecentEdits(2);
            
            expect(recent.length).toBe(2);
            expect(recent[0].toolName).toBe('tool3'); // Most recent first
            expect(recent[1].toolName).toBe('tool2');
        });

        test('should reset session stats on clear', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            await logger.logToolCall('tool', {}, 'r');
            expect(logger.getSessionEditCount()).toBe(1);
            
            logger.resetSessionStats();
            
            expect(logger.getSessionEditCount()).toBe(0);
            expect(logger.getToolUsageStats()).toEqual({});
        });
    });

    // ========================================================================
    // Section 6: Error Handling
    // ========================================================================
    describe('Error Handling', () => {
        test('should handle provider errors gracefully', async () => {
            // Create logger with uninitialized provider
            const badProvider = new PlanProvider('/nonexistent/path');
            const badLogger = new McpToolLogger(badProvider);
            badLogger.setActiveTask('some-task');
            
            const result = await badLogger.logToolCall('tool', {}, 'response');
            
            expect(result.success).toBe(false);
            expect(result.error).toBeDefined();
        });

        test('should handle missing task gracefully', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            // Delete the task
            await provider.deleteTask(task!.id);
            
            const result = await logger.logToolCall('tool', {}, 'response');
            
            expect(result.success).toBe(false);
            expect(result.error).toContain('not found');
        });

        test('should validate tool name', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            const result = await logger.logToolCall('', {}, 'response');
            
            expect(result.success).toBe(false);
            expect(result.error).toContain('Tool name');
        });
    });

    // ========================================================================
    // Section 7: Integration with PlanProvider
    // ========================================================================
    describe('Integration with PlanProvider', () => {
        test('should sync with provider task updates', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            await logger.logToolCall('tool', {}, 'response');
            
            // Reload plan and verify edit is persisted
            const freshProvider = new PlanProvider(tempDir);
            await freshProvider.initialize();
            await freshProvider.getPlan();
            
            const reloadedTask = freshProvider.currentPlan?.getTaskById(task!.id);
            expect(reloadedTask?.editIds.length).toBe(1);
        });

        test('should work with multiple tasks', async () => {
            const { task: task1 } = await provider.addTask('Task 1', 'Desc 1');
            const { task: task2 } = await provider.addTask('Task 2', 'Desc 2');
            
            // Log to task 1
            logger.setActiveTask(task1!.id);
            await logger.logToolCall('tool_a', {}, 'r1');
            
            // Log to task 2
            logger.setActiveTask(task2!.id);
            await logger.logToolCall('tool_b', {}, 'r2');
            await logger.logToolCall('tool_c', {}, 'r3');
            
            const edits1 = await provider.getEditsForTask(task1!.id);
            const edits2 = await provider.getEditsForTask(task2!.id);
            
            expect(edits1.length).toBe(1);
            expect(edits2.length).toBe(2);
        });

        test('should update plan.md after edit', async () => {
            const { task } = await provider.addTask('Test Task', 'Description');
            logger.setActiveTask(task!.id);
            
            await logger.logToolCall('tool', {}, 'response');
            
            // Check plan.md is updated with new editIds
            const planPath = path.join(tempDir, 'plans', 'current', 'plan.md');
            expect(fs.existsSync(planPath)).toBe(true);
            
            const content = fs.readFileSync(planPath, 'utf-8');
            // The plan.md should contain the task with editIds
            expect(content).toContain(task!.id);
        });
    });
});

// ============================================================================
// Extension Integration Tests
// ============================================================================
describe('McpToolLogger Extension Integration', () => {
    let tempDir: string;

    beforeEach(() => {
        tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'mcp-ext-test-'));
    });

    afterEach(() => {
        if (fs.existsSync(tempDir)) {
            fs.rmSync(tempDir, { recursive: true, force: true });
        }
    });

    test('should be creatable from extension context', async () => {
        const provider = new PlanProvider(tempDir);
        await provider.initialize();
        
        const logger = new McpToolLogger(provider);
        
        expect(logger).toBeDefined();
        expect(logger.hasActiveTask()).toBe(false);
    });

    test('should handle rapid sequential tool calls', async () => {
        const provider = new PlanProvider(tempDir);
        await provider.initialize();
        await provider.getPlan();
        
        const logger = new McpToolLogger(provider);
        const { task } = await provider.addTask('Test Task', 'Description');
        logger.setActiveTask(task!.id);
        
        // Rapid fire tool calls
        const promises = [];
        for (let i = 0; i < 10; i++) {
            promises.push(logger.logToolCall(`tool_${i}`, { index: i }, `response_${i}`));
        }
        
        const results = await Promise.all(promises);
        
        // All should succeed
        expect(results.every(r => r.success)).toBe(true);
        expect(logger.getSessionEditCount()).toBe(10);
    });

    test('should preserve edit order in edits.jsonl', async () => {
        const provider = new PlanProvider(tempDir);
        await provider.initialize();
        await provider.getPlan();
        
        const logger = new McpToolLogger(provider);
        const { task } = await provider.addTask('Test Task', 'Description');
        logger.setActiveTask(task!.id);
        
        // Log in sequence
        await logger.logToolCall('tool_1', {}, 'r1');
        await logger.logToolCall('tool_2', {}, 'r2');
        await logger.logToolCall('tool_3', {}, 'r3');
        
        // Read edits file
        const editsPath = path.join(tempDir, 'logs', 'edits.jsonl');
        const lines = fs.readFileSync(editsPath, 'utf-8').trim().split('\n');
        
        expect(lines.length).toBe(3);
        expect(JSON.parse(lines[0]).toolName).toBe('tool_1');
        expect(JSON.parse(lines[1]).toolName).toBe('tool_2');
        expect(JSON.parse(lines[2]).toolName).toBe('tool_3');
    });
});
