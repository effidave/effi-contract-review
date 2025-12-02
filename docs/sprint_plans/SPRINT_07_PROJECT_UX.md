# Sprint 7: Project Management & UX

**Duration:** 2 weeks  
**Goal:** Streamlined project creation, instruction capture, and overall user experience polish.

---

## Objectives

1. **New Project Wizard** - Guided project creation with structure
2. **Instruction Q&A** - Capture deal context via conversation
3. **Client Context** - Store and reuse client information
4. **Dashboard View** - Project overview and quick actions
5. **UX Polish** - Refine workflows based on usage

---

## User Stories

### US7.1: Create New Project
**As a** lawyer starting a new matter,  
**I want** a guided wizard to set up my project,  
**So that** I have the right structure from the start.

**Acceptance Criteria:**
- [ ] "New Project" command in command palette
- [ ] Wizard steps: Name, Client, Type, Source Document
- [ ] Creates folder structure from template
- [ ] Opens project in workspace
- [ ] Test: Create project → see structure ready

### US7.2: Instruction Q&A
**As a** lawyer capturing deal requirements,  
**I want** to answer questions that generate my instruction file,  
**So that** the LLM has the right context.

**Acceptance Criteria:**
- [ ] "Capture Instructions" command
- [ ] Q&A flow: What type? Who are you acting for? Key concerns?
- [ ] Generates `instruction.md` from answers
- [ ] Can edit/refine instruction later
- [ ] Test: Answer questions → instruction.md created

### US7.3: Client Context File
**As a** lawyer working with repeat clients,  
**I want** to store client preferences and history,  
**So that** reviews account for their specific needs.

**Acceptance Criteria:**
- [ ] `client_context.md` in project
- [ ] Capture: Industry, risk tolerance, standard positions
- [ ] Reuse across projects for same client
- [ ] Included in LLM context
- [ ] Test: Create client context → visible in review

### US7.4: Project Dashboard
**As a** lawyer managing multiple projects,  
**I want** a dashboard showing my active work,  
**So that** I can quickly navigate to what needs attention.

**Acceptance Criteria:**
- [ ] Dashboard view in webview
- [ ] Shows: Recent projects, current document status, pending reviews
- [ ] Quick actions: Open, Resume Review, Compare Versions
- [ ] Test: View dashboard → see project status

### US7.5: Keyboard Navigation
**As a** lawyer working efficiently,  
**I want** keyboard shortcuts for common actions,  
**So that** I can work without reaching for the mouse.

**Acceptance Criteria:**
- [ ] Keyboard shortcuts documented
- [ ] Navigation: Next/Prev clause, sections
- [ ] Actions: Save, Comment, Review
- [ ] Shortcuts visible in tooltips
- [ ] Test: Navigate document with keyboard

### US7.6: Status Bar Integration
**As a** lawyer monitoring my work,  
**I want** key status in the VS Code status bar,  
**So that** I know the current state at a glance.

**Acceptance Criteria:**
- [ ] Document name in status bar
- [ ] Save status (saved/unsaved)
- [ ] Review phase if active
- [ ] Click to open dashboard
- [ ] Test: Make changes → status updates

---

## Technical Design

### Project Template Structure

```
EL_Projects/.template/
├── .vscode/
│   └── settings.json          # Project-specific VS Code settings
├── drafts/
│   └── current_drafts/
│       └── .gitkeep
├── analysis/
│   └── .gitkeep
├── documentation/
│   ├── instruction.md         # Generated from Q&A
│   ├── client_context.md      # Client-specific context
│   └── review_notes.md        # Running notes
├── precedents/
│   └── .gitkeep               # Project-specific precedents
└── history/
    └── .gitkeep               # Edit history and checkpoints
```

