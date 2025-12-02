# Sprint 6: Precedent Bank & Tagging

**Duration:** 2 weeks  
**Goal:** Organized precedent library with metadata, search, and context injection for LLM.

---

## Objectives

1. **Precedent Metadata** - Tag precedents with type, stance, topics
2. **Precedent Index** - Searchable catalog of all precedents
3. **Clause Extraction** - Index individual clauses from precedents
4. **Context Injection** - Pull relevant precedent clauses into LLM context
5. **Drafting Notes** - Surface notes from precedents when relevant

---

## Precedent Organization

### Folder Structure

```
EL_Precedents/
├── index.json                    # Master index of all precedents
├── contracts/
│   ├── SaaS/
│   │   ├── pro-customer/
│   │   │   ├── saas-agreement-v1.docx
│   │   │   ├── saas-agreement-v1.meta.yaml
│   │   │   └── saas-agreement-v1.clauses.jsonl
│   │   └── pro-supplier/
│   │       └── ...
│   ├── NDA/
│   │   ├── mutual/
│   │   └── one-way/
│   ├── R&D/
│   ├── Services/
│   └── License/
└── clause-library/               # Standalone clauses
    ├── liability/
    │   ├── liability-cap-standard.md
    │   └── liability-cap-aggressive.md
    └── ip/
        ├── ip-ownership-customer.md
        └── ip-ownership-supplier.md
```

### Metadata Schema

```yaml
# saas-agreement-v1.meta.yaml
id: "550e8400-e29b-41d4-a716-446655440000"
name: "SaaS Agreement (Pro-Customer)"
version: "1.0"
created: "2024-06-15"
updated: "2025-01-10"

# Classification
type: SaaS
stance: pro-customer
jurisdiction: England

# Tags for search
tags:
  - software
  - subscription
  - cloud
  - liability-cap
  - data-protection
  - ip-ownership-customer

# Drafting notes flag
has_drafting_notes: true
drafting_notes_format: comments  # or 'inline' or 'separate-doc'

# Key clauses summary
clauses:
  - ordinal: "5.1"
    topic: liability
    stance: pro-customer
    summary: "Liability cap at 12 months fees with standard carve-outs"
    notes: "Can be negotiated up to 24 months for enterprise deals"
  
  - ordinal: "7"
    topic: data-protection
    stance: neutral
    summary: "GDPR-compliant DPA incorporated by reference"
    notes: "Schedule 3 contains the full DPA terms"
  
  - ordinal: "9.2"
    topic: ip-indemnity
    stance: pro-customer
    summary: "Mutual IP indemnity with uncapped supplier indemnity"
    notes: "Aggressive position - expect pushback"

# Document statistics
stats:
  total_clauses: 45
  pages: 18
  word_count: 8500
```

---

## User Stories

### US6.1: Add Precedent to Library
**As a** lawyer organizing my precedent bank,  
**I want** to add a document with metadata tags,  
**So that** I can find it later when relevant.

**Acceptance Criteria:**
- [ ] "Add Precedent" command/button
- [ ] Wizard for entering metadata
- [ ] Auto-extract basic info (clause count, etc.)
- [ ] Save to appropriate folder
- [ ] Test: Add precedent → find in search

### US6.2: Search Precedents
**As a** lawyer looking for a clause example,  
**I want** to search by type, stance, and topic,  
**So that** I find the most relevant precedent.

**Acceptance Criteria:**
- [ ] Search bar in precedent panel
- [ ] Filter by type (SaaS, NDA, etc.)
- [ ] Filter by stance (pro-customer/supplier)
- [ ] Filter by topic tags
- [ ] Test: Search "liability pro-customer" → find relevant precedents

### US6.3: Browse Precedent Clauses
**As a** lawyer reviewing a precedent,  
**I want** to see individual clauses with their notes,  
**So that** I can quickly find useful language.

**Acceptance Criteria:**
- [ ] Click precedent → see clause list
- [ ] Each clause shows topic, summary, notes
- [ ] Click clause → see full text
- [ ] Copy clause button
- [ ] Test: Browse → find → copy liability clause

