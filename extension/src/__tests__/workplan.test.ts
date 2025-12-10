/**
 * WorkPlan, WorkTask, and Edit Class Tests
 * 
 * TDD Approach: These tests are written to FAIL initially.
 * Implement the classes to make them pass.
 * 
 * Classes:
 * - Edit: Records MCP tool calls with request/response
 * - WorkTask: Individual task with title, description, status, edits
 * - WorkPlan: Manages collection of WorkTasks with ordering and persistence
 */

import { Edit, WorkTask, WorkPlan, LegalDocument, TaskStatus } from '../models/workplan';

// ============================================================================
// SECTION 1: Edit Class Tests
// ============================================================================

describe('Edit class', () => {
    describe('constructor and properties', () => {
        test('should create an Edit with all required properties', () => {
            const edit = new Edit({
                taskId: 'task123',
                toolName: 'search_and_replace',
                request: { filename: 'doc.docx', find_text: 'foo', replace_text: 'bar' },
                response: { success: true, replacements: 3 }
            });

            expect(edit.id).toBeDefined();
            expect(edit.id).toMatch(/^wt[a-f0-9]{8}$/); // wt + 8-char hex hash
            expect(edit.taskId).toBe('task123');
            expect(edit.toolName).toBe('search_and_replace');
            expect(edit.request).toEqual({ filename: 'doc.docx', find_text: 'foo', replace_text: 'bar' });
            expect(edit.response).toEqual({ success: true, replacements: 3 });
            expect(edit.timestamp).toBeInstanceOf(Date);
        });

        test('should auto-generate unique IDs for different edits', () => {
            const edit1 = new Edit({
                taskId: 'task1',
                toolName: 'tool1',
                request: { a: 1 },
                response: { b: 2 }
            });
            const edit2 = new Edit({
                taskId: 'task2',
                toolName: 'tool2',
                request: { c: 3 },
                response: { d: 4 }
            });

            expect(edit1.id).not.toBe(edit2.id);
        });

        test('should allow custom ID when provided', () => {
            const edit = new Edit({
                id: 'customid',
                taskId: 'task1',
                toolName: 'tool1',
                request: {},
                response: {}
            });

            expect(edit.id).toBe('customid');
        });

        test('should use provided timestamp when given', () => {
            const customDate = new Date('2025-01-15T10:30:00Z');
            const edit = new Edit({
                taskId: 'task1',
                toolName: 'tool1',
                request: {},
                response: {},
                timestamp: customDate
            });

            expect(edit.timestamp).toEqual(customDate);
        });
    });

    describe('serialization', () => {
        test('should serialize to JSON object', () => {
            const edit = new Edit({
                id: 'abc12345',
                taskId: 'task123',
                toolName: 'add_paragraph',
                request: { text: 'hello' },
                response: { success: true },
                timestamp: new Date('2025-12-09T12:00:00Z')
            });

            const json = edit.toJSON();

            expect(json).toEqual({
                id: 'abc12345',
                taskId: 'task123',
                toolName: 'add_paragraph',
                request: { text: 'hello' },
                response: { success: true },
                timestamp: '2025-12-09T12:00:00.000Z'
            });
        });

        test('should deserialize from JSON object', () => {
            const json = {
                id: 'abc12345',
                taskId: 'task123',
                toolName: 'add_paragraph',
                request: { text: 'hello' },
                response: { success: true },
                timestamp: '2025-12-09T12:00:00.000Z'
            };

            const edit = Edit.fromJSON(json);

            expect(edit.id).toBe('abc12345');
            expect(edit.taskId).toBe('task123');
            expect(edit.toolName).toBe('add_paragraph');
            expect(edit.request).toEqual({ text: 'hello' });
            expect(edit.response).toEqual({ success: true });
            expect(edit.timestamp).toEqual(new Date('2025-12-09T12:00:00.000Z'));
        });

        test('should serialize to JSONL format string', () => {
            const edit = new Edit({
                id: 'abc12345',
                taskId: 'task123',
                toolName: 'tool1',
                request: { a: 1 },
                response: { b: 2 },
                timestamp: new Date('2025-12-09T12:00:00Z')
            });

            const jsonlLine = edit.toJSONL();

            expect(jsonlLine).not.toContain('\n');
            expect(JSON.parse(jsonlLine)).toEqual(edit.toJSON());
        });
    });
});

// ============================================================================
// SECTION 2: WorkTask Class Tests
// ============================================================================