### New Project Wizard Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    New Project Wizard                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1 of 4: Project Details                                   │
│  ─────────────────────────────────────────────                  │
│                                                                  │
│  Project Name:  [Norton R&D Agreement________]                  │
│                                                                  │
│  Client:        [Norton Industries____________]                 │
│                 ☐ Create new client context                     │
│                 ○ Use existing: [Select...]                     │
│                                                                  │
│  Matter Type:   ○ Services  ○ SaaS  ● R&D  ○ NDA  ○ Other      │
│                                                                  │
│                                                                  │
│                                    [Cancel]  [Next →]           │
└─────────────────────────────────────────────────────────────────┘
```

### Instruction Q&A Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                  Capture Instructions                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🤖 What type of agreement is this?                             │
│     ○ SaaS / Software License                                   │
│     ○ Professional Services                                     │
│     ● Research & Development                                    │
│     ○ NDA / Confidentiality                                     │
│     ○ Other: [____________]                                     │
│                                                                  │
│  🤖 Who are you acting for?                                     │
│     ● Customer (receiving services/IP)                          │
│     ○ Supplier (providing services/IP)                          │
│                                                                  │
│  🤖 What are the key concerns for this deal?                    │
│     ☑ IP ownership                                              │
│     ☑ Liability caps                                            │
│     ☐ Data protection                                           │
│     ☑ Termination rights                                        │
│     ☐ Payment terms                                             │
│     [Add custom concern: _____________]                         │
│                                                                  │
│  🤖 Any specific negotiating context?                           │
│     [Client is in a weak bargaining position - this is a       │
│      strategic supplier. Prioritize relationship over          │
│      aggressive positions. Can accept higher liability if      │
│      offset by better IP terms.___________________________]     │
│                                                                  │
│                              [Back]  [Generate Instruction →]   │
└─────────────────────────────────────────────────────────────────┘
```

### Generated Instruction.md

```markdown
# Deal Instructions: Norton R&D Agreement

## Overview
- **Client:** Norton Industries
- **Agreement Type:** Research & Development
- **Acting For:** Customer (receiving services/IP)
- **Date:** December 2025

## Key Concerns
1. **IP Ownership** - Priority: High
   - Ensure all foreground IP vests in Client
   - Background IP should be licensed, not assigned
   
2. **Liability Caps** - Priority: High
   - Standard 12-month cap acceptable
   - Carve-outs for IP indemnity
   
3. **Termination Rights** - Priority: Medium
   - Need for convenience termination
   - IP rights on termination critical

## Negotiating Context
Client is in a weak bargaining position - this is a strategic supplier. 
Prioritize relationship over aggressive positions. Can accept higher 
liability if offset by better IP terms.

## Review Approach
- Start with gap analysis focusing on IP and liability
- Compare against R&D precedent (pro-customer)
- Flag any unusual supplier-friendly terms
```

---

## Technical Tasks

### T7.1: Project Wizard (3 days)
**File:** `extension/src/projectWizard.ts` (new)