### US6.4: Precedent in Review Workflow
**As a** lawyer in Phase 3 of review,  
**I want** relevant precedent clauses suggested,  
**So that** I can use proven language.

**Acceptance Criteria:**
- [ ] Phase 3 includes precedent references
- [ ] "Similar clauses from precedents" section
- [ ] Can select precedent clause as option
- [ ] Test: Review gap about liability → see precedent options

### US6.5: Drafting Notes Display
**As a** lawyer using a precedent clause,  
**I want** to see the drafting notes,  
**So that** I understand when to use/modify it.

**Acceptance Criteria:**
- [ ] Drafting notes visible with clause
- [ ] Notes from Word comments extracted
- [ ] Notes highlighted distinctly
- [ ] Test: View clause with notes → notes visible

---

## Technical Design

### Precedent Index Schema

```json
// EL_Precedents/index.json
{
  "version": 1,
  "updated": "2025-12-02T10:00:00Z",
  "precedents": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "SaaS Agreement (Pro-Customer)",
      "path": "contracts/SaaS/pro-customer/saas-agreement-v1.docx",
      "metaPath": "contracts/SaaS/pro-customer/saas-agreement-v1.meta.yaml",
      "type": "SaaS",
      "stance": "pro-customer",
      "tags": ["software", "subscription", "liability-cap"],
      "clauseCount": 45,
      "hasDraftingNotes": true
    }
  ],
  "clauseLibrary": [
    {
      "id": "clause-001",
      "name": "Liability Cap (Standard)",
      "path": "clause-library/liability/liability-cap-standard.md",
      "topic": "liability",
      "stance": "neutral",
      "tags": ["liability", "cap", "12-months"]
    }
  ]
}
```

### Clause Extraction Schema

```jsonl
// saas-agreement-v1.clauses.jsonl
{"ordinal": "5.1", "topic": "liability", "text": "Subject to clause 5.2...", "notes": "Standard position", "para_id": "3DD8236A"}
{"ordinal": "5.2", "topic": "liability-exclusions", "text": "Nothing in this Agreement...", "notes": "", "para_id": "4EE9347B"}
```

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Extension                                  │
│  ┌───────────────┐  ┌────────────────────────────────────┐  │
│  │ Precedent     │  │         Webview                     │  │
│  │ Tree View     │  │  ┌──────────────────────────────┐  │  │
│  │               │  │  │ Precedent Search             │  │  │
│  │ ▼ SaaS        │  │  │ [🔍 Search...    ] [Filters] │  │  │
│  │   ▼ Pro-Cust  │  │  ├──────────────────────────────┤  │  │
│  │     📄 v1     │  │  │ Results:                      │  │  │
│  │   ▶ Pro-Supp  │  │  │ 📄 SaaS Pro-Customer v1      │  │  │
│  │ ▶ NDA         │  │  │    Clause 5.1: Liability...  │  │  │
│  │ ▶ Services    │  │  │    [Copy] [Use in Review]    │  │  │
│  │               │  │  └──────────────────────────────┘  │  │
│  └───────────────┘  └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                   MCP Server                                 │
│  - Index management                                          │
│  - Clause extraction                                         │
│  - Search/filter                                             │
│  - Drafting notes extraction                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Technical Tasks

### T6.1: Precedent Index Manager (2 days)
**File:** `effilocal/precedents/index_manager.py` (new)