describe('WorkTask class', () => {
    describe('constructor and properties', () => {
        test('should create a WorkTask with required properties', () => {
            const task = new WorkTask({
                title: 'Review liability clause',
                description: 'Check limitation of liability terms against precedent'
            });

            expect(task.id).toBeDefined();
            expect(task.id).toMatch(/^wt[a-f0-9]{8}$/);
            expect(task.title).toBe('Review liability clause');
            expect(task.description).toBe('Check limitation of liability terms against precedent');
            expect(task.status).toBe('pending');
            expect(task.editIds).toEqual([]);
            expect(task.creationDate).toBeInstanceOf(Date);
            expect(task.completionDate).toBeNull();
            expect(task.ordinal).toBe(0);
        });

        test('should allow custom properties', () => {
            const creationDate = new Date('2025-12-01T10:00:00Z');
            const task = new WorkTask({
                id: 'custom01',
                title: 'Task',
                description: 'Desc',
                status: 'in_progress',
                ordinal: 5,
                creationDate: creationDate,
                editIds: ['edit1', 'edit2']
            });

            expect(task.id).toBe('custom01');
            expect(task.status).toBe('in_progress');
            expect(task.ordinal).toBe(5);
            expect(task.creationDate).toEqual(creationDate);
            expect(task.editIds).toEqual(['edit1', 'edit2']);
        });
    });

    describe('status management', () => {
        test('should change status to in_progress', () => {
            const task = new WorkTask({ title: 'Task', description: 'Desc' });
            
            task.start();

            expect(task.status).toBe('in_progress');
            expect(task.completionDate).toBeNull();
        });

        test('should change status to completed and set completion date', () => {
            const task = new WorkTask({ title: 'Task', description: 'Desc' });
            
            task.complete();

            expect(task.status).toBe('completed');
            expect(task.completionDate).toBeInstanceOf(Date);
        });

        test('should change status to blocked', () => {
            const task = new WorkTask({ title: 'Task', description: 'Desc' });
            
            task.block();

            expect(task.status).toBe('blocked');
        });

        test('should reset to pending', () => {
            const task = new WorkTask({ title: 'Task', description: 'Desc', status: 'completed' });
            
            task.reset();

            expect(task.status).toBe('pending');
            expect(task.completionDate).toBeNull();
        });

        test('should report isOpen correctly', () => {
            const pending = new WorkTask({ title: 'T', description: 'D', status: 'pending' });
            const inProgress = new WorkTask({ title: 'T', description: 'D', status: 'in_progress' });
            const blocked = new WorkTask({ title: 'T', description: 'D', status: 'blocked' });
            const completed = new WorkTask({ title: 'T', description: 'D', status: 'completed' });

            expect(pending.isOpen()).toBe(true);
            expect(inProgress.isOpen()).toBe(true);
            expect(blocked.isOpen()).toBe(true);
            expect(completed.isOpen()).toBe(false);
        });
    });

    describe('edit management', () => {
        test('should add edit ID to task', () => {
            const task = new WorkTask({ title: 'Task', description: 'Desc' });
            
            task.addEditId('edit123');

            expect(task.editIds).toContain('edit123');
        });

        test('should add multiple edit IDs', () => {
            const task = new WorkTask({ title: 'Task', description: 'Desc' });
            
            task.addEditId('edit1');
            task.addEditId('edit2');
            task.addEditId('edit3');

            expect(task.editIds).toEqual(['edit1', 'edit2', 'edit3']);
        });

        test('should not add duplicate edit IDs', () => {
            const task = new WorkTask({ title: 'Task', description: 'Desc' });
            
            task.addEditId('edit1');
            task.addEditId('edit1');

            expect(task.editIds).toEqual(['edit1']);
        });
    });

    describe('serialization', () => {
        test('should serialize to JSON object', () => {
            const task = new WorkTask({
                id: 'task1234',
                title: 'Review clause',
                description: 'Check terms',
                status: 'in_progress',
                ordinal: 2,
                creationDate: new Date('2025-12-09T10:00:00Z'),
                editIds: ['e1', 'e2']
            });

            const json = task.toJSON();

            expect(json).toEqual({
                id: 'task1234',
                title: 'Review clause',
                description: 'Check terms',
                status: 'in_progress',
                ordinal: 2,
                creationDate: '2025-12-09T10:00:00.000Z',
                completionDate: null,
                editIds: ['e1', 'e2']
            });
        });

        test('should deserialize from JSON object', () => {
            const json = {
                id: 'task1234',
                title: 'Review clause',
                description: 'Check terms',
                status: 'completed' as TaskStatus,
                ordinal: 2,
                creationDate: '2025-12-09T10:00:00.000Z',
                completionDate: '2025-12-09T15:00:00.000Z',
                editIds: ['e1', 'e2']
            };

            const task = WorkTask.fromJSON(json);

            expect(task.id).toBe('task1234');
            expect(task.title).toBe('Review clause');
            expect(task.description).toBe('Check terms');
            expect(task.status).toBe('completed');
            expect(task.ordinal).toBe(2);
            expect(task.creationDate).toEqual(new Date('2025-12-09T10:00:00.000Z'));
            expect(task.completionDate).toEqual(new Date('2025-12-09T15:00:00.000Z'));
            expect(task.editIds).toEqual(['e1', 'e2']);
        });

        test('should serialize to YAML-friendly object', () => {
            const task = new WorkTask({
                id: 'task1234',
                title: 'Review clause',
                description: 'Check terms',
                status: 'pending',
                ordinal: 1
            });

            const yaml = task.toYAML();

            expect(yaml).toHaveProperty('id', 'task1234');
            expect(yaml).toHaveProperty('title', 'Review clause');
            expect(yaml).toHaveProperty('status', 'pending');
            expect(yaml).toHaveProperty('ordinal', 1);
        });
    });
});

// ============================================================================
// SECTION 3: WorkPlan Class Tests
// ============================================================================

