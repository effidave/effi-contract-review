/**
 * PlanStorage Persistence Layer Tests
 * 
 * TDD Approach: These tests are written to FAIL initially.
 * Implement the PlanStorage class to make them pass.
 * 
 * File Structure:
 * - [project]/plans/current/plan.md - YAML frontmatter + markdown
 * - [project]/plans/current/plan.meta.json - Fast-load JSON state
 * - [project]/logs/edits.jsonl - Append-only edit log
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { PlanStorage } from '../models/planStorage';
import { WorkPlan, WorkTask, Edit } from '../models/workplan';

// ============================================================================
// Test Helpers
// ============================================================================

/**
 * Create a temporary test directory
 */
function createTempProjectDir(): string {
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'effi-test-'));
    return tempDir;
}

/**
 * Clean up a temporary test directory
 */
function cleanupTempDir(dir: string): void {
    if (fs.existsSync(dir)) {
        fs.rmSync(dir, { recursive: true, force: true });
    }
}

// ============================================================================
// SECTION 1: Directory and File Creation Tests
// ============================================================================

describe('PlanStorage - Directory and File Creation', () => {
    let tempDir: string;

    beforeEach(() => {
        tempDir = createTempProjectDir();
    });

    afterEach(() => {
        cleanupTempDir(tempDir);
    });

    describe('ensureDirectories', () => {
        test('should create plans/current directory if it does not exist', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.ensureDirectories();

            const plansDir = path.join(tempDir, 'plans', 'current');
            expect(fs.existsSync(plansDir)).toBe(true);
        });

        test('should create logs directory if it does not exist', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.ensureDirectories();

            const logsDir = path.join(tempDir, 'logs');
            expect(fs.existsSync(logsDir)).toBe(true);
        });

        test('should not throw if directories already exist', async () => {
            const storage = new PlanStorage(tempDir);
            
            // Create directories first
            fs.mkdirSync(path.join(tempDir, 'plans', 'current'), { recursive: true });
            fs.mkdirSync(path.join(tempDir, 'logs'), { recursive: true });

            // Should not throw
            await expect(storage.ensureDirectories()).resolves.not.toThrow();
        });
    });

    describe('ensurePlanFile', () => {
        test('should create blank plan.md if it does not exist', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.ensurePlanFile();

            const planPath = path.join(tempDir, 'plans', 'current', 'plan.md');
            expect(fs.existsSync(planPath)).toBe(true);
        });

        test('should create plan.md with valid YAML frontmatter', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.ensurePlanFile();

            const planPath = path.join(tempDir, 'plans', 'current', 'plan.md');
            const content = fs.readFileSync(planPath, 'utf-8');
            expect(content).toMatch(/^---\n/);
            expect(content).toContain('tasks:');
            expect(content).toMatch(/\n---\n/);
        });

        test('should not overwrite existing plan.md', async () => {
            const storage = new PlanStorage(tempDir);
            
            // Create directory and file first
            const plansDir = path.join(tempDir, 'plans', 'current');
            fs.mkdirSync(plansDir, { recursive: true });
            const planPath = path.join(plansDir, 'plan.md');
            fs.writeFileSync(planPath, 'existing content');

            await storage.ensurePlanFile();

            const content = fs.readFileSync(planPath, 'utf-8');
            expect(content).toBe('existing content');
        });
    });
});

// ============================================================================
// SECTION 2: Plan File (plan.md) Read/Write Tests
// ============================================================================