```python
"""Manage precedent index and metadata."""

from pathlib import Path
import json
import yaml
from typing import Optional, List

class PrecedentIndexManager:
    def __init__(self, precedent_root: Path):
        self.root = precedent_root
        self.index_path = precedent_root / "index.json"
        self.index = self._load_index()
    
    def _load_index(self) -> dict:
        if self.index_path.exists():
            return json.loads(self.index_path.read_text())
        return {"version": 1, "precedents": [], "clauseLibrary": []}
    
    def add_precedent(
        self, 
        docx_path: Path, 
        metadata: dict,
        analyze: bool = True
    ) -> dict:
        """Add a precedent to the index."""
        # Generate ID
        precedent_id = str(uuid.uuid4())
        
        # Determine destination path
        dest_folder = self.root / "contracts" / metadata["type"] / metadata["stance"]
        dest_folder.mkdir(parents=True, exist_ok=True)
        
        # Copy document
        dest_docx = dest_folder / docx_path.name
        shutil.copy(docx_path, dest_docx)
        
        # Write metadata
        meta_path = dest_docx.with_suffix('.meta.yaml')
        metadata["id"] = precedent_id
        with open(meta_path, 'w') as f:
            yaml.dump(metadata, f)
        
        # Analyze and extract clauses
        if analyze:
            clauses = self.extract_clauses(dest_docx, metadata)
            clauses_path = dest_docx.with_suffix('.clauses.jsonl')
            with open(clauses_path, 'w') as f:
                for clause in clauses:
                    f.write(json.dumps(clause) + '\n')
        
        # Update index
        self.index["precedents"].append({
            "id": precedent_id,
            "name": metadata["name"],
            "path": str(dest_docx.relative_to(self.root)),
            "metaPath": str(meta_path.relative_to(self.root)),
            "type": metadata["type"],
            "stance": metadata["stance"],
            "tags": metadata.get("tags", []),
            "clauseCount": len(clauses) if analyze else 0,
            "hasDraftingNotes": metadata.get("has_drafting_notes", False)
        })
        
        self._save_index()
        return self.index["precedents"][-1]
    
    def search(
        self,
        query: str = None,
        type_filter: str = None,
        stance_filter: str = None,
        tags: List[str] = None
    ) -> List[dict]:
        """Search precedents by various criteria."""
        results = self.index["precedents"]
        
        if type_filter:
            results = [p for p in results if p["type"] == type_filter]
        
        if stance_filter:
            results = [p for p in results if p["stance"] == stance_filter]
        
        if tags:
            results = [p for p in results if any(t in p["tags"] for t in tags)]
        
        if query:
            query_lower = query.lower()
            results = [p for p in results if 
                       query_lower in p["name"].lower() or
                       any(query_lower in t for t in p["tags"])]
        
        return results
    
    def get_clauses(self, precedent_id: str, topic: str = None) -> List[dict]:
        """Get clauses from a precedent, optionally filtered by topic."""
        precedent = self.get_precedent(precedent_id)
        if not precedent:
            return []
        
        clauses_path = self.root / precedent["path"].replace('.docx', '.clauses.jsonl')
        if not clauses_path.exists():
            return []
        
        clauses = []
        with open(clauses_path) as f:
            for line in f:
                clause = json.loads(line)
                if topic is None or clause.get("topic") == topic:
                    clauses.append(clause)
        
        return clauses
```

### T6.2: Clause Extraction with Notes (2 days)
**File:** `effilocal/precedents/clause_extractor.py` (new)

```python
"""Extract clauses and drafting notes from precedent documents."""

from docx import Document
from effilocal.mcp_server.core.comments import extract_all_comments

def extract_clauses(docx_path: Path, metadata: dict) -> List[dict]:
    """Extract all clauses with their drafting notes."""
    
    # Analyze document structure
    from effilocal.flows.analyze_doc import analyze
    analysis_dir = docx_path.parent / f".{docx_path.stem}_analysis"
    analyze(docx_path, doc_id=str(uuid.uuid4()), out_dir=analysis_dir)
    
    # Load blocks
    blocks_path = analysis_dir / "blocks.jsonl"
    blocks = [json.loads(line) for line in blocks_path.read_text().splitlines()]
    
    # Extract comments as drafting notes
    comments = extract_all_comments(str(docx_path))
    comment_by_para = {c["para_id"]: c for c in comments}
    
    # Build clause list
    clauses = []
    for block in blocks:
        if not block.get("list", {}).get("ordinal"):
            continue  # Skip non-numbered blocks
        
        clause = {
            "ordinal": block["list"]["ordinal"],
            "text": block["text"],
            "para_id": block.get("para_id"),
            "topic": infer_topic(block["text"]),  # Simple keyword matching
            "notes": ""
        }
        
        # Add drafting notes from comments
        if block.get("para_id") in comment_by_para:
            comment = comment_by_para[block["para_id"]]
            clause["notes"] = comment["text"]
        
        clauses.append(clause)
    
    # Clean up temp analysis
    shutil.rmtree(analysis_dir)
    
    return clauses

def infer_topic(text: str) -> str:
    """Infer clause topic from text using keyword matching."""
    text_lower = text.lower()
    
    topics = {
        "liability": ["liability", "liable", "damages", "losses"],
        "indemnity": ["indemnify", "indemnification", "hold harmless"],
        "ip": ["intellectual property", "patent", "copyright", "trademark"],
        "confidentiality": ["confidential", "non-disclosure", "proprietary"],
        "termination": ["terminate", "termination", "expiry"],
        "payment": ["payment", "fees", "invoice", "price"],
        "warranty": ["warranty", "warrants", "represents"],
        "data-protection": ["data protection", "gdpr", "personal data", "privacy"]
    }
    
    for topic, keywords in topics.items():
        if any(kw in text_lower for kw in keywords):
            return topic
    
    return "general"
```

