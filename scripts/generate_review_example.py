#!/usr/bin/env python3
"""
Generate legal review examples from email + document pairs.

This script extracts structured markdown examples from:
- Incoming email with client instructions + original agreement
- Outgoing email with advice + edited agreement (with comments and track changes)

Usage:
    python scripts/generate_review_example.py \\
        --incoming instructions.msg \\
        --outgoing advice.msg \\
        --client "Didimo" \\
        --counterparty "NBC" \\
        --output ./output_dir/

Examples:
    # Basic usage
    python scripts/generate_review_example.py \\
        --incoming email_instructions.msg \\
        --outgoing email_advice.msg \\
        --client "Didimo" \\
        --counterparty "NBC"
    
    # With preselected attachment indices (for scripted use)
    python scripts/generate_review_example.py \\
        --incoming email_instructions.msg \\
        --outgoing email_advice.msg \\
        --client "Didimo" \\
        --counterparty "NBC" \\
        --original-index 1 \\
        --edited-index 1
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from dataclasses import dataclass
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
from effilocal.mcp_server.core.comments import extract_all_comments
from effilocal.mcp_server.utils.document_utils import iter_document_paragraphs

# Import docx_to_llm_markdown module functions
from scripts.docx_to_llm_markdown import (
    run_analyze_doc,
    convert_to_markdown,
)


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
    # Try long filename first (3707001F), then short filename (3704001F)
    for prop_id in ("3707001F", "3704001F"):
        try:
            stream_path = f"{attach_dir}/__substg1.0_{prop_id}"
            data = ole.openstream(stream_path).read()
            return data.decode("utf-16-le").rstrip("\x00")
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

def process_comments(
    doc: Document,
    client_name: str,
    counterparty_name: str
) -> dict[str, list[dict[str, Any]]]:
    """
    Extract and categorize comments from a Word document.
    
    Groups comments by prefix:
    - "For {client_name}" -> client
    - "For {counterparty_name}" -> counterparty
    - Other -> other
    
    Each comment includes paragraph_text for full context.
    
    Args:
        doc: python-docx Document object
        client_name: Client short name (e.g., "Didimo")
        counterparty_name: Counterparty short name (e.g., "NBC")
        
    Returns:
        Dict with keys: 'client', 'counterparty', 'other'
    """
    comments = extract_all_comments(doc)
    paragraphs = list(iter_document_paragraphs(doc))
    
    client_prefix = f"For {client_name}"
    counterparty_prefix = f"For {counterparty_name}"
    
    categorized: dict[str, list[dict[str, Any]]] = {
        "client": [],
        "counterparty": [],
        "other": []
    }
    
    for comment in comments:
        # Add paragraph text if available
        para_idx = comment.get("paragraph_index")
        if para_idx is not None and 0 <= para_idx < len(paragraphs):
            comment["paragraph_text"] = paragraphs[para_idx].text
        else:
            comment["paragraph_text"] = "(N/A - comment in table/header)"
        
        # Categorize by prefix
        text = comment.get("text", "")
        if text.startswith(client_prefix):
            categorized["client"].append(comment)
        elif text.startswith(counterparty_prefix):
            categorized["counterparty"].append(comment)
        else:
            categorized["other"].append(comment)
    
    return categorized


# =============================================================================
# Track Changes Processing
# =============================================================================

def process_track_changes(doc: Document) -> list[dict[str, Any]]:
    """
    Extract tracked insertions and deletions from a Word document.
    
    Uses iter_amended_paragraphs to get runs with revision info.
    
    Args:
        doc: python-docx Document object
        
    Returns:
        List of change dicts with: type, text, author, date, paragraph_text
    """
    changes: list[dict[str, Any]] = []
    
    for amended_para in iter_amended_paragraphs(doc):
        paragraph_text = amended_para.amended_text
        
        for run in amended_para.amended_runs:
            formats = run.get("formats", [])
            
            if "insert" in formats:
                # Get the inserted text directly from the run
                inserted_text = run.get("text", "")
                
                if inserted_text.strip():
                    changes.append({
                        "type": "insertion",
                        "text": inserted_text,
                        "author": run.get("author", "Unknown"),
                        "date": run.get("date", ""),
                        "paragraph_text": paragraph_text
                    })
            
            elif "delete" in formats:
                deleted_text = run.get("deleted_text", "")
                
                if deleted_text.strip():
                    changes.append({
                        "type": "deletion",
                        "text": deleted_text,
                        "author": run.get("author", "Unknown"),
                        "date": run.get("date", ""),
                        "paragraph_text": paragraph_text
                    })
    
    return changes


# =============================================================================
# Markdown Generation
# =============================================================================

def generate_instructions_md(email_data: EmailData) -> str:
    """Generate markdown for client instructions email."""
    lines = [
        "# Client Instructions",
        "",
        f"**From:** {email_data.sender}",
        f"**To:** {email_data.recipients}",
        f"**Date:** {email_data.date}",
        f"**Subject:** {email_data.subject}",
        "",
        "---",
        "",
        "## Email Body",
        "",
        email_data.body or "(No body text)",
        "",
        "---",
        "",
        "## Attachments",
        ""
    ]
    
    for i, att in enumerate(email_data.attachments, 1):
        docx_marker = " *(original agreement)*" if att.is_docx else ""
        lines.append(f"{i}. {att.filename}{docx_marker}")
    
    return "\n".join(lines)


def generate_original_agreement_md(docx_bytes: bytes, source_name: str = "agreement") -> str:
    """
    Generate markdown with the full text of the original agreement.
    
    Uses docx_to_llm_markdown module to run analyze_doc and convert to markdown
    with proper clause numbering preserved.
    
    Args:
        docx_bytes: Raw docx file bytes
        source_name: Name for the document (used in output)
        
    Returns:
        Markdown string with agreement content including clause numbers
    """
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
            
            # Wrap with our header
            lines = [
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
    client_name: str,
    counterparty_name: str
) -> str:
    """Generate markdown for review comments grouped by recipient."""
    lines = [
        "# Review Comments",
        ""
    ]
    
    # Client comments section
    lines.extend([
        f"## For {client_name} (Client)",
        ""
    ])
    
    client_comments = categorized_comments.get("client", [])
    if client_comments:
        for i, comment in enumerate(client_comments, 1):
            lines.extend(_format_comment(i, comment))
    else:
        lines.append("*No comments for client.*")
        lines.append("")
    
    # Counterparty comments section
    lines.extend([
        "---",
        "",
        f"## For {counterparty_name} (Counterparty)",
        ""
    ])
    
    counterparty_comments = categorized_comments.get("counterparty", [])
    if counterparty_comments:
        for i, comment in enumerate(counterparty_comments, 1):
            lines.extend(_format_comment(i, comment))
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
            lines.extend(_format_comment(i, comment))
    
    return "\n".join(lines)


def _format_comment(index: int, comment: dict[str, Any]) -> list[str]:
    """Format a single comment as markdown lines."""
    author = comment.get("author", "Unknown")
    date = comment.get("date", "")
    text = comment.get("text", "")
    reference_text = comment.get("reference_text", "")
    paragraph_text = comment.get("paragraph_text", "")
    
    lines = [
        f"### Comment {index}",
        f"**Author:** {author} | **Date:** {date}",
        "",
        f"> {text}",
        ""
    ]
    
    if reference_text:
        lines.extend([
            f"**Referenced text:** \"{reference_text}\"",
            ""
        ])
    
    if paragraph_text and paragraph_text != "(N/A - comment in table/header)":
        # Quote each line of the paragraph
        para_lines = paragraph_text.split("\n")
        lines.append("**Full paragraph:**")
        for para_line in para_lines:
            lines.append(f"> {para_line}")
        lines.append("")
    
    lines.extend(["---", ""])
    
    return lines


def generate_track_changes_md(changes: list[dict[str, Any]]) -> str:
    """Generate markdown for tracked insertions and deletions."""
    lines = [
        "# Tracked Changes",
        ""
    ]
    
    insertions = [c for c in changes if c["type"] == "insertion"]
    deletions = [c for c in changes if c["type"] == "deletion"]
    
    # Insertions section
    lines.extend([
        "## Insertions",
        ""
    ])
    
    if insertions:
        for i, change in enumerate(insertions, 1):
            lines.extend(_format_change(i, change))
    else:
        lines.append("*No insertions found.*")
        lines.append("")
    
    # Deletions section
    lines.extend([
        "---",
        "",
        "## Deletions",
        ""
    ])
    
    if deletions:
        for i, change in enumerate(deletions, 1):
            lines.extend(_format_change(i, change))
    else:
        lines.append("*No deletions found.*")
        lines.append("")
    
    return "\n".join(lines)


def _format_change(index: int, change: dict[str, Any]) -> list[str]:
    """Format a single track change as markdown lines."""
    change_type = change["type"].capitalize()
    text = change.get("text", "")
    author = change.get("author", "Unknown")
    date = change.get("date", "")
    paragraph_text = change.get("paragraph_text", "")
    
    lines = [
        f"### {change_type} {index}",
        f"**Author:** {author} | **Date:** {date}",
        "",
        f"**{'Added' if change['type'] == 'insertion' else 'Removed'} text:** \"{text}\"",
        ""
    ]
    
    if paragraph_text:
        lines.append("**Context paragraph:**")
        for para_line in paragraph_text.split("\n"):
            lines.append(f"> {para_line}")
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


def generate_advice_note_md(email_data: EmailData) -> str:
    """Generate markdown for the advice note email."""
    # Extract only the first email from the thread (not the reply chain)
    body = extract_first_email_from_thread(email_data.body) if email_data.body else "(No body text)"
    
    lines = [
        "# Advice Note",
        "",
        f"**From:** {email_data.sender}",
        f"**To:** {email_data.recipients}",
        f"**Date:** {email_data.date}",
        f"**Subject:** {email_data.subject}",
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


def generate_single_file_md(
    instructions_md: str,
    original_md: str,
    comments_md: str,
    track_changes_md: str,
    advice_md: str
) -> str:
    """Combine all markdown sections into a single file."""
    sections = [
        instructions_md,
        "\n\n" + "=" * 80 + "\n\n",
        original_md,
        "\n\n" + "=" * 80 + "\n\n",
        comments_md,
        "\n\n" + "=" * 80 + "\n\n",
        track_changes_md,
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
    client_name: str,
    counterparty_name: str,
    output_dir: Path,
    original_index: int | None = None,
    edited_index: int | None = None,
    single_file: bool = False
) -> None:
    """
    Generate legal review example markdown files.
    
    Args:
        incoming_path: Path to incoming .msg with instructions
        outgoing_path: Path to outgoing .msg with advice
        client_name: Client short name (e.g., "Didimo")
        counterparty_name: Counterparty short name (e.g., "NBC")
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
    
    # Load edited document for comments and track changes
    edited_doc = Document(BytesIO(edited_attachment.data))
    
    # Process comments and track changes
    print("\nProcessing comments...")
    categorized_comments = process_comments(edited_doc, client_name, counterparty_name)
    client_count = len(categorized_comments["client"])
    counterparty_count = len(categorized_comments["counterparty"])
    print(f"  Found: {client_count} for {client_name}, {counterparty_count} for {counterparty_name}")
    
    print("Processing track changes...")
    track_changes = process_track_changes(edited_doc)
    insertions = len([c for c in track_changes if c["type"] == "insertion"])
    deletions = len([c for c in track_changes if c["type"] == "deletion"])
    print(f"  Found: {insertions} insertions, {deletions} deletions")
    
    # Generate markdown
    print("\nGenerating markdown files...")
    instructions_md = generate_instructions_md(incoming_email)
    original_md = generate_original_agreement_md(
        original_attachment.data, 
        source_name=original_attachment.filename.replace(".docx", "")
    )
    comments_md = generate_comments_md(categorized_comments, client_name, counterparty_name)
    track_changes_md = generate_track_changes_md(track_changes)
    advice_md = generate_advice_note_md(outgoing_email)
    
    # Write output
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if single_file:
        combined_md = generate_single_file_md(
            instructions_md, original_md, comments_md, track_changes_md, advice_md
        )
        output_file = output_dir / "review_example.md"
        output_file.write_text(combined_md, encoding="utf-8")
        print(f"\nGenerated: {output_file}")
    else:
        files = [
            ("01_instructions.md", instructions_md),
            ("02_original_agreement.md", original_md),
            ("03_review_comments.md", comments_md),
            ("04_tracked_changes.md", track_changes_md),
            ("05_advice_note.md", advice_md)
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
      --outgoing advice.msg \\
      --client "Didimo" \\
      --counterparty "NBC"
  
  # With preselected indices (for scripted use)
  python scripts/generate_review_example.py \\
      --incoming instructions.msg \\
      --outgoing advice.msg \\
      --client "Didimo" \\
      --counterparty "NBC" \\
      --original-index 1 \\
      --edited-index 1
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
        "--client",
        required=True,
        help="Client short name (e.g., 'Didimo')"
    )
    parser.add_argument(
        "--counterparty",
        required=True,
        help="Counterparty short name (e.g., 'NBC')"
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
            client_name=args.client,
            counterparty_name=args.counterparty,
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
