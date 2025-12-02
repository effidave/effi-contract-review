# Sprint 5: Multi-Phase Review Workflow

**Duration:** 2 weeks  
**Goal:** Implement the structured 4-phase contract review workflow with LLM guidance.

---

## Objectives

1. **Phase 1: Analysis** - LLM analyzes document structure and clause interactions
2. **Phase 2: Gap Analysis** - Identify issues, risks, and missing provisions
3. **Phase 3: Suggestions** - Present options for lawyer to choose/modify
4. **Phase 4: Execution** - LLM carries out approved changes

---

## The Four Phases

### Phase 1: Document Analysis
**Input:** instruction.md + all blocks  
**Output:** Structured understanding of what each clause does and how they interact

```markdown
## Analysis Report

### Document Overview
- Type: Services Agreement
- Parties: Customer (Acme Corp) vs Supplier (TechCo)
- Governing Law: England & Wales

### Clause Analysis
| Clause | Topic | Effect | Interacts With |
|--------|-------|--------|----------------|
| 3.1 | Service Delivery | Supplier must deliver per Schedule 1 | 4.1 (Payment), 8.1 (Liability) |
| 3.2 | Service Levels | 99.9% uptime SLA | 3.3 (Credits), 8.2 (Exclusions) |
| ...

### Key Observations
1. Service credits (3.3) are the exclusive remedy for SLA failures
2. Liability cap (8.1) applies to all claims including service failures
3. Definition of "Services" in 1.5 is broad - includes support
```

### Phase 2: Gap Analysis
**Input:** instruction.md + all blocks + Phase 1 output  
**Output:** Issues, risks, and gaps requiring attention

```markdown
## Gap Analysis

### Issues Identified

#### HIGH PRIORITY
1. **Unlimited Liability for IP Indemnity (Clause 9.2)**
   - Current: No cap on IP indemnification
   - Risk: Exposure to unlimited claims
   - Recommendation: Add carve-out from general liability cap

2. **No Data Protection Provisions**
   - Current: No mention of GDPR/data handling
   - Risk: Non-compliance, regulator action
   - Recommendation: Add DPA schedule or clause

#### MEDIUM PRIORITY
3. **Vague Change Control (Clause 5)**
   - Current: "Changes by mutual agreement"
   - Risk: Disputes over scope creep
   - Recommendation: Add formal change request process

#### LOW PRIORITY
4. **Notice Period Inconsistency**
   - Clause 12.1 says 30 days, 12.4 says 14 days
   - Recommendation: Standardize to 30 days
```

### Phase 3: Suggestions
**Input:** instruction.md + relevant blocks + Phase 2 output + precedent clauses  
**Output:** Specific drafting options for lawyer review

```markdown
## Suggested Changes

### Issue 1: Unlimited Liability for IP Indemnity

**Option A: Carve-out with sub-cap**
> "9.2A Notwithstanding clause 8.1, the Supplier's liability under clause 9.2 shall not exceed [5x] the annual fees."

**Option B: Include in general cap**  
> Amend 8.1: "...including claims under clause 9.2..."

**Option C: Mutual indemnity**
> Add 9.3: "Each party shall indemnify the other for IP claims arising from materials provided by that party."

**Lawyer Notes:**
- Option A is market standard for tech contracts
- Option B favors Supplier (lower exposure)
- Option C shifts risk to party who created the problem

[Select Option: A / B / C / Custom]
```

### Phase 4: Execution
**Input:** instruction.md + target blocks + lawyer choices + MCP tools  
**Output:** Actual document modifications

```markdown
## Execution Log

### Change 1: Add IP liability sub-cap
- Tool: `add_paragraph_after_clause`
- Target: After clause 9.2
- Text: "9.2A Notwithstanding clause 8.1, the Supplier's total aggregate liability under clause 9.2 shall not exceed an amount equal to five (5) times the Fees paid or payable in the twelve (12) month period preceding the claim."
- Status: ✅ Applied

### Change 2: Add Data Protection clause
- Tool: `add_heading` + `add_paragraph_after_clause`
- Target: New clause 15
- Status: ✅ Applied

### Change 3: Standardize notice period
- Tool: `replace_clause_text_by_ordinal`
- Target: Clause 12.4
- Status: ✅ Applied

## Summary
- 3 changes applied successfully
- Document saved
- Git commit: [effi] review: Applied 3 changes from gap analysis
```