### T6.3: Precedent Tree View (2 days)
**File:** `extension/src/precedentProvider.ts` (new)

```typescript
import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

export class PrecedentProvider implements vscode.TreeDataProvider<PrecedentItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<PrecedentItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
  
  constructor(private precedentRoot: string) {}
  
  refresh(): void {
    this._onDidChangeTreeData.fire(undefined);
  }
  
  getTreeItem(element: PrecedentItem): vscode.TreeItem {
    return element;
  }
  
  async getChildren(element?: PrecedentItem): Promise<PrecedentItem[]> {
    if (!element) {
      // Root level - show types
      return this.getTypes();
    }
    
    if (element.contextValue === 'type') {
      // Show stances
      return this.getStances(element.type);
    }
    
    if (element.contextValue === 'stance') {
      // Show precedents
      return this.getPrecedents(element.type, element.stance);
    }
    
    if (element.contextValue === 'precedent') {
      // Show clauses
      return this.getClauses(element.precedentId);
    }
    
    return [];
  }
  
  private getTypes(): PrecedentItem[] {
    const types = ['SaaS', 'NDA', 'Services', 'R&D', 'License'];
    return types.map(t => new PrecedentItem(
      t,
      vscode.TreeItemCollapsibleState.Collapsed,
      'type',
      { type: t }
    ));
  }
  
  // ... other methods
}

class PrecedentItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly contextValue: string,
    public readonly metadata: any = {}
  ) {
    super(label, collapsibleState);
    
    this.type = metadata.type;
    this.stance = metadata.stance;
    this.precedentId = metadata.precedentId;
  }
}
```

### T6.4: Precedent Search Panel (2 days)
**File:** `extension/src/webview/precedent-search.js` (new)

```javascript
class PrecedentSearch {
  constructor(container) {
    this.container = container;
    this.results = [];
    this.filters = {
      type: null,
      stance: null,
      tags: []
    };
  }
  
  render() {
    this.container.innerHTML = `
      <div class="precedent-search">
        <div class="search-bar">
          <input type="text" id="precedent-query" placeholder="Search precedents...">
          <button id="search-btn">🔍</button>
        </div>
        
        <div class="filters">
          <select id="type-filter">
            <option value="">All Types</option>
            <option value="SaaS">SaaS</option>
            <option value="NDA">NDA</option>
            <option value="Services">Services</option>
          </select>
          
          <select id="stance-filter">
            <option value="">All Stances</option>
            <option value="pro-customer">Pro-Customer</option>
            <option value="pro-supplier">Pro-Supplier</option>
            <option value="neutral">Neutral</option>
          </select>
        </div>
        
        <div class="results">
          ${this.renderResults()}
        </div>
      </div>
    `;
    
    this.setupEventListeners();
  }
  
  renderResults() {
    if (this.results.length === 0) {
      return '<p class="no-results">No precedents found</p>';
    }
    
    return this.results.map(p => `
      <div class="precedent-result" data-id="${p.id}">
        <div class="result-header">
          <span class="result-name">${p.name}</span>
          <span class="result-stance ${p.stance}">${p.stance}</span>
        </div>
        <div class="result-tags">
          ${p.tags.map(t => `<span class="tag">${t}</span>`).join('')}
        </div>
        <div class="result-actions">
          <button class="view-clauses-btn" data-id="${p.id}">View Clauses</button>
          <button class="use-in-review-btn" data-id="${p.id}">Use in Review</button>
        </div>
      </div>
    `).join('');
  }
  
  async search(query) {
    vscode.postMessage({
      command: 'searchPrecedents',
      query,
      filters: this.filters
    });
  }
  
  showClauses(precedentId) {
    vscode.postMessage({
      command: 'getPrecedentClauses',
      precedentId
    });
  }
}
```

