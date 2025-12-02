# Effi Contract Editor - Sprint Roadmap

## Vision Statement

Build a VS Code extension that serves as a lightweight Word-like editor for contract drafting, with integrated LLM assistance that can analyze documents, identify issues, suggest improvements, and execute edits—all within VS Code's webview.

**Target User:** Solo lawyer drafting commercial contracts.

**Core Value Proposition:** 
- Edit contracts directly in VS Code (no external Word dependency for basic editing)
- LLM-powered multi-phase contract review workflow
- Precedent-aware drafting with context from precedent banks
- Version control and audit trail built-in

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     VS Code Extension                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────────────────────────┐  │
│  │  Project Tree   │  │           Webview Editor             │  │
│  │  (Side Panel)   │  │  ┌────────────────────────────────┐  │  │
│  │                 │  │  │  Toolbar (B/I/U, Comments)     │  │  │
│  │  - Projects     │  │  ├────────────────────────────────┤  │  │
│  │  - Precedents   │  │  │                                │  │  │
│  │  - Instructions │  │  │  WYSIWYG Document Editor       │  │  │
│  │                 │  │  │  (ContentEditable + Blocks)    │  │  │
│  │                 │  │  │                                │  │  │
│  │                 │  │  ├────────────────────────────────┤  │  │
│  │                 │  │  │  LLM Chat Panel (collapsible)  │  │  │
│  └─────────────────┘  │  └────────────────────────────────┘  │  │
├─────────────────────────────────────────────────────────────────┤
│                    MCP Server (Python)                           │
│  - Document read/write (.docx ↔ JSON ↔ .docx)                   │
│  - Block ID management (para_id + hash fallback)                  │
│  - Precedent indexing & search                                    │
│  - LLM orchestration (multi-phase workflow)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Sprint Overview

| Sprint | Theme | Duration | Key Deliverables |
|--------|-------|----------|------------------|
| **S1** | Foundation & UUID Persistence | 2 weeks | Embedded UUIDs, hybrid git, re-analysis stability |
| **S2** | WYSIWYG Editor Core | 2 weeks | ContentEditable editor, basic formatting, save to .docx |
| **S3** | Comments & Track Changes | 2 weeks | Comment system, change tracking, accept/reject |
| **S4** | LLM Chat Integration | 2 weeks | Chat panel, VS Code chat bridge, context assembly |
| **S5** | Multi-Phase Review Workflow | 2 weeks | 4-phase review: Analyze → Gap → Suggest → Execute |
| **S6** | Precedent Bank & Tagging | 2 weeks | Precedent metadata, search, context injection |
| **S7** | Project Management & UX | 2 weeks | New project wizard, instruction Q&A, polish |

**Total: ~14 weeks (3.5 months)**

---

## Detailed Sprint Plans

### Sprint 1: Foundation & UUID Persistence
**Goal:** Stable document identity that survives external edits and re-analysis.

See: [SPRINT_01_FOUNDATION.md](./SPRINT_01_FOUNDATION.md)

### Sprint 2: WYSIWYG Editor Core  
**Goal:** Replace read-only view with editable document interface.

See: [SPRINT_02_WYSIWYG_EDITOR.md](./SPRINT_02_WYSIWYG_EDITOR.md)

### Sprint 3: Comments & Track Changes
**Goal:** Full commenting and revision tracking within the editor.

See: [SPRINT_03_COMMENTS_TRACKCHANGES.md](./SPRINT_03_COMMENTS_TRACKCHANGES.md)

### Sprint 4: LLM Chat Integration
**Goal:** Seamless chat experience with document context.

See: [SPRINT_04_LLM_CHAT.md](./SPRINT_04_LLM_CHAT.md)

### Sprint 5: Multi-Phase Review Workflow
**Goal:** Structured 4-phase contract review with LLM guidance.

See: [SPRINT_05_REVIEW_WORKFLOW.md](./SPRINT_05_REVIEW_WORKFLOW.md)