---

## User Stories

### US5.1: Start Review Workflow
**As a** lawyer beginning a contract review,  
**I want** to start the 4-phase workflow with my instructions,  
**So that** I get a structured analysis.

**Acceptance Criteria:**
- [ ] "Start Review" button in toolbar
- [ ] Prompt for instruction file selection
- [ ] Progress indicator for each phase
- [ ] Test: Start review → see Phase 1 begin

### US5.2: Phase 1 Analysis Output
**As a** lawyer reviewing Phase 1 output,  
**I want** to see the analysis in a readable format,  
**So that** I can verify the LLM understood the document.

**Acceptance Criteria:**
- [ ] Analysis displayed in review panel
- [ ] Clause-by-clause breakdown
- [ ] Interaction matrix visible
- [ ] Can expand/collapse sections
- [ ] Test: View Phase 1 output → understand document structure

### US5.3: Phase 2 Gap Report
**As a** lawyer reviewing Phase 2 output,  
**I want** issues prioritized by severity,  
**So that** I can focus on what matters most.

**Acceptance Criteria:**
- [ ] Issues categorized: High/Medium/Low
- [ ] Each issue has: description, risk, recommendation
- [ ] Click issue to highlight relevant clauses
- [ ] Test: View gaps → understand risks

### US5.4: Phase 3 Option Selection
**As a** lawyer reviewing suggestions,  
**I want** to pick between drafting options,  
**So that** I control the final output.

**Acceptance Criteria:**
- [ ] Multiple options per issue
- [ ] Preview of each option's text
- [ ] Radio/checkbox selection
- [ ] "Custom" option with text input
- [ ] "Skip" option to leave unchanged
- [ ] Test: Select options → proceed to execution

### US5.5: Phase 4 Execution Confirmation
**As a** lawyer approving changes,  
**I want** to review all changes before they're applied,  
**So that** I don't make unintended modifications.

**Acceptance Criteria:**
- [ ] Summary of all changes to be made
- [ ] "Apply All" or individual apply buttons
- [ ] Diff preview for each change
- [ ] Rollback if something goes wrong
- [ ] Test: Confirm → changes applied → document updated

### US5.6: Review State Persistence
**As a** lawyer who stepped away mid-review,  
**I want** to resume where I left off,  
**So that** I don't lose my progress.

**Acceptance Criteria:**
- [ ] Review state saved to project folder
- [ ] Resume button shows current phase
- [ ] Previous phase outputs accessible
- [ ] Test: Close VS Code → reopen → resume review

---

## Technical Design

### Review State Model

```typescript
interface ReviewState {
  id: string;  // Review session UUID
  documentPath: string;
  instructionPath: string;
  currentPhase: 1 | 2 | 3 | 4;
  startedAt: string;
  
  phase1?: {
    completedAt: string;
    analysis: DocumentAnalysis;
  };
  
  phase2?: {
    completedAt: string;
    gaps: GapReport;
  };
  
  phase3?: {
    completedAt: string;
    suggestions: Suggestion[];
    selections: Record<string, string>;  // issueId -> optionId
  };
  
  phase4?: {
    completedAt: string;
    executionLog: ExecutionEntry[];
    success: boolean;
  };
}

interface DocumentAnalysis {
  overview: {
    type: string;
    parties: string[];
    governingLaw: string;
  };
  clauses: ClauseAnalysis[];
  interactions: ClauseInteraction[];
  observations: string[];
}

interface GapReport {
  high: Issue[];
  medium: Issue[];
  low: Issue[];
}

interface Suggestion {
  issueId: string;
  options: DraftOption[];
}

interface DraftOption {
  id: string;
  label: string;
  text: string;
  notes: string;
}
```

### Review Panel UI