describe('PlanStorage - plan.md Read/Write', () => {
    let tempDir: string;

    beforeEach(() => {
        tempDir = createTempProjectDir();
    });

    afterEach(() => {
        cleanupTempDir(tempDir);
    });

    describe('savePlan', () => {
        test('should save WorkPlan to plan.md', async () => {
            const storage = new PlanStorage(tempDir);
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({
                id: 'task001',
                title: 'Review contract',
                description: 'Check all clauses',
                status: 'pending'
            }));

            await storage.savePlan(plan);

            const planPath = path.join(tempDir, 'plans', 'current', 'plan.md');
            expect(fs.existsSync(planPath)).toBe(true);
            const content = fs.readFileSync(planPath, 'utf-8');
            expect(content).toContain('task001');
            expect(content).toContain('Review contract');
        });

        test('should create directories if they do not exist when saving', async () => {
            const storage = new PlanStorage(tempDir);
            const plan = new WorkPlan();

            await storage.savePlan(plan);

            const plansDir = path.join(tempDir, 'plans', 'current');
            expect(fs.existsSync(plansDir)).toBe(true);
        });

        test('should overwrite existing plan.md', async () => {
            const storage = new PlanStorage(tempDir);
            
            // Save first plan
            const plan1 = new WorkPlan();
            plan1.addTaskAtEnd(new WorkTask({ id: 'old', title: 'Old Task', description: 'D' }));
            await storage.savePlan(plan1);

            // Save second plan
            const plan2 = new WorkPlan();
            plan2.addTaskAtEnd(new WorkTask({ id: 'new', title: 'New Task', description: 'D' }));
            await storage.savePlan(plan2);

            const planPath = path.join(tempDir, 'plans', 'current', 'plan.md');
            const content = fs.readFileSync(planPath, 'utf-8');
            expect(content).toContain('New Task');
            expect(content).not.toContain('Old Task');
        });
    });

    describe('loadPlan', () => {
        test('should load WorkPlan from plan.md', async () => {
            const storage = new PlanStorage(tempDir);
            
            // Save a plan first
            const originalPlan = new WorkPlan();
            originalPlan.addTaskAtEnd(new WorkTask({
                id: 'task001',
                title: 'Review contract',
                description: 'Check all clauses',
                status: 'in_progress'
            }));
            await storage.savePlan(originalPlan);

            // Load it back
            const loadedPlan = await storage.loadPlan();

            expect(loadedPlan).toBeDefined();
            expect(loadedPlan!.getTaskCount()).toBe(1);
            expect(loadedPlan!.tasks[0].id).toBe('task001');
            expect(loadedPlan!.tasks[0].title).toBe('Review contract');
            expect(loadedPlan!.tasks[0].status).toBe('in_progress');
        });

        test('should return null if plan.md does not exist', async () => {
            const storage = new PlanStorage(tempDir);

            const loadedPlan = await storage.loadPlan();

            expect(loadedPlan).toBeNull();
        });

        test('should handle empty plan.md', async () => {
            const storage = new PlanStorage(tempDir);
            
            // Create empty file
            const plansDir = path.join(tempDir, 'plans', 'current');
            fs.mkdirSync(plansDir, { recursive: true });
            fs.writeFileSync(path.join(plansDir, 'plan.md'), '');

            const loadedPlan = await storage.loadPlan();

            expect(loadedPlan).toBeDefined();
            expect(loadedPlan!.getTaskCount()).toBe(0);
        });

        test('should preserve all task properties through save/load cycle', async () => {
            const storage = new PlanStorage(tempDir);
            const creationDate = new Date('2025-12-01T10:00:00Z');
            const completionDate = new Date('2025-12-09T15:30:00Z');
            
            const originalPlan = new WorkPlan();
            originalPlan.addTaskAtEnd(new WorkTask({
                id: 'task001',
                title: 'Complex Task',
                description: 'With all properties',
                status: 'completed',
                ordinal: 0,
                creationDate: creationDate,
                completionDate: completionDate,
                editIds: ['edit1', 'edit2']
            }));
            await storage.savePlan(originalPlan);

            const loadedPlan = await storage.loadPlan();

            expect(loadedPlan!.tasks[0].id).toBe('task001');
            expect(loadedPlan!.tasks[0].status).toBe('completed');
            expect(loadedPlan!.tasks[0].creationDate.toISOString()).toBe(creationDate.toISOString());
            expect(loadedPlan!.tasks[0].completionDate!.toISOString()).toBe(completionDate.toISOString());
            expect(loadedPlan!.tasks[0].editIds).toEqual(['edit1', 'edit2']);
        });
    });
});

// ============================================================================
// SECTION 3: Meta File (plan.meta.json) Read/Write Tests
// ============================================================================