### Sprint 6: Precedent Bank & Tagging
**Goal:** Organized precedent library with metadata and search.

See: [SPRINT_06_PRECEDENTS.md](./SPRINT_06_PRECEDENTS.md)

### Sprint 7: Project Management & UX
**Goal:** Streamlined project creation and workflow polish.

See: [SPRINT_07_PROJECT_UX.md](./SPRINT_07_PROJECT_UX.md)

---

## Key Technical Decisions

### 1. Block ID Matching Strategy
- **Primary:** Native `w14:paraId` attribute on each paragraph (8-char hex, Word-assigned)
- **Fallback:** SHA-256 content hash for matching after external edits
- **Recovery:** Position + neighbor heuristics when hash fails

### 2. Document Format Flow
```
.docx (source) 
  → analyze → blocks.jsonl + sections.json (canonical)
    → webview renders blocks as ContentEditable divs
      → edits update in-memory block model
        → save → regenerate .docx with UUIDs preserved
```

### 3. Git Integration
- **Auto-commit:** On explicit save (Ctrl+S) or "Save Checkpoint"
- **Message format:** `[effi] <action>: <summary>` (e.g., `[effi] edit: Modified clause 3.2.1`)
- **Artifact commits:** Include both .docx and analysis artifacts

### 4. LLM Context Strategy
| Phase | Context Includes |
|-------|------------------|
| Analysis | instruction.md + all blocks |
| Gap Analysis | instruction.md + all blocks + phase 1 output |
| Suggestions | instruction.md + relevant blocks + precedent clauses |
| Execution | instruction.md + target blocks + user choices + MCP tools |

### 5. Precedent Metadata Schema
```yaml
# precedent.meta.yaml (sidecar file)
id: uuid
name: "SaaS Agreement (Pro-Customer)"
type: SaaS
stance: pro-customer
tags: [software, subscription, liability-cap]
has_drafting_notes: true
clauses:
  - ordinal: "5.1"
    topic: liability
    notes: "Standard carve-outs for fraud, death, IP"
```

---

## Dependencies & Risks

### Technical Dependencies
- **python-docx:** Paragraph property manipulation (XML-level access for w:tag)
- **VS Code Chat API:** For triggering Copilot from webview
- **ContentEditable:** Browser quirks with rich text editing

### Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| ContentEditable complexity | High | Use established library (Lexical, Slate, or ProseMirror) |
| UUID loss on external edit | Medium | Hash fallback + user notification |
| LLM context limits | Medium | Smart truncation, section-based chunking |
| .docx fidelity on round-trip | High | Extensive testing, preserve original XML where possible |

---

## Success Metrics

### Sprint 1 Complete When:
- [x] Block IDs matched via `w14:paraId` survive Word edits
- [x] Re-analysis matches 95%+ of blocks by para_id
- [x] Git commits on save with meaningful messages

### Sprint 2 Complete When:
- [ ] User can edit text directly in webview
- [ ] Bold/Italic/Underline formatting works
- [ ] Changes persist to .docx on save

### Sprint 3 Complete When:
- [ ] Comments visible and addable in editor
- [ ] Track changes shows insertions/deletions
- [ ] Accept/reject individual changes

### Sprint 4 Complete When:
- [ ] Chat panel opens from webview button
- [ ] Selected text/clauses sent as context
- [ ] LLM responses can trigger MCP tools

### Sprint 5 Complete When:
- [ ] 4-phase workflow executable end-to-end
- [ ] Each phase produces structured output
- [ ] User can steer suggestions before execution

### Sprint 6 Complete When:
- [ ] Precedents indexed with metadata
- [ ] Search by type/stance/topic works
- [ ] LLM can pull relevant precedent clauses

### Sprint 7 Complete When:
- [ ] "New Project" wizard creates structure
- [ ] Instruction Q&A generates context file
- [ ] Overall UX feels cohesive

---

## Next Steps

1. Review and approve this roadmap
2. Begin Sprint 1 implementation
3. Set up weekly check-ins for progress review