describe('WorkPlan class', () => {
    describe('constructor', () => {
        test('should create an empty WorkPlan', () => {
            const plan = new WorkPlan();

            expect(plan.tasks).toEqual([]);
            expect(plan.getTaskCount()).toBe(0);
        });

        test('should create WorkPlan with initial tasks', () => {
            const task1 = new WorkTask({ title: 'Task 1', description: 'Desc 1' });
            const task2 = new WorkTask({ title: 'Task 2', description: 'Desc 2' });
            
            const plan = new WorkPlan([task1, task2]);

            expect(plan.getTaskCount()).toBe(2);
        });
    });

    describe('task addition', () => {
        test('should add task at end', () => {
            const plan = new WorkPlan();
            const task = new WorkTask({ title: 'Task 1', description: 'Desc' });

            plan.addTaskAtEnd(task);

            expect(plan.getTaskCount()).toBe(1);
            expect(plan.tasks[0].title).toBe('Task 1');
            expect(plan.tasks[0].ordinal).toBe(0);
        });

        test('should add multiple tasks at end with correct ordinals', () => {
            const plan = new WorkPlan();
            
            plan.addTaskAtEnd(new WorkTask({ title: 'Task 1', description: 'D1' }));
            plan.addTaskAtEnd(new WorkTask({ title: 'Task 2', description: 'D2' }));
            plan.addTaskAtEnd(new WorkTask({ title: 'Task 3', description: 'D3' }));

            expect(plan.tasks[0].ordinal).toBe(0);
            expect(plan.tasks[1].ordinal).toBe(1);
            expect(plan.tasks[2].ordinal).toBe(2);
        });

        test('should add task at start', () => {
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({ title: 'Original', description: 'D' }));

            plan.addTaskAtStart(new WorkTask({ title: 'New First', description: 'D' }));

            expect(plan.tasks[0].title).toBe('New First');
            expect(plan.tasks[0].ordinal).toBe(0);
            expect(plan.tasks[1].title).toBe('Original');
            expect(plan.tasks[1].ordinal).toBe(1);
        });

        test('should add task at specific ordinal', () => {
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({ title: 'Task 0', description: 'D' }));
            plan.addTaskAtEnd(new WorkTask({ title: 'Task 1', description: 'D' }));
            plan.addTaskAtEnd(new WorkTask({ title: 'Task 2', description: 'D' }));

            // ordinal is 0-based: ordinal 1 = insert at index 1
            plan.addTaskAtOrdinal(new WorkTask({ title: 'Inserted', description: 'D' }), 1);

            expect(plan.tasks[0].title).toBe('Task 0');
            expect(plan.tasks[0].ordinal).toBe(0);
            expect(plan.tasks[1].title).toBe('Inserted');
            expect(plan.tasks[1].ordinal).toBe(1);
            expect(plan.tasks[2].title).toBe('Task 1');
            expect(plan.tasks[2].ordinal).toBe(2);
            expect(plan.tasks[3].title).toBe('Task 2');
            expect(plan.tasks[3].ordinal).toBe(3);
        });

        test('should handle adding at ordinal beyond current length', () => {
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({ title: 'Task 0', description: 'D' }));

            plan.addTaskAtOrdinal(new WorkTask({ title: 'At End', description: 'D' }), 100);

            expect(plan.getTaskCount()).toBe(2);
            expect(plan.tasks[1].title).toBe('At End');
            expect(plan.tasks[1].ordinal).toBe(1);
        });
    });

    describe('task removal', () => {
        test('should remove task by ID', () => {
            const plan = new WorkPlan();
            const task = new WorkTask({ id: 'remove01', title: 'To Remove', description: 'D' });
            plan.addTaskAtEnd(task);
            plan.addTaskAtEnd(new WorkTask({ title: 'Keep', description: 'D' }));

            const removed = plan.removeTask('remove01');

            expect(removed).toBe(true);
            expect(plan.getTaskCount()).toBe(1);
            expect(plan.tasks[0].title).toBe('Keep');
        });

        test('should update ordinals after removal', () => {
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({ id: 't0', title: 'Task 0', description: 'D' }));
            plan.addTaskAtEnd(new WorkTask({ id: 't1', title: 'Task 1', description: 'D' }));
            plan.addTaskAtEnd(new WorkTask({ id: 't2', title: 'Task 2', description: 'D' }));

            plan.removeTask('t1');

            expect(plan.tasks[0].ordinal).toBe(0);
            expect(plan.tasks[1].ordinal).toBe(1);
            expect(plan.tasks[1].title).toBe('Task 2');
        });

        test('should return false when removing non-existent task', () => {
            const plan = new WorkPlan();

            const removed = plan.removeTask('nonexistent');

            expect(removed).toBe(false);
        });
    });

    describe('task movement', () => {
        test('should move task to new ordinal', () => {
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({ id: 't0', title: 'Task 0', description: 'D' }));
            plan.addTaskAtEnd(new WorkTask({ id: 't1', title: 'Task 1', description: 'D' }));
            plan.addTaskAtEnd(new WorkTask({ id: 't2', title: 'Task 2', description: 'D' }));

            // ordinal is 0-based: ordinal 0 = first position (index 0)
            plan.moveTask('t2', 0);

            expect(plan.tasks[0].id).toBe('t2');
            expect(plan.tasks[1].id).toBe('t0');
            expect(plan.tasks[2].id).toBe('t1');
            expect(plan.tasks[0].ordinal).toBe(0);
            expect(plan.tasks[1].ordinal).toBe(1);
            expect(plan.tasks[2].ordinal).toBe(2);
        });

        test('should move task forward in list', () => {
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({ id: 't0', title: 'Task 0', description: 'D' }));
            plan.addTaskAtEnd(new WorkTask({ id: 't1', title: 'Task 1', description: 'D' }));
            plan.addTaskAtEnd(new WorkTask({ id: 't2', title: 'Task 2', description: 'D' }));

            // ordinal is 0-based: ordinal 2 = third position (index 2)
            plan.moveTask('t0', 2);

            expect(plan.tasks[0].id).toBe('t1');
            expect(plan.tasks[1].id).toBe('t2');
            expect(plan.tasks[2].id).toBe('t0');
        });

        test('should return false when moving non-existent task', () => {
            const plan = new WorkPlan();

            // ordinal 0 = first position
            const moved = plan.moveTask('nonexistent', 0);

            expect(moved).toBe(false);
        });
    });

    describe('task retrieval', () => {
        test('should get task by ID', () => {
            const plan = new WorkPlan();
            const task = new WorkTask({ id: 'findme', title: 'Find Me', description: 'D' });
            plan.addTaskAtEnd(task);

            const found = plan.getTaskById('findme');

            expect(found).toBeDefined();
            expect(found?.title).toBe('Find Me');
        });

        test('should return undefined for non-existent task', () => {
            const plan = new WorkPlan();

            const found = plan.getTaskById('nonexistent');

            expect(found).toBeUndefined();
        });

        test('should get open tasks (pending, in_progress, blocked)', () => {
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({ title: 'Pending', description: 'D', status: 'pending' }));
            plan.addTaskAtEnd(new WorkTask({ title: 'In Progress', description: 'D', status: 'in_progress' }));
            plan.addTaskAtEnd(new WorkTask({ title: 'Blocked', description: 'D', status: 'blocked' }));
            plan.addTaskAtEnd(new WorkTask({ title: 'Completed', description: 'D', status: 'completed' }));

            const open = plan.getOpenTasks();

            expect(open.length).toBe(3);
            expect(open.map((t: WorkTask) => t.title)).toEqual(['Pending', 'In Progress', 'Blocked']);
        });

        test('should get completed tasks', () => {
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({ title: 'Pending', description: 'D', status: 'pending' }));
            plan.addTaskAtEnd(new WorkTask({ title: 'Completed 1', description: 'D', status: 'completed' }));
            plan.addTaskAtEnd(new WorkTask({ title: 'Completed 2', description: 'D', status: 'completed' }));

            const completed = plan.getCompletedTasks();

            expect(completed.length).toBe(2);
            expect(completed.map((t: WorkTask) => t.title)).toEqual(['Completed 1', 'Completed 2']);
        });

        test('should get tasks by status', () => {
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({ title: 'P1', description: 'D', status: 'pending' }));
            plan.addTaskAtEnd(new WorkTask({ title: 'IP1', description: 'D', status: 'in_progress' }));
            plan.addTaskAtEnd(new WorkTask({ title: 'P2', description: 'D', status: 'pending' }));

            const pending = plan.getTasksByStatus('pending');

            expect(pending.length).toBe(2);
            expect(pending.map((t: WorkTask) => t.title)).toEqual(['P1', 'P2']);
        });
    });

    describe('serialization - YAML frontmatter', () => {
        test('should serialize to YAML frontmatter format', () => {
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({
                id: 'task1',
                title: 'First Task',
                description: 'Do something',
                status: 'pending',
                ordinal: 0
            }));

            const yaml = plan.toYAMLFrontmatter();

            expect(yaml).toContain('---');
            expect(yaml).toContain('tasks:');
            expect(yaml).toContain('id: task1');
            expect(yaml).toContain('title: First Task');
            expect(yaml).toContain('status: pending');
        });

        test('should deserialize from YAML frontmatter', () => {
            const yaml = `---
tasks:
  - id: task1
    title: First Task
    description: Do something
    status: pending
    ordinal: 0
    creationDate: '2025-12-09T10:00:00.000Z'
    completionDate: null
    editIds: []
  - id: task2
    title: Second Task
    description: Another thing
    status: in_progress
    ordinal: 1
    creationDate: '2025-12-09T11:00:00.000Z'
    completionDate: null
    editIds:
      - edit1
---

# Work Plan

Content here...
`;

            const plan = WorkPlan.fromYAMLFrontmatter(yaml);

            expect(plan.getTaskCount()).toBe(2);
            expect(plan.tasks[0].title).toBe('First Task');
            expect(plan.tasks[1].title).toBe('Second Task');
            expect(plan.tasks[1].editIds).toEqual(['edit1']);
        });
    });

    describe('serialization - Markdown', () => {
        test('should convert to readable markdown', () => {
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({
                title: 'Review liability',
                description: 'Check clause 5.2',
                status: 'in_progress'
            }));
            plan.addTaskAtEnd(new WorkTask({
                title: 'Update definitions',
                description: 'Add Software definition',
                status: 'pending'
            }));

            const md = plan.toMarkdown();

            expect(md).toContain('# Work Plan');
            expect(md).toContain('## 1. Review liability');
            expect(md).toContain('Status: in_progress');
            expect(md).toContain('## 2. Update definitions');
            expect(md).toContain('Status: pending');
        });

        test('should generate full plan.md content with frontmatter and markdown', () => {
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({
                id: 'task1',
                title: 'First Task',
                description: 'Description here',
                status: 'pending'
            }));

            const content = plan.toPlanFile();

            // Should have YAML frontmatter
            expect(content).toMatch(/^---\n/);
            expect(content).toContain('tasks:');
            
            // Should have markdown body after frontmatter
            expect(content).toContain('---\n\n# Work Plan');
            expect(content).toContain('## 1. First Task');
        });

        test('should parse plan.md content back to WorkPlan', () => {
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({
                id: 'original',
                title: 'Original Task',
                description: 'Test roundtrip',
                status: 'in_progress'
            }));

            const content = plan.toPlanFile();
            const restored = WorkPlan.fromPlanFile(content);

            expect(restored.getTaskCount()).toBe(1);
            expect(restored.tasks[0].id).toBe('original');
            expect(restored.tasks[0].title).toBe('Original Task');
            expect(restored.tasks[0].status).toBe('in_progress');
        });
    });

    describe('JSON serialization', () => {
        test('should serialize to JSON', () => {
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({
                id: 'task1',
                title: 'Task',
                description: 'Desc',
                status: 'pending'
            }));

            const json = plan.toJSON();

            expect(json).toHaveProperty('tasks');
            expect(json.tasks.length).toBe(1);
            expect(json.tasks[0].id).toBe('task1');
        });

        test('should deserialize from JSON', () => {
            const json = {
                tasks: [
                    {
                        id: 'task1',
                        title: 'Task',
                        description: 'Desc',
                        status: 'pending' as TaskStatus,
                        ordinal: 0,
                        creationDate: '2025-12-09T10:00:00.000Z',
                        completionDate: null,
                        editIds: []
                    }
                ]
            };

            const plan = WorkPlan.fromJSON(json);

            expect(plan.getTaskCount()).toBe(1);
            expect(plan.tasks[0].title).toBe('Task');
        });
    });
});

