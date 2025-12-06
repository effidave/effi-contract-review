#!/usr/bin/env python3
"""
Generate legal review examples from email + document pairs.

This script extracts structured markdown examples from:
- Incoming email with client instructions + original agreement
- Outgoing email with advice + edited agreement (with comments and track changes)

The script automatically:
1. Detects party names from the contract (looking for words before shall/will/may)
2. Extracts company names from the preamble (Ltd, Inc, LLC, etc.)
3. Identifies "For X:" prefixes in comments
4. Asks user to confirm which party is the client
5. Asks who provided the original agreement
6. Anonymizes all output with [CLIENT] and [COUNTERPARTY] labels

Usage:
    python scripts/generate_review_example.py \\
        --incoming instructions.msg \\
        --outgoing advice.msg \\
        --output ./output_dir/

Examples:
    # Basic usage (interactive prompts for party selection)
    python scripts/generate_review_example.py \\
        --incoming email_instructions.msg \\
        --outgoing email_advice.msg
    
    # With preselected attachment indices (for scripted use)
    python scripts/generate_review_example.py \\
        --incoming email_instructions.msg \\
        --outgoing email_advice.msg \\
        --original-index 1 \\
        --edited-index 1
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any

import extract_msg
import olefile
from docx import Document

# Add project root to path for effilocal imports
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from effilocal.doc.amended_paragraph import iter_amended_paragraphs
from effilocal.doc.uuid_embedding import get_paragraph_para_id
from effilocal.mcp_server.core.comments import extract_all_comments
from effilocal.mcp_server.utils.document_utils import iter_document_paragraphs

# Import docx_to_llm_markdown module functions
from scripts.docx_to_llm_markdown import (
    run_analyze_doc,
    convert_to_markdown,
)


def extract_clause_numbers_from_doc(docx_bytes: bytes) -> tuple[dict[str, str], dict[str, str]]:
    """
    Analyze a document and extract clause numbers (ordinals) and text for each paragraph.
    
    Args:
        docx_bytes: Raw bytes of the .docx document
        
    Returns:
        Tuple of:
        - Dictionary mapping para_id to clause ordinal (e.g., {"3DD8236A": "11.2"})
        - Dictionary mapping para_id to paragraph text (e.g., {"3DD8236A": "Full clause text..."})
    """
    import tempfile
    import json
    
    # Write bytes to temp file for analyze_doc
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp.write(docx_bytes)
        tmp_path = Path(tmp.name)
    
    ordinal_map: dict[str, str] = {}
    text_map: dict[str, str] = {}
    
    # Create temp directory for analysis artifacts
    with tempfile.TemporaryDirectory() as tmp_dir:
        analysis_dir = Path(tmp_dir) / "analysis"
        
        try:
            # Run analyze_doc to extract blocks with numbering
            run_analyze_doc(tmp_path, analysis_dir)
            
            # Load blocks and extract ordinals keyed by para_id
            blocks_file = analysis_dir / "blocks.jsonl"
            if blocks_file.exists():
                with open(blocks_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            block = json.loads(line)
                            para_id = block.get("para_id")
                            text = block.get("text", "")
                            list_info = block.get("list") or {}
                            ordinal = list_info.get("ordinal", "")
                            
                            if para_id:
                                # Store paragraph text
                                if text:
                                    text_map[para_id] = text
                                
                                # Store ordinal if present
                                if ordinal:
                                    # Clean ordinal (remove trailing spaces/periods for cleaner display)
                                    clean_ordinal = ordinal.strip().rstrip('.')
                                    ordinal_map[para_id] = clean_ordinal
        finally:
            # Clean up temp docx file
            tmp_path.unlink(missing_ok=True)
    
    return ordinal_map, text_map


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Attachment:
    """Represents an email attachment with filename and binary data."""
    
    filename: str
    data: bytes
    
    @property
    def is_docx(self) -> bool:
        """Return True if this attachment is a .docx file."""
        return self.filename.lower().endswith(".docx")


@dataclass
class EmailData:
    """Represents parsed email data with metadata and attachments."""
    
    subject: str
    sender: str
    recipients: str
    date: str
    body: str
    attachments: list[Attachment]


# =============================================================================
# Email Parsing
# =============================================================================

def parse_msg_file(msg_path: Path) -> EmailData:
    """
    Parse an Outlook MSG file and extract metadata + attachments.
    
    Uses extract_msg for metadata and olefile for attachment data,
    since extract_msg fails on some non-standard MSG formats.
    
    Args:
        msg_path: Path to the .msg file
        
    Returns:
        EmailData with subject, sender, recipients, date, body, attachments
        
    Raises:
        FileNotFoundError: If the MSG file doesn't exist
    """
    if not msg_path.exists():
        raise FileNotFoundError(f"MSG file not found: {msg_path}")
    
    # Extract metadata using extract_msg (with delayed attachments to avoid errors)
    msg = extract_msg.openMsg(str(msg_path), delayAttachments=True)
    
    subject = msg.subject or ""
    sender = msg.sender or ""
    recipients = msg.to or ""
    date = str(msg.date) if msg.date else ""
    body = msg.body or ""
    
    # Extract attachments using olefile directly (more reliable)
    attachments = _extract_attachments_olefile(msg_path)
    
    return EmailData(
        subject=subject,
        sender=sender,
        recipients=recipients,
        date=date,
        body=body,
        attachments=attachments
    )


def _extract_attachments_olefile(msg_path: Path) -> list[Attachment]:
    """
    Extract attachments from MSG file using olefile directly.
    
    This bypasses extract_msg's attachment parsing which fails on some MSG files
    with non-standard attachment properties.
    
    Property IDs:
        - 3707001F: Long filename (UTF-16LE)
        - 3704001F: Short filename (UTF-16LE)
        - 37010102: Binary data
    """
    ole = olefile.OleFileIO(str(msg_path))
    attachments = []
    
    # Find all attachment directories
    attach_dirs = set()
    for stream in ole.listdir():
        stream_path = "/".join(stream)
        if stream_path.startswith("__attach_version1.0_"):
            attach_dirs.add(stream[0])
    
    for attach_dir in sorted(attach_dirs):
        filename = _get_attachment_filename(ole, attach_dir)
        data = _get_attachment_data(ole, attach_dir)
        
        if filename and data:
            attachments.append(Attachment(filename=filename, data=data))
    
    ole.close()
    return attachments


def _get_attachment_filename(ole: olefile.OleFileIO, attach_dir: str) -> str | None:
    """Get attachment filename from MSG OLE stream."""
    # Try long filename first (3707), then short filename (3704)
    # Property type suffix: 001F = UTF-16, 001E = ANSI
    for prop_base in ("3707", "3704"):
        for prop_suffix in ("001F", "001E"):
            try:
                stream_path = f"{attach_dir}/__substg1.0_{prop_base}{prop_suffix}"
                data = ole.openstream(stream_path).read()
                if prop_suffix == "001F":
                    return data.decode("utf-16-le").rstrip("\x00")
                else:
                    return data.decode("latin-1").rstrip("\x00")
            except Exception:
                continue
    return None


def _get_attachment_data(ole: olefile.OleFileIO, attach_dir: str) -> bytes | None:
    """Get attachment binary data from MSG OLE stream."""
    try:
        stream_path = f"{attach_dir}/__substg1.0_37010102"
        return ole.openstream(stream_path).read()
    except Exception:
        return None


# =============================================================================
# Attachment Selection
# =============================================================================

def select_docx_attachment(
    attachments: list[Attachment],
    prompt_text: str,
    preselected_index: int | None = None
) -> Attachment:
    """
    Select a .docx attachment from the list.
    
    - If single .docx: auto-select
    - If preselected_index provided: use that (1-based)
    - Otherwise: prompt user with numbered list
    
    Args:
        attachments: List of attachments to choose from
        prompt_text: Text to display when prompting user
        preselected_index: Optional 1-based index to skip prompt
        
    Returns:
        Selected Attachment
        
    Raises:
        ValueError: If no .docx attachments found or invalid index
    """
    docx_attachments = [a for a in attachments if a.is_docx]
    
    if not docx_attachments:
        raise ValueError("No .docx attachments found")
    
    if len(docx_attachments) == 1:
        return docx_attachments[0]
    
    if preselected_index is not None:
        if 1 <= preselected_index <= len(docx_attachments):
            return docx_attachments[preselected_index - 1]
        raise ValueError(
            f"Invalid index {preselected_index}. "
            f"Must be 1-{len(docx_attachments)}"
        )
    
    # Interactive selection
    print(f"\n{prompt_text}")
    for i, att in enumerate(docx_attachments, 1):
        print(f"  [{i}] {att.filename}")
    
    while True:
        try:
            choice = int(input("Enter number: "))
            if 1 <= choice <= len(docx_attachments):
                return docx_attachments[choice - 1]
            print(f"Please enter a number between 1 and {len(docx_attachments)}")
        except ValueError:
            print("Please enter a valid number")


# =============================================================================
# Comment Processing
# =============================================================================

def categorize_comments_by_prefix(
    comments: list[dict[str, Any]],
    client_prefix: str,
    counterparty_prefix: str
) -> dict[str, list[dict[str, Any]]]:
    """
    Categorize comments by their "For X:" prefix.
    
    Args:
        comments: List of comment dictionaries
        client_prefix: Client identifier (e.g., "Didimo")
        counterparty_prefix: Counterparty identifier (e.g., "NBC")
        
    Returns:
        Dict with keys: 'client', 'counterparty', 'other'
    """
    import re
    
    categorized: dict[str, list[dict[str, Any]]] = {
        "client": [],
        "counterparty": [],
        "other": []
    }
    
    # Build case-insensitive patterns
    client_pattern = re.compile(rf'^For\s+{re.escape(client_prefix)}\s*:', re.IGNORECASE)
    counterparty_pattern = re.compile(rf'^For\s+{re.escape(counterparty_prefix)}\s*:', re.IGNORECASE)
    
    for comment in comments:
        text = comment.get("text", "").strip()
        
        if client_pattern.match(text):
            categorized["client"].append(comment)
        elif counterparty_pattern.match(text):
            categorized["counterparty"].append(comment)
        else:
            categorized["other"].append(comment)
    
    return categorized


# =============================================================================
# Track Changes Processing
# =============================================================================

@dataclass
class ParagraphDiff:
    """Represents before/after state of a paragraph with track changes."""
    
    before_text: str  # Text with deletions, without insertions
    after_text: str   # Text with insertions, without deletions (= amended_text)
    authors: set[str]
    dates: set[str]
    insertions: list[str]
    deletions: list[str]
    rationale: list[str] = None  # Comments explaining the changes
    parent_title: str = None  # Title of parent clause (e.g., "LIMITATION OF LIABILITY")
    clause_number: str = None  # Rendered clause number (e.g., "11.1", "11.2")
    para_id: str = None  # Word's native paragraph ID (w14:paraId)
    
    def __post_init__(self):
        if self.rationale is None:
            self.rationale = []
        if self.parent_title is None:
            self.parent_title = ""
        if self.clause_number is None:
            self.clause_number = ""
    
    @property
    def has_changes(self) -> bool:
        """Return True if this paragraph has any tracked changes."""
        return bool(self.insertions or self.deletions)
    
    @property
    def primary_author(self) -> str:
        """Return the first author or 'Unknown'."""
        return next(iter(self.authors), "Unknown") if self.authors else "Unknown"
    
    @property
    def primary_date(self) -> str:
        """Return the first date or empty string."""
        return next(iter(self.dates), "") if self.dates else ""
    
    @property
    def has_own_title(self) -> bool:
        """Check if this paragraph has its own clause title (e.g., 'TITLE.' or 'Fees & Payment.')."""
        import re
        text = self.after_text.strip() or self.before_text.strip()
        if not text:
            return False
        
        # A title should be:
        # 1. Short (max ~50 chars before the period)
        # 2. Either ALL CAPS, or Title Case words only (not a sentence)
        # 3. Followed by period then space (or end of text if just the title)
        
        # Pattern for ALL CAPS title: "LIMITATION OF LIABILITY."
        all_caps_match = re.match(r'^([A-Z][A-Z\s&,\-]+?)\.(?:\s|$)', text)
        if all_caps_match:
            title = all_caps_match.group(1).strip()
            if len(title) <= 50:
                return True
        
        # Pattern for Title Case: "Fees & Payment." - each word capitalized, no lowercase-starting words
        # Must be short and look like a heading, not a sentence
        title_case_match = re.match(r'^([A-Z][a-z]*(?:\s+(?:[A-Z][a-z]*|&|of|and|the|in|to|for))*?)\.(?:\s|$)', text)
        if title_case_match:
            title = title_case_match.group(1).strip()
            # Must be short to be a title
            if len(title) <= 50:
                return True
        
        return False
    
    @property
    def own_title(self) -> str:
        """Extract this paragraph's own title if it has one, otherwise empty string."""
        import re
        text = self.after_text.strip() or self.before_text.strip()
        if not text:
            return ""
        
        # ALL CAPS title
        all_caps_match = re.match(r'^([A-Z][A-Z\s&,\-]+?)\.(?:\s|$)', text)
        if all_caps_match:
            title = all_caps_match.group(1).strip()
            if len(title) <= 50:
                return title
        
        # Title Case
        title_case_match = re.match(r'^([A-Z][a-z]*(?:\s+(?:[A-Z][a-z]*|&|of|and|the|in|to|for))*?)\.(?:\s|$)', text)
        if title_case_match:
            title = title_case_match.group(1).strip()
            if len(title) <= 50:
                return title
        
        return ""
    
    @property
    def clause_title(self) -> str:
        """
        Extract clause title from the paragraph text.
        
        Looks for patterns like "TITLE." or "Title Case." at the start of the paragraph.
        If not found but a parent_title is set, uses that instead.
        Returns the title without the period, or a short preview if not found.
        """
        # First check if we have our own title
        if self.has_own_title:
            return self.own_title
        
        # If we have a parent title from a previous clause, use it
        if self.parent_title:
            return self.parent_title
        
        # Fallback: first few words, capped at ~40 chars
        text = self.after_text.strip() or self.before_text.strip()
        if not text:
            return "New Paragraph"
            
        words = text.split()
        preview = ""
        for word in words:
            if len(preview) + len(word) + 1 > 40:
                break
            preview = (preview + " " + word).strip()
        
        if preview and len(preview) < len(text):
            return preview + "..."
        return preview or text[:40] + "..."


