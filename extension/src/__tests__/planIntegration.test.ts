/**
 * Plan Tab Integration Tests
 * 
 * These tests verify the integration between:
 * - PlanProvider class (manages plan operations for extension)
 * - Message handlers (webview ↔ extension communication)
 * - PlanStorage (file persistence)
 */

import * as path from 'path';
import * as fs from 'fs';
import { WorkPlan, WorkTask, Edit } from '../models/workplan';
import { PlanStorage } from '../models/planStorage';
import { PlanProvider } from '../models/planProvider';

// Helper to create a task quickly
function createTask(title: string, description: string): WorkTask {
    return new WorkTask({ title, description });
}

// Helper to create an edit quickly
function createEdit(taskId: string, toolName: string, request: Record<string, unknown>, response: Record<string, unknown>): Edit {
    return new Edit({ taskId, toolName, request, response });
}

// ============================================================================
// SECTION 1: PlanProvider Class Tests
// ============================================================================

describe('PlanProvider class', () => {
    const TEST_DIR = path.join(__dirname, 'test-plan-provider');
    const PROJECT_PATH = path.join(TEST_DIR, 'TestProject');
    
    beforeEach(() => {
        if (fs.existsSync(TEST_DIR)) {
            fs.rmSync(TEST_DIR, { recursive: true, force: true });
        }
        fs.mkdirSync(PROJECT_PATH, { recursive: true });
    });
    
    afterEach(() => {
        if (fs.existsSync(TEST_DIR)) {
            fs.rmSync(TEST_DIR, { recursive: true, force: true });
        }
    });
    
    describe('constructor and initialization', () => {
        test('should be importable', () => {
            expect(PlanProvider).toBeDefined();
        });
        
        test('should accept project path in constructor', () => {
            const provider = new PlanProvider(PROJECT_PATH);
            expect(provider).toBeDefined();
        });
        
        test('should have planStorage property', () => {
            const provider = new PlanProvider(PROJECT_PATH);
            expect(provider.planStorage).toBeInstanceOf(PlanStorage);
        });
        
        test('should have currentPlan property initially null', () => {
            const provider = new PlanProvider(PROJECT_PATH);
            expect(provider.currentPlan).toBeNull();
        });
        
        test('should create plans/current directory on initialize()', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            
            const plansDir = path.join(PROJECT_PATH, 'plans', 'current');
            expect(fs.existsSync(plansDir)).toBe(true);
        });
    });
    
    describe('getPlan()', () => {
        test('should return empty plan if none exists', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            
            const plan = await provider.getPlan();
            expect(plan).toBeInstanceOf(WorkPlan);
            expect(plan.tasks.length).toBe(0);
        });
        
        test('should return existing plan if one exists', async () => {
            // Create a plan first
            const storage = new PlanStorage(PROJECT_PATH);
            const plan = new WorkPlan();
            plan.addTaskAtEnd(createTask('Test Task', 'Test description'));
            await storage.savePlan(plan);
            
            // Now get it via provider
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            const retrievedPlan = await provider.getPlan();
            
            expect(retrievedPlan.tasks.length).toBe(1);
            expect(retrievedPlan.tasks[0].title).toBe('Test Task');
        });
        
        test('should cache plan in currentPlan property', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            
            const plan = await provider.getPlan();
            expect(provider.currentPlan).toBe(plan);
        });
        
        test('should load edits when getting plan', async () => {
            // Create a plan with an edit
            const storage = new PlanStorage(PROJECT_PATH);
            const plan = new WorkPlan();
            const task = createTask('Test Task', 'Test description');
            plan.addTaskAtEnd(task);
            const edit = createEdit(task.id, 'test_tool', { arg: 'value' }, { result: 'success' });
            task.addEditId(edit.id);  // Link edit to task
            await storage.savePlan(plan);
            await storage.appendEdit(edit);  // Save edit to edits.jsonl
            
            // Get via provider
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            const retrievedPlan = await provider.getPlan();
            
            expect(retrievedPlan.edits.length).toBe(1);
            expect(retrievedPlan.edits[0].toolName).toBe('test_tool');
        });
    });
    
    describe('savePlan()', () => {
        test('should save plan to file system', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            
            const plan = new WorkPlan();
            plan.addTaskAtEnd(createTask('New Task', 'New description'));
            await provider.savePlan(plan);
            
            const planPath = path.join(PROJECT_PATH, 'plans', 'current', 'plan.md');
            expect(fs.existsSync(planPath)).toBe(true);
        });
        
        test('should update currentPlan property after save', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            
            const plan = new WorkPlan();
            plan.addTaskAtEnd(createTask('New Task', 'New description'));
            await provider.savePlan(plan);
            
            expect(provider.currentPlan).toBe(plan);
        });
        
        test('should return success result', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            
            const plan = new WorkPlan();
            const result = await provider.savePlan(plan);
            
            expect(result.success).toBe(true);
        });
    });
    
    describe('addTask()', () => {
        test('should add task to plan and save', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const result = await provider.addTask('New Task', 'Task description');
            
            expect(result.success).toBe(true);
            expect(result.task).toBeDefined();
            expect(result.task!.title).toBe('New Task');
            expect(provider.currentPlan?.tasks.length).toBe(1);
        });
        
        test('should persist task to file', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            await provider.addTask('Persisted Task', 'Description');
            
            // Load fresh from storage
            const storage = new PlanStorage(PROJECT_PATH);
            const loadedPlan = await storage.loadPlan();
            expect(loadedPlan!.tasks.length).toBe(1);
            expect(loadedPlan!.tasks[0].title).toBe('Persisted Task');
        });
        
        test('should add task at specific position', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            await provider.addTask('First', 'desc');
            await provider.addTask('Third', 'desc');
            // ordinal is 0-based: ordinal 1 = insert at index 1
            await provider.addTask('Second', 'desc', { ordinal: 1 });
            
            expect(provider.currentPlan?.tasks[0].title).toBe('First');
            expect(provider.currentPlan?.tasks[1].title).toBe('Second');
            expect(provider.currentPlan?.tasks[2].title).toBe('Third');
        });
        
        test('should add task at start if position is "start"', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            await provider.addTask('First', 'desc');
            await provider.addTask('At Start', 'desc', { position: 'start' });
            
            expect(provider.currentPlan?.tasks[0].title).toBe('At Start');
        });
    });
    
    describe('updateTask()', () => {
        test('should update task title', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task } = await provider.addTask('Original', 'desc');
            const result = await provider.updateTask(task!.id, { title: 'Updated' });
            
            expect(result.success).toBe(true);
            expect(provider.currentPlan?.getTaskById(task!.id)?.title).toBe('Updated');
        });
        
        test('should update task description', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task } = await provider.addTask('Task', 'Original');
            await provider.updateTask(task!.id, { description: 'Updated description' });
            
            expect(provider.currentPlan?.getTaskById(task!.id)?.description).toBe('Updated description');
        });
        
        test('should update task status', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task } = await provider.addTask('Task', 'desc');
            await provider.updateTask(task!.id, { status: 'in_progress' });
            
            expect(provider.currentPlan?.getTaskById(task!.id)?.status).toBe('in_progress');
        });
        
        test('should persist updates to file', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task } = await provider.addTask('Task', 'desc');
            await provider.updateTask(task!.id, { title: 'Updated Title' });
            
            const storage = new PlanStorage(PROJECT_PATH);
            const loaded = await storage.loadPlan();
            expect(loaded!.tasks[0].title).toBe('Updated Title');
        });
        
        test('should return error for non-existent task', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const result = await provider.updateTask('nonexistent-id', { title: 'Updated' });
            
            expect(result.success).toBe(false);
            expect(result.error).toBeDefined();
        });
    });
    
    describe('deleteTask()', () => {
        test('should remove task from plan', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task } = await provider.addTask('To Delete', 'desc');
            const result = await provider.deleteTask(task!.id);
            
            expect(result.success).toBe(true);
            expect(provider.currentPlan?.tasks.length).toBe(0);
        });
        
        test('should persist deletion to file', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task } = await provider.addTask('To Delete', 'desc');
            await provider.deleteTask(task!.id);
            
            const storage = new PlanStorage(PROJECT_PATH);
            const loaded = await storage.loadPlan();
            expect(loaded!.tasks.length).toBe(0);
        });
        
        test('should return error for non-existent task', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const result = await provider.deleteTask('nonexistent-id');
            
            expect(result.success).toBe(false);
        });
    });
    
    describe('moveTask()', () => {
        test('should reorder task to new position', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task: task1 } = await provider.addTask('Task 1', 'desc');
            const { task: task2 } = await provider.addTask('Task 2', 'desc');
            const { task: task3 } = await provider.addTask('Task 3', 'desc');
            
            // ordinal is 0-based: ordinal 0 = first position
            await provider.moveTask(task3!.id, 0);
            
            expect(provider.currentPlan?.tasks[0].id).toBe(task3!.id);
            expect(provider.currentPlan?.tasks[1].id).toBe(task1!.id);
            expect(provider.currentPlan?.tasks[2].id).toBe(task2!.id);
        });
        
        test('should persist reorder to file', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task: task1 } = await provider.addTask('Task 1', 'desc');
            const { task: task2 } = await provider.addTask('Task 2', 'desc');
            
            // ordinal is 0-based: ordinal 0 = first position
            await provider.moveTask(task2!.id, 0);
            
            const storage = new PlanStorage(PROJECT_PATH);
            const loaded = await storage.loadPlan();
            expect(loaded!.tasks[0].title).toBe('Task 2');
        });
    });
    
    describe('logEdit()', () => {
        test('should log edit to edits.jsonl', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task } = await provider.addTask('Task', 'desc');
            const result = await provider.logEdit(task!.id, 'mcp_tool_name', { arg: 'value' }, 'success response');
            
            expect(result.success).toBe(true);
            expect(result.edit).toBeDefined();
            expect(result.edit!.toolName).toBe('mcp_tool_name');
        });
        
        test('should add edit id to task', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task } = await provider.addTask('Task', 'desc');
            const { edit } = await provider.logEdit(task!.id, 'tool', {}, 'response');
            
            const updatedTask = provider.currentPlan?.getTaskById(task!.id);
            expect(updatedTask?.editIds).toContain(edit!.id);
        });
        
        test('should persist edit to file', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task } = await provider.addTask('Task', 'desc');
            await provider.logEdit(task!.id, 'tool', { key: 'value' }, 'response');
            
            const editsPath = path.join(PROJECT_PATH, 'logs', 'edits.jsonl');
            expect(fs.existsSync(editsPath)).toBe(true);
            
            const content = fs.readFileSync(editsPath, 'utf-8');
            expect(content).toContain('tool');
        });
        
        test('should return error for non-existent task', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const result = await provider.logEdit('nonexistent', 'tool', {}, 'response');
            
            expect(result.success).toBe(false);
        });
    });
    
    describe('getEditsForTask()', () => {
        test('should return edits for a specific task', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task } = await provider.addTask('Task', 'desc');
            await provider.logEdit(task!.id, 'tool1', {}, 'response1');
            await provider.logEdit(task!.id, 'tool2', {}, 'response2');
            
            const edits = await provider.getEditsForTask(task!.id);
            
            expect(edits.length).toBe(2);
            expect(edits[0].toolName).toBe('tool1');
            expect(edits[1].toolName).toBe('tool2');
        });
        
        test('should return empty array for task with no edits', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task } = await provider.addTask('Task', 'desc');
            const edits = await provider.getEditsForTask(task!.id);
            
            expect(edits).toEqual([]);
        });
    });
    
    describe('toWebviewData()', () => {
        test('should return plan data formatted for webview', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            await provider.addTask('Task 1', 'Description 1');
            await provider.addTask('Task 2', 'Description 2');
            
            const data = provider.toWebviewData();
            
            expect(data).toHaveProperty('tasks');
            expect(Array.isArray(data.tasks)).toBe(true);
            expect(data.tasks.length).toBe(2);
            expect(data.tasks[0]).toHaveProperty('id');
            expect(data.tasks[0]).toHaveProperty('title');
            expect(data.tasks[0]).toHaveProperty('description');
            expect(data.tasks[0]).toHaveProperty('status');
        });
        
        test('should include task metadata', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task } = await provider.addTask('Task', 'desc');
            task!.start();
            await provider.savePlan(provider.currentPlan!);
            
            const data = provider.toWebviewData();
            
            expect(data.tasks[0].status).toBe('in_progress');
            expect(data.tasks[0]).toHaveProperty('creationDate');
        });
        
        test('should handle empty plan', () => {
            const provider = new PlanProvider(PROJECT_PATH);
            provider.currentPlan = new WorkPlan();
            
            const data = provider.toWebviewData();
            
            expect(data.tasks).toEqual([]);
        });
    });
});