// ============================================================================
// SECTION 4: Edit Logging Tests
// ============================================================================

describe('Edit logging', () => {
    test('should log edit to task via WorkPlan', () => {
        const plan = new WorkPlan();
        const task = new WorkTask({ id: 'task1', title: 'Task', description: 'D' });
        plan.addTaskAtEnd(task);

        const edit = new Edit({
            taskId: 'task1',
            toolName: 'search_and_replace',
            request: { find: 'foo' },
            response: { success: true }
        });

        plan.logEdit(edit);

        expect(task.editIds).toContain(edit.id);
    });

    test('should retrieve all edits for a task', () => {
        const plan = new WorkPlan();
        const task = new WorkTask({ id: 'task1', title: 'Task', description: 'D' });
        plan.addTaskAtEnd(task);

        const edit1 = new Edit({ taskId: 'task1', toolName: 'tool1', request: {}, response: {} });
        const edit2 = new Edit({ taskId: 'task1', toolName: 'tool2', request: {}, response: {} });

        plan.logEdit(edit1);
        plan.logEdit(edit2);

        const edits = plan.getEditsForTask('task1');

        expect(edits.length).toBe(2);
        expect(edits.map((e: Edit) => e.id)).toContain(edit1.id);
        expect(edits.map((e: Edit) => e.id)).toContain(edit2.id);
    });

    test('should generate JSONL lines for all edits', () => {
        const plan = new WorkPlan();
        const task = new WorkTask({ id: 'task1', title: 'Task', description: 'D' });
        plan.addTaskAtEnd(task);

        plan.logEdit(new Edit({ taskId: 'task1', toolName: 'tool1', request: {}, response: {} }));
        plan.logEdit(new Edit({ taskId: 'task1', toolName: 'tool2', request: {}, response: {} }));

        const jsonl = plan.editsToJSONL();
        const lines = jsonl.trim().split('\n');

        expect(lines.length).toBe(2);
        lines.forEach((line: string) => {
            expect(() => JSON.parse(line)).not.toThrow();
        });
    });
});