```typescript
import * as vscode from 'vscode';

export async function showNewProjectWizard(): Promise<void> {
  // Step 1: Project Name
  const projectName = await vscode.window.showInputBox({
    prompt: 'Enter project name',
    placeHolder: 'e.g., Norton R&D Agreement'
  });
  if (!projectName) return;
  
  // Step 2: Client
  const clients = await getExistingClients();
  const clientChoice = await vscode.window.showQuickPick([
    { label: '$(add) Create New Client', value: 'new' },
    ...clients.map(c => ({ label: c.name, value: c.id }))
  ], { placeHolder: 'Select or create client' });
  
  // Step 3: Matter Type
  const matterType = await vscode.window.showQuickPick([
    { label: 'SaaS / Software License', value: 'SaaS' },
    { label: 'Professional Services', value: 'Services' },
    { label: 'Research & Development', value: 'R&D' },
    { label: 'NDA / Confidentiality', value: 'NDA' },
    { label: 'Other', value: 'Other' }
  ], { placeHolder: 'Select matter type' });
  
  // Step 4: Source Document
  const docUri = await vscode.window.showOpenDialog({
    canSelectFiles: true,
    canSelectFolders: false,
    filters: { 'Word Documents': ['docx'] }
  });
  
  // Create project
  await createProject({
    name: projectName,
    client: clientChoice?.value,
    type: matterType?.value,
    sourceDoc: docUri?.[0]?.fsPath
  });
}

async function createProject(config: ProjectConfig): Promise<void> {
  const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
  const projectDir = path.join(workspaceRoot, 'EL_Projects', config.name);
  
  // Copy template
  const templateDir = path.join(workspaceRoot, 'EL_Projects', '.template');
  await fs.promises.cp(templateDir, projectDir, { recursive: true });
  
  // Copy source document
  if (config.sourceDoc) {
    const destDoc = path.join(projectDir, 'drafts', 'current_drafts', path.basename(config.sourceDoc));
    await fs.promises.copyFile(config.sourceDoc, destDoc);
  }
  
  // Create/link client context
  if (config.client === 'new') {
    await showClientContextWizard(projectDir);
  }
  
  // Open instruction capture
  await showInstructionCapture(projectDir);
  
  // Notify success
  vscode.window.showInformationMessage(`Created project: ${config.name}`);
}
```

### T7.2: Instruction Q&A Panel (3 days)
**File:** `extension/src/webview/instruction-capture.js` (new)

```javascript
class InstructionCapture {
  constructor(container) {
    this.container = container;
    this.currentStep = 0;
    this.answers = {};
    
    this.questions = [
      {
        id: 'agreementType',
        question: 'What type of agreement is this?',
        type: 'radio',
        options: [
          { value: 'SaaS', label: 'SaaS / Software License' },
          { value: 'Services', label: 'Professional Services' },
          { value: 'R&D', label: 'Research & Development' },
          { value: 'NDA', label: 'NDA / Confidentiality' },
          { value: 'Other', label: 'Other' }
        ]
      },
      {
        id: 'actingFor',
        question: 'Who are you acting for?',
        type: 'radio',
        options: [
          { value: 'customer', label: 'Customer (receiving services/IP)' },
          { value: 'supplier', label: 'Supplier (providing services/IP)' }
        ]
      },
      {
        id: 'concerns',
        question: 'What are the key concerns for this deal?',
        type: 'checkbox',
        options: [
          { value: 'ip', label: 'IP ownership' },
          { value: 'liability', label: 'Liability caps' },
          { value: 'data', label: 'Data protection' },
          { value: 'termination', label: 'Termination rights' },
          { value: 'payment', label: 'Payment terms' },
          { value: 'confidentiality', label: 'Confidentiality' }
        ],
        allowCustom: true
      },
      {
        id: 'context',
        question: 'Any specific negotiating context?',
        type: 'textarea',
        placeholder: 'Describe the relationship, bargaining positions, priorities...'
      }
    ];
  }
  
  render() {
    const q = this.questions[this.currentStep];
    
    this.container.innerHTML = `
      <div class="instruction-capture">
        <div class="progress">
          Step ${this.currentStep + 1} of ${this.questions.length}
        </div>
        
        <div class="question">
          <span class="bot-icon">🤖</span>
          <span class="question-text">${q.question}</span>
        </div>
        
        <div class="answer-area">
          ${this.renderAnswerInput(q)}
        </div>
        
        <div class="navigation">
          <button ${this.currentStep === 0 ? 'disabled' : ''} onclick="capturePanel.prevStep()">
            Back
          </button>
          <button onclick="capturePanel.nextStep()">
            ${this.currentStep === this.questions.length - 1 ? 'Generate Instruction' : 'Next'}
          </button>
        </div>
      </div>
    `;
  }
  
  renderAnswerInput(question) {
    switch (question.type) {
      case 'radio':
        return question.options.map(opt => `
          <label class="option">
            <input type="radio" name="${question.id}" value="${opt.value}"
                   ${this.answers[question.id] === opt.value ? 'checked' : ''}>
            ${opt.label}
          </label>
        `).join('');
        
      case 'checkbox':
        return question.options.map(opt => `
          <label class="option">
            <input type="checkbox" name="${question.id}" value="${opt.value}"
                   ${(this.answers[question.id] || []).includes(opt.value) ? 'checked' : ''}>
            ${opt.label}
          </label>
        `).join('') + (question.allowCustom ? `
          <input type="text" class="custom-option" placeholder="Add custom...">
        ` : '');
        
      case 'textarea':
        return `
          <textarea name="${question.id}" placeholder="${question.placeholder || ''}"
                    rows="6">${this.answers[question.id] || ''}</textarea>
        `;
    }
  }
  
  generateInstruction() {
    const template = `# Deal Instructions: {projectName}

