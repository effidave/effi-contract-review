# Artifact System Guide

This guide covers the document analysis artifacts and how to use them in the VSCode webview application.

## Overview

The analysis pipeline converts Word documents into structured JSON artifacts that power the webview UI and enable programmatic document editing via MCP tools.

**Workflow:**
```
Word .docx 
  → analyze CLI 
    → JSON artifacts 
      → VSCode webview (display + edit) 
        → MCP tools (modify document) 
          → re-analyze 
            → update artifacts 
              → refresh webview
```

## Core Artifacts

### 1. manifest.json
**Purpose**: Document metadata and integrity verification

**Key fields:**
```json
{
  "doc_id": "123e4567-...",           // Unique document identifier
  "v": 1,                              // Artifact version
  "created_at": "2025-11-29T14:28:02+00:00",
  "checksums": {                       // SHA-256 for integrity checks
    "raw.docx": "sha256:9c73d...",
    "blocks.jsonl": "sha256:1c1dc...",
    // ... other artifacts
  },
  "attachments": [                     // Detected schedules/annexes
    {
      "attachment_id": "24e1c939-...",
      "type": "schedule",
      "label": "Schedule 1",
      // ... metadata
    }
  ]
}
```

**Usage:**
- Verify document hasn't changed (compare checksums)
- Discover detected schedules/annexes
- Track artifact versions

### 2. blocks.jsonl
**Purpose**: Line-delimited JSON containing every document content block

**One block per line:**
```json
{
  "id": "4b12c339-...",                          // Unique block ID (UUID)
  "type": "paragraph|list_item|heading|table",
  "text": "This agreement is dated [DATE]",
  "content_hash": "sha256:e8afd63f...",
  "style": "Intro Default",                      // Word style name
  "style_id": "IntroDefault",
  "para_id": "3DD8236A",                         // Word's internal paragraph ID
  "para_idx": 0,                                 // 0-based paragraph index
  "list": {                                      // Only if numbered/bulleted
    "ordinal": "1.2.3",                          // Rendered clause number
    "level": 2,                                  // Nesting depth (0-based)
    "counters": [1, 2, 3],                       // Counter values at each level
    "format": "decimal",                         // decimal, lowerLetter, upperLetter, etc.
    "pattern": "%1.%2.%3",                       // Rendering template
    "is_legal": false,
    "restart_boundary": true,                    // True if numbering restarts here
    // ... additional numbering metadata
  },
  "section_id": "d8026558-...",                  // Links to sections.json
  "attachment_id": null,                         // Set if block is in schedule/annex
  "clause_group_id": "4b12c339-...",             // Groups clause + continuations
  "continuation_of": null,                       // Block ID of main clause (if continuation)
  "heading": {
    "text": "Body (no heading)",
    "source": "none|explicit|toc_synthesized",
    "fallback_label": "Body (no heading)"
  }
}
```

**Usage:**
- **Display**: Render blocks in webview with proper styling
- **Search**: Grep for text, filter by type/style
- **Edit targeting**: Use `para_id` to locate blocks for MCP operations
- **Navigation**: Follow `section_id` to understand hierarchy

**Key patterns:**
- `list` field present = numbered/bulleted block
- `attachment_id` present = block is in a schedule/annex
- `continuation_of` present = unnumbered paragraph continuing a clause

### 3. sections.json
**Purpose**: Hierarchical tree structure of document sections

**Structure:**
```json
{
  "doc_id": "123e4567-...",
  "hierarchy_depth": 4,                // Maximum nesting depth
  "root": {
    "children": [
      {
        "id": "cdbe0dc5-...",          // Section ID
        "title": "Interpretation",      // Section heading
        "level": 1,                     // Hierarchy level (1-based)
        "block_ids": [                  // Blocks in this section
          "ca64a674-...",
          "4a52aabc-..."
        ],
        "role": "definitions",          // Semantic role (optional)
        "attachment_id": null,          // Set if section is in schedule
        "children": [                   // Nested subsections
          {
            "id": "bcd1dc02-...",
            "title": "Body (no heading)",
            "level": 2,
            "block_ids": ["1124b350-..."],
            "children": []
          }
        ]
      }
    ]
  }
}
```