```
┌─────────────────────────────────────────────────────────────────┐
│  Review: Norton R&D Agreement                                    │
│  ────────────────────────────────────────────────────────────── │
│  [●] Phase 1: Analysis     ✓ Complete                           │
│  [●] Phase 2: Gap Analysis ✓ Complete                           │
│  [○] Phase 3: Suggestions  ← In Progress                        │
│  [ ] Phase 4: Execution                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Issue 1 of 5: Unlimited Liability for IP Indemnity             │
│  ─────────────────────────────────────────────────────────      │
│  Clause 9.2 exposes you to unlimited liability for IP claims.   │
│                                                                  │
│  ○ Option A: Add sub-cap (5x annual fees)                       │
│    "9.2A Notwithstanding clause 8.1, the Supplier's total..."   │
│                                                                  │
│  ○ Option B: Include in general cap                             │
│    Amend 8.1: "...including claims under clause 9.2..."         │
│                                                                  │
│  ○ Option C: Skip (leave unchanged)                             │
│                                                                  │
│  ○ Custom: [Enter your own text...]                             │
│                                                                  │
│  [← Previous]                              [Next Issue →]        │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  [Cancel Review]              [Save & Exit]    [Finish Phase 3] │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Tasks

### T5.1: Review State Management (2 days)
**File:** `extension/src/review/state.ts` (new)

```typescript
class ReviewStateManager {
  private state: ReviewState | null = null;
  private statePath: string;
  
  constructor(projectPath: string) {
    this.statePath = path.join(projectPath, 'review_state.json');
  }
  
  async startReview(documentPath: string, instructionPath: string): Promise<ReviewState> {
    this.state = {
      id: uuid(),
      documentPath,
      instructionPath,
      currentPhase: 1,
      startedAt: new Date().toISOString()
    };
    await this.save();
    return this.state;
  }
  
  async completePhase1(analysis: DocumentAnalysis): Promise<void> {
    this.state!.phase1 = {
      completedAt: new Date().toISOString(),
      analysis
    };
    this.state!.currentPhase = 2;
    await this.save();
  }
  
  // ... similar for phases 2, 3, 4
  
  async save(): Promise<void> {
    await fs.promises.writeFile(
      this.statePath, 
      JSON.stringify(this.state, null, 2)
    );
  }
  
  async load(): Promise<ReviewState | null> {
    if (await fs.promises.access(this.statePath).then(() => true).catch(() => false)) {
      const data = await fs.promises.readFile(this.statePath, 'utf-8');
      this.state = JSON.parse(data);
      return this.state;
    }
    return null;
  }
}
```

### T5.2: Phase 1 Implementation (2 days)
**File:** `effilocal/flows/review_phase1.py` (new)

```python
"""Phase 1: Document Analysis"""

import json
from pathlib import Path
from typing import Any
from effilocal.ai.llm_client import call_llm

ANALYSIS_PROMPT = """You are a legal document analyst. Analyze this contract and provide:

1. Document Overview
   - Contract type
   - Parties and their roles
   - Governing law
   - Key dates

2. Clause-by-Clause Analysis
   For each numbered clause, identify:
   - Topic (e.g., "Service Delivery", "Payment", "Liability")
   - Effect (what does it actually do?)
   - Interacts With (which other clauses does it relate to?)

3. Key Observations
   - Notable provisions
   - Unusual terms
   - Missing standard clauses

Instructions from lawyer:
{instruction}

Document content:
{document}

Respond in JSON format matching this schema:
{schema}
"""

def run_phase1(
    instruction_path: Path,
    blocks: list[dict],
    model: str = "gpt-4o"
) -> dict:
    """Execute Phase 1 analysis."""
    
    instruction = instruction_path.read_text() if instruction_path.exists() else ""
    document = format_blocks_for_llm(blocks)
    
    schema = {
        "overview": {"type": "string", "parties": ["string"], "governingLaw": "string"},
        "clauses": [{"ordinal": "string", "topic": "string", "effect": "string", "interactsWith": ["string"]}],
        "observations": ["string"]
    }
    
    prompt = ANALYSIS_PROMPT.format(
        instruction=instruction,
        document=document,
        schema=json.dumps(schema, indent=2)
    )
    
    response = call_llm(prompt, model=model, response_format="json")
    return json.loads(response)

def format_blocks_for_llm(blocks: list[dict]) -> str:
    """Format blocks as readable document."""
    lines = []
    for block in blocks:
        ordinal = block.get('list', {}).get('ordinal', '')
        text = block.get('text', '')
        if ordinal:
            lines.append(f"{ordinal} {text}")
        else:
            lines.append(text)
    return '\n\n'.join(lines)