## Overview
- **Client:** {clientName}
- **Agreement Type:** ${this.answers.agreementType}
- **Acting For:** ${this.answers.actingFor === 'customer' ? 'Customer' : 'Supplier'}
- **Date:** ${new Date().toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })}

## Key Concerns
${(this.answers.concerns || []).map((c, i) => `${i + 1}. **${this.formatConcern(c)}** - Priority: High`).join('\n')}

## Negotiating Context
${this.answers.context || 'No specific context provided.'}

## Review Approach
- Start with gap analysis focusing on: ${(this.answers.concerns || []).join(', ')}
- Compare against ${this.answers.agreementType} precedent (${this.answers.actingFor === 'customer' ? 'pro-customer' : 'pro-supplier'})
- Flag any unusual ${this.answers.actingFor === 'customer' ? 'supplier' : 'customer'}-friendly terms
`;
    
    return template;
  }
  
  formatConcern(concern) {
    const labels = {
      ip: 'IP Ownership',
      liability: 'Liability Caps',
      data: 'Data Protection',
      termination: 'Termination Rights',
      payment: 'Payment Terms',
      confidentiality: 'Confidentiality'
    };
    return labels[concern] || concern;
  }
}
```

### T7.3: Dashboard View (2 days)
**File:** `extension/src/webview/dashboard.js` (new)

```javascript
class Dashboard {
  constructor(container) {
    this.container = container;
    this.projects = [];
  }
  
  async load() {
    // Load projects from EL_Projects
    vscode.postMessage({ command: 'loadProjects' });
  }
  
  render() {
    this.container.innerHTML = `
      <div class="dashboard">
        <div class="dashboard-header">
          <h1>Effi Contract Editor</h1>
          <button class="new-project-btn" onclick="dashboard.newProject()">
            + New Project
          </button>
        </div>
        
        <div class="section">
          <h2>Recent Projects</h2>
          <div class="project-grid">
            ${this.projects.map(p => this.renderProjectCard(p)).join('')}
          </div>
        </div>
        
        <div class="section">
          <h2>Quick Actions</h2>
          <div class="action-grid">
            <button class="action-btn" onclick="dashboard.openPrecedents()">
              📚 Browse Precedents
            </button>
            <button class="action-btn" onclick="dashboard.openSettings()">
              ⚙️ Settings
            </button>
          </div>
        </div>
      </div>
    `;
  }
  
  renderProjectCard(project) {
    return `
      <div class="project-card" onclick="dashboard.openProject('${project.path}')">
        <div class="project-name">${project.name}</div>
        <div class="project-meta">
          <span class="client">${project.client}</span>
          <span class="date">${project.lastModified}</span>
        </div>
        <div class="project-status ${project.reviewStatus}">
          ${this.getStatusLabel(project.reviewStatus)}
        </div>
      </div>
    `;
  }
  
  getStatusLabel(status) {
    switch (status) {
      case 'not-started': return '○ Not Started';
      case 'in-review': return '◐ In Review';
      case 'complete': return '● Complete';
      default: return '';
    }
  }
}
```