describe('PlanStorage - plan.meta.json Read/Write', () => {
    let tempDir: string;

    beforeEach(() => {
        tempDir = createTempProjectDir();
    });

    afterEach(() => {
        cleanupTempDir(tempDir);
    });

    describe('savePlanMeta', () => {
        test('should save WorkPlan to plan.meta.json', async () => {
            const storage = new PlanStorage(tempDir);
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({
                id: 'task001',
                title: 'Review contract',
                description: 'Check all clauses'
            }));

            await storage.savePlanMeta(plan);

            const metaPath = path.join(tempDir, 'plans', 'current', 'plan.meta.json');
            expect(fs.existsSync(metaPath)).toBe(true);
        });

        test('should save valid JSON', async () => {
            const storage = new PlanStorage(tempDir);
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({
                id: 'task001',
                title: 'Test',
                description: 'Desc'
            }));

            await storage.savePlanMeta(plan);

            const metaPath = path.join(tempDir, 'plans', 'current', 'plan.meta.json');
            const content = fs.readFileSync(metaPath, 'utf-8');
            expect(() => JSON.parse(content)).not.toThrow();
        });
    });

    describe('loadPlanMeta', () => {
        test('should load WorkPlan from plan.meta.json', async () => {
            const storage = new PlanStorage(tempDir);
            
            const originalPlan = new WorkPlan();
            originalPlan.addTaskAtEnd(new WorkTask({
                id: 'task001',
                title: 'Test Task',
                description: 'Description'
            }));
            await storage.savePlanMeta(originalPlan);

            const loadedPlan = await storage.loadPlanMeta();

            expect(loadedPlan).toBeDefined();
            expect(loadedPlan!.getTaskCount()).toBe(1);
            expect(loadedPlan!.tasks[0].id).toBe('task001');
        });

        test('should return null if plan.meta.json does not exist', async () => {
            const storage = new PlanStorage(tempDir);

            const loadedPlan = await storage.loadPlanMeta();

            expect(loadedPlan).toBeNull();
        });

        test('should be faster than loading from plan.md', async () => {
            const storage = new PlanStorage(tempDir);
            
            // Create plan with multiple tasks
            const plan = new WorkPlan();
            for (let i = 0; i < 20; i++) {
                plan.addTaskAtEnd(new WorkTask({
                    title: `Task ${i}`,
                    description: `Description for task ${i}`,
                    editIds: ['e1', 'e2', 'e3']
                }));
            }
            await storage.savePlan(plan);
            await storage.savePlanMeta(plan);

            // Time JSON load
            const jsonStart = performance.now();
            await storage.loadPlanMeta();
            const jsonTime = performance.now() - jsonStart;

            // Time YAML load
            const yamlStart = performance.now();
            await storage.loadPlan();
            const yamlTime = performance.now() - yamlStart;

            // JSON should be at least as fast (usually faster)
            // We're not strictly enforcing this as it depends on file size
            expect(jsonTime).toBeLessThanOrEqual(yamlTime * 2);
        });
    });
});

// ============================================================================
// SECTION 4: Edit Log (edits.jsonl) Read/Write Tests
// ============================================================================