def match_comments_to_diffs(
    diffs: list[ParagraphDiff], 
    comments: list[dict[str, Any]]
) -> None:
    """
    Match comments to paragraph diffs based on text overlap.
    
    A comment is matched to a diff if:
    - The comment's reference_text appears in any of the diff's insertions, OR
    - The comment's reference_text overlaps with the diff's after_text
    
    Modifies diffs in place, adding matched comment text to rationale field.
    """
    for diff in diffs:
        matched_rationales = []
        
        for comment in comments:
            comment_text = comment.get("text", "")
            ref_text = comment.get("reference_text", "")
            
            # Skip empty comments
            if not comment_text:
                continue
            
            matched = False
            
            # Check if reference_text matches any insertion
            if ref_text:
                for insertion in diff.insertions:
                    if ref_text in insertion or insertion in ref_text:
                        matched = True
                        break
            
            # Check if reference_text overlaps with the paragraph's after_text
            if not matched and ref_text and diff.after_text:
                # Normalize for comparison
                ref_norm = ref_text.strip().lower()
                after_norm = diff.after_text.strip().lower()
                
                # Match if one contains the other (comment is on text within this paragraph)
                if (ref_norm and after_norm and 
                    (ref_norm in after_norm or after_norm in ref_norm)):
                    matched = True
            
            if matched:
                matched_rationales.append(comment_text)
        
        diff.rationale = matched_rationales


def process_track_changes(doc: Document) -> list[ParagraphDiff]:
    """
    Extract tracked changes as paragraph-level before/after diffs.
    
    For each paragraph with changes, reconstructs:
    - before_text: What the paragraph looked like before edits
    - after_text: What it looks like after edits (visible text)
    - Summary of insertions and deletions
    
    Args:
        doc: python-docx Document object
        
    Returns:
        List of ParagraphDiff objects (only paragraphs with changes)
    """
    diffs: list[ParagraphDiff] = []
    
    for para_idx, amended_para in enumerate(iter_amended_paragraphs(doc)):
        # Build before and after text from runs
        before_parts: list[str] = []
        after_parts: list[str] = []
        authors: set[str] = set()
        dates: set[str] = set()
        
        # Track consecutive insertions/deletions for consolidation
        current_insertions: list[str] = []
        current_deletions: list[str] = []
        all_insertions: list[str] = []
        all_deletions: list[str] = []
        
        def flush_changes():
            """Consolidate and flush accumulated changes."""
            nonlocal current_insertions, current_deletions
            if current_insertions:
                consolidated = "".join(current_insertions).strip()
                if consolidated:
                    all_insertions.append(consolidated)
                current_insertions = []
            if current_deletions:
                consolidated = "".join(current_deletions).strip()
                if consolidated:
                    all_deletions.append(consolidated)
                current_deletions = []
        
        for run in amended_para.amended_runs:
            formats = run.get("formats", [])
            
            if "delete" in formats:
                # Deleted text: in before, not in after
                deleted_text = run.get("deleted_text", "")
                if deleted_text:
                    before_parts.append(deleted_text)
                    current_deletions.append(deleted_text)
                    if run.get("author"):
                        authors.add(run["author"])
                    if run.get("date"):
                        dates.add(run["date"])
                # Flush insertions if we switched to deletions
                if current_insertions:
                    consolidated = "".join(current_insertions).strip()
                    if consolidated:
                        all_insertions.append(consolidated)
                    current_insertions = []
            
            elif "insert" in formats:
                # Inserted text: in after, not in before
                inserted_text = run.get("text", "")
                if inserted_text:
                    after_parts.append(inserted_text)
                    current_insertions.append(inserted_text)
                    if run.get("author"):
                        authors.add(run["author"])
                    if run.get("date"):
                        dates.add(run["date"])
                # Flush deletions if we switched to insertions
                if current_deletions:
                    consolidated = "".join(current_deletions).strip()
                    if consolidated:
                        all_deletions.append(consolidated)
                    current_deletions = []
            
            else:
                # Normal text: in both before and after - flush accumulated changes
                flush_changes()
                normal_text = run.get("text", "")
                if normal_text:
                    before_parts.append(normal_text)
                    after_parts.append(normal_text)
        
        # Flush any remaining changes at end of paragraph
        flush_changes()
        
        # Only include paragraphs with actual changes
        if all_insertions or all_deletions:
            # Get the native para_id from the paragraph element
            para_id = get_paragraph_para_id(amended_para._paragraph._element)
            diffs.append(ParagraphDiff(
                before_text="".join(before_parts),
                after_text="".join(after_parts),
                authors=authors,
                dates=dates,
                insertions=all_insertions,
                deletions=all_deletions,
                para_id=para_id
            ))
    
    # Post-process: assign parent titles to sub-clauses
    # When a paragraph has a title (e.g., "LIMITATION OF LIABILITY."),
    # subsequent paragraphs without titles inherit that as parent_title
    current_parent_title = ""
    for diff in diffs:
        if diff.has_own_title:
            # This paragraph has its own title - update the current parent
            current_parent_title = diff.own_title
        else:
            # This paragraph doesn't have a title - inherit parent
            diff.parent_title = current_parent_title
    
    return diffs


# =============================================================================
# Party Detection and Matching
# =============================================================================

def extract_defined_party_terms(doc: Document) -> list[str]:
    """
    Extract likely defined terms for parties from contract text.
    
    Looks for capitalized words that commonly precede shall/will/may,
    which typically indicate party definitions (e.g., "Vendor", "Company", "Licensor").
    
    Args:
        doc: The Word document to analyze
        
    Returns:
        List of likely party defined terms, sorted by frequency
    """
    import re
    from collections import Counter
    
    party_candidates: Counter[str] = Counter()
    
    # Pattern: Capitalized word followed by shall/will/may
    # e.g., "Vendor shall", "Company will", "Licensor may"
    pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:shall|will|may)\b')
    
    for para in doc.paragraphs:
        text = para.text
        matches = pattern.findall(text)
        for match in matches:
            # Filter out common false positives
            if match.lower() not in {'the', 'each', 'either', 'neither', 'any', 'no', 'such', 'this', 'that'}:
                party_candidates[match] += 1
    
    # Also check tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                matches = pattern.findall(cell.text)
                for match in matches:
                    if match.lower() not in {'the', 'each', 'either', 'neither', 'any', 'no', 'such', 'this', 'that'}:
                        party_candidates[match] += 1
    
    # Return terms sorted by frequency (most common first)
    return [term for term, _ in party_candidates.most_common()]


def extract_company_to_defined_term_mapping(doc: Document, max_paragraphs: int = 20) -> dict[str, str]:
    """
    Extract mapping of company names to their defined terms from the preamble.
    
    Looks for patterns like:
    - 'NBCUniversal Media, LLC ... ("Company" or "NBCUniversal")'
    - 'Didimo, Inc. ... ("Vendor")'
    
    Args:
        doc: The Word document to analyze
        max_paragraphs: How many paragraphs to scan (default: 20, covers preamble)
        
    Returns:
        Dictionary mapping company names to their defined terms
        e.g., {"NBCUniversal": "Company", "Didimo": "Vendor"}
    """
    import re
    
    mapping: dict[str, str] = {}
    
    # Legal entity suffixes
    suffixes = r'(?:[Ll]td\.?|[Ll]imited|LLP|[Ii]nc\.?|LLC|CIC|[Cc]orp\.?|[Cc]orporation|PLC|plc|S\.?A\.?|GmbH|B\.?V\.?|N\.?V\.?)'
    
    # Quote characters: straight quotes and curly quotes (Unicode U+201C/U+201D)
    quotes = r'["\'\u201C\u201D]'
    
    # Pattern to match: "Company Name, LLC ... ("DefinedTerm")" or "Company Name, LLC ... ("DefinedTerm" or "Alias")"
    # The defined term is typically in quotes/parentheses after the company description
    pattern = re.compile(
        rf'([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*)*)\s*,?\s*{suffixes}'  # Company name with suffix
        rf'[^()]*'  # Skip jurisdiction/description
        rf'\(\s*{quotes}([A-Z][A-Za-z]+){quotes}'  # First quoted defined term in parentheses
        rf'(?:\s+or\s+{quotes}[A-Za-z]+{quotes})?'  # Optional "or Alias"
        rf'\s*\)'  # Close paren
    )
    
    paragraphs_scanned = 0
    for para in doc.paragraphs:
        if paragraphs_scanned >= max_paragraphs:
            break
        
        text = para.text
        if not text.strip():
            continue
            
        paragraphs_scanned += 1
        
        matches = pattern.findall(text)
        for company_name, defined_term in matches:
            # Clean up company name
            company_name = company_name.strip()
            for prefix in ("Between", "between", "And", "and"):
                if company_name.startswith(prefix + " "):
                    company_name = company_name[len(prefix) + 1:]
            
            if company_name and defined_term:
                mapping[company_name] = defined_term
    
    return mapping


def extract_party_alternate_names(doc: Document, max_paragraphs: int = 20) -> dict[str, list[str]]:
    """
    Extract all alternate names for each party from the preamble.
    
    Looks for patterns like:
    - '("Company" or "NBCUniversal")' → {"Company": ["Company", "NBCUniversal"]}
    - '("Vendor")' → {"Vendor": ["Vendor"]}
    
    Args:
        doc: The Word document to analyze
        max_paragraphs: How many paragraphs to scan
        
    Returns:
        Dictionary mapping primary defined term to list of all names for that party
    """
    import re
    
    alternates: dict[str, list[str]] = {}
    
    # Quote characters: straight quotes and curly quotes
    quotes = r'["\'\u201C\u201D]'
    
    # Pattern to match: ("DefinedTerm") or ("DefinedTerm" or "Alternate")
    pattern = re.compile(
        rf'\(\s*{quotes}([A-Z][A-Za-z]+){quotes}'  # First quoted term
        rf'(?:\s+or\s+{quotes}([A-Za-z]+){quotes})?'  # Optional "or Alternate"
        rf'\s*\)'  # Close paren
    )
    
    paragraphs_scanned = 0
    for para in doc.paragraphs:
        if paragraphs_scanned >= max_paragraphs:
            break
        
        text = para.text
        if not text.strip():
            continue
            
        paragraphs_scanned += 1
        
        for match in pattern.finditer(text):
            primary = match.group(1)
            alternate = match.group(2)
            
            if primary not in alternates:
                alternates[primary] = [primary]
            
            if alternate and alternate not in alternates[primary]:
                alternates[primary].append(alternate)
    
    return alternates