### T7.4: Status Bar Items (1 day)
**File:** `extension/src/statusBar.ts` (new)

```typescript
import * as vscode from 'vscode';

let documentStatusItem: vscode.StatusBarItem;
let reviewStatusItem: vscode.StatusBarItem;

export function createStatusBarItems(context: vscode.ExtensionContext) {
  // Document status
  documentStatusItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Left,
    100
  );
  documentStatusItem.command = 'effi-contract-viewer.showWebview';
  context.subscriptions.push(documentStatusItem);
  
  // Review status
  reviewStatusItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Left,
    99
  );
  reviewStatusItem.command = 'effi-contract-viewer.resumeReview';
  context.subscriptions.push(reviewStatusItem);
}

export function updateDocumentStatus(docName: string, saved: boolean) {
  documentStatusItem.text = `$(file) ${docName} ${saved ? '✓' : '●'}`;
  documentStatusItem.tooltip = saved ? 'All changes saved' : 'Unsaved changes';
  documentStatusItem.show();
}

export function updateReviewStatus(phase: number | null, total: number = 4) {
  if (phase === null) {
    reviewStatusItem.hide();
    return;
  }
  
  const phases = ['Analysis', 'Gap Analysis', 'Suggestions', 'Execution'];
  reviewStatusItem.text = `$(checklist) Review: Phase ${phase}/${total} (${phases[phase - 1]})`;
  reviewStatusItem.tooltip = 'Click to resume review';
  reviewStatusItem.show();
}
```

### T7.5: Keyboard Shortcuts (1 day)
**File:** `extension/package.json` (modify)

```json
{
  "contributes": {
    "keybindings": [
      {
        "command": "effi-contract-viewer.showWebview",
        "key": "ctrl+shift+e",
        "mac": "cmd+shift+e"
      },
      {
        "command": "effi-contract-viewer.saveDocument",
        "key": "ctrl+s",
        "mac": "cmd+s",
        "when": "effiEditorActive"
      },
      {
        "command": "effi-contract-viewer.nextClause",
        "key": "ctrl+down",
        "mac": "cmd+down",
        "when": "effiEditorActive"
      },
      {
        "command": "effi-contract-viewer.prevClause",
        "key": "ctrl+up",
        "mac": "cmd+up",
        "when": "effiEditorActive"
      },
      {
        "command": "effi-contract-viewer.addComment",
        "key": "ctrl+alt+m",
        "mac": "cmd+alt+m",
        "when": "effiEditorActive"
      },
      {
        "command": "effi-contract-viewer.startReview",
        "key": "ctrl+shift+r",
        "mac": "cmd+shift+r",
        "when": "effiEditorActive"
      }
    ]
  }
}
```

### T7.6: Polish & Bug Fixes (2 days)

Based on sprint retrospectives, address:
- Performance issues with large documents
- Edge cases in editing
- Error message improvements
- Loading states and feedback
- Accessibility improvements

---

## Testing Plan

### Unit Tests
- `test_project_creation.ts`: Wizard flow
- `test_instruction_generation.js`: Template generation

### Integration Tests
- Create project → capture instructions → start review
- Full workflow end-to-end

### Manual Tests
1. Create new project with wizard
2. Complete instruction Q&A
3. Set up client context
4. View dashboard
5. Test keyboard navigation

---

## Definition of Done

- [ ] Project wizard creates correct structure
- [ ] Instruction Q&A generates useful instruction.md
- [ ] Client context reusable across projects
- [ ] Dashboard shows project status
- [ ] Keyboard shortcuts documented and working
- [ ] Status bar shows relevant info
- [ ] No critical bugs remaining
- [ ] Documentation complete

---

## Dependencies

- All previous sprints complete
- Project template finalized

---

## Post-Launch Activities

After Sprint 7, consider:
- User feedback collection
- Performance optimization
- Additional precedent types
- Multi-document comparison
- Team features (if needed later)
- Publishing extension to marketplace