// ============================================================================
// SECTION 5: ID Generation Tests
// ============================================================================

describe('ID generation', () => {
    test('should generate 8-character hex IDs', () => {
        const task1 = new WorkTask({ title: 'T1', description: 'D' });
        const task2 = new WorkTask({ title: 'T2', description: 'D' });
        const edit1 = new Edit({ taskId: 't', toolName: 'tool', request: {}, response: {} });

        expect(task1.id).toMatch(/^wt[a-f0-9]{8}$/);
        expect(task2.id).toMatch(/^wt[a-f0-9]{8}$/);
        expect(edit1.id).toMatch(/^wt[a-f0-9]{8}$/);
    });

    test('should generate unique IDs', () => {
        const ids = new Set<string>();
        for (let i = 0; i < 100; i++) {
            const task = new WorkTask({ title: `Task ${i}`, description: 'D' });
            ids.add(task.id);
        }
        expect(ids.size).toBe(100);
    });
});

// ============================================================================
// SECTION 6: LegalDocument Class Tests
// ============================================================================

describe('LegalDocument class', () => {
    describe('constructor and properties', () => {
        test('should create a LegalDocument with required filename', () => {
            const doc = new LegalDocument({
                filename: 'C:/Projects/Acme/drafts/nda.docx'
            });

            expect(doc.id).toBeDefined();
            expect(doc.id).toMatch(/^wt[a-f0-9]{8}$/);
            expect(doc.filename).toBe('C:/Projects/Acme/drafts/nda.docx');
            expect(doc.displayName).toBe('nda.docx'); // Auto-derived from filename
            expect(doc.addedDate).toBeInstanceOf(Date);
        });

        test('should allow custom ID and displayName', () => {
            const doc = new LegalDocument({
                id: 'doc12345',
                filename: 'C:/Projects/Acme/drafts/nda.docx',
                displayName: 'NDA v2 (Final)'
            });

            expect(doc.id).toBe('doc12345');
            expect(doc.displayName).toBe('NDA v2 (Final)');
        });

        test('should use provided addedDate', () => {
            const customDate = new Date('2025-12-01T10:00:00Z');
            const doc = new LegalDocument({
                filename: 'doc.docx',
                addedDate: customDate
            });

            expect(doc.addedDate).toEqual(customDate);
        });

        test('should auto-derive displayName from Windows path', () => {
            const doc = new LegalDocument({
                filename: 'C:\\Users\\Test\\EL_Projects\\Acme\\drafts\\current_drafts\\agreement.docx'
            });

            expect(doc.displayName).toBe('agreement.docx');
        });

        test('should auto-derive displayName from Unix path', () => {
            const doc = new LegalDocument({
                filename: '/home/user/projects/contract.docx'
            });

            expect(doc.displayName).toBe('contract.docx');
        });
    });

    describe('serialization', () => {
        test('should serialize to JSON object', () => {
            const doc = new LegalDocument({
                id: 'doc12345',
                filename: 'C:/Projects/Acme/drafts/nda.docx',
                displayName: 'NDA v2',
                addedDate: new Date('2025-12-09T12:00:00Z')
            });

            const json = doc.toJSON();

            expect(json).toEqual({
                id: 'doc12345',
                filename: 'C:/Projects/Acme/drafts/nda.docx',
                displayName: 'NDA v2',
                addedDate: '2025-12-09T12:00:00.000Z'
            });
        });

        test('should deserialize from JSON object', () => {
            const json = {
                id: 'doc12345',
                filename: 'C:/Projects/Acme/drafts/nda.docx',
                displayName: 'NDA v2',
                addedDate: '2025-12-09T12:00:00.000Z'
            };

            const doc = LegalDocument.fromJSON(json);

            expect(doc.id).toBe('doc12345');
            expect(doc.filename).toBe('C:/Projects/Acme/drafts/nda.docx');
            expect(doc.displayName).toBe('NDA v2');
            expect(doc.addedDate).toEqual(new Date('2025-12-09T12:00:00.000Z'));
        });

        test('should serialize to YAML-friendly object', () => {
            const doc = new LegalDocument({
                id: 'doc12345',
                filename: 'C:/Projects/nda.docx',
                displayName: 'NDA Draft'
            });

            const yaml = doc.toYAML();

            expect(yaml).toHaveProperty('id', 'doc12345');
            expect(yaml).toHaveProperty('filename', 'C:/Projects/nda.docx');
            expect(yaml).toHaveProperty('displayName', 'NDA Draft');
        });
    });

    describe('equality and matching', () => {
        test('should check if filename matches', () => {
            const doc = new LegalDocument({
                filename: 'C:/Projects/Acme/drafts/nda.docx'
            });

            expect(doc.matchesFilename('C:/Projects/Acme/drafts/nda.docx')).toBe(true);
            expect(doc.matchesFilename('C:/Projects/Other/drafts/nda.docx')).toBe(false);
        });

        test('should match filename case-insensitively on Windows', () => {
            const doc = new LegalDocument({
                filename: 'C:/Projects/Acme/drafts/NDA.docx'
            });

            // Assuming we want case-insensitive matching for Windows paths
            expect(doc.matchesFilename('C:/Projects/Acme/drafts/nda.docx')).toBe(true);
        });

        test('should normalize path separators when matching', () => {
            const doc = new LegalDocument({
                filename: 'C:\\Projects\\Acme\\drafts\\nda.docx'
            });

            expect(doc.matchesFilename('C:/Projects/Acme/drafts/nda.docx')).toBe(true);
        });
    });
});