```

### T5.3: Phase 2 Implementation (2 days)
**File:** `effilocal/flows/review_phase2.py` (new)

```python
"""Phase 2: Gap Analysis"""

GAP_ANALYSIS_PROMPT = """You are a legal risk analyst. Based on the document analysis, identify:

## Issues to Identify

### HIGH PRIORITY
- Legal risks that could cause significant harm
- Non-compliance with regulations
- Unlimited liability exposure
- Missing mandatory provisions

### MEDIUM PRIORITY  
- Unfavorable terms that could be negotiated
- Vague provisions that could cause disputes
- Inconsistencies between clauses

### LOW PRIORITY
- Style/formatting issues
- Minor ambiguities
- Nice-to-have improvements

For each issue, provide:
- Description of the problem
- Which clause(s) are affected
- The risk if not addressed
- Recommended action

Instructions from lawyer:
{instruction}

Phase 1 Analysis:
{phase1_output}

Document content:
{document}

Respond in JSON format:
{{
  "high": [{{ "id": "1", "title": "...", "description": "...", "clauses": ["3.1"], "risk": "...", "recommendation": "..." }}],
  "medium": [...],
  "low": [...]
}}
"""

def run_phase2(
    instruction_path: Path,
    blocks: list[dict],
    phase1_output: dict,
    model: str = "gpt-4o"
) -> dict:
    """Execute Phase 2 gap analysis."""
    # Similar structure to Phase 1
    pass
```

### T5.4: Phase 3 Implementation (3 days)
**File:** `effilocal/flows/review_phase3.py` (new)

```python
"""Phase 3: Suggestions"""

SUGGESTIONS_PROMPT = """You are a legal drafting expert. For each identified issue, provide 2-3 drafting options.

For each option, provide:
- Label (e.g., "Option A: Add sub-cap")
- Full draft text (ready to insert)
- Notes explaining trade-offs

Consider:
- Market standard approaches
- Client's position (pro-customer vs pro-supplier from instruction)
- Risk/benefit balance

Instructions:
{instruction}

Issues to address:
{gaps}

Relevant document clauses:
{relevant_blocks}

{precedent_context}

Respond in JSON:
{{
  "suggestions": [
    {{
      "issueId": "1",
      "options": [
        {{ "id": "1a", "label": "Option A: ...", "text": "...", "notes": "..." }},
        {{ "id": "1b", "label": "Option B: ...", "text": "...", "notes": "..." }}
      ]
    }}
  ]
}}
"""

def run_phase3(
    instruction_path: Path,
    blocks: list[dict],
    phase2_output: dict,
    precedents: list[dict] = None,  # Relevant precedent clauses
    model: str = "gpt-4o"
) -> dict:
    """Execute Phase 3 suggestions."""
    
    # Filter to relevant blocks based on issues
    relevant_block_ids = extract_affected_clauses(phase2_output)
    relevant_blocks = [b for b in blocks if b['id'] in relevant_block_ids]
    
    # Format precedent context if available
    precedent_context = ""
    if precedents:
        precedent_context = "Reference precedent clauses:\n" + format_precedents(precedents)
    
    # Call LLM
    # ...
```

### T5.5: Phase 4 Implementation (2 days)
**File:** `effilocal/flows/review_phase4.py` (new)

```python
"""Phase 4: Execution"""

def run_phase4(
    document_path: Path,
    selections: dict[str, str],  # issueId -> optionId or custom text
    suggestions: list[dict],
    blocks: list[dict]
) -> dict:
    """Execute selected changes."""
    
    execution_log = []
    
    for issue_id, selection in selections.items():
        if selection == 'skip':
            continue
            
        suggestion = find_suggestion(suggestions, issue_id)
        option = find_option(suggestion, selection)
        
        if option:
            # Determine which MCP tool to use
            tool_call = plan_tool_call(option, blocks)
            
            # Execute
            result = execute_mcp_tool(document_path, tool_call)
            
            execution_log.append({
                "issueId": issue_id,
                "tool": tool_call["tool"],
                "success": result["success"],
                "message": result.get("message", "")
            })
    
    return {
        "success": all(e["success"] for e in execution_log),
        "log": execution_log
    }