// ============================================================================
// SECTION 2: Message Handler Tests
// ============================================================================

describe('Plan message handlers', () => {
    const TEST_DIR = path.join(__dirname, 'test-message-handlers');
    const PROJECT_PATH = path.join(TEST_DIR, 'TestProject');
    
    let postedMessages: unknown[];
    
    beforeEach(() => {
        if (fs.existsSync(TEST_DIR)) {
            fs.rmSync(TEST_DIR, { recursive: true, force: true });
        }
        fs.mkdirSync(PROJECT_PATH, { recursive: true });
        postedMessages = [];
    });
    
    afterEach(() => {
        if (fs.existsSync(TEST_DIR)) {
            fs.rmSync(TEST_DIR, { recursive: true, force: true });
        }
    });
    
    describe('Message structure verification', () => {
        test('getPlan message should have correct structure', () => {
            const message = { command: 'getPlan', projectPath: PROJECT_PATH };
            expect(message).toHaveProperty('command', 'getPlan');
            expect(message).toHaveProperty('projectPath');
        });
        
        test('savePlan message should have correct structure', () => {
            const message = { command: 'savePlan', projectPath: PROJECT_PATH, markdown: '---\ntasks: []\n---\n' };
            expect(message).toHaveProperty('command', 'savePlan');
            expect(message).toHaveProperty('projectPath');
            expect(message).toHaveProperty('markdown');
        });
        
        test('addTask message should have correct structure', () => {
            const message = { command: 'addTask', projectPath: PROJECT_PATH, title: 'New Task', description: 'Task description' };
            expect(message).toHaveProperty('command', 'addTask');
            expect(message).toHaveProperty('title');
            expect(message).toHaveProperty('description');
        });
        
        test('updateTask message should have correct structure', () => {
            const message = { command: 'updateTask', projectPath: PROJECT_PATH, taskId: 'abc12345', updates: { title: 'Updated Title' } };
            expect(message).toHaveProperty('command', 'updateTask');
            expect(message).toHaveProperty('taskId');
            expect(message).toHaveProperty('updates');
        });
        
        test('deleteTask message should have correct structure', () => {
            const message = { command: 'deleteTask', projectPath: PROJECT_PATH, taskId: 'abc12345' };
            expect(message).toHaveProperty('command', 'deleteTask');
            expect(message).toHaveProperty('taskId');
        });
        
        test('logEdit message should have correct structure', () => {
            const message = { command: 'logEdit', projectPath: PROJECT_PATH, taskId: 'abc12345', toolName: 'mcp_tool', request: {}, response: 'ok' };
            expect(message).toHaveProperty('command', 'logEdit');
            expect(message).toHaveProperty('taskId');
            expect(message).toHaveProperty('toolName');
        });
        
        test('moveTask message should have correct structure', () => {
            const message = { command: 'moveTask', projectPath: PROJECT_PATH, taskId: 'abc12345', newOrdinal: 2 };
            expect(message).toHaveProperty('command', 'moveTask');
            expect(message).toHaveProperty('taskId');
            expect(message).toHaveProperty('newOrdinal');
        });
    });
    
    describe('Response message structure', () => {
        test('planData response should have correct structure', () => {
            const response = { command: 'planData', plan: { tasks: [] } };
            expect(response).toHaveProperty('command', 'planData');
            expect(response).toHaveProperty('plan');
            expect(response.plan).toHaveProperty('tasks');
        });
        
        test('planSaved response should have correct structure', () => {
            const response = { command: 'planSaved', success: true };
            expect(response).toHaveProperty('command', 'planSaved');
            expect(response).toHaveProperty('success', true);
        });
        
        test('taskAdded response should have correct structure', () => {
            const response = { command: 'taskAdded', success: true, task: { id: 'abc', title: 'T' } };
            expect(response).toHaveProperty('command', 'taskAdded');
            expect(response).toHaveProperty('success', true);
            expect(response).toHaveProperty('task');
        });
        
        test('planError response should have correct structure', () => {
            const response = { command: 'planError', error: 'Task not found', originalCommand: 'updateTask' };
            expect(response).toHaveProperty('command', 'planError');
            expect(response).toHaveProperty('error');
        });
    });
});