**Semantic roles:**
- `"front_matter"` - Agreement date, parties
- `"definitions"` - Definitions clause
- `"main_body"` - Main clauses
- `null` - Standard section

**Usage:**
- **Tree view**: Display collapsible section hierarchy in webview
- **Navigation**: Click section → load corresponding blocks
- **Context**: Show which section user is viewing/editing

### 4. relationships.json
**Purpose**: Block-level parent/child relationships and full numbering metadata

**Structure:**
```json
{
  "doc_id": "123e4567-...",
  "relationships": [
    {
      "block_id": "ca64a674-...",
      "parent_block_id": null,          // Parent block ID or null for roots
      "child_block_ids": [              // Direct children
        "1124b350-...",
        "efe880c4-..."
      ],
      "sibling_ordinal": 10,            // Position among siblings (0-based)
      "source": "heading|list|paragraph",
      "restart_group_id": "listgrp-2725fd...",  // Numbering restart group
      "attachment_id": null,
      "clause_group_id": "ca64a674-...",        // Groups clause + continuations
      "continuation_of": null,                  // Main clause ID if continuation
      "list_meta": {                    // Full numbering details (if numbered)
        "num_id": 24,
        "abstract_num_id": 0,
        "level": 0,
        "counters": [1],
        "ordinal": "1.",
        "format": "decimal",
        "pattern": "%1.",
        "is_legal": false,
        "restart_boundary": true,
        "list_instance_id": "listinst-c883d40c...",
        "numbering_digest": "num-d6afb0ea...",
        "ordinal_at_parse": 1
      }
    }
  ]
}
```

**Usage:**
- **Hierarchy traversal**: Find parent/child/sibling blocks
- **Clause grouping**: Get all blocks in a clause group (main + continuations)
- **Numbering queries**: Find blocks by ordinal (e.g., "3.2.1")
- **Restart detection**: Identify schedule boundaries via `restart_group_id`

### 5. styles.json
**Purpose**: Aggregated style usage statistics

**Structure:**
```json
{
  "doc_id": "123e4567-...",
  "styles": [
    {
      "style_id": "Normal",
      "style_name": "Normal",
      "count": 156,
      "semantic_hint": "body_text"
    }
  ]
}
```

**Usage:**
- Style analysis and consistency checking
- Understanding document formatting patterns

### 6. index.json
**Purpose**: Artifact statistics and file map

**Structure:**
```json
{
  "doc_id": "123e4567-...",
  "block_count": 660,
  "section_count": 198,
  "attachment_count": 3,
  "files": {
    "blocks": "blocks.jsonl",
    "sections": "sections.json",
    // ... other file paths
  }
}
```

**Usage:**
- Quick document statistics
- Artifact file discovery

## Common Queries

### Display Document in Webview

```python
import json

# Load artifacts
with open('blocks.jsonl') as f:
    blocks = [json.loads(line) for line in f]

sections = json.load(open('sections.json'))

# Create lookup indexes
blocks_by_id = {b['id']: b for b in blocks}

# Render sections recursively
def render_section(section, depth=0):
    print(f"{'  ' * depth}{section['title']}")
    for block_id in section['block_ids']:
        block = blocks_by_id[block_id]
        ordinal = block.get('list', {}).get('ordinal', '') if block.get('list') else ''
        print(f"{'  ' * (depth+1)}{ordinal} {block['text'][:60]}...")
    
    for child in section.get('children', []):
        render_section(child, depth + 1)

# Render from root
for section in sections['root']['children']:
    render_section(section)
```

### Find Clause by Number

```python
# Find all blocks with ordinal "3.2.1"
target_ordinal = "3.2.1"

matching_blocks = [
    b for b in blocks 
    if b.get('list', {}).get('ordinal') == target_ordinal
]

# Get full clause including continuations
def get_clause_group(block):
    clause_group_id = block['clause_group_id']
    return [
        b for b in blocks 
        if b['clause_group_id'] == clause_group_id
    ]

full_clause = get_clause_group(matching_blocks[0])
```

### Get Section Context for Block

