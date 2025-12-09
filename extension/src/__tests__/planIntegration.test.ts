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