// ============================================================================
// SECTION 3: Error handling
// ============================================================================

describe('Plan error handling', () => {
    const TEST_DIR = path.join(__dirname, 'test-plan-errors');
    const PROJECT_PATH = path.join(TEST_DIR, 'TestProject');
    
    beforeEach(() => {
        if (fs.existsSync(TEST_DIR)) {
            fs.rmSync(TEST_DIR, { recursive: true, force: true });
        }
        fs.mkdirSync(PROJECT_PATH, { recursive: true });
    });
    
    afterEach(() => {
        if (fs.existsSync(TEST_DIR)) {
            fs.rmSync(TEST_DIR, { recursive: true, force: true });
        }
    });
    
    test('should handle missing project path gracefully', () => {
        expect(() => {
            new PlanProvider('');
        }).toThrow();
    });
    
    test('should handle corrupted plan file', async () => {
        const plansDir = path.join(PROJECT_PATH, 'plans', 'current');
        fs.mkdirSync(plansDir, { recursive: true });
        fs.writeFileSync(path.join(plansDir, 'plan.md'), 'not valid yaml frontmatter');
        
        const provider = new PlanProvider(PROJECT_PATH);
        await provider.initialize();
        
        const plan = await provider.getPlan();
        expect(plan).toBeInstanceOf(WorkPlan);
        expect(plan.tasks.length).toBe(0);
    });
    
    test('should handle corrupted edits file', async () => {
        const plansDir = path.join(PROJECT_PATH, 'plans', 'current');
        const logsDir = path.join(PROJECT_PATH, 'logs');
        fs.mkdirSync(plansDir, { recursive: true });
        fs.mkdirSync(logsDir, { recursive: true });
        
        const plan = new WorkPlan();
        plan.addTaskAtEnd(createTask('Task', 'desc'));
        const storage = new PlanStorage(PROJECT_PATH);
        await storage.savePlan(plan);
        
        fs.writeFileSync(path.join(logsDir, 'edits.jsonl'), 'not json\nalso not json');
        
        const provider = new PlanProvider(PROJECT_PATH);
        await provider.initialize();
        
        const loadedPlan = await provider.getPlan();
        expect(loadedPlan.tasks.length).toBe(1);
        expect(loadedPlan.edits.length).toBe(0);
    });
});