def extract_full_company_names(doc: Document, max_paragraphs: int = 20) -> list[str]:
    """
    Extract full company names including legal suffix from the preamble.
    
    Looks for patterns like "NBCUniversal Media, LLC" or "Didimo, Inc."
    Returns the complete legal name for replacement purposes.
    
    Args:
        doc: The Word document to analyze
        max_paragraphs: How many paragraphs to scan
        
    Returns:
        List of full company names with their legal suffixes
    """
    import re
    
    full_names: list[str] = []
    
    # Legal entity suffixes - base forms (without trailing period handling)
    # We'll handle trailing periods explicitly
    suffix_bases = [
        'Ltd', 'Limited', 'LLP', 'Inc', 'LLC', 'CIC', 'Corp', 'Corporation',
        'PLC', 'plc', 'SA', 'S.A.', 'GmbH', 'BV', 'B.V.', 'NV', 'N.V.'
    ]
    # Build pattern that captures suffix with optional trailing period
    suffixes = '(' + '|'.join(re.escape(s) for s in suffix_bases) + r')\.?'
    
    # Pattern: Company name followed by optional comma and legal suffix
    # e.g., "NBCUniversal Media, LLC" or "Didimo, Inc."
    # Capture: (company name)(comma/space)(suffix with optional period)
    # Lookahead matches: space, comma, quote, paren, or end of string
    pattern = re.compile(
        rf'([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*)*)(\s*,\s*|\s+){suffixes}(?=\s|[,"\'\(\)]|$)'
    )
    
    paragraphs_scanned = 0
    for para in doc.paragraphs:
        if paragraphs_scanned >= max_paragraphs:
            break
        
        text = para.text
        if not text.strip():
            continue
            
        paragraphs_scanned += 1
        
        for match in pattern.finditer(text):
            name_part = match.group(1).strip()
            separator = match.group(2)
            suffix_part = match.group(3)
            
            # Check if there's a period after the suffix in the full match
            full_match = match.group(0)
            has_trailing_period = full_match.rstrip().endswith('.')
            
            # Remove common leading words
            for prefix in ("Between", "between", "And", "and"):
                if name_part.startswith(prefix + " "):
                    name_part = name_part[len(prefix) + 1:]
            
            if name_part and len(name_part) > 2:
                # Build full name preserving original format
                if ',' in separator:
                    full_name = f"{name_part}, {suffix_part}"
                else:
                    full_name = f"{name_part} {suffix_part}"
                
                # Add trailing period if original had it
                if has_trailing_period and not full_name.endswith('.'):
                    full_name += '.'
                    
                full_names.append(full_name)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_names = []
    for name in full_names:
        if name.lower() not in seen:
            seen.add(name.lower())
            unique_names.append(name)
    
    return unique_names


def extract_company_names(doc: Document, max_paragraphs: int = 20) -> list[str]:
    """
    Extract company names from the early paragraphs of a contract.
    
    Looks for patterns with common company suffixes like Ltd, Limited, LLP, Inc, LLC, CIC.
    
    Args:
        doc: The Word document to analyze
        max_paragraphs: How many paragraphs to scan (default: 20, covers preamble)
        
    Returns:
        List of detected company names
    """
    import re
    
    company_names: list[str] = []
    
    # Pattern for company names with legal suffixes
    # Matches: "Company Name Ltd", "Company Name Limited", "Company Name, Inc.", etc.
    # Company names typically start with capital letters
    # Suffixes can be any case (Ltd, LTD, ltd)
    suffixes = r'(?:[Ll]td\.?|[Ll]imited|LLP|[Ii]nc\.?|LLC|CIC|[Cc]orp\.?|[Cc]orporation|PLC|plc|S\.?A\.?|GmbH|B\.?V\.?|N\.?V\.?)'
    
    # Pattern: One or more capitalized words followed by a legal suffix
    # Only matches words starting with uppercase (company names are proper nouns)
    pattern = re.compile(
        rf'([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*)*)\s*,?\s*{suffixes}\b'
    )
    
    paragraphs_scanned = 0
    for para in doc.paragraphs:
        if paragraphs_scanned >= max_paragraphs:
            break
        
        text = para.text
        if not text.strip():
            continue
            
        paragraphs_scanned += 1
        
        matches = pattern.findall(text)
        for match in matches:
            # Clean up the match
            name = match.strip().rstrip(',')
            # Remove common leading words that aren't part of company names
            for prefix in ("Between", "between", "And", "and"):
                if name.startswith(prefix + " "):
                    name = name[len(prefix) + 1:]
            if name and len(name) > 2:  # Filter out very short matches
                company_names.append(name)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_names = []
    for name in company_names:
        if name.lower() not in seen:
            seen.add(name.lower())
            unique_names.append(name)
    
    return unique_names


def extract_comment_prefixes(comments: list[dict[str, Any]]) -> list[str]:
    """
    Extract unique "For X:" prefixes from comments.
    
    Looks for patterns like "For Didimo:", "For NBC:", etc.
    
    Args:
        comments: List of comment dictionaries with 'text' field
        
    Returns:
        List of unique party identifiers found in comment prefixes
    """
    import re
    
    prefixes: set[str] = set()
    
    # Pattern: "For X:" at the start of a comment
    pattern = re.compile(r'^For\s+([^:]+):', re.IGNORECASE)
    
    for comment in comments:
        text = comment.get("text", "")
        match = pattern.match(text.strip())
        if match:
            prefixes.add(match.group(1).strip())
    
    return list(prefixes)


def compute_similarity(s1: str, s2: str) -> float:
    """
    Compute similarity between two strings using token overlap and substring matching.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Similarity score between 0 and 1
    """
    s1_lower = s1.lower()
    s2_lower = s2.lower()
    
    # Exact match
    if s1_lower == s2_lower:
        return 1.0
    
    # One contains the other
    if s1_lower in s2_lower or s2_lower in s1_lower:
        return 0.9
    
    # Token overlap (Jaccard similarity)
    tokens1 = set(s1_lower.split())
    tokens2 = set(s2_lower.split())
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    jaccard = len(intersection) / len(union) if union else 0
    
    # First word match bonus (common for company names)
    first_word_match = 0.3 if s1_lower.split()[0] == s2_lower.split()[0] else 0
    
    return min(jaccard + first_word_match, 1.0)