```python
def find_section_by_id(sections, section_id, path=[]):
    """Find section and return path from root"""
    for section in sections:
        current_path = path + [section['title']]
        if section['id'] == section_id:
            return current_path
        if section.get('children'):
            result = find_section_by_id(section['children'], section_id, current_path)
            if result:
                return result
    return None

# Get context for a block
block = blocks[0]
section_path = find_section_by_id(
    sections['root']['children'], 
    block['section_id']
)
print(" > ".join(section_path))  # e.g., "Interpretation > Definitions"
```

### Get All Schedules

```python
manifest = json.load(open('manifest.json'))

# List schedules
for attachment in manifest['attachments']:
    print(f"{attachment['label']}: {attachment['attachment_id']}")
    
    # Get all blocks in this schedule
    schedule_blocks = [
        b for b in blocks 
        if b.get('attachment_id') == attachment['attachment_id']
    ]
    print(f"  {len(schedule_blocks)} blocks")
```

### Verify Document Unchanged

```python
import hashlib

def compute_sha256(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"

manifest = json.load(open('manifest.json'))
current_hash = compute_sha256('raw.docx')

if current_hash == manifest['checksums']['raw.docx']:
    print("✓ Document unchanged")
else:
    print("✗ Document modified - re-analyze needed")
```

## MCP Integration

### Edit Workflow (with versioning)

```python
# 1. Find block to edit
target_clause = "2.1"
block = next(
    b for b in blocks 
    if b.get('list', {}).get('ordinal') == target_clause
)

# 2. Prepare MCP request
mcp_request = {
    'tool': 'add_paragraph_after_clause',
    'args': {
        'filename': 'contract.docx',
        'clause_number': '2.1',
        'text': 'New subclause text',
        'inherit_numbering': True
    }
}

# 3. Record edit (handles execution + versioning)
history = EditHistory(project_dir='EL_Projects/Test Project')

version = history.record_edit(
    mcp_request=mcp_request,
    description="Added confidentiality clause",
    llm_reasoning="User requested non-disclosure terms in Services section"
)

# 4. Execute MCP tool
from mcp import add_paragraph_after_clause
result = add_paragraph_after_clause(**mcp_request['args'])

# 5. History manager automatically:
#    - Re-analyzes document
#    - Computes artifact diff
#    - Creates checkpoint if needed
#    - Appends to edit log
#    - Returns new version number

# 6. Reload artifacts in webview
blocks = [json.loads(line) for line in open('blocks.jsonl')]
sections = json.load(open('sections.json'))
# ... refresh UI with version indicator
```

**Note**: The EditHistory class can be enhanced to execute MCP tools directly, ensuring atomic edit+log operations.

### Available MCP Tools

Key MCP tools for document editing:

- **add_paragraph_after_clause()** - Insert text after specific clause
- **add_paragraphs_after_clause()** - Bulk insert
- **search_and_replace()** - Find/replace with whole-word option
- **add_heading()** - Insert section headings
- **get_document_outline()** - Get Word document structure
- **get_document_text()** - Extract all text

See MCP server documentation for full tool list.

## Version History & Rollback

### Architecture Considerations

**Goal**: Permanent sequential history of edits with rollback capability

**Recommended approach**: Event-sourced edit log

```
Edit Event = {
  timestamp,
  user_action_description,    // LLM-generated explanation
  mcp_request,                 // Tool name + parameters
  artifact_diff,               // Changes to blocks/sections/relationships
  document_checkpoint          // Optional: full .docx snapshot
}
```

**Storage strategy:**

```
project/
  ├─ contract.docx                    # Current version
  ├─ analysis/                        # Current artifacts
  │   ├─ manifest.json
  │   ├─ blocks.jsonl
  │   └─ ...
  └─ history/                         # Edit history
      ├─ edit_log.jsonl               # Append-only log
      ├─ checkpoints/                 # Periodic full snapshots
      │   ├─ v1_2025-11-29_14-30.docx
      │   ├─ v2_2025-11-29_15-45.docx
      │   └─ ...
      └─ artifact_versions/           # Optional: full artifact snapshots
          ├─ v1/
          └─ v2/
```

### Edit Log Format

**edit_log.jsonl** (one event per line):