// ============================================================================
// SECTION 4: Concurrent operations
// ============================================================================

describe('Concurrent plan operations', () => {
    const TEST_DIR = path.join(__dirname, 'test-concurrent');
    const PROJECT_PATH = path.join(TEST_DIR, 'TestProject');
    
    beforeEach(() => {
        if (fs.existsSync(TEST_DIR)) {
            fs.rmSync(TEST_DIR, { recursive: true, force: true });
        }
        fs.mkdirSync(PROJECT_PATH, { recursive: true });
    });
    
    afterEach(() => {
        if (fs.existsSync(TEST_DIR)) {
            fs.rmSync(TEST_DIR, { recursive: true, force: true });
        }
    });
    
    test('should handle rapid task additions', async () => {
        const provider = new PlanProvider(PROJECT_PATH);
        await provider.initialize();
        await provider.getPlan();
        
        const promises = [];
        for (let i = 0; i < 5; i++) {
            promises.push(provider.addTask(`Task ${i}`, `Description ${i}`));
        }
        
        const results = await Promise.all(promises);
        
        results.forEach(r => expect(r.success).toBe(true));
        expect(provider.currentPlan?.tasks.length).toBe(5);
    });
    
    test('should handle rapid edits to same task', async () => {
        const provider = new PlanProvider(PROJECT_PATH);
        await provider.initialize();
        await provider.getPlan();
        
        const { task } = await provider.addTask('Task', 'desc');
        
        const promises = [];
        for (let i = 0; i < 5; i++) {
            promises.push(provider.logEdit(task!.id, `tool_${i}`, { i }, `response_${i}`));
        }
        
        const results = await Promise.all(promises);
        
        results.forEach(r => expect(r.success).toBe(true));
        
        const edits = await provider.getEditsForTask(task!.id);
        expect(edits.length).toBe(5);
    });
});