def match_prefixes_to_parties(
    prefixes: list[str],
    defined_terms: list[str],
    company_names: list[str]
) -> dict[str, str]:
    """
    Match comment prefixes to detected party names/terms.
    
    Args:
        prefixes: Comment prefixes (e.g., ["Didimo", "NBC"])
        defined_terms: Defined terms from contract (e.g., ["Vendor", "Company"])
        company_names: Company names from preamble (e.g., ["Didimo, Inc", "NBC Universal"])
        
    Returns:
        Mapping of prefix -> best matching party identifier
    """
    all_candidates = defined_terms + company_names
    
    matches: dict[str, str] = {}
    
    for prefix in prefixes:
        best_match = prefix  # Default to the prefix itself
        best_score = 0.0
        
        for candidate in all_candidates:
            score = compute_similarity(prefix, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate
        
        # Only use the match if score is reasonable
        if best_score >= 0.3:
            matches[prefix] = best_match
        else:
            matches[prefix] = prefix  # Keep original if no good match
    
    return matches


@dataclass
class PartyInfo:
    """Information about the parties in a contract."""
    client_prefix: str  # The prefix used in comments for client (e.g., "Didimo")
    counterparty_prefix: str  # The prefix used in comments for counterparty (e.g., "NBC")
    client_defined_term: str  # The primary defined term in contract (e.g., "Vendor")
    counterparty_defined_term: str  # The primary defined term (e.g., "Company")
    original_provided_by: str  # "client" or "counterparty"
    client_role: str = "party"  # Semantic role (e.g., "supplier", "licensor")
    counterparty_role: str = "party"  # Semantic role (e.g., "customer", "licensee")
    # Alternate names for each party (e.g., ["Company", "NBCUniversal"])
    client_alternate_names: list[str] = field(default_factory=list)
    counterparty_alternate_names: list[str] = field(default_factory=list)
    
    @property
    def client_placeholder(self) -> str:
        """Get the placeholder string for the client based on their role."""
        return get_role_placeholder(self.client_role)
    
    @property
    def counterparty_placeholder(self) -> str:
        """Get the placeholder string for the counterparty based on their role."""
        return get_role_placeholder(self.counterparty_role)
    
    @property
    def all_client_names(self) -> list[str]:
        """Get all names that should be replaced for the client."""
        names = [self.client_prefix, self.client_defined_term]
        names.extend(self.client_alternate_names)
        # Deduplicate while preserving order
        seen = set()
        result = []
        for name in names:
            if name and name not in seen:
                seen.add(name)
                result.append(name)
        return result
    
    @property
    def all_counterparty_names(self) -> list[str]:
        """Get all names that should be replaced for the counterparty."""
        names = [self.counterparty_prefix, self.counterparty_defined_term]
        names.extend(self.counterparty_alternate_names)
        # Deduplicate while preserving order
        seen = set()
        result = []
        for name in names:
            if name and name not in seen:
                seen.add(name)
                result.append(name)
        return result


# Mapping of common defined terms to semantic roles
DEFINED_TERM_TO_ROLE: dict[str, str] = {
    # Service/supply relationships
    "vendor": "supplier",
    "supplier": "supplier",
    "provider": "supplier",
    "contractor": "supplier",
    "consultant": "supplier",
    "company": "customer",  # Often the customer in service agreements
    "customer": "customer",
    "client": "customer",
    "buyer": "customer",
    "purchaser": "customer",
    # Licensing relationships
    "licensor": "licensor",
    "licensee": "licensee",
    # Property relationships
    "landlord": "landlord",
    "lessor": "landlord",
    "tenant": "tenant",
    "lessee": "tenant",
    # Employment/agency
    "employer": "employer",
    "employee": "employee",
    "principal": "principal",
    "agent": "agent",
    # Financial
    "lender": "lender",
    "borrower": "borrower",
    "creditor": "creditor",
    "debtor": "debtor",
    # Sale
    "seller": "seller",
}


def infer_party_role(defined_term: str) -> str:
    """
    Infer the semantic role of a party from its defined term.
    
    This helps the LLM understand the contractual relationship.
    
    Args:
        defined_term: The defined term in the contract (e.g., "Vendor", "Company")
        
    Returns:
        Semantic role (e.g., "supplier", "customer") or "party" if unknown
    """
    term_lower = defined_term.lower().strip()
    return DEFINED_TERM_TO_ROLE.get(term_lower, "party")


def get_role_placeholder(role: str) -> str:
    """
    Convert a semantic role to its placeholder format.
    
    This is used for anonymization - replacing company names with semantic
    role placeholders that preserve meaning for LLM training.
    
    Args:
        role: The semantic role (e.g., "supplier", "customer", "party")
        
    Returns:
        Placeholder string (e.g., "[SUPPLIER]", "[CUSTOMER]", "[PARTY]")
    """
    return f"[{role.upper()}]"


def detect_and_confirm_parties(
    original_doc: Document,
    comments: list[dict[str, Any]]
) -> PartyInfo:
    """
    Detect parties from the contract and comments, then ask user to confirm.
    
    Args:
        original_doc: The original agreement document
        comments: All comments from the edited document
        
    Returns:
        PartyInfo with confirmed party information
    """
    print("\n" + "=" * 60)
    print("PARTY DETECTION")
    print("=" * 60)
    
    # Extract information
    defined_terms = extract_defined_party_terms(original_doc)
    company_names = extract_company_names(original_doc)
    comment_prefixes = extract_comment_prefixes(comments)
    
    # Extract company name to defined term mapping from preamble
    # e.g., {"NBCUniversal": "Company", "Didimo": "Vendor"}
    company_to_term = extract_company_to_defined_term_mapping(original_doc)
    
    print(f"\nDetected defined terms (from 'X shall/will/may'): {defined_terms[:5]}")
    print(f"Detected company names (from preamble): {company_names[:5]}")
    print(f"Company -> defined term mapping: {company_to_term}")
    print(f"Comment prefixes (from 'For X:'): {comment_prefixes}")
    
    # Match prefixes to parties
    prefix_matches = match_prefixes_to_parties(comment_prefixes, defined_terms, company_names)
    print(f"\nPrefix matches: {prefix_matches}")
    
    # If we have exactly 2 prefixes, ask user to identify client
    if len(comment_prefixes) >= 2:
        print("\n" + "-" * 40)
        print("Please identify the parties:")
        print("-" * 40)
        
        for i, prefix in enumerate(comment_prefixes[:2], 1):
            matched_term = prefix_matches.get(prefix, prefix)
            # Check if we can find the defined term via company mapping
            defined_term = company_to_term.get(prefix) or company_to_term.get(matched_term)
            if defined_term:
                print(f"  {i}. {prefix} (defined as '{defined_term}' in contract)")
            elif matched_term != prefix:
                print(f"  {i}. {prefix} (matched to '{matched_term}' in contract)")
            else:
                print(f"  {i}. {prefix}")
        
        # Ask which is client
        while True:
            choice = input(f"\nWhich party is YOUR CLIENT? Enter 1 or 2: ").strip()
            if choice in ("1", "2"):
                client_idx = int(choice) - 1
                counterparty_idx = 1 - client_idx
                break
            print("Please enter 1 or 2.")
        
        client_prefix = comment_prefixes[client_idx]
        counterparty_prefix = comment_prefixes[counterparty_idx]
        
    elif len(comment_prefixes) == 1:
        # Only one prefix found - ask for the other
        client_prefix = comment_prefixes[0]
        counterparty_prefix = input(f"\nOnly found '{client_prefix}' in comments. Enter counterparty name: ").strip()
        
    else:
        # No prefixes found - ask for both
        print("\nNo 'For X:' prefixes found in comments.")
        client_prefix = input("Enter your client's name: ").strip()
        counterparty_prefix = input("Enter the counterparty's name: ").strip()
    
    # Match to defined terms - prioritize the company→term mapping
    client_defined = company_to_term.get(client_prefix, "")
    counterparty_defined = company_to_term.get(counterparty_prefix, "")
    
    # If no direct mapping, try matching via prefix_matches
    if not client_defined:
        matched = prefix_matches.get(client_prefix, "")
        client_defined = company_to_term.get(matched, matched)
    if not counterparty_defined:
        matched = prefix_matches.get(counterparty_prefix, "")
        counterparty_defined = company_to_term.get(matched, matched)
    
    # If still no good match, use similarity matching to defined terms
    if not client_defined or client_defined == client_prefix:
        for term in defined_terms:
            if compute_similarity(client_prefix, term) > 0.3:
                client_defined = term
                break
        if not client_defined:
            client_defined = defined_terms[0] if defined_terms else "Vendor"
    
    if not counterparty_defined or counterparty_defined == counterparty_prefix:
        for term in defined_terms:
            if term != client_defined and compute_similarity(counterparty_prefix, term) > 0.3:
                counterparty_defined = term
                break
        if not counterparty_defined:
            counterparty_defined = defined_terms[1] if len(defined_terms) > 1 else "Company"
    
    # Ask who provided the original
    print("\n" + "-" * 40)
    print("Who provided the original agreement?")
    print("-" * 40)
    print(f"  1. {client_prefix} (your client)")
    print(f"  2. {counterparty_prefix} (counterparty)")
    
    while True:
        choice = input("\nEnter 1 or 2: ").strip()
        if choice == "1":
            original_provided_by = "client"
            break
        elif choice == "2":
            original_provided_by = "counterparty"
            break
        print("Please enter 1 or 2.")
    
    # Infer semantic roles from defined terms
    client_role = infer_party_role(client_defined)
    counterparty_role = infer_party_role(counterparty_defined)
    
    # Extract alternate names for each party (e.g., "Company" and "NBCUniversal")
    party_alternates = extract_party_alternate_names(original_doc)
    client_alternates = party_alternates.get(client_defined, [])
    counterparty_alternates = party_alternates.get(counterparty_defined, [])
    
    # Extract full company names (e.g., "NBCUniversal Media, LLC") and associate with parties
    full_names = extract_full_company_names(original_doc)
    for full_name in full_names:
        # Check if this full name belongs to client or counterparty by matching against prefix
        # The prefix might be a short form like "NBC" for "NBCUniversal Media, LLC"
        # So check: is prefix contained in full_name, OR is any part of full_name contained in prefix?
        full_name_lower = full_name.lower()
        full_name_parts = [full_name.split(',')[0].lower(), full_name.split()[0].lower()]
        
        # Check client match: prefix in full_name OR full_name part in prefix
        client_match = (
            client_prefix.lower() in full_name_lower or 
            any(part in client_prefix.lower() for part in full_name_parts if len(part) > 3)
        )
        # Check counterparty match: prefix in full_name OR full_name part in prefix  
        counterparty_match = (
            counterparty_prefix.lower() in full_name_lower or
            any(part in counterparty_prefix.lower() for part in full_name_parts if len(part) > 3)
        )
        
        if client_match and not counterparty_match:
            if full_name not in client_alternates:
                client_alternates.append(full_name)
            # Also add ALL-CAPS version for signature blocks
            upper_name = full_name.upper()
            if upper_name not in client_alternates:
                client_alternates.append(upper_name)
        elif counterparty_match and not client_match:
            if full_name not in counterparty_alternates:
                counterparty_alternates.append(full_name)
            # Also add ALL-CAPS version for signature blocks
            upper_name = full_name.upper()
            if upper_name not in counterparty_alternates:
                counterparty_alternates.append(upper_name)
    
    # Summary
    print("\n" + "-" * 40)
    print("CONFIRMED PARTIES:")
    print("-" * 40)
    client_names_str = f"'{client_defined}'"
    if client_alternates and len(client_alternates) > 1:
        client_names_str = f"'{client_defined}' (also: {', '.join(n for n in client_alternates if n != client_defined)})"
    counterparty_names_str = f"'{counterparty_defined}'"
    if counterparty_alternates and len(counterparty_alternates) > 1:
        counterparty_names_str = f"'{counterparty_defined}' (also: {', '.join(n for n in counterparty_alternates if n != counterparty_defined)})"
    print(f"  Client: {client_prefix} -> defined as {client_names_str} (role: {client_role}) -> [CLIENT]")
    print(f"  Counterparty: {counterparty_prefix} -> defined as {counterparty_names_str} (role: {counterparty_role}) -> [COUNTERPARTY]")
    print(f"  Original provided by: {original_provided_by}")
    print("-" * 40)
    
    return PartyInfo(
        client_prefix=client_prefix,
        counterparty_prefix=counterparty_prefix,
        client_defined_term=client_defined,
        counterparty_defined_term=counterparty_defined,
        original_provided_by=original_provided_by,
        client_role=client_role,
        counterparty_role=counterparty_role,
        client_alternate_names=client_alternates,
        counterparty_alternate_names=counterparty_alternates
    )


# =============================================================================
# Anonymization
# =============================================================================

def anonymize_text(
    text: str,
    client_names: str | list[str],
    counterparty_names: str | list[str],
    client_role: str = "CLIENT",
    counterparty_role: str = "COUNTERPARTY"
) -> str:
    """
    Replace party names with generic role placeholders.
    
    This helps the LLM generalize patterns without memorizing specific names.
    Handles special patterns like ("Company" or "NBCUniversal") → ("[CUSTOMER]")
    
    Note: Replacements are CASE-SENSITIVE. "Company" (defined term) is replaced,
    but "company" (generic word) is not. This prevents replacing "a Delaware 
    limited liability company" incorrectly.
    
    Args:
        text: Text to anonymize
        client_names: Client name(s) to replace (single string or list of variations)
        counterparty_names: Counterparty name(s) to replace
        client_role: Role label for client (default: "CLIENT")
        counterparty_role: Role label for counterparty (default: "COUNTERPARTY")
        
    Returns:
        Text with party names replaced by role placeholders
    """
    import re
    
    # Normalize to lists
    if isinstance(client_names, str):
        client_names = [client_names] if client_names else []
    if isinstance(counterparty_names, str):
        counterparty_names = [counterparty_names] if counterparty_names else []
    
    # Quote characters: straight quotes and curly quotes
    quotes = r'["\'\u201C\u201D]'
    
    # First, handle ("X" or "Y") patterns where both names belong to the same party
    # This prevents them from becoming ("[PLACEHOLDER]" or "[PLACEHOLDER]")
    def collapse_or_pattern(names: list[str], placeholder: str) -> None:
        nonlocal text
        # Generate all pairs of names from the list
        for i, name1 in enumerate(names):
            for name2 in names[i+1:]:
                if name1 and name2:
                    # Match ("Name1" or "Name2") or ("Name2" or "Name1") - case sensitive
                    for n1, n2 in [(name1, name2), (name2, name1)]:
                        pattern = rf'\(\s*{quotes}{re.escape(n1)}{quotes}\s+or\s+{quotes}{re.escape(n2)}{quotes}\s*\)'
                        text = re.sub(pattern, f'("{placeholder}")', text)
    
    collapse_or_pattern(client_names, f'[{client_role}]')
    collapse_or_pattern(counterparty_names, f'[{counterparty_role}]')
    
    def make_replacement_pattern(name: str) -> str:
        """Create regex pattern for name replacement.
        
        Uses word boundaries for names ending in word characters,
        but uses lookahead for names ending in punctuation (like 'Inc.')
        """
        escaped = re.escape(name)
        # Names ending in word characters use normal word boundary
        if re.match(r'\w', name[-1]) if name else False:
            return rf'\b{escaped}\b'
        else:
            # Names ending in non-word chars (like period) - use lookahead
            # Match start word boundary but end with lookahead for space/punctuation/end
            return rf'\b{escaped}(?=\s|["\'\(\)]|$)'
    
    # Replace client names (CASE-SENSITIVE)
    # Process longer names first to avoid partial replacements
    # Case-sensitive ensures "Company" is replaced but "company" is not
    for name in sorted(client_names, key=len, reverse=True):
        if name:
            pattern = make_replacement_pattern(name)
            text = re.sub(pattern, f'[{client_role}]', text)
    
    # Replace counterparty names (CASE-SENSITIVE)
    for name in sorted(counterparty_names, key=len, reverse=True):
        if name:
            pattern = make_replacement_pattern(name)
            text = re.sub(pattern, f'[{counterparty_role}]', text)
    
    return text


def generate_yaml_header(
    document_type: str,
    acting_for: str = "client",
    original_provided_by: str = "counterparty",
    extra_fields: dict[str, str] | None = None,
    party_info: PartyInfo | None = None
) -> str:
    """
    Generate YAML front matter header for markdown files.
    
    Args:
        document_type: Type of document (e.g., "instructions", "agreement")
        acting_for: Which party we represent ("client")
        original_provided_by: Who provided the original agreement ("client" or "counterparty")
        extra_fields: Additional YAML fields to include
        party_info: Optional PartyInfo for enhanced parties mapping
        
    Returns:
        YAML front matter string with --- delimiters
    """
    # Use party_info.original_provided_by if available
    if party_info:
        original_provided_by = party_info.original_provided_by
    
    lines = [
        "---",
        f"document_type: {document_type}",
        f"acting_for: {acting_for}",
        f"original_provided_by: {original_provided_by}",
    ]
    
    # Add enhanced parties mapping if party_info is provided
    if party_info:
        # Use semantic role placeholders (e.g., [SUPPLIER], [CUSTOMER])
        # instead of generic [CLIENT]/[COUNTERPARTY]
        lines.extend([
            "parties:",
            "  client:",
            f'    identifier: "{party_info.client_placeholder}"',
            f'    role: "{party_info.client_role}"',
            "  counterparty:",
            f'    identifier: "{party_info.counterparty_placeholder}"',
            f'    role: "{party_info.counterparty_role}"',
        ])
    else:
        # Fallback to simple format for backwards compatibility
        lines.extend([
            'our_client: "[CLIENT]"',
            'counterparty: "[COUNTERPARTY]"',
        ])
    
    if extra_fields:
        for key, value in extra_fields.items():
            lines.append(f"{key}: {value}")
    
    lines.append("---")
    lines.append("")
    
    return "\n".join(lines)


# =============================================================================
# Markdown Generation
# =============================================================================

def generate_instructions_md(
    email_data: EmailData,
    client_names: list[str] | str = "",
    counterparty_names: list[str] | str = "",
    original_provided_by: str = "counterparty",
    party_info: PartyInfo | None = None
) -> str:
    """Generate markdown for client instructions email."""
    # Get role placeholders for anonymization
    client_role = party_info.client_placeholder.strip("[]") if party_info else "CLIENT"
    counterparty_role = party_info.counterparty_placeholder.strip("[]") if party_info else "COUNTERPARTY"
    
    # YAML header
    yaml_header = generate_yaml_header(
        document_type="client_instructions",
        acting_for="client",
        original_provided_by=original_provided_by,
        extra_fields={"description": "\"Email from client with review instructions\""},
        party_info=party_info
    )
    
    # Anonymize email content
    body = email_data.body or "(No body text)"
    if client_names or counterparty_names:
        body = anonymize_text(body, client_names, counterparty_names, client_role, counterparty_role)
    
    lines = [
        yaml_header,
        "# Client Instructions",
        "",
        f"**From:** [REDACTED]",
        f"**To:** [REDACTED]",
        f"**Date:** {email_data.date}",
        f"**Subject:** {anonymize_text(email_data.subject, client_names, counterparty_names, client_role, counterparty_role) if client_names or counterparty_names else email_data.subject}",
        "",
        "---",
        "",
        "## Email Body",
        "",
        body,
        "",
        "---",
        "",
        "## Attachments",
        ""
    ]
    
    for i, att in enumerate(email_data.attachments, 1):
        docx_marker = " *(original agreement)*" if att.is_docx else ""
        filename = anonymize_text(att.filename, client_names, counterparty_names, client_role, counterparty_role) if client_names or counterparty_names else att.filename
        lines.append(f"{i}. {filename}{docx_marker}")
    
    return "\n".join(lines)


def generate_original_agreement_md(
    docx_bytes: bytes,
    source_name: str = "agreement",
    client_names: list[str] | str = "",
    counterparty_names: list[str] | str = "",
    original_provided_by: str = "counterparty",
    party_info: PartyInfo | None = None
) -> str:
    """
    Generate markdown with the full text of the original agreement.
    
    Uses docx_to_llm_markdown module to run analyze_doc and convert to markdown
    with proper clause numbering preserved.
    
    Args:
        docx_bytes: Raw docx file bytes
        source_name: Name for the document (used in output)
        client_names: Client name(s) to anonymize
        counterparty_names: Counterparty name(s) to anonymize
        original_provided_by: Who provided the original ("client" or "counterparty")
        party_info: Optional PartyInfo for enhanced YAML output
        
    Returns:
        Markdown string with agreement content including clause numbers
    """
    # Get role placeholders for anonymization
    client_role = party_info.client_placeholder.strip("[]") if party_info else "CLIENT"
    counterparty_role = party_info.counterparty_placeholder.strip("[]") if party_info else "COUNTERPARTY"
    
    # Determine description based on who provided it
    if original_provided_by == "client":
        description = "\"Our client's draft agreement\""
    else:
        description = "\"The counterparty's draft agreement before our review\""
    
    # YAML header
    yaml_header = generate_yaml_header(
        document_type="original_agreement",
        acting_for="client",
        original_provided_by=original_provided_by,
        extra_fields={"description": description},
        party_info=party_info
    )
    
    # Write bytes to temp file for analyze_doc
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp.write(docx_bytes)
        tmp_path = Path(tmp.name)
    
    # Create temp directory for analysis artifacts
    with tempfile.TemporaryDirectory() as tmp_dir:
        analysis_dir = Path(tmp_dir) / "analysis"
        
        try:
            # Run analyze_doc to extract blocks with numbering
            run_analyze_doc(tmp_path, analysis_dir)
            
            # Convert to markdown using the module
            markdown = convert_to_markdown(analysis_dir, source_name)
            
            # Anonymize party names in the agreement text
            if client_names or counterparty_names:
                markdown = anonymize_text(markdown, client_names, counterparty_names, client_role, counterparty_role)
            
            # Wrap with our header
            lines = [
                yaml_header,
                "# Original Agreement",
                "",
                "---",
                "",
                markdown
            ]
            return "\n".join(lines)
            
        finally:
            # Clean up temp docx file
            tmp_path.unlink(missing_ok=True)


def generate_comments_md(
    categorized_comments: dict[str, list[dict[str, Any]]],
    client_names: list[str] | str,
    counterparty_names: list[str] | str,
    original_provided_by: str = "counterparty",
    party_info: PartyInfo | None = None
) -> str:
    """Generate markdown for review comments grouped by recipient."""
    # YAML front matter
    yaml_header = generate_yaml_header(
        document_type="review_comments",
        acting_for="client",
        original_provided_by=original_provided_by,
        extra_fields={"description": "\"Comments addressed to each party\""},
        party_info=party_info
    )
    
    lines = [
        yaml_header,
        "# Review Comments",
        ""
    ]
    
    # Get role placeholders (use semantic roles if available)
    client_placeholder = party_info.client_placeholder if party_info else "[CLIENT]"
    counterparty_placeholder = party_info.counterparty_placeholder if party_info else "[COUNTERPARTY]"
    
    # Client comments section
    lines.extend([
        f"## For {client_placeholder} (Our Client)",
        ""
    ])
    
    client_comments = categorized_comments.get("client", [])
    if client_comments:
        for i, comment in enumerate(client_comments, 1):
            lines.extend(_format_comment(i, comment, client_names, counterparty_names, party_info))
    else:
        lines.append("*No comments for client.*")
        lines.append("")
    
    # Counterparty comments section
    lines.extend([
        "---",
        "",
        f"## For {counterparty_placeholder} (Counterparty)",
        ""
    ])
    
    counterparty_comments = categorized_comments.get("counterparty", [])
    if counterparty_comments:
        for i, comment in enumerate(counterparty_comments, 1):
            lines.extend(_format_comment(i, comment, client_names, counterparty_names, party_info))
    else:
        lines.append("*No comments for counterparty.*")
        lines.append("")
    
    # Other comments (if any)
    other_comments = categorized_comments.get("other", [])
    if other_comments:
        lines.extend([
            "---",
            "",
            "## Other Comments",
            ""
        ])
        for i, comment in enumerate(other_comments, 1):
            lines.extend(_format_comment(i, comment, client_names, counterparty_names, party_info))
    
    return "\n".join(lines)


def _format_comment(
    index: int, 
    comment: dict[str, Any],
    client_names: list[str] | str,
    counterparty_names: list[str] | str,
    party_info: PartyInfo | None = None
) -> list[str]:
    """Format a single comment as markdown lines."""
    # Get role placeholders for anonymization
    client_role = party_info.client_placeholder.strip("[]") if party_info else "CLIENT"
    counterparty_role = party_info.counterparty_placeholder.strip("[]") if party_info else "COUNTERPARTY"
    
    author = comment.get("author", "Unknown")
    date = comment.get("date", "")
    text = anonymize_text(comment.get("text", ""), client_names, counterparty_names, client_role, counterparty_role)
    reference_text = anonymize_text(comment.get("reference_text", ""), client_names, counterparty_names, client_role, counterparty_role)
    
    lines = [
        f"### Comment {index}",
        "",
        f"> {text}",
        ""
    ]
    
    if reference_text:
        lines.extend([
            f"**Referenced text:** \"{reference_text}\"",
            ""
        ])
    
    lines.extend(["---", ""])
    
    return lines


def generate_track_changes_md(
    diffs: list[ParagraphDiff],
    client_names: list[str] | str = "",
    counterparty_names: list[str] | str = "",
    original_provided_by: str = "counterparty",
    party_info: PartyInfo | None = None
) -> str:
    """
    Generate markdown for tracked changes using paragraph-level before/after diffs.
    
    This format is optimized for LLM learning - each edit shows the full context
    of the paragraph before and after the change, making it easy to understand
    what was changed and why.
    """
    yaml_header = generate_yaml_header(
        document_type="tracked_changes",
        acting_for="client",
        original_provided_by=original_provided_by,
        extra_fields={"description": "\"Edits made during contract review\""},
        party_info=party_info
    )
    
    lines = [
        yaml_header,
        "# Tracked Changes",
        "",
        "This section contains examples of contract edits made by this lawyer, extracted from Word's Track Changes.",
        "Each edit shows a paragraph that was modified, with:",
        "",
        "- **Before**: The original text from the counterparty's draft",
        "- **After**: The revised text after the lawyer's edits", 
        "- **Changes**: A summary of specific deletions and insertions",
        "- **Rationale**: The lawyer's comments explaining their reasoning (when available)",
        "",
        "These examples illustrate this particular lawyer's negotiation style and preferences.",
        "You may use these as a reference when assisting this user with similar contract reviews.",
        "",
        "---",
        ""
    ]
    
    if not diffs:
        lines.append("*No tracked changes found in the document.*")
        lines.append("")
        return "\n".join(lines)
    
    for i, diff in enumerate(diffs, 1):
        lines.extend(_format_paragraph_diff(i, diff, client_names, counterparty_names, party_info))
    
    return "\n".join(lines)


def generate_review_edits_md(
    diffs: list[ParagraphDiff],
    all_comments: list[dict[str, Any]],
    client_names: list[str] | str = "",
    counterparty_names: list[str] | str = "",
    original_provided_by: str = "counterparty",
    party_info: PartyInfo | None = None,
    paragraph_text_map: dict[str, str] | None = None
) -> str:
    """
    Generate merged markdown for comments and tracked changes, ordered by clause number.
    
    Groups edits and comments by clause:
    - Clauses with edits: "Edits to clause X" with Original clause, Changes, and Rationale (comments)
    - Clauses with only comments: "Comments on clause X" with Clause text and Comments
    """
    from collections import defaultdict
    
    def parse_clause_number(clause_num: str) -> tuple:
        """Parse clause number into sortable tuple (e.g., '11.2' -> (11, 2))."""
        if not clause_num:
            return (999999,)  # Put items without clause number at end
        parts = []
        for part in clause_num.replace('(', '.').replace(')', '').split('.'):
            part = part.strip()
            if part.isdigit():
                parts.append(int(part))
            elif part:
                # Handle letters like 'a', 'b', etc.
                parts.append(ord(part.lower()) - ord('a') + 1000)
        return tuple(parts) if parts else (999999,)
    
    # Get role placeholders for anonymization
    client_role = party_info.client_placeholder.strip("[]") if party_info else "CLIENT"
    counterparty_role = party_info.counterparty_placeholder.strip("[]") if party_info else "COUNTERPARTY"
    
    # Group items by clause number
    clause_edits: dict[str, list[ParagraphDiff]] = defaultdict(list)
    clause_comments: dict[str, list[dict[str, Any]]] = defaultdict(list)
    clause_titles: dict[str, str] = {}
    
    for diff in diffs:
        clause_num = diff.clause_number or ""
        clause_edits[clause_num].append(diff)
        if diff.clause_title and clause_num:
            clause_titles[clause_num] = diff.clause_title
    
    for comment in all_comments:
        clause_num = comment.get("clause_number", "") or ""
        clause_comments[clause_num].append(comment)
        # Extract clause title from reference_text if we don't have one
        if clause_num and clause_num not in clause_titles:
            ref_text = comment.get("reference_text", "")
            title = _extract_clause_title_from_text(ref_text)
            if title:
                clause_titles[clause_num] = title
    
    # Get all unique clause numbers and sort them
    all_clauses = set(clause_edits.keys()) | set(clause_comments.keys())
    sorted_clauses = sorted(all_clauses, key=parse_clause_number)
    
    # Generate YAML header
    yaml_header = generate_yaml_header(
        document_type="review_edits",
        acting_for="client",
        original_provided_by=original_provided_by,
        extra_fields={"description": "\"Comments and edits made during contract review, ordered by clause\""},
        party_info=party_info
    )
    
    lines = [
        yaml_header,
        "# Review Comments and Edits",
        "",
        "This section contains the lawyer's review comments and tracked changes, ordered by clause number.",
        "Comments provide rationale for edits, or standalone observations about clause text.",
        "",
        "---",
        ""
    ]
    
    if not sorted_clauses or (len(sorted_clauses) == 1 and sorted_clauses[0] == ""):
        if not clause_edits.get("") and not clause_comments.get(""):
            lines.append("*No comments or tracked changes found.*")
            lines.append("")
            return "\n".join(lines)
    
    for clause_num in sorted_clauses:
        edits = clause_edits.get(clause_num, [])
        comments = clause_comments.get(clause_num, [])
        title = clause_titles.get(clause_num, "")
        
        if not edits and not comments:
            continue
        
        # Format clause header
        if clause_num:
            title_display = f'"{title}"' if title else "(untitled)"
            if edits:
                lines.append(f"## Edits to clause {clause_num}: {title_display}")
            else:
                lines.append(f"## Comments on clause {clause_num}: {title_display}")
            lines.append("")
            
            if edits:
                # Format with: Original clause, Changes, Rationale
                for i, diff in enumerate(edits):
                    lines.extend(_format_clause_edit(
                        diff, comments if i == 0 else [],  # Only show comments once per clause
                        client_names, counterparty_names, party_info
                    ))
            else:
                # Comments only - show full clause text and comments
                lines.extend(_format_clause_comments_only(
                    comments, client_names, counterparty_names, party_info,
                    paragraph_text_map=paragraph_text_map
                ))
        else:
            # Other Items (no clause number) - format each comment individually
            lines.append("## Other Items (no clause number)")
            lines.append("")
            for comment in comments:
                lines.extend(_format_other_item_comment(
                    comment, client_names, counterparty_names, party_info,
                    paragraph_text_map=paragraph_text_map
                ))
                lines.append("---")
                lines.append("")
            # Remove the last separator since we add one after the block anyway
            if comments:
                lines = lines[:-2]
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def _format_clause_edit(
    diff: ParagraphDiff,
    comments: list[dict[str, Any]],
    client_names: list[str] | str,
    counterparty_names: list[str] | str,
    party_info: PartyInfo | None = None
) -> list[str]:
    """Format an edit with Original clause, Changes, and Rationale (from comments)."""
    client_role = party_info.client_placeholder.strip("[]") if party_info else "CLIENT"
    counterparty_role = party_info.counterparty_placeholder.strip("[]") if party_info else "COUNTERPARTY"
    
    before_text = anonymize_text(diff.before_text, client_names, counterparty_names, client_role, counterparty_role)
    after_text = anonymize_text(diff.after_text, client_names, counterparty_names, client_role, counterparty_role)
    
    deletions = [anonymize_text(d, client_names, counterparty_names, client_role, counterparty_role) for d in diff.deletions]
    insertions = [anonymize_text(i, client_names, counterparty_names, client_role, counterparty_role) for i in diff.insertions]
    
    lines = []
    
    is_new_insertion = not before_text.strip()
    
    if is_new_insertion:
        lines.extend([
            "### New clause inserted",
            "",
            f"> {after_text.strip()}",
            ""
        ])
    else:
        # Original clause
        lines.extend([
            "### Original clause",
            "",
            f"> {before_text.strip()}",
            ""
        ])
        
        # Changes - show focused before/after snippets
        change_snippets = _find_change_regions(before_text, after_text, deletions, insertions)
        
        if change_snippets:
            lines.append("### Changes")
            for before_snippet, after_snippet in change_snippets:
                if before_snippet:
                    lines.append(f"**Before:** {before_snippet}")
                if after_snippet:
                    lines.append(f"**After:** {after_snippet}")
            lines.append("")
    
    # Rationale - comments related to this clause
    if comments:
        lines.append("### Rationale")
        for comment in comments:
            text = anonymize_text(comment.get("text", ""), client_names, counterparty_names, client_role, counterparty_role)
            lines.append(f"> {text}")
            lines.append("")
    
    return lines


def _format_clause_comments_only(
    comments: list[dict[str, Any]],
    client_names: list[str] | str,
    counterparty_names: list[str] | str,
    party_info: PartyInfo | None = None,
    paragraph_text_map: dict[str, str] | None = None
) -> list[str]:
    """Format comments-only clause with Full clause text, Reference text, and Comments."""
    client_role = party_info.client_placeholder.strip("[]") if party_info else "CLIENT"
    counterparty_role = party_info.counterparty_placeholder.strip("[]") if party_info else "COUNTERPARTY"
    
    lines = []
    paragraph_text_map = paragraph_text_map or {}
    
    # Get the full clause text - first try from comment itself (includes table cells),
    # then fall back to paragraph_text_map (from blocks.jsonl)
    full_clause_text = ""
    if comments:
        full_clause_text = comments[0].get("paragraph_text", "")
        if not full_clause_text:
            para_id = comments[0].get("para_id", "")
            if para_id and para_id in paragraph_text_map:
                full_clause_text = paragraph_text_map[para_id]
    
    # Show full clause text
    if full_clause_text:
        anon_full_text = anonymize_text(full_clause_text, client_names, counterparty_names, client_role, counterparty_role)
        lines.extend([
            "### Full clause text",
            "",
            f"> {anon_full_text}",
            ""
        ])
    
    # Show reference text (the highlighted portion the comment is attached to)
    if comments:
        first_ref = comments[0].get("reference_text", "")
        if first_ref:
            ref_text = anonymize_text(first_ref, client_names, counterparty_names, client_role, counterparty_role)
            lines.extend([
                "### Reference text",
                "",
                f"> {ref_text}",
                ""
            ])
    
    # Show all comments
    lines.append("### Comments")
    for comment in comments:
        text = anonymize_text(comment.get("text", ""), client_names, counterparty_names, client_role, counterparty_role)
        lines.append(f"> {text}")
        lines.append("")
    
    return lines


def _format_other_item_comment(
    comment: dict[str, Any],
    client_names: list[str] | str,
    counterparty_names: list[str] | str,
    party_info: PartyInfo | None = None,
    paragraph_text_map: dict[str, str] | None = None
) -> list[str]:
    """Format a single comment in 'Other Items' with Full paragraph text, Reference text, and Comment."""
    client_role = party_info.client_placeholder.strip("[]") if party_info else "CLIENT"
    counterparty_role = party_info.counterparty_placeholder.strip("[]") if party_info else "COUNTERPARTY"
    
    lines = []
    paragraph_text_map = paragraph_text_map or {}
    
    # Get the full paragraph text - first try from comment itself (includes table cells),
    # then fall back to paragraph_text_map (from blocks.jsonl)
    full_para_text = comment.get("paragraph_text", "")
    if not full_para_text:
        para_id = comment.get("para_id", "")
        full_para_text = paragraph_text_map.get(para_id, "") if para_id else ""
    
    # Show full paragraph text
    if full_para_text:
        anon_full_text = anonymize_text(full_para_text, client_names, counterparty_names, client_role, counterparty_role)
        lines.extend([
            "### Full paragraph text",
            "",
            f"> {anon_full_text}",
            ""
        ])
    
    # Show reference text (the highlighted portion the comment is attached to)
    ref_text = comment.get("reference_text", "")
    if ref_text:
        anon_ref_text = anonymize_text(ref_text, client_names, counterparty_names, client_role, counterparty_role)
        lines.extend([
            "### Reference text",
            "",
            f"> {anon_ref_text}",
            ""
        ])
    
    # Show comment
    lines.append("### Comments")
    text = anonymize_text(comment.get("text", ""), client_names, counterparty_names, client_role, counterparty_role)
    lines.append(f"> {text}")
    lines.append("")
    
    return lines


def _extract_clause_title_from_text(text: str) -> str:
    """Extract clause title from paragraph text (e.g., 'LIMITATION OF LIABILITY.' -> 'LIMITATION OF LIABILITY')."""
    import re
    if not text:
        return ""
    
    # ALL CAPS title pattern (e.g., "INDEMNIFICATION.", "LIMITATION OF LIABILITY.")
    match = re.match(r'^([A-Z][A-Z\s&,\-]*)\.(?:\s|$)', text)
    if match:
        title = match.group(1).strip()
        # Must be at least 3 chars and all uppercase (excluding spaces/punctuation)
        if len(title) >= 3 and title.replace(' ', '').replace('&', '').replace(',', '').replace('-', '').isupper():
            return title
    
    # Title Case pattern (e.g., "Indemnification.", "Limitation of Liability.")
    match = re.match(r'^([A-Z][a-z]+(?:\s+(?:[A-Z][a-z]+|&|of|and|the|in|to|for))*)\.(?:\s|$)', text)
    if match:
        title = match.group(1).strip()
        if len(title) <= 50:
            return title
    
    return ""


def _format_comment_for_merged(
    comment: dict[str, Any],
    client_names: list[str] | str,
    counterparty_names: list[str] | str,
    party_info: PartyInfo | None = None
) -> list[str]:
    """Format a single comment for the merged output."""
    client_role = party_info.client_placeholder.strip("[]") if party_info else "CLIENT"
    counterparty_role = party_info.counterparty_placeholder.strip("[]") if party_info else "COUNTERPARTY"
    
    text = anonymize_text(comment.get("text", ""), client_names, counterparty_names, client_role, counterparty_role)
    reference = anonymize_text(comment.get("reference_text", ""), client_names, counterparty_names, client_role, counterparty_role)
    
    # Determine recipient from comment prefix
    recipient = ""
    if text.startswith("For ["):
        # Extract the recipient placeholder
        import re
        match = re.match(r'^For \[([^\]]+)\]:', text)
        if match:
            recipient = f" (to {match.group(1)})"
    
    lines = [
        f"### Comment{recipient}",
        "",
        f"> {text}",
        ""
    ]
    
    if reference:
        lines.extend([
            f"**Referenced text:** \"{reference}\"",
            ""
        ])
    
    lines.append("---")
    lines.append("")
    
    return lines


def _format_edit_for_merged(
    diff: ParagraphDiff,
    client_names: list[str] | str,
    counterparty_names: list[str] | str,
    party_info: PartyInfo | None = None
) -> list[str]:
    """Format a single edit for the merged output."""
    client_role = party_info.client_placeholder.strip("[]") if party_info else "CLIENT"
    counterparty_role = party_info.counterparty_placeholder.strip("[]") if party_info else "COUNTERPARTY"
    
    before_text = anonymize_text(diff.before_text, client_names, counterparty_names, client_role, counterparty_role)
    after_text = anonymize_text(diff.after_text, client_names, counterparty_names, client_role, counterparty_role)
    
    deletions = [anonymize_text(d, client_names, counterparty_names, client_role, counterparty_role) for d in diff.deletions]
    insertions = [anonymize_text(i, client_names, counterparty_names, client_role, counterparty_role) for i in diff.insertions]
    
    is_new_insertion = not before_text.strip()
    
    lines = [
        "### Edit",
        ""
    ]
    
    if is_new_insertion:
        lines.extend([
            "**New clause inserted:**",
            f"> {after_text.strip()}",
            ""
        ])
    else:
        lines.extend([
            "**Original:**",
            f"> {before_text.strip()}",
            ""
        ])
        
        # Show focused changes
        change_snippets = _find_change_regions(before_text, after_text, deletions, insertions)
        
        if change_snippets:
            lines.append("**Changes:**")
            for before_snippet, after_snippet in change_snippets:
                if before_snippet:
                    lines.append(f"- Before: {before_snippet}")
                if after_snippet:
                    lines.append(f"- After: {after_snippet}")
            lines.append("")
    
    lines.append("---")
    lines.append("")
    
    return lines


def _snap_to_word_boundary(text: str, pos: int, direction: str) -> int:
    """
    Snap a position to the nearest word boundary.
    
    Args:
        text: The text to search in
        pos: The starting position
        direction: 'left' to find start of word, 'right' to find end of word
        
    Returns:
        Adjusted position at a word boundary
    """
    if direction == 'left':
        # Move left to find start of current word or previous space
        while pos > 0 and text[pos - 1] not in ' \t\n':
            pos -= 1
        return pos
    else:  # direction == 'right'
        # Move right to find end of current word or next space
        while pos < len(text) and text[pos] not in ' \t\n':
            pos += 1
        return pos


def _extract_snippet_with_context(text: str, start: int, end: int, context_chars: int = 20) -> str:
    """
    Extract a snippet from text with context, snapping to word boundaries.
    
    Returns snippet with ellipsis if truncated.
    """
    # Expand to include context
    snippet_start = max(0, start - context_chars)
    snippet_end = min(len(text), end + context_chars)
    
    # Snap to word boundaries
    if snippet_start > 0:
        snippet_start = _snap_to_word_boundary(text, snippet_start, 'right')
    if snippet_end < len(text):
        snippet_end = _snap_to_word_boundary(text, snippet_end, 'left')
    
    # Ensure we don't go backwards
    snippet_start = min(snippet_start, start)
    snippet_end = max(snippet_end, end)
    
    snippet = text[snippet_start:snippet_end]
    
    # Add ellipsis
    if snippet_start > 0:
        snippet = "..." + snippet
    if snippet_end < len(text):
        snippet = snippet + "..."
    
    return snippet


def _normalize_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters to single space."""
    import re
    return re.sub(r'\s+', ' ', text)


@dataclass
class ChangeRegion:
    """A region of text that was changed, with before/after snippets."""
    before_start: int
    before_end: int
    after_start: int
    after_end: int
    
    def overlaps_with(self, other: 'ChangeRegion', margin: int = 30) -> bool:
        """Check if two regions overlap or are close enough to merge."""
        # Check before_text overlap
        before_overlaps = not (self.before_end + margin < other.before_start or 
                               other.before_end + margin < self.before_start)
        # Check after_text overlap  
        after_overlaps = not (self.after_end + margin < other.after_start or
                              other.after_end + margin < self.after_start)
        return before_overlaps or after_overlaps
    
    def merge_with(self, other: 'ChangeRegion') -> 'ChangeRegion':
        """Merge two regions into one spanning both."""
        return ChangeRegion(
            before_start=min(self.before_start, other.before_start),
            before_end=max(self.before_end, other.before_end),
            after_start=min(self.after_start, other.after_start),
            after_end=max(self.after_end, other.after_end),
        )


def _find_change_regions(
    before_text: str, 
    after_text: str, 
    deletions: list[str], 
    insertions: list[str],
    context_chars: int = 20
) -> list[tuple[str, str]]:
    """
    Find all change regions and merge overlapping ones.
    
    Returns list of (before_snippet, after_snippet) tuples with context.
    """
    regions: list[ChangeRegion] = []
    
    # Find positions of all deletions in before_text
    for deletion in deletions:
        if deletion and deletion in before_text:
            pos = before_text.find(deletion)
            regions.append(ChangeRegion(
                before_start=pos,
                before_end=pos + len(deletion),
                after_start=-1,  # Will be matched with insertion if possible
                after_end=-1,
            ))
    
    # Find positions of all insertions in after_text
    for insertion in insertions:
        if insertion and insertion in after_text:
            pos = after_text.find(insertion)
            # Try to find a region without after position to pair with
            paired = False
            for region in regions:
                if region.after_start == -1:
                    region.after_start = pos
                    region.after_end = pos + len(insertion)
                    paired = True
                    break
            if not paired:
                regions.append(ChangeRegion(
                    before_start=-1,
                    before_end=-1,
                    after_start=pos,
                    after_end=pos + len(insertion),
                ))
    
    # Merge overlapping regions
    if len(regions) > 1:
        merged = True
        while merged:
            merged = False
            new_regions = []
            skip_indices = set()
            
            for i, region in enumerate(regions):
                if i in skip_indices:
                    continue
                    
                current = region
                for j in range(i + 1, len(regions)):
                    if j in skip_indices:
                        continue
                    if current.overlaps_with(regions[j]):
                        current = current.merge_with(regions[j])
                        skip_indices.add(j)
                        merged = True
                
                new_regions.append(current)
            
            regions = new_regions
    
    # Convert regions to aligned before/after snippets
    results: list[tuple[str, str]] = []
    
    for region in regions:
        before_snippet, after_snippet = _build_aligned_snippets(
            before_text, after_text, region, context_chars
        )
        results.append((before_snippet, after_snippet))
    
    return results


def _build_aligned_snippets(
    before_text: str,
    after_text: str, 
    region: ChangeRegion,
    context_chars: int = 20
) -> tuple[str | None, str | None]:
    """
    Build before/after snippets that share common prefix and suffix text.
    
    This ensures both snippets start and end at the same anchor points,
    making the actual change crystal clear.
    """
    # Case 1: We have positions in both texts (deletion + insertion)
    if region.before_start >= 0 and region.after_start >= 0:
        # Find common prefix: text before the change
        prefix_start_before = max(0, region.before_start - context_chars)
        prefix_start_after = max(0, region.after_start - context_chars)
        
        # Snap to word boundaries
        if prefix_start_before > 0:
            prefix_start_before = _snap_to_word_boundary(before_text, prefix_start_before, 'right')
        if prefix_start_after > 0:
            prefix_start_after = _snap_to_word_boundary(after_text, prefix_start_after, 'right')
        
        prefix_before = before_text[prefix_start_before:region.before_start]
        prefix_after = after_text[prefix_start_after:region.after_start]
        
        # Use the shorter common prefix
        common_prefix = prefix_before if len(prefix_before) <= len(prefix_after) else prefix_after
        
        # Find common suffix: text after the change
        suffix_end_before = min(len(before_text), region.before_end + context_chars)
        suffix_end_after = min(len(after_text), region.after_end + context_chars)
        
        # Snap to word boundaries
        if suffix_end_before < len(before_text):
            suffix_end_before = _snap_to_word_boundary(before_text, suffix_end_before, 'left')
        if suffix_end_after < len(after_text):
            suffix_end_after = _snap_to_word_boundary(after_text, suffix_end_after, 'left')
        
        suffix_before = before_text[region.before_end:suffix_end_before]
        suffix_after = after_text[region.after_end:suffix_end_after]
        
        # Use the shorter common suffix
        common_suffix = suffix_before if len(suffix_before) <= len(suffix_after) else suffix_after
        
        # Build the snippets: common_prefix + changed_part + common_suffix
        deleted_part = before_text[region.before_start:region.before_end]
        inserted_part = after_text[region.after_start:region.after_end]
        
        before_snippet = common_prefix + deleted_part + common_suffix
        after_snippet = common_prefix + inserted_part + common_suffix
        
        # Add ellipsis
        if prefix_start_before > 0 or prefix_start_after > 0:
            before_snippet = "..." + before_snippet
            after_snippet = "..." + after_snippet
        if suffix_end_before < len(before_text) or suffix_end_after < len(after_text):
            before_snippet = before_snippet + "..."
            after_snippet = after_snippet + "..."
        
        return before_snippet, after_snippet
    
    # Case 2: Only after position (insertion only, no deletion)
    elif region.after_start >= 0:
        # Find the context around insertion point in after_text
        prefix_start = max(0, region.after_start - context_chars)
        if prefix_start > 0:
            prefix_start = _snap_to_word_boundary(after_text, prefix_start, 'right')
        
        suffix_end = min(len(after_text), region.after_end + context_chars)
        if suffix_end < len(after_text):
            suffix_end = _snap_to_word_boundary(after_text, suffix_end, 'left')
        
        prefix = after_text[prefix_start:region.after_start]
        suffix = after_text[region.after_end:suffix_end]
        inserted_part = after_text[region.after_start:region.after_end]
        
        after_snippet = prefix + inserted_part + suffix
        if prefix_start > 0:
            after_snippet = "..." + after_snippet
        if suffix_end < len(after_text):
            after_snippet = after_snippet + "..."
        
        # Try to find the same prefix and suffix in before_text for alignment
        before_snippet = None
        if before_text and prefix:
            prefix_pos = before_text.find(prefix)
            if prefix_pos >= 0:
                # Find where suffix appears in before_text (after the prefix)
                prefix_end_in_before = prefix_pos + len(prefix)
                suffix_pos_in_before = before_text.find(suffix.strip(), prefix_end_in_before) if suffix.strip() else -1
                
                if suffix_pos_in_before >= 0:
                    # Extract what's between prefix and suffix in before_text
                    between_text = before_text[prefix_end_in_before:suffix_pos_in_before]
                    # Use lstrip() on suffix since we searched for suffix.strip() - 
                    # the between_text already includes any leading whitespace
                    before_snippet = prefix + between_text + suffix.lstrip()
                else:
                    # Suffix not found, just show prefix + whatever follows up to context_chars
                    end_pos = min(len(before_text), prefix_end_in_before + context_chars)
                    if end_pos < len(before_text):
                        end_pos = _snap_to_word_boundary(before_text, end_pos, 'left')
                    before_snippet = prefix + before_text[prefix_end_in_before:end_pos]
                
                if prefix_pos > 0:
                    before_snippet = "..." + before_snippet
                # Check if there's more text after our snippet in before_text
                snippet_end = suffix_pos_in_before + len(suffix) if suffix_pos_in_before >= 0 else prefix_end_in_before + context_chars
                if snippet_end < len(before_text):
                    before_snippet = before_snippet + "..."
        
        return before_snippet, after_snippet
    
    # Case 3: Only before position (deletion only, no insertion)
    elif region.before_start >= 0:
        before_snippet = _extract_snippet_with_context(
            before_text, region.before_start, region.before_end, context_chars
        )
        # For deletion-only, after would show the gap
        # Find the same anchors in after_text
        prefix_start = max(0, region.before_start - context_chars)
        if prefix_start > 0:
            prefix_start = _snap_to_word_boundary(before_text, prefix_start, 'right')
        
        suffix_end = min(len(before_text), region.before_end + context_chars)
        if suffix_end < len(before_text):
            suffix_end = _snap_to_word_boundary(before_text, suffix_end, 'left')
        
        prefix = before_text[prefix_start:region.before_start]
        suffix = before_text[region.before_end:suffix_end]
        
        after_snippet = None
        if after_text and prefix:
            prefix_pos = after_text.find(prefix)
            if prefix_pos >= 0:
                after_snippet = prefix + suffix
                if prefix_pos > 0:
                    after_snippet = "..." + after_snippet
                suffix_pos_in_after = prefix_pos + len(prefix)
                if suffix_pos_in_after + len(suffix) < len(after_text):
                    after_snippet = after_snippet + "..."
        
        return before_snippet, after_snippet
    
    return None, None


def _format_paragraph_diff(
    index: int, 
    diff: ParagraphDiff,
    client_names: list[str] | str,
    counterparty_names: list[str] | str,
    party_info: PartyInfo | None = None
) -> list[str]:
    """Format a single paragraph diff as markdown lines with focused diffs."""
    # Get role placeholders for anonymization
    client_role = party_info.client_placeholder.strip("[]") if party_info else "CLIENT"
    counterparty_role = party_info.counterparty_placeholder.strip("[]") if party_info else "COUNTERPARTY"
    
    # Anonymize text fields
    before_text = anonymize_text(diff.before_text, client_names, counterparty_names, client_role, counterparty_role)
    after_text = anonymize_text(diff.after_text, client_names, counterparty_names, client_role, counterparty_role)
    clause_title = anonymize_text(diff.clause_title, client_names, counterparty_names, client_role, counterparty_role)
    
    # Anonymize deletions and insertions lists
    deletions = [anonymize_text(d, client_names, counterparty_names, client_role, counterparty_role) for d in diff.deletions]
    insertions = [anonymize_text(i, client_names, counterparty_names, client_role, counterparty_role) for i in diff.insertions]
    rationales = [anonymize_text(r, client_names, counterparty_names, client_role, counterparty_role) for r in diff.rationale] if diff.rationale else []
    
    # Determine if this is a new clause insertion (no before_text)
    is_new_insertion = not before_text.strip()
    
    # Build heading with clause number if available
    if diff.clause_number:
        heading = f"## Edits to clause {diff.clause_number}: \"{clause_title}\""
    else:
        heading = f"## Edits to clause: \"{clause_title}\""
    
    lines = [
        heading,
        "",
    ]
    
    if is_new_insertion:
        # This is a newly inserted clause/paragraph
        lines.append("### New clause inserted")
        lines.append(f"> {after_text.strip()}")
        lines.append("")
    else:
        # This is a modification to existing text
        # Show full original clause for context
        lines.append("### Original clause")
        lines.append(f"> {before_text.strip()}")
        lines.append("")
        
        # Show focused changes with context (merged overlapping regions)
        lines.append("### Changes")
        
        change_snippets = _find_change_regions(
            before_text, after_text,
            deletions, insertions
        )
        
        for before_snippet, after_snippet in change_snippets:
            if before_snippet:
                lines.append(f"**Before:** {before_snippet}")
            if after_snippet:
                lines.append(f"**After:** {after_snippet}")
            lines.append("")
    
    # Show rationale if available
    if rationales:
        lines.append("### Rationale")
        for rationale in rationales:
            lines.append(f"> {rationale}")
            lines.append("")
    
    lines.extend(["---", ""])
    
    return lines


def extract_first_email_from_thread(body: str) -> str:
    """
    Extract only the first (most recent) email from an email thread.
    
    Looks for common reply markers like "From:", "On ... wrote:", etc.
    and truncates the body at the first occurrence.
    """
    import re
    
    if not body:
        return body
    
    # Common patterns that indicate the start of a quoted/forwarded email
    # These patterns mark where the reply chain begins
    reply_patterns = [
        # "From: Name <email>" pattern (common in Outlook)
        r'\n\s*From:\s+[^\n]+<[^>]+>\s*\n\s*Sent:',
        # "On [date], [name] wrote:" pattern (common in Gmail)
        r'\n\s*On\s+.{10,60}\s+wrote:\s*\n',
        # Outlook-style separator with underscores
        r'\n_{20,}\n',
        # "-----Original Message-----" pattern
        r'\n-{3,}\s*Original Message\s*-{3,}',
        # Simple "From:" at start of line after blank line
        r'\n\n\s*From:\s+',
    ]
    
    # Find the earliest match
    earliest_pos = len(body)
    for pattern in reply_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match and match.start() < earliest_pos:
            earliest_pos = match.start()
    
    # Return the body up to the first reply marker (or full body if none found)
    if earliest_pos < len(body):
        return body[:earliest_pos].rstrip()
    
    return body


def generate_advice_note_md(
    email_data: EmailData,
    client_names: list[str] | str = "",
    counterparty_names: list[str] | str = "",
    original_provided_by: str = "counterparty",
    party_info: PartyInfo | None = None
) -> str:
    """Generate markdown for the advice note email."""
    # Get role placeholders for anonymization
    client_role = party_info.client_placeholder.strip("[]") if party_info else "CLIENT"
    counterparty_role = party_info.counterparty_placeholder.strip("[]") if party_info else "COUNTERPARTY"
    
    # Extract only the first email from the thread (not the reply chain)
    body = extract_first_email_from_thread(email_data.body) if email_data.body else "(No body text)"
    body = anonymize_text(body, client_names, counterparty_names, client_role, counterparty_role)
    subject = anonymize_text(email_data.subject or "", client_names, counterparty_names, client_role, counterparty_role)
    
    yaml_header = generate_yaml_header(
        document_type="advice_note",
        acting_for="client",
        original_provided_by=original_provided_by,
        extra_fields={"description": "\"Email from lawyer with review and markup\""},
        party_info=party_info
    )
    
    lines = [
        yaml_header,
        "# Advice Note",
        "",
        f"**From:** {email_data.sender}",
        f"**To:** {email_data.recipients}",
        f"**Date:** {email_data.date}",
        f"**Subject:** {subject}",
        "",
        "---",
        "",
        "## Email Body",
        "",
        body,
        "",
        "---",
        "",
        "## Attachments",
        ""
    ]
    
    for i, att in enumerate(email_data.attachments, 1):
        docx_marker = " *(edited agreement)*" if att.is_docx else ""
        lines.append(f"{i}. {att.filename}{docx_marker}")
    
    return "\n".join(lines)


def generate_mappings_md(
    party_info: PartyInfo,
    client_names: list[str],
    counterparty_names: list[str]
) -> str:
    """
    Generate a markdown file documenting the party mappings and replacements.
    
    This file serves as a reference for what text was replaced with which
    placeholder during anonymization.
    
    Args:
        party_info: Party information with roles and identifiers
        client_names: List of client name variations that were replaced
        counterparty_names: List of counterparty name variations that were replaced
    
    Returns:
        Markdown content documenting the mappings
    """
    lines = [
        "---",
        "document_type: mappings",
        "description: \"Party anonymization mappings used in this review\"",
        "---",
        "",
        "# Anonymization Mappings",
        "",
        "This file documents the text replacements used to anonymize party names in the review materials.",
        "",
        "## Party Roles",
        "",
        "| Party | Role | Placeholder |",
        "|-------|------|-------------|",
        f"| Client | {party_info.client_role} | {party_info.client_placeholder} |",
        f"| Counterparty | {party_info.counterparty_role} | {party_info.counterparty_placeholder} |",
        "",
        "## Client Replacements",
        "",
        f"The following terms are replaced with `{party_info.client_placeholder}`:",
        "",
    ]
    
    # Deduplicate and sort client names
    unique_client_names = sorted(set(n for n in client_names if n))
    for name in unique_client_names:
        lines.append(f"- `{name}`")
    
    lines.extend([
        "",
        "## Counterparty Replacements",
        "",
        f"The following terms are replaced with `{party_info.counterparty_placeholder}`:",
        "",
    ])
    
    # Deduplicate and sort counterparty names
    unique_counterparty_names = sorted(set(n for n in counterparty_names if n))
    for name in unique_counterparty_names:
        lines.append(f"- `{name}`")
    
    lines.extend([
        "",
        "## Original Agreement Source",
        "",
        f"The original agreement was provided by: **{party_info.original_provided_by}**",
        "",
    ])
    
    return "\n".join(lines)


def generate_single_file_md(
    instructions_md: str,
    original_md: str,
    review_edits_md: str,
    _unused: str | None,  # For backward compatibility (was track_changes_md)
    advice_md: str
) -> str:
    """Combine all markdown sections into a single file."""
    sections = [
        instructions_md,
        "\n\n" + "=" * 80 + "\n\n",
        original_md,
        "\n\n" + "=" * 80 + "\n\n",
        review_edits_md,  # Now contains merged comments + edits
        "\n\n" + "=" * 80 + "\n\n",
        advice_md
    ]
    return "".join(sections)


# =============================================================================
# Main Workflow
# =============================================================================

def generate_review_example(
    incoming_path: Path,
    outgoing_path: Path,
    output_dir: Path,
    original_index: int | None = None,
    edited_index: int | None = None,
    single_file: bool = False
) -> None:
    """
    Generate legal review example markdown files.
    
    Automatically detects parties from the contract and comments, then asks
    the user to confirm which is the client vs counterparty.
    
    Args:
        incoming_path: Path to incoming .msg with instructions
        outgoing_path: Path to outgoing .msg with advice
        output_dir: Directory for output files
        original_index: Optional 1-based index for original .docx selection
        edited_index: Optional 1-based index for edited .docx selection
        single_file: If True, combine all outputs into one file
    """
    # Parse emails
    print(f"Parsing incoming email: {incoming_path}")
    incoming_email = parse_msg_file(incoming_path)
    
    print(f"Parsing outgoing email: {outgoing_path}")
    outgoing_email = parse_msg_file(outgoing_path)
    
    # Select attachments
    print("\nSelecting original agreement...")
    original_attachment = select_docx_attachment(
        incoming_email.attachments,
        "Select original agreement:",
        original_index
    )
    print(f"  Selected: {original_attachment.filename}")
    
    print("\nSelecting edited agreement...")
    edited_attachment = select_docx_attachment(
        outgoing_email.attachments,
        "Select edited agreement:",
        edited_index
    )
    print(f"  Selected: {edited_attachment.filename}")
    
    # Load documents
    original_doc = Document(BytesIO(original_attachment.data))
    edited_doc = Document(BytesIO(edited_attachment.data))
    
    # Extract all comments first (before party detection)
    print("\nExtracting comments...")
    all_comments = extract_all_comments(edited_doc)
    print(f"  Found {len(all_comments)} comments total")
    
    # Detect and confirm parties
    party_info = detect_and_confirm_parties(original_doc, all_comments)
    
    # Build lists of name variations to anonymize
    # Uses all_client_names/all_counterparty_names which include prefix, defined term, and alternates
    client_names = party_info.all_client_names
    counterparty_names = party_info.all_counterparty_names
    
    # Categorize comments based on detected prefixes
    print("\nCategorizing comments...")
    categorized_comments = categorize_comments_by_prefix(
        all_comments, 
        party_info.client_prefix, 
        party_info.counterparty_prefix
    )
    client_count = len(categorized_comments["client"])
    counterparty_count = len(categorized_comments["counterparty"])
    print(f"  Found: {client_count} for [CLIENT], {counterparty_count} for [COUNTERPARTY]")
    
    print("Processing track changes...")
    paragraph_diffs = process_track_changes(edited_doc)
    
    # Extract clause numbers and text from document analysis (keyed by para_id)
    print("  Extracting clause numbers...")
    clause_number_map, paragraph_text_map = extract_clause_numbers_from_doc(edited_attachment.data)
    
    # Also get paragraph text from original document (for comments on unchanged clauses)
    _, original_text_map = extract_clause_numbers_from_doc(original_attachment.data)
    # Merge: prefer edited text, fall back to original
    for para_id, text in original_text_map.items():
        if para_id not in paragraph_text_map:
            paragraph_text_map[para_id] = text
    
    # Merge clause numbers into diffs using para_id matching
    for diff in paragraph_diffs:
        if diff.para_id:
            diff.clause_number = clause_number_map.get(diff.para_id, "")
    
    matched_clause_numbers = sum(1 for d in paragraph_diffs if d.clause_number)
    print(f"  Matched clause numbers for {matched_clause_numbers}/{len(paragraph_diffs)} paragraphs")
    
    # Also add clause numbers to comments
    for comment in all_comments:
        para_id = comment.get("para_id")
        if para_id:
            comment["clause_number"] = clause_number_map.get(para_id, "")
    
    matched_comment_clauses = sum(1 for c in all_comments if c.get("clause_number"))
    print(f"  Matched clause numbers for {matched_comment_clauses}/{len(all_comments)} comments")
    
    # Match comments to track changes to provide rationale
    match_comments_to_diffs(paragraph_diffs, all_comments)
    
    total_insertions = sum(len(d.insertions) for d in paragraph_diffs)
    total_deletions = sum(len(d.deletions) for d in paragraph_diffs)
    matched_rationales = sum(1 for d in paragraph_diffs if d.rationale)
    print(f"  Found: {len(paragraph_diffs)} paragraphs with changes ({total_insertions} insertions, {total_deletions} deletions)")
    print(f"  Matched {matched_rationales} edits to comments for rationale")
    
    # Generate markdown with anonymization
    print("\nGenerating markdown files...")
    instructions_md = generate_instructions_md(
        incoming_email, 
        client_names, counterparty_names, 
        party_info.original_provided_by,
        party_info=party_info
    )
    original_md = generate_original_agreement_md(
        original_attachment.data, 
        source_name=original_attachment.filename.replace(".docx", ""),
        client_names=client_names,
        counterparty_names=counterparty_names,
        original_provided_by=party_info.original_provided_by,
        party_info=party_info
    )
    comments_md = generate_comments_md(
        categorized_comments, 
        client_names, counterparty_names,
        party_info.original_provided_by,
        party_info=party_info
    )
    track_changes_md = generate_track_changes_md(
        paragraph_diffs,
        client_names, counterparty_names,
        party_info.original_provided_by,
        party_info=party_info
    )
    # Generate merged comments + edits ordered by clause
    review_edits_md = generate_review_edits_md(
        paragraph_diffs,
        all_comments,
        client_names, counterparty_names,
        party_info.original_provided_by,
        party_info=party_info,
        paragraph_text_map=paragraph_text_map
    )
    advice_md = generate_advice_note_md(
        outgoing_email,
        client_names, counterparty_names,
        party_info.original_provided_by,
        party_info=party_info
    )
    mappings_md = generate_mappings_md(
        party_info,
        client_names,
        counterparty_names
    )
    
    # Write output
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if single_file:
        # Use merged review_edits instead of separate comments + track_changes
        combined_md = generate_single_file_md(
            instructions_md, original_md, review_edits_md, None, advice_md
        )
        output_file = output_dir / "review_example.md"
        output_file.write_text(combined_md, encoding="utf-8")
        print(f"\nGenerated: {output_file}")
        # Also write mappings separately (always useful as reference)
        mappings_file = output_dir / "00_mappings.md"
        mappings_file.write_text(mappings_md, encoding="utf-8")
        print(f"Generated: {mappings_file}")
    else:
        files = [
            ("00_mappings.md", mappings_md),
            ("01_instructions.md", instructions_md),
            ("02_original_agreement.md", original_md),
            ("03_review_edits.md", review_edits_md),  # Merged comments + edits
            ("04_advice_note.md", advice_md)
        ]
        
        for filename, content in files:
            output_file = output_dir / filename
            output_file.write_text(content, encoding="utf-8")
            print(f"  Generated: {output_file}")
    
    print("\nDone!")


# =============================================================================
# CLI
# =============================================================================

def create_argument_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description="Generate legal review examples from email + document pairs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_review_example.py \\
      --incoming instructions.msg \\
      --outgoing advice.msg
  
  # With preselected indices (for scripted use)
  python scripts/generate_review_example.py \\
      --incoming instructions.msg \\
      --outgoing advice.msg \\
      --original-index 1 \\
      --edited-index 1

The script will:
1. Auto-detect party names from the contract and comments
2. Ask you to confirm which party is your client
3. Ask who provided the original agreement
4. Generate anonymized markdown with [CLIENT] and [COUNTERPARTY] labels
"""
    )
    
    parser.add_argument(
        "--incoming",
        required=True,
        type=Path,
        help="Path to incoming .msg file (instructions + original agreement)"
    )
    parser.add_argument(
        "--outgoing",
        required=True,
        type=Path,
        help="Path to outgoing .msg file (advice + edited agreement)"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output directory (default: same as incoming .msg)"
    )
    parser.add_argument(
        "--original-index",
        type=int,
        help="1-based index of original .docx attachment (skip prompt)"
    )
    parser.add_argument(
        "--edited-index",
        type=int,
        help="1-based index of edited .docx attachment (skip prompt)"
    )
    parser.add_argument(
        "--single-file",
        action="store_true",
        help="Combine all outputs into one markdown file"
    )
    
    return parser


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    incoming_path = args.incoming
    outgoing_path = args.outgoing
    output_dir = args.output or incoming_path.parent
    
    if not incoming_path.exists():
        print(f"Error: Incoming file not found: {incoming_path}")
        sys.exit(1)
    
    if not outgoing_path.exists():
        print(f"Error: Outgoing file not found: {outgoing_path}")
        sys.exit(1)
    
    try:
        generate_review_example(
            incoming_path=incoming_path,
            outgoing_path=outgoing_path,
            output_dir=output_dir,
            original_index=args.original_index,
            edited_index=args.edited_index,
            single_file=args.single_file
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