```json
{
  "version": 1,
  "timestamp": "2025-11-29T15:45:23+00:00",
  "user": "david@example.com",
  "action": {
    "type": "add_clause",
    "description": "Added confidentiality obligations to clause 8.2",
    "llm_reasoning": "User requested addition of non-disclosure terms..."
  },
  "mcp_request": {
    "tool": "add_paragraph_after_clause",
    "args": {
      "filename": "contract.docx",
      "clause_number": "8.2",
      "text": "The Recipient shall...",
      "inherit_numbering": true
    }
  },
  "changes": {
    "blocks_added": [
      {
        "id": "new-uuid-123",
        "type": "list_item",
        "text": "The Recipient shall...",
        "list": {"ordinal": "8.2.1", "level": 1}
      }
    ],
    "blocks_modified": [],
    "blocks_deleted": [],
    "sections_affected": ["section-uuid-456"]
  },
  "checksums": {
    "before": {
      "raw.docx": "sha256:abc123...",
      "blocks.jsonl": "sha256:def456..."
    },
    "after": {
      "raw.docx": "sha256:xyz789...",
      "blocks.jsonl": "sha256:uvw012..."
    }
  },
  "checkpoint": "checkpoints/v1_2025-11-29_15-45.docx"  // Optional
}
```

### Rollback Strategies

**Option 1: Replay from checkpoint** (recommended for frequent edits)
- Keep full snapshots every N edits (e.g., every 10)
- Store diffs between snapshots
- Rollback: Load nearest checkpoint + replay/reverse diffs

**Option 2: Full snapshots** (simpler, more storage)
- Store complete .docx + artifacts after each edit
- Rollback: Just load the target version
- Trade-off: ~100KB per version vs. complex diff logic

**Option 3: Hybrid** (recommended)
- Store full .docx checkpoint every 5-10 edits
- Store artifact diffs for every edit
- Rollback: Load checkpoint + regenerate artifacts

### Implementation Pattern

```python
class EditHistory:
    def __init__(self, project_dir):
        self.project_dir = Path(project_dir)
        self.log_file = self.project_dir / 'history' / 'edit_log.jsonl'
        self.checkpoint_dir = self.project_dir / 'history' / 'checkpoints'
    
    def record_edit(self, mcp_request, description, llm_reasoning=None):
        """Record edit before and after MCP tool execution"""
        # 1. Capture before state
        before_checksums = self._compute_checksums()
        
        # 2. Execute MCP tool (caller's responsibility)
        # ... MCP tool runs ...
        
        # 3. Re-analyze to get new artifacts
        self._run_analysis()
        
        # 4. Compute diff
        after_checksums = self._compute_checksums()
        artifact_diff = self._compute_artifact_diff()
        
        # 5. Create checkpoint if threshold reached
        checkpoint_path = None
        if self._should_checkpoint():
            checkpoint_path = self._create_checkpoint()
        
        # 6. Append to log
        event = {
            'version': self._next_version(),
            'timestamp': datetime.utcnow().isoformat(),
            'action': {
                'type': mcp_request['tool'],
                'description': description,
                'llm_reasoning': llm_reasoning
            },
            'mcp_request': mcp_request,
            'changes': artifact_diff,
            'checksums': {
                'before': before_checksums,
                'after': after_checksums
            },
            'checkpoint': str(checkpoint_path) if checkpoint_path else None
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
        
        return event['version']
    
    def rollback(self, target_version):
        """Rollback to specific version"""
        # Find nearest checkpoint <= target_version
        checkpoint = self._find_checkpoint(target_version)
        
        # Restore checkpoint
        shutil.copy(checkpoint, self.project_dir / 'contract.docx')
        
        # Re-analyze to regenerate artifacts
        self._run_analysis()
        
        # Optional: Replay diffs if target is between checkpoints
        if checkpoint.version < target_version:
            self._replay_diffs(checkpoint.version, target_version)
    
    def get_history(self, limit=50):
        """Get recent edit history for UI display"""
        events = []
        with open(self.log_file) as f:
            for line in f:
                events.append(json.loads(line))
        return events[-limit:]
```

### Artifact Diff Format

**Efficient storage** - only record changes:

