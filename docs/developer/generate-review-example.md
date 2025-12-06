# Legal Review Example Generator

## Overview

The `generate_review_example.py` script extracts structured training examples from legal review workflows. It takes an email chain (incoming instructions + outgoing advice) with attached Word documents, and produces markdown files that can be used as LLM context for similar review tasks.

## Quick Start

```bash
# From project root, with venv activated
python scripts/generate_review_example.py \
    --incoming email_instructions.msg \
    --outgoing email_advice.msg \
    --client "Didimo" \
    --counterparty "NBC" \
    --output ./output_dir/
```

## What It Does

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT                                   │
├─────────────────────────────────────────────────────────────────┤
│  email_instructions.msg                                         │
│  └── Original Agreement.docx (attached)                         │
│                                                                 │
│  email_advice.msg                                               │
│  └── Edited Agreement.docx (attached, with comments + changes)  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        OUTPUT                                   │
├─────────────────────────────────────────────────────────────────┤
│  01_instructions.md      - Client email with context            │
│  02_original_agreement.md - Full text of original document      │
│  03_review_comments.md   - Comments grouped by recipient        │
│  04_tracked_changes.md   - Insertions and deletions             │
│  05_advice_note.md       - Outgoing advice email                │
└─────────────────────────────────────────────────────────────────┘
```

## CLI Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--incoming` | Yes | Path to incoming .msg file (client instructions + original agreement) |
| `--outgoing` | Yes | Path to outgoing .msg file (advice + edited agreement) |
| `--client` | Yes | Client short name (e.g., "Didimo") - used for comment grouping |
| `--counterparty` | Yes | Counterparty short name (e.g., "NBC") - used for comment grouping |
| `--output`, `-o` | No | Output directory (default: same as incoming .msg) |
| `--original-index` | No | 1-based index of original .docx attachment (skip interactive prompt) |
| `--edited-index` | No | 1-based index of edited .docx attachment (skip interactive prompt) |
| `--single-file` | No | Combine all outputs into one markdown file |

## How Comment Grouping Works

Comments in the edited document are categorized by their text prefix:

- `"For Didimo: ..."` → grouped under **Client** section
- `"For NBC: ..."` → grouped under **Counterparty** section
- Other comments → grouped under **Other** section

Each comment includes:
- **Comment text** - The full comment
- **Referenced text** - The specific text the comment is anchored to
- **Full paragraph** - Complete paragraph for context

## Architecture

### Dependencies

```
extract-msg>=0.55.0  # For parsing Outlook .msg files
olefile              # Direct OLE file access (transitive, more reliable for attachments)
python-docx          # Word document manipulation
```

### Key Components

```
scripts/
├── __init__.py
├── generate_review_example.py    # Main script (~550 lines)
└── test_msg_extraction.py        # Standalone test for MSG parsing

tests/
└── test_generate_review_example.py  # 26 comprehensive tests
```

### Data Classes

```python
@dataclass
class Attachment:
    filename: str
    data: bytes
    
    @property
    def is_docx(self) -> bool: ...

@dataclass  
class EmailData:
    subject: str
    sender: str
    recipients: str
    date: str
    body: str
    attachments: list[Attachment]
```

### Core Functions

| Function | Purpose |
|----------|---------|
| `parse_msg_file(path)` | Parse .msg, extract metadata + attachments |
| `select_docx_attachment(attachments, prompt, index)` | Auto-select or prompt for .docx |
| `process_comments(doc, client, counterparty)` | Extract and categorize comments |
| `process_track_changes(doc)` | Extract insertions and deletions |
| `generate_*_md()` | Five functions for markdown generation |

### MSG Parsing Strategy

The script uses a hybrid approach for parsing Outlook .msg files:

1. **Metadata via `extract_msg`** - Subject, sender, recipients, date, body
2. **Attachments via `olefile`** - Direct OLE stream access (more reliable)

This bypasses `extract_msg`'s attachment parsing which fails on some non-standard MSG formats with missing `AttachMethod` properties.

```python
# OLE property IDs for attachments
3707001F  # Long filename (UTF-16LE)
3704001F  # Short filename (UTF-16LE)  
37010102  # Binary data
```

