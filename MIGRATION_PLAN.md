# Migration Plan: Move Customizations to effilocal

## Overview
**Strategy: Pristine Upstream + Complete Override**

Keep `word_document_server` 100% identical to upstream (https://github.com/GongRzhe/Office-Word-MCP-Server), and move ALL custom changes to `effilocal`. effilocal overrides and extends word_document_server functionality.

**Key Principle:** word_document_server folder must remain perfectly in sync with upstream. Zero modifications.

---

## Phase 1: Create effilocal MCP Module Structure

### 1.1 Create effilocal MCP server structure
```
effilocal/
├── mcp_server/
│   ├── __init__.py
│   ├── main.py                    # New: effilocal MCP server (registers ALL tools)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── attachment_tools.py    # MOVED from word_document_server (NEW functionality)
│   │   ├── numbering_tools.py     # MOVED from word_document_server (NEW functionality)
│   │   ├── content_tools.py       # OVERRIDES + EXTENDS word_document_server
│   │   ├── comment_tools.py       # OVERRIDES + EXTENDS word_document_server
│   │   ├── document_tools.py      # OVERRIDES + EXTENDS word_document_server
│   │   └── format_tools.py        # OVERRIDES + EXTENDS word_document_server
│   ├── core/
│   │   └── comments.py            # OVERRIDES word_document_server
│   └── utils/
│       └── document_utils.py      # OVERRIDES word_document_server
```

### 1.2 Dependencies
- `word_document_server` = clean external dependency from GitHub upstream
- effilocal imports word_document_server and selectively overrides functions
- All custom code lives in effilocal only

---

## Phase 2: File-by-File Migration

### Strategy: Override Pattern
For modified files, create effilocal versions that:
1. Import upstream functions from word_document_server
2. Override only what's needed
3. Add new functionality
4. Re-export everything for seamless replacement

Example:
```python
# effilocal/mcp_server/tools/content_tools.py
from word_document_server.tools import content_tools as upstream

# Re-export unchanged functions
add_paragraph = upstream.add_paragraph
add_table = upstream.add_table

# Override with extended functionality
async def add_heading(filename, text, level=1, color=None, **kwargs):
    """Extended version with color parameter"""
    if color:
        # Your custom implementation
        pass
    else:
        return upstream.add_heading(filename, text, level, **kwargs)

# Add new functions
async def add_paragraph_after_clause(filename, clause_number, text):
    """NEW: Custom clause insertion"""
    pass
```

---

### 📦 NEW FILES (Move entirely to effilocal)

#### 1. `word_document_server/tools/attachment_tools.py` → `effilocal/mcp_server/tools/attachment_tools.py`
**Type:** NEW functionality (doesn't exist in upstream)
**Dependencies:** effilocal's `direct_docx.iter_blocks()`
**Action:** Move entire file, update imports

#### 2. `word_document_server/tools/numbering_tools.py` → `effilocal/mcp_server/tools/numbering_tools.py`
**Type:** NEW functionality (doesn't exist in upstream)
**Dependencies:** effilocal's `NumberingInspector`
**Action:** Move entire file as-is

#### 3. `word_document_server/tools/review_tools.py` → Check if exists
**Action:** Move if it exists

---

### 🔄 MODIFIED FILES (Create override versions in effilocal)

#### 4. `word_document_server/tools/content_tools.py` → `effilocal/mcp_server/tools/content_tools.py`
**Changes:** 736 additions, 124 deletions
**Strategy:** 
```python
# Import all upstream functions
from word_document_server.tools.content_tools import *
from word_document_server.tools import content_tools as upstream

# Override extended functions
async def add_heading(filename, text, level=1, color=None, **kwargs):
    # Extended with color support
    pass

# Add new functions  
async def add_paragraph_after_clause(filename, clause_number, text):
    # NEW
    pass

async def edit_run_text_tool(filename, paragraph_index, run_index, new_text, ...):
    # NEW
    pass
```

#### 5. `word_document_server/core/comments.py` → `effilocal/mcp_server/core/comments.py`
**Action:** Create override version with your changes

#### 6. `word_document_server/tools/comment_tools.py` → `effilocal/mcp_server/tools/comment_tools.py`
**Action:** Create override version

#### 7. `word_document_server/tools/document_tools.py` → `effilocal/mcp_server/tools/document_tools.py`
**Action:** Override with `save_document_as_markdown()` addition

#### 8. `word_document_server/tools/format_tools.py` → `effilocal/mcp_server/tools/format_tools.py`
**Action:** Create override version

#### 9. `word_document_server/utils/document_utils.py` → `effilocal/mcp_server/utils/document_utils.py`
**Action:** Create override version

---

## Phase 3: Create effilocal MCP Server

### 3.1 Create `effilocal/mcp_server/main.py`
**Purpose:** Single MCP server that registers ALL tools (upstream + custom)

```python
"""
effilocal MCP Server - Contract review and Word document tools.
Combines upstream word_document_server with effilocal extensions.
"""
import os
import sys
import logging
from dotenv import load_dotenv

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
os.environ.setdefault('FASTMCP_LOG_LEVEL', 'INFO')

from fastmcp import FastMCP

# Import effilocal tools (these override/extend upstream)
from effilocal.mcp_server.tools import (
    content_tools,      # Overrides word_document_server
    document_tools,     # Overrides word_document_server
    format_tools,       # Overrides word_document_server
    attachment_tools,   # NEW: Schedule/Annex tools
    numbering_tools,    # NEW: Numbering analysis
    comment_tools,      # Overrides word_document_server
)

# Import remaining upstream tools directly
from word_document_server.tools import (
    protection_tools,
    footnote_tools,
    extended_document_tools,
)

mcp = FastMCP("effilocal Contract Review Server")

def register_tools():
    """Register all tools - custom and upstream."""
    
    # Document tools
    @mcp.tool()
    async def create_document(filename: str):
        return await document_tools.create_document(filename)
    
    # Content tools (extended versions)
    @mcp.tool()
    async def add_heading(filename, text, level=1, color=None, **kwargs):
        return await content_tools.add_heading(filename, text, level, color=color, **kwargs)
    
    @mcp.tool()
    async def add_paragraph_after_clause(filename, clause_number, text):
        return await content_tools.add_paragraph_after_clause(filename, clause_number, text)
    
    # Attachment tools (NEW)
    @mcp.tool()
    async def add_paragraph_after_attachment(filename, attachment_identifier, text, **kwargs):
        return await attachment_tools.add_paragraph_after_attachment(
            filename, attachment_identifier, text, **kwargs
        )
    
    # Numbering tools (NEW)
    @mcp.tool()
    async def analyze_document_numbering(filename, debug=False, include_non_numbered=False):
        return await numbering_tools.analyze_document_numbering(
            filename, debug, include_non_numbered
        )
    
    # Protection tools (upstream - unchanged)
    @mcp.tool()
    def protect_document(filename: str, password: str):
        return protection_tools.protect_document(filename, password)
    
    # ... register all other tools

if __name__ == "__main__":
    register_tools()
    mcp.run()
```

### 3.2 Import structure
effilocal tools automatically use overrides:
```python
# When you import from effilocal, you get the extended versions
from effilocal.mcp_server.tools import content_tools

# This calls your extended version with color support
content_tools.add_heading(filename, "Title", color="#FF0000")
```

---

## Phase 4: Update Dependencies

### 4.1 pyproject.toml changes
```toml
[project]
dependencies = [
    "python-docx>=1.1.0",
    "fastmcp>=2.8.1",
    # Add word_document_server as dependency
    "word-document-server @ git+https://github.com/GongRzhe/Office-Word-MCP-Server.git",
    # OR after you fork:
    # "word-document-server @ git+https://github.com/effidave/Office-Word-MCP-Server.git@your-branch",
]
```

### 4.2 Create requirements for word_document_server fork
If you want to maintain improvements to word_document_server, fork it first:
1. Fork https://github.com/GongRzhe/Office-Word-MCP-Server to your account
2. Push general improvements to your fork
3. Reference your fork in dependencies

---

## Phase 5: Testing Strategy

### 5.1 Test files to update
```
tests/
├── test_attachment_insertion.py        # Update imports to effilocal
├── test_comprehensive_custom_ids.py    # Update imports to effilocal
├── test_custom_para_ids.py            # Update imports to effilocal
├── test_new_attachment_creation.py    # Update imports to effilocal
├── test_para_id_insertion.py          # Update imports to effilocal
```

### 5.2 Import changes
Before:
```python
from word_document_server.tools.attachment_tools import add_paragraph_after_attachment
```

After:
```python
from effilocal.mcp_server.tools.attachment_tools import add_paragraph_after_attachment
```

---

## Phase 6: Cleanup

### 6.1 Remove from word_document_server
- Delete `word_document_server/tools/attachment_tools.py`
- Delete `word_document_server/tools/numbering_tools.py`
- Delete `word_document_server/tools/review_tools.py` (if exists)
- Delete `word_document_server/utils/hash.py`
- Revert modified files to upstream versions (or keep general improvements in fork)

### 6.2 Verify upstream parity
```bash
# Clone fresh upstream
git clone https://github.com/GongRzhe/Office-Word-MCP-Server.git temp_check
# Compare
diff -r temp_check/word_document_server word_document_server
# Should show only general improvements you want to keep
```

---

## Decision: Clean Dependency (No Fork)

**Selected Strategy:** Use upstream word_document_server as-is, no modifications.

**Why:**
- ✅ Zero maintenance burden
- ✅ Easy to update (just pip upgrade)
- ✅ Perfect separation: upstream = general, effilocal = custom
- ✅ All customizations are overrides in effilocal
- ✅ No fork to manage
- ✅ Can still contribute improvements back to upstream

**How it works:**
- word_document_server = pristine copy from GitHub
- effilocal overrides what it needs via Python imports
- Your MCP server (effilocal) imports both and presents unified interface

---

## Execution Order

### Step 1: Backup
```bash
git checkout -b backup-before-migration
git commit -am "Backup before migration"
git push origin backup-before-migration
```

### Step 2: Create effilocal structure
```bash
mkdir -p effilocal/mcp_server/tools
mkdir -p effilocal/mcp_server/core
mkdir -p effilocal/mcp_server/utils
touch effilocal/mcp_server/__init__.py
touch effilocal/mcp_server/tools/__init__.py
```

### Step 3: Move NEW files to effilocal
- Copy `word_document_server/tools/attachment_tools.py` → `effilocal/mcp_server/tools/`
- Copy `word_document_server/tools/numbering_tools.py` → `effilocal/mcp_server/tools/`
- Update imports to use `word_document_server` as external dependency

### Step 4: Create override files
For each modified file, create effilocal version:
- `effilocal/mcp_server/tools/content_tools.py` - import upstream, add overrides
- `effilocal/mcp_server/tools/comment_tools.py` - import upstream, add overrides
- `effilocal/mcp_server/tools/document_tools.py` - import upstream, add overrides
- `effilocal/mcp_server/tools/format_tools.py` - import upstream, add overrides
- `effilocal/mcp_server/core/comments.py` - import upstream, add overrides
- `effilocal/mcp_server/utils/document_utils.py` - import upstream, add overrides

### Step 5: Create effilocal MCP server
- Create `effilocal/mcp_server/main.py`
- Register all tools (custom + upstream)
- Configure transport and logging

### Step 6: Replace word_document_server with upstream
```bash
# Backup your current version
mv word_document_server word_document_server_backup

# Get fresh upstream
git clone https://github.com/GongRzhe/Office-Word-MCP-Server.git temp_upstream
mv temp_upstream/word_document_server word_document_server
rm -rf temp_upstream

# Or use as dependency (better):
# Remove word_document_server folder entirely
# Install via pip from GitHub in pyproject.toml
```

### Step 7: Update dependencies
Edit `pyproject.toml`:
```toml
dependencies = [
    "word-document-server @ git+https://github.com/GongRzhe/Office-Word-MCP-Server.git",
    # ... other deps
]
```

### Step 8: Update all imports in tests
```bash
# Find all test files importing from word_document_server
grep -r "from word_document_server.tools.attachment_tools" tests/
grep -r "from word_document_server.tools.numbering_tools" tests/

# Change to:
# from effilocal.mcp_server.tools.attachment_tools import ...
```

### Step 9: Update MCP config
Edit `mcp-config.json` to point to `effilocal.mcp_server.main`

### Step 10: Test
```bash
# Run test suite
cd tests
pytest -v

# Test MCP server
python -m effilocal.mcp_server.main
```

### Step 11: Cleanup
```bash
# Remove backup after verification
rm -rf word_document_server_backup
rm -rf temp_upstream_comparison
```

---

## Summary

**Goal:** Keep word_document_server pristine, move all customizations to effilocal

**Architecture:**
```
word_document_server/          # Pristine upstream (GitHub dependency)
├── tools/*.py                 # Unmodified
├── core/*.py                  # Unmodified
└── main.py                    # Unmodified

effilocal/
└── mcp_server/                # Your MCP server
    ├── main.py                # Registers all tools
    ├── tools/
    │   ├── attachment_tools.py    # NEW (moved from word_document_server)
    │   ├── numbering_tools.py     # NEW (moved from word_document_server)
    │   ├── content_tools.py       # Imports upstream + adds overrides
    │   ├── comment_tools.py       # Imports upstream + adds overrides
    │   └── ...                    # Other overrides as needed
    └── core/
        └── comments.py            # Imports upstream + adds overrides
```

**Benefits:**
- ✅ word_document_server stays in perfect sync with upstream
- ✅ Easy to update: just `pip install --upgrade word-document-server`
- ✅ All your customizations in one place (effilocal)
- ✅ Clear ownership and maintainability
- ✅ Can contribute improvements back to upstream easily

**Next Action:** Ready to execute when you are. Start with Step 1 (backup).