### T6.5: Context Injection for Review (2 days)
**File:** `effilocal/precedents/context_builder.py` (new)

```python
"""Build precedent context for LLM review phases."""

def build_precedent_context(
    gaps: List[dict],
    index_manager: PrecedentIndexManager,
    stance_preference: str = None,
    max_clauses: int = 10
) -> str:
    """Build precedent context relevant to identified gaps."""
    
    context_parts = []
    
    for gap in gaps:
        # Get topic from gap
        topic = gap.get("topic") or infer_topic_from_gap(gap)
        
        # Find relevant precedents
        filters = {"tags": [topic]}
        if stance_preference:
            filters["stance_filter"] = stance_preference
        
        precedents = index_manager.search(**filters)
        
        if not precedents:
            continue
        
        # Get clauses from top precedent
        clauses = index_manager.get_clauses(precedents[0]["id"], topic=topic)
        
        if clauses:
            context_parts.append(f"\n## Precedent for: {gap['title']}")
            context_parts.append(f"From: {precedents[0]['name']} ({precedents[0]['stance']})")
            
            for clause in clauses[:3]:  # Limit to 3 per gap
                context_parts.append(f"\nClause {clause['ordinal']}:")
                context_parts.append(clause['text'])
                if clause.get('notes'):
                    context_parts.append(f"[Drafting Note: {clause['notes']}]")
    
    return '\n'.join(context_parts)
```

### T6.6: MCP Tools for Precedents (1 day)
**File:** `effilocal/mcp_server/tools/precedent_tools.py` (new)

```python
"""MCP tools for precedent management."""

async def search_precedents(
    query: str = None,
    type_filter: str = None,
    stance_filter: str = None,
    tags: list = None
) -> str:
    """Search the precedent library."""
    manager = get_precedent_manager()
    results = manager.search(query, type_filter, stance_filter, tags)
    return json.dumps(results, indent=2)

async def get_precedent_clauses(
    precedent_id: str,
    topic: str = None
) -> str:
    """Get clauses from a specific precedent."""
    manager = get_precedent_manager()
    clauses = manager.get_clauses(precedent_id, topic)
    return json.dumps(clauses, indent=2)

async def add_precedent(
    docx_path: str,
    name: str,
    type: str,
    stance: str,
    tags: list = None
) -> str:
    """Add a new precedent to the library."""
    manager = get_precedent_manager()
    result = manager.add_precedent(
        Path(docx_path),
        {"name": name, "type": type, "stance": stance, "tags": tags or []}
    )
    return f"Added precedent: {result['name']} (ID: {result['id']})"
```

---

## Testing Plan

### Unit Tests
- `test_index_manager.py`: Add, search, get operations
- `test_clause_extractor.py`: Extraction with notes
- `test_context_builder.py`: Context generation

### Integration Tests
- Add precedent → search → find
- Extract clauses → include in review context
- End-to-end with review workflow

### Manual Tests
1. Add precedent via command
2. Search by type and stance
3. Browse clauses with notes
4. Use precedent in Phase 3 review

---

## Definition of Done

- [ ] Can add precedents with metadata
- [ ] Search works by type/stance/tags
- [ ] Clauses extracted with drafting notes
- [ ] Precedent context available in review Phase 3
- [ ] Tree view shows precedent library
- [ ] Unit tests passing
- [ ] Documentation updated

---

## Dependencies

- Sprint 5 complete (review workflow)
- Comment extraction for drafting notes

---

## Notes

- Consider versioning for precedents (v1, v2, etc.)
- Add "compare precedents" feature in future
- Consider embedding-based similarity search
- May want to support non-.docx formats (Markdown, PDF)