def plan_tool_call(option: dict, blocks: list[dict]) -> dict:
    """Determine the right MCP tool for this change."""
    
    # Analyze option to determine action type
    if "add" in option.get("action", "").lower():
        return {
            "tool": "add_paragraph_after_clause",
            "args": {
                "clause_number": option["targetClause"],
                "text": option["text"],
                "inherit_numbering": True
            }
        }
    elif "replace" in option.get("action", "").lower():
        return {
            "tool": "replace_clause_text_by_ordinal",
            "args": {
                "clause_number": option["targetClause"],
                "new_text": option["text"]
            }
        }
    # etc.
```

### T5.6: Review Panel UI (3 days)
**File:** `extension/src/webview/review-panel.js` (new)

```javascript
class ReviewPanel {
  constructor(container, state) {
    this.container = container;
    this.state = state;
  }
  
  render() {
    this.container.innerHTML = `
      <div class="review-panel">
        ${this.renderProgress()}
        ${this.renderCurrentPhase()}
        ${this.renderActions()}
      </div>
    `;
  }
  
  renderProgress() {
    const phases = [
      { num: 1, name: 'Analysis', status: this.getPhaseStatus(1) },
      { num: 2, name: 'Gap Analysis', status: this.getPhaseStatus(2) },
      { num: 3, name: 'Suggestions', status: this.getPhaseStatus(3) },
      { num: 4, name: 'Execution', status: this.getPhaseStatus(4) }
    ];
    
    return `
      <div class="phase-progress">
        ${phases.map(p => `
          <div class="phase ${p.status}">
            <span class="indicator">${this.getIndicator(p.status)}</span>
            <span class="name">Phase ${p.num}: ${p.name}</span>
            ${p.status === 'complete' ? '<span class="check">✓</span>' : ''}
          </div>
        `).join('')}
      </div>
    `;
  }
  
  renderPhase3() {
    const { suggestions, currentIssueIndex } = this.state.phase3View;
    const current = suggestions[currentIssueIndex];
    
    return `
      <div class="phase3-content">
        <h3>Issue ${currentIssueIndex + 1} of ${suggestions.length}: ${current.title}</h3>
        <p class="issue-description">${current.description}</p>
        
        <div class="options">
          ${current.options.map((opt, i) => `
            <label class="option">
              <input type="radio" name="selection" value="${opt.id}" 
                     ${this.state.selections[current.issueId] === opt.id ? 'checked' : ''}>
              <div class="option-content">
                <div class="option-label">${opt.label}</div>
                <pre class="option-text">${opt.text}</pre>
                <div class="option-notes">${opt.notes}</div>
              </div>
            </label>
          `).join('')}
          
          <label class="option">
            <input type="radio" name="selection" value="skip">
            <div class="option-content">
              <div class="option-label">Skip (leave unchanged)</div>
            </div>
          </label>
        </div>
        
        <div class="navigation">
          <button ${currentIssueIndex === 0 ? 'disabled' : ''} onclick="prevIssue()">
            ← Previous
          </button>
          <button onclick="nextIssue()">
            ${currentIssueIndex === suggestions.length - 1 ? 'Finish Phase 3' : 'Next Issue →'}
          </button>
        </div>
      </div>
    `;
  }
}
```

---

## Testing Plan

### Unit Tests
- `test_phase1.py`: Analysis output structure
- `test_phase2.py`: Gap categorization
- `test_phase3.py`: Suggestion generation
- `test_phase4.py`: Tool execution planning

### Integration Tests
- Full 4-phase flow with test document
- State persistence across sessions
- Error recovery at each phase

### Manual Tests
1. Start review with instruction file
2. Review Phase 1 output
3. Review Phase 2 gaps
4. Select options in Phase 3
5. Confirm and execute Phase 4
6. Verify document changes

---

## Definition of Done

- [ ] All 4 phases functional
- [ ] State persists across sessions
- [ ] Lawyer can select/modify suggestions
- [ ] Changes applied correctly to document
- [ ] Execution log provides audit trail
- [ ] Unit tests passing
- [ ] Documentation updated

---

## Dependencies

- Sprint 4 complete (chat integration for LLM calls)
- MCP tools for document modification
- OpenAI/Anthropic API access

---

## Notes

- Consider caching LLM responses for replay
- Long documents may need chunked analysis
- Add "regenerate" option for each phase
- Future: Compare multiple precedents in Phase 3
