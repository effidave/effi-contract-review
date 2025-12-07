"""
Email parsing utilities for Outlook MSG files.

This module provides classes for parsing Outlook MSG files and extracting
metadata, body text, and attachments. Uses a hybrid approach: extract_msg
for metadata and olefile for reliable attachment extraction.

Typical usage:
    from effilocal.doc.email_parser import MsgParser, EmailMessage
    
    # Parse an MSG file
    email = MsgParser.parse("path/to/email.msg")
    
    # Access properties
    print(email.subject)
    print(email.body)
    
    # Get docx attachments
    for attachment in email.docx_attachments:
        print(attachment.filename)
        doc = Document(BytesIO(attachment.data))
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterator

import extract_msg
import olefile


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class Attachment:
    """
    Represents an email attachment with filename and binary data.
    
    Attributes:
        filename: The attachment filename
        data: Raw binary data of the attachment
    """
    
    filename: str
    data: bytes
    
    @property
    def is_docx(self) -> bool:
        """Return True if this attachment is a .docx file."""
        return self.filename.lower().endswith(".docx")
    
    @property
    def is_pdf(self) -> bool:
        """Return True if this attachment is a PDF file."""
        return self.filename.lower().endswith(".pdf")
    
    @property
    def extension(self) -> str:
        """Return the file extension (lowercase, including the dot)."""
        if "." in self.filename:
            return "." + self.filename.rsplit(".", 1)[-1].lower()
        return ""
    
    def to_bytes_io(self) -> BytesIO:
        """Return attachment data as a BytesIO object for reading."""
        return BytesIO(self.data)


@dataclass
class EmailMessage:
    """
    Represents a parsed email message with metadata and attachments.
    
    This is an immutable data class that holds the parsed contents of an
    email. Use MsgParser.parse() to create instances.
    
    Attributes:
        subject: Email subject line
        sender: Sender email address or name
        recipients: Recipient(s) as a string
        date: Date string from the email
        body: Plain text body of the email
        attachments: List of Attachment objects
    """
    
    subject: str
    sender: str
    recipients: str
    date: str
    body: str
    attachments: list[Attachment]
    
    @property
    def docx_attachments(self) -> list[Attachment]:
        """Return only .docx attachments."""
        return [a for a in self.attachments if a.is_docx]
    
    @property
    def has_docx(self) -> bool:
        """Return True if the email has at least one .docx attachment."""
        return any(a.is_docx for a in self.attachments)
    
    def get_attachment_by_name(self, filename: str) -> Attachment | None:
        """
        Find an attachment by filename (case-insensitive).
        
        Args:
            filename: The filename to search for
            
        Returns:
            The matching Attachment, or None if not found
        """
        filename_lower = filename.lower()
        for attachment in self.attachments:
            if attachment.filename.lower() == filename_lower:
                return attachment
        return None
    
    def iter_attachments_by_extension(self, extension: str) -> Iterator[Attachment]:
        """
        Iterate over attachments with a specific extension.
        
        Args:
            extension: File extension (with or without leading dot)
            
        Yields:
            Matching Attachment objects
        """
        ext = extension.lower()
        if not ext.startswith("."):
            ext = "." + ext
        for attachment in self.attachments:
            if attachment.extension == ext:
                yield attachment


# =============================================================================
# Parser Class
# =============================================================================


class MsgParser:
    """
    Parser for Outlook MSG files.
    
    Uses extract_msg for metadata extraction and olefile for reliable
    attachment parsing, since extract_msg fails on some non-standard
    MSG files with unusual attachment properties.
    
    Usage:
        email = MsgParser.parse("email.msg")
        
        # Or create an instance for multiple operations
        parser = MsgParser("email.msg")
        email = parser.parse_message()
    """
    
    # OLE property IDs for attachment data
    PROP_LONG_FILENAME = "3707"   # Long filename
    PROP_SHORT_FILENAME = "3704"  # Short filename (fallback)
    PROP_ATTACHMENT_DATA = "37010102"  # Binary attachment data
    
    # Property type suffixes
    PROP_UTF16 = "001F"  # UTF-16LE encoded
    PROP_ANSI = "001E"   # ANSI/Latin-1 encoded
    
    def __init__(self, msg_path: str | Path) -> None:
        """
        Initialize parser with path to MSG file.
        
        Args:
            msg_path: Path to the .msg file
            
        Raises:
            FileNotFoundError: If the MSG file doesn't exist
        """
        self.path = Path(msg_path)
        if not self.path.exists():
            raise FileNotFoundError(f"MSG file not found: {self.path}")
    
    @classmethod
    def parse(cls, msg_path: str | Path) -> EmailMessage:
        """
        Parse an MSG file and return an EmailMessage.
        
        This is a convenience class method for one-off parsing.
        
        Args:
            msg_path: Path to the .msg file
            
        Returns:
            EmailMessage with parsed content
            
        Raises:
            FileNotFoundError: If the MSG file doesn't exist
        """
        parser = cls(msg_path)
        return parser.parse_message()
    
    def parse_message(self) -> EmailMessage:
        """
        Parse the MSG file and return an EmailMessage.
        
        Returns:
            EmailMessage with parsed content
        """
        # Extract metadata using extract_msg (with delayed attachments to avoid errors)
        msg = extract_msg.openMsg(str(self.path), delayAttachments=True)
        
        subject = msg.subject or ""
        sender = msg.sender or ""
        recipients = msg.to or ""
        date = str(msg.date) if msg.date else ""
        body = msg.body or ""
        
        # Extract attachments using olefile directly (more reliable)
        attachments = self._extract_attachments()
        
        return EmailMessage(
            subject=subject,
            sender=sender,
            recipients=recipients,
            date=date,
            body=body,
            attachments=attachments
        )
    
    def _extract_attachments(self) -> list[Attachment]:
        """
        Extract attachments from MSG file using olefile.
        
        This bypasses extract_msg's attachment parsing which fails on some
        MSG files with non-standard attachment properties.
        
        Returns:
            List of Attachment objects
        """
        ole = olefile.OleFileIO(str(self.path))
        attachments = []
        
        try:
            # Find all attachment directories
            attach_dirs = self._find_attachment_dirs(ole)
            
            for attach_dir in sorted(attach_dirs):
                filename = self._get_attachment_filename(ole, attach_dir)
                data = self._get_attachment_data(ole, attach_dir)
                
                if filename and data:
                    attachments.append(Attachment(filename=filename, data=data))
        finally:
            ole.close()
        
        return attachments
    
    def _find_attachment_dirs(self, ole: olefile.OleFileIO) -> set[str]:
        """Find all attachment directory names in the OLE structure."""
        attach_dirs: set[str] = set()
        for stream in ole.listdir():
            stream_path = "/".join(stream)
            if stream_path.startswith("__attach_version1.0_"):
                attach_dirs.add(stream[0])
        return attach_dirs
    
    def _get_attachment_filename(self, ole: olefile.OleFileIO, attach_dir: str) -> str | None:
        """
        Get attachment filename from MSG OLE stream.
        
        Tries long filename first (property 3707), then falls back to
        short filename (property 3704). Handles both UTF-16 and ANSI encodings.
        
        Args:
            ole: Open OleFileIO object
            attach_dir: Attachment directory name
            
        Returns:
            Filename string, or None if not found
        """
        # Try long filename first, then short filename
        for prop_base in (self.PROP_LONG_FILENAME, self.PROP_SHORT_FILENAME):
            # Try UTF-16 first, then ANSI
            for prop_suffix in (self.PROP_UTF16, self.PROP_ANSI):
                try:
                    stream_path = f"{attach_dir}/__substg1.0_{prop_base}{prop_suffix}"
                    data = ole.openstream(stream_path).read()
                    
                    if prop_suffix == self.PROP_UTF16:
                        return data.decode("utf-16-le").rstrip("\x00")
                    else:
                        return data.decode("latin-1").rstrip("\x00")
                except Exception:
                    continue
        
        return None
    
    def _get_attachment_data(self, ole: olefile.OleFileIO, attach_dir: str) -> bytes | None:
        """
        Get attachment binary data from MSG OLE stream.
        
        Args:
            ole: Open OleFileIO object
            attach_dir: Attachment directory name
            
        Returns:
            Binary data, or None if not found
        """
        try:
            stream_path = f"{attach_dir}/__substg1.0_{self.PROP_ATTACHMENT_DATA}"
            return ole.openstream(stream_path).read()
        except Exception:
            return None


# =============================================================================
# Utility Functions
# =============================================================================


def select_docx_attachment(
    attachments: list[Attachment],
    prompt_text: str = "Select a .docx attachment:",
    preselected_index: int | None = None
) -> Attachment:
    """
    Select a .docx attachment from a list.
    
    Behavior:
    - If single .docx: auto-select it
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


# Backward compatibility aliases
EmailData = EmailMessage  # Old name -> new name
parse_msg_file = MsgParser.parse  # Function -> class method