### Reused Utilities

The script leverages existing effilocal utilities:

```python
from effilocal.mcp_server.core.comments import extract_all_comments
from effilocal.mcp_server.utils.document_utils import iter_document_paragraphs
from effilocal.doc.amended_paragraph import iter_amended_paragraphs
```

## Output Format Examples

### 03_review_comments.md

```markdown
# Review Comments

## For Didimo (Client)

### Comment 1
**Author:** David Sant | **Date:** 2025-12-05T10:20:00+00:00

> For Didimo: Trial also extends to all group companies - is that ok?

**Referenced text:** "and its Affiliates"

**Full paragraph:**
> License Grant. Vendor hereby grants to Company and its Affiliates 
> a non-exclusive, worldwide, non-transferable right...

---
```

### 04_tracked_changes.md

```markdown
# Tracked Changes

## Insertions

### Insertion 1
**Author:** David Sant | **Date:** 2025-12-05T10:38:00Z

**Added text:** "forty"

**Context paragraph:**
> Fees & Payment. In consideration for Vendor's performance...
> within forty-five (45) days of Company's receipt...

---

## Deletions

### Deletion 1
**Author:** David Sant | **Date:** 2025-12-05T10:40:00Z

**Removed text:** "seventy-five"

**Context paragraph:**
> ...within forty-five (45) days...
```

## Testing

```bash
# Run all tests
pytest tests/test_generate_review_example.py -v

# Run specific test class
pytest tests/test_generate_review_example.py::TestProcessComments -v
```

### Test Coverage

- **Data classes** - Field validation, `is_docx` property
- **Email parsing** - Metadata extraction, attachment handling, error cases
- **Attachment selection** - Auto-select, index selection, validation
- **Comment processing** - Grouping by prefix, paragraph text lookup
- **Track changes** - Insertion/deletion detection, metadata extraction
- **Markdown generation** - Content formatting, section structure
- **CLI** - Required/optional arguments, flags

## Example Workflow

```bash
# 1. Place MSG files in a directory
cp incoming_email.msg outgoing_email.msg ./review_example/

# 2. Run the generator
python scripts/generate_review_example.py \
    --incoming ./review_example/incoming_email.msg \
    --outgoing ./review_example/outgoing_email.msg \
    --client "Acme Corp" \
    --counterparty "BigCo Inc" \
    --output ./review_example/output/

# 3. Check generated files
ls ./review_example/output/
# 01_instructions.md
# 02_original_agreement.md
# 03_review_comments.md
# 04_tracked_changes.md
# 05_advice_note.md

# 4. Use as LLM context
cat ./review_example/output/*.md > combined_example.md
```

## Scripted Usage (No Prompts)

For automation, use index flags to skip interactive prompts:

```bash
python scripts/generate_review_example.py \
    --incoming email_in.msg \
    --outgoing email_out.msg \
    --client "Client" \
    --counterparty "Counter" \
    --original-index 1 \
    --edited-index 1 \
    --output ./output/
```

## Troubleshooting

### "No .docx attachments found"

The MSG file doesn't contain any Word documents. Check attachments manually:

```python
from scripts.generate_review_example import parse_msg_file
from pathlib import Path

email = parse_msg_file(Path("email.msg"))
for att in email.attachments:
    print(f"{att.filename} - {len(att.data)} bytes")
```

### Attachment extraction fails silently

Some MSG files have non-standard attachment formats. The script uses `olefile` directly to handle this, but very corrupted files may still fail. Try opening the MSG in Outlook and re-saving it.

### Comments not grouped correctly

Ensure comments start with the exact prefix `"For {client_name}"` or `"For {counterparty_name}"`. The matching is case-sensitive and prefix-based.

### Missing paragraph text for comments

Comments in tables or headers may show `"(N/A - comment in table/header)"` for paragraph text. This is expected behavior - the `paragraph_index` mapping only covers main body paragraphs.

## Related Documentation

- [Comment Extraction](./sprint-3-comments-implementation.md) - How comments are extracted with status
- [Track Changes](../doc_analysis/track-changes.md) - How insertions/deletions are detected
- [Artifact Guide](../ARTIFACT_GUIDE.md) - Document analysis artifact format