describe('PlanStorage - edits.jsonl Read/Write', () => {
    let tempDir: string;

    beforeEach(() => {
        tempDir = createTempProjectDir();
    });

    afterEach(() => {
        cleanupTempDir(tempDir);
    });

    describe('appendEdit', () => {
        test('should append edit to edits.jsonl', async () => {
            const storage = new PlanStorage(tempDir);
            const edit = new Edit({
                taskId: 'task001',
                toolName: 'search_and_replace',
                request: { find: 'foo', replace: 'bar' },
                response: { success: true }
            });

            await storage.appendEdit(edit);

            const editsPath = path.join(tempDir, 'logs', 'edits.jsonl');
            expect(fs.existsSync(editsPath)).toBe(true);
        });

        test('should create logs directory if it does not exist', async () => {
            const storage = new PlanStorage(tempDir);
            const edit = new Edit({
                taskId: 'task001',
                toolName: 'tool',
                request: {},
                response: {}
            });

            await storage.appendEdit(edit);

            const logsDir = path.join(tempDir, 'logs');
            expect(fs.existsSync(logsDir)).toBe(true);
        });

        test('should append multiple edits on separate lines', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({
                id: 'edit1',
                taskId: 'task001',
                toolName: 'tool1',
                request: {},
                response: {}
            }));
            await storage.appendEdit(new Edit({
                id: 'edit2',
                taskId: 'task001',
                toolName: 'tool2',
                request: {},
                response: {}
            }));

            const editsPath = path.join(tempDir, 'logs', 'edits.jsonl');
            const content = fs.readFileSync(editsPath, 'utf-8');
            const lines = content.trim().split('\n');
            expect(lines.length).toBe(2);
        });

        test('should write valid JSON on each line', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({
                taskId: 'task001',
                toolName: 'tool1',
                request: { complex: { nested: true } },
                response: { data: [1, 2, 3] }
            }));

            const editsPath = path.join(tempDir, 'logs', 'edits.jsonl');
            const content = fs.readFileSync(editsPath, 'utf-8');
            const lines = content.trim().split('\n');
            lines.forEach(line => {
                expect(() => JSON.parse(line)).not.toThrow();
            });
        });
    });

    describe('loadEdits', () => {
        test('should load all edits from edits.jsonl', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({
                id: 'edit1',
                taskId: 'task001',
                toolName: 'tool1',
                request: {},
                response: {}
            }));
            await storage.appendEdit(new Edit({
                id: 'edit2',
                taskId: 'task001',
                toolName: 'tool2',
                request: {},
                response: {}
            }));

            const edits = await storage.loadEdits();

            expect(edits.length).toBe(2);
            expect(edits[0].id).toBe('edit1');
            expect(edits[1].id).toBe('edit2');
        });

        test('should return empty array if edits.jsonl does not exist', async () => {
            const storage = new PlanStorage(tempDir);

            const edits = await storage.loadEdits();

            expect(edits).toEqual([]);
        });

        test('should preserve all edit properties', async () => {
            const storage = new PlanStorage(tempDir);
            const timestamp = new Date('2025-12-09T12:00:00Z');
            
            await storage.appendEdit(new Edit({
                id: 'edit1',
                taskId: 'task001',
                toolName: 'search_and_replace',
                request: { find: 'foo', replace: 'bar' },
                response: { success: true, count: 5 },
                timestamp: timestamp
            }));

            const edits = await storage.loadEdits();

            expect(edits[0].id).toBe('edit1');
            expect(edits[0].taskId).toBe('task001');
            expect(edits[0].toolName).toBe('search_and_replace');
            expect(edits[0].request).toEqual({ find: 'foo', replace: 'bar' });
            expect(edits[0].response).toEqual({ success: true, count: 5 });
            expect(edits[0].timestamp.toISOString()).toBe(timestamp.toISOString());
        });
    });

    describe('loadEditsForTask', () => {
        test('should filter edits by task ID', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({
                id: 'edit1',
                taskId: 'task001',
                toolName: 'tool1',
                request: {},
                response: {}
            }));
            await storage.appendEdit(new Edit({
                id: 'edit2',
                taskId: 'task002',
                toolName: 'tool2',
                request: {},
                response: {}
            }));
            await storage.appendEdit(new Edit({
                id: 'edit3',
                taskId: 'task001',
                toolName: 'tool3',
                request: {},
                response: {}
            }));

            const task1Edits = await storage.loadEditsForTask('task001');

            expect(task1Edits.length).toBe(2);
            expect(task1Edits.map((e: Edit) => e.id)).toEqual(['edit1', 'edit3']);
        });

        test('should return empty array if no edits for task', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({
                taskId: 'task001',
                toolName: 'tool1',
                request: {},
                response: {}
            }));

            const edits = await storage.loadEditsForTask('nonexistent');

            expect(edits).toEqual([]);
        });
    });
});

// ============================================================================
// SECTION 5: Combined Save/Load Operations
// ============================================================================

describe('PlanStorage - Combined Operations', () => {
    let tempDir: string;

    beforeEach(() => {
        tempDir = createTempProjectDir();
    });

    afterEach(() => {
        cleanupTempDir(tempDir);
    });

    describe('saveAll', () => {
        test('should save both plan.md and plan.meta.json', async () => {
            const storage = new PlanStorage(tempDir);
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({
                title: 'Test',
                description: 'Desc'
            }));

            await storage.saveAll(plan);

            const planPath = path.join(tempDir, 'plans', 'current', 'plan.md');
            const metaPath = path.join(tempDir, 'plans', 'current', 'plan.meta.json');
            expect(fs.existsSync(planPath)).toBe(true);
            expect(fs.existsSync(metaPath)).toBe(true);
        });
    });

    describe('loadWithEdits', () => {
        test('should load plan and attach edits', async () => {
            const storage = new PlanStorage(tempDir);
            
            // Create and save plan
            const plan = new WorkPlan();
            const task = new WorkTask({
                id: 'task001',
                title: 'Test',
                description: 'Desc'
            });
            plan.addTaskAtEnd(task);
            await storage.savePlan(plan);

            // Add edits
            const edit = new Edit({
                id: 'edit001',
                taskId: 'task001',
                toolName: 'tool',
                request: {},
                response: {}
            });
            await storage.appendEdit(edit);

            // Update task with edit ID and save again
            task.addEditId('edit001');
            await storage.savePlan(plan);

            // Load with edits
            const { plan: loadedPlan, edits } = await storage.loadWithEdits();

            expect(loadedPlan).toBeDefined();
            expect(loadedPlan!.getTaskCount()).toBe(1);
            expect(loadedPlan!.tasks[0].editIds).toContain('edit001');
            expect(edits.length).toBe(1);
            expect(edits[0].id).toBe('edit001');
        });
    });

    describe('getOrCreatePlan', () => {
        test('should create new plan if none exists', async () => {
            const storage = new PlanStorage(tempDir);

            const plan = await storage.getOrCreatePlan();

            expect(plan).toBeDefined();
            expect(plan.getTaskCount()).toBe(0);
            
            // Should have created the file
            const planPath = path.join(tempDir, 'plans', 'current', 'plan.md');
            expect(fs.existsSync(planPath)).toBe(true);
        });

        test('should load existing plan if it exists', async () => {
            const storage = new PlanStorage(tempDir);
            
            // Create a plan first
            const originalPlan = new WorkPlan();
            originalPlan.addTaskAtEnd(new WorkTask({
                id: 'existing',
                title: 'Existing Task',
                description: 'D'
            }));
            await storage.savePlan(originalPlan);

            const plan = await storage.getOrCreatePlan();

            expect(plan.getTaskCount()).toBe(1);
            expect(plan.tasks[0].id).toBe('existing');
        });
    });
});