```json
{
  "blocks": {
    "added": [
      {"id": "uuid-1", "type": "list_item", "text": "...", "list": {...}}
    ],
    "modified": [
      {
        "id": "uuid-2",
        "before": {"text": "old text", "list": {"ordinal": "3.1"}},
        "after": {"text": "new text", "list": {"ordinal": "3.1"}}
      }
    ],
    "deleted": [
      {"id": "uuid-3", "type": "paragraph", "text": "removed text"}
    ]
  },
  "sections": {
    "modified": [
      {
        "id": "section-uuid",
        "before": {"block_ids": ["a", "b"]},
        "after": {"block_ids": ["a", "b", "c"]}
      }
    ]
  },
  "relationships": {
    "modified": [
      {
        "block_id": "uuid-4",
        "before": {"child_block_ids": ["x"]},
        "after": {"child_block_ids": ["x", "y"]}
      }
    ]
  }
}
```

### UI Integration

**History panel in webview:**
```
┌─ Edit History ─────────────────┐
│ ✓ v5  15:45  Added clause 8.2.1│ ← Current
│   v4  15:30  Modified clause 3  │
│   v3  14:20  Deleted clause 5   │
│ ⚡ v2  14:00  [checkpoint]       │
│   v1  13:45  Initial analysis   │
└────────────────────────────────┘
   [Rollback to v3] [View diff]
```

**Features:**
- Click version → preview changes
- Rollback button → restore that version
- Diff view → show before/after blocks
- LLM explanation visible in tooltip

### Performance Considerations

**Checkpoint frequency:**
- Too frequent: Wasted storage (~100KB per .docx)
- Too sparse: Slow rollback (many diffs to replay)
- **Recommended**: Every 5-10 edits or every 30 minutes

**Log file size:**
- ~1-5KB per edit event (depends on diff size)
- 1000 edits = ~1-5MB log file
- Compact log periodically (keep recent + checkpoints)

**Diff computation:**
- Compare block IDs: O(n) where n = block count
- Use sets for fast added/deleted detection
- Deep compare modified blocks (text, list, etc.)

## Webview Architecture

### Recommended Structure

```
VSCode Extension
  ├─ Webview (React/Vue/Svelte)
  │   ├─ Document viewer (sections + blocks)
  │   ├─ Search interface
  │   ├─ Edit controls
  │   ├─ History panel (versions, rollback)
  │   └─ LLM agent chat UI
  │
  ├─ Extension Host
  │   ├─ Load artifacts
  │   ├─ Index for fast queries
  │   ├─ MCP client
  │   ├─ Edit history manager
  │   └─ LLM agent orchestration
  │
  └─ Message passing (extension ↔ webview)
```

### State Management

**Extension maintains:**
- Loaded artifacts (blocks, sections, relationships, manifest)
- Block/section lookup indexes
- Current document checksum
- MCP server connection

**Webview displays:**
- Section tree (collapsible)
- Block content (with formatting)
- Active selection/cursor
- LLM agent responses

**Update flow:**
1. User action in webview → message to extension
2. Extension executes MCP tool → modifies Word doc
3. Extension re-analyzes → new artifacts
4. Extension sends update message → webview
5. Webview refreshes display

## Performance Considerations

**Loading:**
- blocks.jsonl can be large (660+ blocks) - load once, keep in memory
## Next Steps

1. **Create artifact loader module** - Load and index artifacts efficiently
2. **Implement EditHistory class** - Version tracking and rollback
3. **Build webview prototype** - Display sections + blocks + history panel
4. **Integrate MCP client** - Connect to MCP server
5. **Implement edit workflow** - Test full cycle (edit → version → re-analyze → refresh)
6. **Add LLM agent layer** - Chat interface that calls MCP tools with versioning

**Updates:**
- Only re-analyze after MCP edits (not on every read)
- Delta updates: compare checksums to detect changes
- Incremental refresh: only reload affected sections if possible

## Next Steps

1. **Create artifact loader module** - Load and index artifacts efficiently
2. **Build webview prototype** - Display sections + blocks
3. **Integrate MCP client** - Connect to MCP server
4. **Implement edit workflow** - Test full cycle (edit → re-analyze → refresh)
5. **Add LLM agent layer** - Chat interface that calls MCP tools

## Reference

- **Analysis CLI**: `python -m effilocal.cli analyze <file.docx> --doc-id <uuid> --out <dir>`
- **MCP Server**: `effilocal-document-server` (configured in mcp-config.json)
- **Schemas**: `schemas/` directory contains JSON schemas for validation
- **Tests**: `tests/` directory shows artifact usage patterns