// ============================================================================
// SECTION 7: WorkPlan Documents Tests
// ============================================================================

describe('WorkPlan documents', () => {
    describe('document management', () => {
        test('should initialize with empty documents array', () => {
            const plan = new WorkPlan();

            expect(plan.documents).toEqual([]);
            expect(plan.getDocumentCount()).toBe(0);
        });

        test('should add a document', () => {
            const plan = new WorkPlan();
            const doc = new LegalDocument({ filename: 'C:/Projects/nda.docx' });

            plan.addDocument(doc);

            expect(plan.getDocumentCount()).toBe(1);
            expect(plan.documents[0].filename).toBe('C:/Projects/nda.docx');
        });

        test('should not add duplicate document (same filename)', () => {
            const plan = new WorkPlan();
            const doc1 = new LegalDocument({ filename: 'C:/Projects/nda.docx' });
            const doc2 = new LegalDocument({ filename: 'C:/Projects/nda.docx' });

            plan.addDocument(doc1);
            plan.addDocument(doc2);

            expect(plan.getDocumentCount()).toBe(1);
        });

        test('should remove document by ID', () => {
            const plan = new WorkPlan();
            const doc = new LegalDocument({ id: 'doc1', filename: 'C:/Projects/nda.docx' });
            plan.addDocument(doc);

            const removed = plan.removeDocument('doc1');

            expect(removed).toBe(true);
            expect(plan.getDocumentCount()).toBe(0);
        });

        test('should return false when removing non-existent document', () => {
            const plan = new WorkPlan();

            const removed = plan.removeDocument('nonexistent');

            expect(removed).toBe(false);
        });

        test('should get document by ID', () => {
            const plan = new WorkPlan();
            const doc = new LegalDocument({ id: 'findme', filename: 'C:/Projects/nda.docx' });
            plan.addDocument(doc);

            const found = plan.getDocumentById('findme');

            expect(found).toBeDefined();
            expect(found?.filename).toBe('C:/Projects/nda.docx');
        });

        test('should get document by filename', () => {
            const plan = new WorkPlan();
            const doc = new LegalDocument({ filename: 'C:/Projects/nda.docx', displayName: 'NDA' });
            plan.addDocument(doc);

            const found = plan.getDocumentByFilename('C:/Projects/nda.docx');

            expect(found).toBeDefined();
            expect(found?.displayName).toBe('NDA');
        });

        test('should check if document exists by filename', () => {
            const plan = new WorkPlan();
            plan.addDocument(new LegalDocument({ filename: 'C:/Projects/nda.docx' }));

            expect(plan.hasDocument('C:/Projects/nda.docx')).toBe(true);
            expect(plan.hasDocument('C:/Projects/other.docx')).toBe(false);
        });
    });

    describe('filtering edits by document', () => {
        test('should get edits for a specific document', () => {
            const plan = new WorkPlan();
            plan.addDocument(new LegalDocument({ filename: 'C:/Projects/nda.docx' }));
            plan.addTaskAtEnd(new WorkTask({ id: 'task1', title: 'Task', description: 'D' }));

            // Edit affecting our document
            const edit1 = new Edit({
                taskId: 'task1',
                toolName: 'search_and_replace',
                request: { filename: 'C:/Projects/nda.docx', find_text: 'foo' },
                response: { success: true }
            });

            // Edit affecting a different document
            const edit2 = new Edit({
                taskId: 'task1',
                toolName: 'search_and_replace',
                request: { filename: 'C:/Projects/other.docx', find_text: 'bar' },
                response: { success: true }
            });

            plan.logEdit(edit1);
            plan.logEdit(edit2);

            const docEdits = plan.getEditsForDocument('C:/Projects/nda.docx');

            expect(docEdits.length).toBe(1);
            expect(docEdits[0].id).toBe(edit1.id);
        });

        test('should get all edits affecting plan documents', () => {
            const plan = new WorkPlan();
            plan.addDocument(new LegalDocument({ filename: 'C:/Projects/nda.docx' }));
            plan.addDocument(new LegalDocument({ filename: 'C:/Projects/agreement.docx' }));
            plan.addTaskAtEnd(new WorkTask({ id: 'task1', title: 'Task', description: 'D' }));

            const edit1 = new Edit({
                taskId: 'task1',
                toolName: 'tool1',
                request: { filename: 'C:/Projects/nda.docx' },
                response: {}
            });
            const edit2 = new Edit({
                taskId: 'task1',
                toolName: 'tool2',
                request: { filename: 'C:/Projects/agreement.docx' },
                response: {}
            });
            const edit3 = new Edit({
                taskId: 'task1',
                toolName: 'tool3',
                request: { filename: 'C:/Projects/unrelated.docx' },
                response: {}
            });

            plan.logEdit(edit1);
            plan.logEdit(edit2);
            plan.logEdit(edit3);

            const docEdits = plan.getDocumentEdits();

            expect(docEdits.length).toBe(2);
            expect(docEdits.map(e => e.id)).toContain(edit1.id);
            expect(docEdits.map(e => e.id)).toContain(edit2.id);
            expect(docEdits.map(e => e.id)).not.toContain(edit3.id);
        });

        test('should return empty array when no documents registered', () => {
            const plan = new WorkPlan();
            plan.addTaskAtEnd(new WorkTask({ id: 'task1', title: 'Task', description: 'D' }));

            plan.logEdit(new Edit({
                taskId: 'task1',
                toolName: 'tool1',
                request: { filename: 'C:/Projects/nda.docx' },
                response: {}
            }));

            const docEdits = plan.getDocumentEdits();

            expect(docEdits).toEqual([]);
        });
    });

    describe('YAML serialization with documents', () => {
        test('should include documents in YAML frontmatter', () => {
            const plan = new WorkPlan();
            plan.addDocument(new LegalDocument({
                id: 'doc1',
                filename: 'C:/Projects/nda.docx',
                displayName: 'NDA Draft'
            }));

            const yaml = plan.toYAMLFrontmatter();

            expect(yaml).toContain('documents:');
            expect(yaml).toContain('id: doc1');
            // js-yaml determines quoting automatically based on YAML spec
            expect(yaml).toContain('filename: C:/Projects/nda.docx');
            expect(yaml).toContain('displayName: NDA Draft');
        });

        test('should parse documents from YAML frontmatter', () => {
            const yaml = `---
documents:
  - id: doc1
    filename: C:/Projects/nda.docx
    displayName: NDA Draft
    addedDate: '2025-12-09T10:00:00.000Z'
tasks:
  - id: task1
    title: Review
    description: Check terms
    status: pending
    ordinal: 0
    creationDate: '2025-12-09T10:00:00.000Z'
    completionDate: null
    editIds: []
---

# Work Plan
`;

            const plan = WorkPlan.fromYAMLFrontmatter(yaml);

            expect(plan.getDocumentCount()).toBe(1);
            expect(plan.documents[0].id).toBe('doc1');
            expect(plan.documents[0].filename).toBe('C:/Projects/nda.docx');
            expect(plan.documents[0].displayName).toBe('NDA Draft');
        });

        test('should handle plan.md with no documents', () => {
            const yaml = `---
tasks:
  - id: task1
    title: Review
    description: Check terms
    status: pending
    ordinal: 0
    creationDate: '2025-12-09T10:00:00.000Z'
    completionDate: null
    editIds: []
---

# Work Plan
`;

            const plan = WorkPlan.fromYAMLFrontmatter(yaml);

            expect(plan.getDocumentCount()).toBe(0);
            expect(plan.documents).toEqual([]);
        });
    });

    describe('JSON serialization with documents', () => {
        test('should include documents in JSON', () => {
            const plan = new WorkPlan();
            plan.addDocument(new LegalDocument({
                id: 'doc1',
                filename: 'C:/Projects/nda.docx'
            }));

            const json = plan.toJSON();

            expect(json).toHaveProperty('documents');
            expect(json.documents!.length).toBe(1);
            expect(json.documents![0].id).toBe('doc1');
        });

        test('should deserialize documents from JSON', () => {
            const json = {
                tasks: [],
                documents: [
                    {
                        id: 'doc1',
                        filename: 'C:/Projects/nda.docx',
                        displayName: 'NDA',
                        addedDate: '2025-12-09T10:00:00.000Z'
                    }
                ]
            };

            const plan = WorkPlan.fromJSON(json);

            expect(plan.getDocumentCount()).toBe(1);
            expect(plan.documents[0].filename).toBe('C:/Projects/nda.docx');
        });
    });

    describe('Python YAML compatibility', () => {
        test('should parse Python-generated YAML (no leading spaces before list items)', () => {
            // Python's YAML library uses no indent before list items
            const pythonYaml = `---
tasks:
- id: 905bd222
  title: Fix critical drafting issues
  description: Correct Schedule numbering inconsistency
  status: pending
  ordinal: 0
  creationDate: '2025-12-09T19:51:13.454897Z'
  completionDate: null
  editIds: []
- id: 09b4f841
  title: Expand clause 21
  description: Add exit/transition provisions
  status: in_progress
  ordinal: 1
  creationDate: '2025-12-09T19:51:19.582753Z'
  completionDate: null
  editIds: []
---

# Work Plan
`;

            const plan = WorkPlan.fromYAMLFrontmatter(pythonYaml);

            expect(plan.getTaskCount()).toBe(2);
            expect(plan.tasks[0].id).toBe('905bd222');
            expect(plan.tasks[0].title).toBe('Fix critical drafting issues');
            expect(plan.tasks[0].status).toBe('pending');
            expect(plan.tasks[1].id).toBe('09b4f841');
            expect(plan.tasks[1].status).toBe('in_progress');
        });

        test('should parse Python YAML with multi-line descriptions', () => {
            // Python wraps long descriptions across lines
            const pythonYaml = `---
tasks:
- id: task1
  title: Complex task
  description: 'This is a long description that spans
    multiple lines in the YAML file.'
  status: pending
  ordinal: 0
  creationDate: '2025-12-09T10:00:00.000Z'
  completionDate: null
  editIds: []
---
`;

            const plan = WorkPlan.fromYAMLFrontmatter(pythonYaml);

            expect(plan.getTaskCount()).toBe(1);
            expect(plan.tasks[0].title).toBe('Complex task');
            // Multi-line description should be joined with spaces
            expect(plan.tasks[0].description).toContain('long description that spans');
            expect(plan.tasks[0].description).toContain('multiple lines');
        });

        test('should parse Python YAML with unquoted multi-line descriptions', () => {
            // Real example from Python ruamel.yaml output
            const pythonYaml = `---
tasks:
- id: 905bd222
  title: 1.1 Fix critical drafting issues
  description: Correct Schedule numbering inconsistency (Schedule 2 heading should
    be Schedule 1). Add missing 'Data Protection Legislation' definition to clause
    1 referencing UK GDPR and EU GDPR.
  status: pending
  ordinal: 0
  creationDate: '2025-12-09T19:51:13.454897Z'
  completionDate: null
  editIds: []
---
`;

            const plan = WorkPlan.fromYAMLFrontmatter(pythonYaml);

            expect(plan.getTaskCount()).toBe(1);
            expect(plan.tasks[0].description).toContain('Correct Schedule numbering');
            expect(plan.tasks[0].description).toContain('be Schedule 1');
            expect(plan.tasks[0].description).toContain('Data Protection Legislation');
        });
    });
});