// ============================================================================
// SECTION 7: Edit Auto-Association Tests
// ============================================================================

describe('Edit auto-association', () => {
    const TEST_DIR = path.join(__dirname, 'test-auto-association');
    const PROJECT_PATH = path.join(TEST_DIR, 'TestProject');
    
    beforeEach(() => {
        if (fs.existsSync(TEST_DIR)) {
            fs.rmSync(TEST_DIR, { recursive: true, force: true });
        }
        fs.mkdirSync(PROJECT_PATH, { recursive: true });
    });
    
    afterEach(() => {
        if (fs.existsSync(TEST_DIR)) {
            fs.rmSync(TEST_DIR, { recursive: true, force: true });
        }
    });

    describe('getActiveTask', () => {
        test('should return task with status in_progress', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            // Add tasks with different statuses
            await provider.addTask('Pending Task', 'desc');
            const { task } = await provider.addTask('Active Task', 'desc');
            await provider.addTask('Another Pending', 'desc');
            
            // Set one to in_progress
            await provider.updateTask(task!.id, { status: 'in_progress' });
            
            const activeTask = provider.getActiveTask();
            
            expect(activeTask).toBeDefined();
            expect(activeTask!.id).toBe(task!.id);
            expect(activeTask!.status).toBe('in_progress');
        });

        test('should return null if no task is in_progress', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            await provider.addTask('Pending Task', 'desc');
            await provider.addTask('Another Pending', 'desc');
            
            const activeTask = provider.getActiveTask();
            
            expect(activeTask).toBeNull();
        });

        test('should return first in_progress task if multiple are active', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task: task1 } = await provider.addTask('Task 1', 'desc');
            const { task: task2 } = await provider.addTask('Task 2', 'desc');
            
            await provider.updateTask(task1!.id, { status: 'in_progress' });
            await provider.updateTask(task2!.id, { status: 'in_progress' });
            
            const activeTask = provider.getActiveTask();
            
            // Should return first one (by ordinal)
            expect(activeTask!.id).toBe(task1!.id);
        });
    });

    describe('processUnassociatedEdits', () => {
        test('should associate unassigned edits with active task', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            // Add a document to the plan
            const { LegalDocument } = require('../models/workplan');
            provider.currentPlan!.addDocument(new LegalDocument({
                filename: 'C:/Projects/nda.docx'
            }));
            
            // Add a task and set it to in_progress
            const { task } = await provider.addTask('Review NDA', 'Check liability');
            await provider.updateTask(task!.id, { status: 'in_progress' });
            
            // Simulate MCP server writing unassociated edits to log
            const logsDir = path.join(PROJECT_PATH, 'logs');
            fs.mkdirSync(logsDir, { recursive: true });
            const editsContent = [
                JSON.stringify({
                    id: 'mcp_edit_1',
                    taskId: null,
                    toolName: 'search_and_replace',
                    request: { filename: 'C:/Projects/nda.docx', find: 'foo', replace: 'bar' },
                    response: { success: true },
                    timestamp: new Date().toISOString()
                }),
                JSON.stringify({
                    id: 'mcp_edit_2',
                    taskId: null,
                    toolName: 'add_paragraph',
                    request: { filename: 'C:/Projects/nda.docx', text: 'hello' },
                    response: { success: true },
                    timestamp: new Date().toISOString()
                })
            ].join('\n');
            fs.writeFileSync(path.join(logsDir, 'edits.jsonl'), editsContent);
            
            // Process unassociated edits
            const result = await provider.processUnassociatedEdits();
            
            expect(result.success).toBe(true);
            expect(result.associatedCount).toBe(2);
            expect(result.associatedEditIds).toContain('mcp_edit_1');
            expect(result.associatedEditIds).toContain('mcp_edit_2');
            
            // Verify task now has these edits
            const updatedTask = provider.currentPlan!.getTaskById(task!.id);
            expect(updatedTask!.editIds).toContain('mcp_edit_1');
            expect(updatedTask!.editIds).toContain('mcp_edit_2');
        });

        test('should only associate edits for plan documents', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            // Add a document to the plan
            const { LegalDocument } = require('../models/workplan');
            provider.currentPlan!.addDocument(new LegalDocument({
                filename: 'C:/Projects/nda.docx'
            }));
            
            // Add active task
            const { task } = await provider.addTask('Review', 'desc');
            await provider.updateTask(task!.id, { status: 'in_progress' });
            
            // Write edits - some for plan doc, some for other doc
            const logsDir = path.join(PROJECT_PATH, 'logs');
            fs.mkdirSync(logsDir, { recursive: true });
            const editsContent = [
                JSON.stringify({
                    id: 'relevant_edit',
                    taskId: null,
                    toolName: 'tool',
                    request: { filename: 'C:/Projects/nda.docx' },
                    response: {},
                    timestamp: new Date().toISOString()
                }),
                JSON.stringify({
                    id: 'unrelated_edit',
                    taskId: null,
                    toolName: 'tool',
                    request: { filename: 'C:/Projects/other.docx' },
                    response: {},
                    timestamp: new Date().toISOString()
                })
            ].join('\n');
            fs.writeFileSync(path.join(logsDir, 'edits.jsonl'), editsContent);
            
            const result = await provider.processUnassociatedEdits();
            
            expect(result.associatedCount).toBe(1);
            expect(result.associatedEditIds).toContain('relevant_edit');
            expect(result.associatedEditIds).not.toContain('unrelated_edit');
        });

        test('should skip edits that are already associated', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            // Add document and active task
            const { LegalDocument } = require('../models/workplan');
            provider.currentPlan!.addDocument(new LegalDocument({
                filename: 'C:/Projects/nda.docx'
            }));
            const { task } = await provider.addTask('Review', 'desc');
            await provider.updateTask(task!.id, { status: 'in_progress' });
            
            // Write mix of associated and unassociated edits
            const logsDir = path.join(PROJECT_PATH, 'logs');
            fs.mkdirSync(logsDir, { recursive: true });
            const editsContent = [
                JSON.stringify({
                    id: 'already_assigned',
                    taskId: 'some_other_task',
                    toolName: 'tool',
                    request: { filename: 'C:/Projects/nda.docx' },
                    response: {},
                    timestamp: new Date().toISOString()
                }),
                JSON.stringify({
                    id: 'needs_assignment',
                    taskId: null,
                    toolName: 'tool',
                    request: { filename: 'C:/Projects/nda.docx' },
                    response: {},
                    timestamp: new Date().toISOString()
                })
            ].join('\n');
            fs.writeFileSync(path.join(logsDir, 'edits.jsonl'), editsContent);
            
            const result = await provider.processUnassociatedEdits();
            
            expect(result.associatedCount).toBe(1);
            expect(result.associatedEditIds).toContain('needs_assignment');
            expect(result.associatedEditIds).not.toContain('already_assigned');
        });

        test('should do nothing if no active task', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            // Add document but no active task
            const { LegalDocument } = require('../models/workplan');
            provider.currentPlan!.addDocument(new LegalDocument({
                filename: 'C:/Projects/nda.docx'
            }));
            await provider.addTask('Pending Task', 'desc'); // status: pending
            
            // Write unassociated edits
            const logsDir = path.join(PROJECT_PATH, 'logs');
            fs.mkdirSync(logsDir, { recursive: true });
            fs.writeFileSync(path.join(logsDir, 'edits.jsonl'), JSON.stringify({
                id: 'orphan_edit',
                taskId: null,
                toolName: 'tool',
                request: { filename: 'C:/Projects/nda.docx' },
                response: {},
                timestamp: new Date().toISOString()
            }));
            
            const result = await provider.processUnassociatedEdits();
            
            expect(result.success).toBe(true);
            expect(result.associatedCount).toBe(0);
            expect(result.skippedReason).toBe('no_active_task');
        });

        test('should do nothing if no plan documents registered', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            // Add active task but no documents
            const { task } = await provider.addTask('Task', 'desc');
            await provider.updateTask(task!.id, { status: 'in_progress' });
            
            // Write unassociated edits
            const logsDir = path.join(PROJECT_PATH, 'logs');
            fs.mkdirSync(logsDir, { recursive: true });
            fs.writeFileSync(path.join(logsDir, 'edits.jsonl'), JSON.stringify({
                id: 'orphan_edit',
                taskId: null,
                toolName: 'tool',
                request: { filename: 'C:/Projects/nda.docx' },
                response: {},
                timestamp: new Date().toISOString()
            }));
            
            const result = await provider.processUnassociatedEdits();
            
            expect(result.success).toBe(true);
            expect(result.associatedCount).toBe(0);
            expect(result.skippedReason).toBe('no_documents');
        });
    });

    describe('associateEditWithTask', () => {
        test('should associate a specific edit with a task', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task } = await provider.addTask('Task', 'desc');
            
            // Write an edit to log
            const logsDir = path.join(PROJECT_PATH, 'logs');
            fs.mkdirSync(logsDir, { recursive: true });
            fs.writeFileSync(path.join(logsDir, 'edits.jsonl'), JSON.stringify({
                id: 'edit_to_associate',
                taskId: null,
                toolName: 'tool',
                request: { filename: 'doc.docx' },
                response: {},
                timestamp: new Date().toISOString()
            }));
            
            const result = await provider.associateEditWithTask('edit_to_associate', task!.id);
            
            expect(result.success).toBe(true);
            
            const updatedTask = provider.currentPlan!.getTaskById(task!.id);
            expect(updatedTask!.editIds).toContain('edit_to_associate');
        });

        test('should fail if edit does not exist', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            const { task } = await provider.addTask('Task', 'desc');
            
            const result = await provider.associateEditWithTask('nonexistent', task!.id);
            
            expect(result.success).toBe(false);
            expect(result.error).toContain('not found');
        });

        test('should fail if task does not exist', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            // Write an edit to log
            const logsDir = path.join(PROJECT_PATH, 'logs');
            fs.mkdirSync(logsDir, { recursive: true });
            fs.writeFileSync(path.join(logsDir, 'edits.jsonl'), JSON.stringify({
                id: 'edit_exists',
                taskId: null,
                toolName: 'tool',
                request: {},
                response: {},
                timestamp: new Date().toISOString()
            }));
            
            const result = await provider.associateEditWithTask('edit_exists', 'nonexistent_task');
            
            expect(result.success).toBe(false);
            expect(result.error).toContain('Task not found');
        });
    });

    describe('getLastProcessedTimestamp / setLastProcessedTimestamp', () => {
        test('should persist and retrieve last processed timestamp', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            
            const timestamp = new Date('2025-12-09T12:00:00Z');
            await provider.setLastProcessedTimestamp(timestamp);
            
            const retrieved = await provider.getLastProcessedTimestamp();
            
            expect(retrieved).toEqual(timestamp);
        });

        test('should return null if no timestamp stored', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            
            const retrieved = await provider.getLastProcessedTimestamp();
            
            expect(retrieved).toBeNull();
        });
    });

    describe('processNewEdits (incremental)', () => {
        test('should only process edits newer than last processed timestamp', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            // Add document and active task
            const { LegalDocument } = require('../models/workplan');
            provider.currentPlan!.addDocument(new LegalDocument({
                filename: 'C:/Projects/nda.docx'
            }));
            const { task } = await provider.addTask('Task', 'desc');
            await provider.updateTask(task!.id, { status: 'in_progress' });
            
            // Set last processed timestamp
            const cutoff = new Date('2025-12-09T11:00:00Z');
            await provider.setLastProcessedTimestamp(cutoff);
            
            // Write edits - some before cutoff, some after
            const logsDir = path.join(PROJECT_PATH, 'logs');
            fs.mkdirSync(logsDir, { recursive: true });
            const editsContent = [
                JSON.stringify({
                    id: 'old_edit',
                    taskId: null,
                    toolName: 'tool',
                    request: { filename: 'C:/Projects/nda.docx' },
                    response: {},
                    timestamp: '2025-12-09T10:00:00.000Z'
                }),
                JSON.stringify({
                    id: 'new_edit',
                    taskId: null,
                    toolName: 'tool',
                    request: { filename: 'C:/Projects/nda.docx' },
                    response: {},
                    timestamp: '2025-12-09T12:00:00.000Z'
                })
            ].join('\n');
            fs.writeFileSync(path.join(logsDir, 'edits.jsonl'), editsContent);
            
            const result = await provider.processNewEdits();
            
            expect(result.associatedCount).toBe(1);
            expect(result.associatedEditIds).toContain('new_edit');
            expect(result.associatedEditIds).not.toContain('old_edit');
        });

        test('should update last processed timestamp after processing', async () => {
            const provider = new PlanProvider(PROJECT_PATH);
            await provider.initialize();
            await provider.getPlan();
            
            // Add document and active task
            const { LegalDocument } = require('../models/workplan');
            provider.currentPlan!.addDocument(new LegalDocument({
                filename: 'C:/Projects/nda.docx'
            }));
            const { task } = await provider.addTask('Task', 'desc');
            await provider.updateTask(task!.id, { status: 'in_progress' });
            
            // Write an edit
            const logsDir = path.join(PROJECT_PATH, 'logs');
            fs.mkdirSync(logsDir, { recursive: true });
            const editTimestamp = new Date('2025-12-09T14:00:00Z');
            fs.writeFileSync(path.join(logsDir, 'edits.jsonl'), JSON.stringify({
                id: 'new_edit',
                taskId: null,
                toolName: 'tool',
                request: { filename: 'C:/Projects/nda.docx' },
                response: {},
                timestamp: editTimestamp.toISOString()
            }));
            
            await provider.processNewEdits();
            
            const lastProcessed = await provider.getLastProcessedTimestamp();
            expect(lastProcessed!.getTime()).toBeGreaterThanOrEqual(editTimestamp.getTime());
        });
    });
});