// ============================================================================
// SECTION 6: File Path Tests
// ============================================================================

describe('PlanStorage - File Paths', () => {
    let tempDir: string;

    beforeEach(() => {
        tempDir = createTempProjectDir();
    });

    afterEach(() => {
        cleanupTempDir(tempDir);
    });

    test('should expose correct file paths', () => {
        const storage = new PlanStorage(tempDir);

        expect(storage.planFilePath).toBe(path.join(tempDir, 'plans', 'current', 'plan.md'));
        expect(storage.planMetaFilePath).toBe(path.join(tempDir, 'plans', 'current', 'plan.meta.json'));
        expect(storage.editsFilePath).toBe(path.join(tempDir, 'logs', 'edits.jsonl'));
    });

    test('should handle Windows-style paths', () => {
        // This test ensures path handling works on Windows
        const windowsPath = tempDir.replace(/\//g, '\\');
        const storage = new PlanStorage(windowsPath);

        expect(storage.planFilePath).toContain('plans');
        expect(storage.planFilePath).toContain('current');
        expect(storage.planFilePath).toContain('plan.md');
    });
});

// ============================================================================
// SECTION 7: Error Handling Tests
// ============================================================================

describe('PlanStorage - Error Handling', () => {
    let tempDir: string;

    beforeEach(() => {
        tempDir = createTempProjectDir();
    });

    afterEach(() => {
        cleanupTempDir(tempDir);
    });

    test('should handle corrupted plan.md gracefully', async () => {
        const storage = new PlanStorage(tempDir);
        
        // Create corrupted file
        const plansDir = path.join(tempDir, 'plans', 'current');
        fs.mkdirSync(plansDir, { recursive: true });
        fs.writeFileSync(path.join(plansDir, 'plan.md'), '---\ninvalid: yaml: content\n---');

        // Should not throw, should return empty plan
        const plan = await storage.loadPlan();
        expect(plan).toBeDefined();
    });

    test('should handle corrupted plan.meta.json gracefully', async () => {
        const storage = new PlanStorage(tempDir);
        
        // Create corrupted file
        const plansDir = path.join(tempDir, 'plans', 'current');
        fs.mkdirSync(plansDir, { recursive: true });
        fs.writeFileSync(path.join(plansDir, 'plan.meta.json'), 'not valid json');

        // Should not throw, should return null
        const plan = await storage.loadPlanMeta();
        expect(plan).toBeNull();
    });

    test('should handle corrupted edits.jsonl gracefully', async () => {
        const storage = new PlanStorage(tempDir);
        
        // Create file with some valid and some invalid lines
        const logsDir = path.join(tempDir, 'logs');
        fs.mkdirSync(logsDir, { recursive: true });
        const validEdit = new Edit({
            id: 'valid',
            taskId: 't1',
            toolName: 'tool',
            request: {},
            response: {}
        });
        fs.writeFileSync(
            path.join(logsDir, 'edits.jsonl'),
            validEdit.toJSONL() + '\n' + 'not valid json\n'
        );

        // Should skip invalid lines and return valid ones
        const edits = await storage.loadEdits();
        expect(edits.length).toBe(1);
        expect(edits[0].id).toBe('valid');
    });
});

// ============================================================================
// SECTION 8: Edit Retrieval by ID Tests
// ============================================================================

describe('PlanStorage - Edit Retrieval by ID', () => {
    let tempDir: string;

    beforeEach(() => {
        tempDir = createTempProjectDir();
    });

    afterEach(() => {
        cleanupTempDir(tempDir);
    });

    describe('getEditsByIds', () => {
        test('should retrieve specific edits by their IDs', async () => {
            const storage = new PlanStorage(tempDir);
            
            // Create multiple edits
            await storage.appendEdit(new Edit({
                id: 'edit001',
                taskId: 'task1',
                toolName: 'search_and_replace',
                request: { find: 'foo' },
                response: { success: true }
            }));
            await storage.appendEdit(new Edit({
                id: 'edit002',
                taskId: 'task1',
                toolName: 'add_paragraph',
                request: { text: 'hello' },
                response: { success: true }
            }));
            await storage.appendEdit(new Edit({
                id: 'edit003',
                taskId: 'task2',
                toolName: 'delete_clause',
                request: { clause: '5.1' },
                response: { success: true }
            }));

            // Retrieve only specific IDs
            const edits = await storage.getEditsByIds(['edit001', 'edit003']);

            expect(edits.length).toBe(2);
            expect(edits.map(e => e.id)).toContain('edit001');
            expect(edits.map(e => e.id)).toContain('edit003');
            expect(edits.map(e => e.id)).not.toContain('edit002');
        });

        test('should return empty array for non-existent IDs', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({
                id: 'edit001',
                taskId: 'task1',
                toolName: 'tool',
                request: {},
                response: {}
            }));

            const edits = await storage.getEditsByIds(['nonexistent', 'alsonotreal']);

            expect(edits).toEqual([]);
        });

        test('should return empty array when log file does not exist', async () => {
            const storage = new PlanStorage(tempDir);

            const edits = await storage.getEditsByIds(['edit001']);

            expect(edits).toEqual([]);
        });

        test('should preserve edit order matching requested IDs order', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({ id: 'aaa', taskId: 't', toolName: 'tool', request: {}, response: {} }));
            await storage.appendEdit(new Edit({ id: 'bbb', taskId: 't', toolName: 'tool', request: {}, response: {} }));
            await storage.appendEdit(new Edit({ id: 'ccc', taskId: 't', toolName: 'tool', request: {}, response: {} }));

            // Request in different order than log
            const edits = await storage.getEditsByIds(['ccc', 'aaa']);

            expect(edits[0].id).toBe('ccc');
            expect(edits[1].id).toBe('aaa');
        });

        test('should preserve all edit properties when retrieving', async () => {
            const storage = new PlanStorage(tempDir);
            const timestamp = new Date('2025-12-09T14:30:00Z');
            
            await storage.appendEdit(new Edit({
                id: 'edit001',
                taskId: 'task123',
                toolName: 'search_and_replace',
                request: { filename: 'doc.docx', find: 'foo', replace: 'bar' },
                response: { success: true, replacements: 5 },
                timestamp: timestamp
            }));

            const edits = await storage.getEditsByIds(['edit001']);

            expect(edits[0].id).toBe('edit001');
            expect(edits[0].taskId).toBe('task123');
            expect(edits[0].toolName).toBe('search_and_replace');
            expect(edits[0].request).toEqual({ filename: 'doc.docx', find: 'foo', replace: 'bar' });
            expect(edits[0].response).toEqual({ success: true, replacements: 5 });
            expect(edits[0].timestamp.toISOString()).toBe(timestamp.toISOString());
        });

        test('should handle partial matches (some IDs exist, some do not)', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({ id: 'exists1', taskId: 't', toolName: 'tool', request: {}, response: {} }));
            await storage.appendEdit(new Edit({ id: 'exists2', taskId: 't', toolName: 'tool', request: {}, response: {} }));

            const edits = await storage.getEditsByIds(['exists1', 'notreal', 'exists2', 'alsonotreal']);

            expect(edits.length).toBe(2);
            expect(edits.map(e => e.id)).toEqual(['exists1', 'exists2']);
        });
    });

    describe('getAllEdits', () => {
        test('should return all edits from the log', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({ id: 'e1', taskId: 't1', toolName: 'tool1', request: {}, response: {} }));
            await storage.appendEdit(new Edit({ id: 'e2', taskId: 't1', toolName: 'tool2', request: {}, response: {} }));
            await storage.appendEdit(new Edit({ id: 'e3', taskId: 't2', toolName: 'tool3', request: {}, response: {} }));

            const edits = await storage.getAllEdits();

            expect(edits.length).toBe(3);
            expect(edits.map(e => e.id)).toEqual(['e1', 'e2', 'e3']);
        });

        test('should return empty array when log file does not exist', async () => {
            const storage = new PlanStorage(tempDir);

            const edits = await storage.getAllEdits();

            expect(edits).toEqual([]);
        });

        test('should return edits in chronological order (as logged)', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({ id: 'first', taskId: 't', toolName: 'tool', request: {}, response: {}, timestamp: new Date('2025-12-09T10:00:00Z') }));
            await storage.appendEdit(new Edit({ id: 'second', taskId: 't', toolName: 'tool', request: {}, response: {}, timestamp: new Date('2025-12-09T11:00:00Z') }));
            await storage.appendEdit(new Edit({ id: 'third', taskId: 't', toolName: 'tool', request: {}, response: {}, timestamp: new Date('2025-12-09T12:00:00Z') }));

            const edits = await storage.getAllEdits();

            expect(edits[0].id).toBe('first');
            expect(edits[1].id).toBe('second');
            expect(edits[2].id).toBe('third');
        });
    });

    describe('getEditById', () => {
        test('should return single edit by ID', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({ id: 'target', taskId: 't1', toolName: 'tool', request: { data: 123 }, response: { ok: true } }));
            await storage.appendEdit(new Edit({ id: 'other', taskId: 't2', toolName: 'tool', request: {}, response: {} }));

            const edit = await storage.getEditById('target');

            expect(edit).toBeDefined();
            expect(edit!.id).toBe('target');
            expect(edit!.request).toEqual({ data: 123 });
        });

        test('should return null for non-existent ID', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({ id: 'exists', taskId: 't', toolName: 'tool', request: {}, response: {} }));

            const edit = await storage.getEditById('nonexistent');

            expect(edit).toBeNull();
        });

        test('should return null when log file does not exist', async () => {
            const storage = new PlanStorage(tempDir);

            const edit = await storage.getEditById('anyid');

            expect(edit).toBeNull();
        });
    });

    describe('getNewEditsSince', () => {
        test('should return edits after a given timestamp', async () => {
            const storage = new PlanStorage(tempDir);
            const cutoff = new Date('2025-12-09T11:00:00Z');
            
            await storage.appendEdit(new Edit({ id: 'old1', taskId: 't', toolName: 'tool', request: {}, response: {}, timestamp: new Date('2025-12-09T10:00:00Z') }));
            await storage.appendEdit(new Edit({ id: 'old2', taskId: 't', toolName: 'tool', request: {}, response: {}, timestamp: new Date('2025-12-09T10:30:00Z') }));
            await storage.appendEdit(new Edit({ id: 'new1', taskId: 't', toolName: 'tool', request: {}, response: {}, timestamp: new Date('2025-12-09T11:30:00Z') }));
            await storage.appendEdit(new Edit({ id: 'new2', taskId: 't', toolName: 'tool', request: {}, response: {}, timestamp: new Date('2025-12-09T12:00:00Z') }));

            const newEdits = await storage.getNewEditsSince(cutoff);

            expect(newEdits.length).toBe(2);
            expect(newEdits.map(e => e.id)).toEqual(['new1', 'new2']);
        });

        test('should return all edits if cutoff is before all entries', async () => {
            const storage = new PlanStorage(tempDir);
            const cutoff = new Date('2020-01-01T00:00:00Z');
            
            await storage.appendEdit(new Edit({ id: 'e1', taskId: 't', toolName: 'tool', request: {}, response: {}, timestamp: new Date('2025-12-09T10:00:00Z') }));
            await storage.appendEdit(new Edit({ id: 'e2', taskId: 't', toolName: 'tool', request: {}, response: {}, timestamp: new Date('2025-12-09T11:00:00Z') }));

            const newEdits = await storage.getNewEditsSince(cutoff);

            expect(newEdits.length).toBe(2);
        });

        test('should return empty array if cutoff is after all entries', async () => {
            const storage = new PlanStorage(tempDir);
            const cutoff = new Date('2030-01-01T00:00:00Z');
            
            await storage.appendEdit(new Edit({ id: 'e1', taskId: 't', toolName: 'tool', request: {}, response: {}, timestamp: new Date('2025-12-09T10:00:00Z') }));

            const newEdits = await storage.getNewEditsSince(cutoff);

            expect(newEdits).toEqual([]);
        });

        test('should return empty array when log file does not exist', async () => {
            const storage = new PlanStorage(tempDir);

            const newEdits = await storage.getNewEditsSince(new Date());

            expect(newEdits).toEqual([]);
        });
    });

    describe('getUnassociatedEdits', () => {
        test('should return edits with null taskId', async () => {
            const storage = new PlanStorage(tempDir);
            
            // Manually write edits with null taskId (simulating MCP server logs)
            const logsDir = path.join(tempDir, 'logs');
            fs.mkdirSync(logsDir, { recursive: true });
            const editsContent = [
                JSON.stringify({ id: 'assigned1', taskId: 'task1', toolName: 'tool', request: {}, response: {}, timestamp: new Date().toISOString() }),
                JSON.stringify({ id: 'unassigned1', taskId: null, toolName: 'tool', request: { filename: 'doc.docx' }, response: {}, timestamp: new Date().toISOString() }),
                JSON.stringify({ id: 'assigned2', taskId: 'task2', toolName: 'tool', request: {}, response: {}, timestamp: new Date().toISOString() }),
                JSON.stringify({ id: 'unassigned2', taskId: null, toolName: 'tool', request: { filename: 'other.docx' }, response: {}, timestamp: new Date().toISOString() })
            ].join('\n');
            fs.writeFileSync(path.join(logsDir, 'edits.jsonl'), editsContent);

            const unassigned = await storage.getUnassociatedEdits();

            expect(unassigned.length).toBe(2);
            expect(unassigned.map((e: Edit) => e.id)).toEqual(['unassigned1', 'unassigned2']);
        });

        test('should return empty array if all edits are assigned', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({ id: 'e1', taskId: 'task1', toolName: 'tool', request: {}, response: {} }));
            await storage.appendEdit(new Edit({ id: 'e2', taskId: 'task2', toolName: 'tool', request: {}, response: {} }));

            const unassigned = await storage.getUnassociatedEdits();

            expect(unassigned).toEqual([]);
        });

        test('should return empty array when log file does not exist', async () => {
            const storage = new PlanStorage(tempDir);

            const unassigned = await storage.getUnassociatedEdits();

            expect(unassigned).toEqual([]);
        });
    });

    describe('getEditsForDocument', () => {
        test('should return edits that affected a specific document', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({
                id: 'e1', taskId: 't1', toolName: 'search_and_replace',
                request: { filename: 'C:/Projects/nda.docx', find: 'foo' },
                response: {}
            }));
            await storage.appendEdit(new Edit({
                id: 'e2', taskId: 't1', toolName: 'add_paragraph',
                request: { filename: 'C:/Projects/agreement.docx', text: 'hello' },
                response: {}
            }));
            await storage.appendEdit(new Edit({
                id: 'e3', taskId: 't1', toolName: 'delete_clause',
                request: { filename: 'C:/Projects/nda.docx', clause: '5.1' },
                response: {}
            }));

            const ndaEdits = await storage.getEditsForDocument('C:/Projects/nda.docx');

            expect(ndaEdits.length).toBe(2);
            expect(ndaEdits.map((e: Edit) => e.id)).toEqual(['e1', 'e3']);
        });

        test('should match filenames case-insensitively', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({
                id: 'e1', taskId: 't1', toolName: 'tool',
                request: { filename: 'C:/Projects/NDA.docx' },
                response: {}
            }));

            const edits = await storage.getEditsForDocument('C:/Projects/nda.docx');

            expect(edits.length).toBe(1);
        });

        test('should normalize path separators when matching', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({
                id: 'e1', taskId: 't1', toolName: 'tool',
                request: { filename: 'C:\\Projects\\nda.docx' },
                response: {}
            }));

            const edits = await storage.getEditsForDocument('C:/Projects/nda.docx');

            expect(edits.length).toBe(1);
        });

        test('should return empty array if no edits for document', async () => {
            const storage = new PlanStorage(tempDir);
            
            await storage.appendEdit(new Edit({
                id: 'e1', taskId: 't1', toolName: 'tool',
                request: { filename: 'C:/Projects/other.docx' },
                response: {}
            }));

            const edits = await storage.getEditsForDocument('C:/Projects/nda.docx');

            expect(edits).toEqual([]);
        });
    });
});
