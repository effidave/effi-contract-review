#!/usr/bin/env python3
"""
Comprehensive tests for generate_review_example.py script.

These tests verify the complete workflow of extracting legal review examples
from email + document pairs, including:
- Email parsing and attachment extraction
- Comment categorization by recipient
- Track changes extraction
- Markdown generation
"""

import tempfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from docx import Document

# Test data paths
TEST_DATA_DIR = Path(__file__).parent.parent / "EL_Precedents" / "analysis" / "quick_contract_review"
INSTRUCTIONS_MSG = TEST_DATA_DIR / "email_instructions.msg"
ADVICE_MSG = TEST_DATA_DIR / "email_advice.msg"


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_msg_paths() -> tuple[Path, Path]:
    """Return paths to sample MSG files for integration tests."""
    return INSTRUCTIONS_MSG, ADVICE_MSG


@pytest.fixture
def temp_output_dir() -> Path:
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# =============================================================================
# Tests for EmailData dataclass
# =============================================================================

class TestEmailData:
    """Tests for EmailData dataclass structure."""
    
    def test_email_data_has_required_fields(self) -> None:
        """EmailData should have subject, sender, recipients, date, body, attachments."""
        from scripts.generate_review_example import EmailData
        
        email = EmailData(
            subject="Test Subject",
            sender="sender@test.com",
            recipients="recipient@test.com",
            date="2025-12-01",
            body="Test body",
            attachments=[]
        )
        
        assert email.subject == "Test Subject"
        assert email.sender == "sender@test.com"
        assert email.recipients == "recipient@test.com"
        assert email.date == "2025-12-01"
        assert email.body == "Test body"
        assert email.attachments == []


# =============================================================================
# Tests for Attachment dataclass
# =============================================================================

class TestAttachment:
    """Tests for Attachment dataclass structure."""
    
    def test_attachment_has_filename_and_data(self) -> None:
        """Attachment should have filename and binary data."""
        from scripts.generate_review_example import Attachment
        
        attachment = Attachment(
            filename="test.docx",
            data=b"test data"
        )
        
        assert attachment.filename == "test.docx"
        assert attachment.data == b"test data"
    
    def test_attachment_is_docx_property(self) -> None:
        """Attachment should have is_docx property."""
        from scripts.generate_review_example import Attachment
        
        docx_att = Attachment(filename="test.docx", data=b"")
        pdf_att = Attachment(filename="test.pdf", data=b"")
        
        assert docx_att.is_docx is True
        assert pdf_att.is_docx is False


# =============================================================================
# Tests for parse_msg_file function
# =============================================================================

class TestParseMsgFile:
    """Tests for parsing Outlook MSG files."""
    
    def test_parse_msg_file_returns_email_data(self, sample_msg_paths: tuple[Path, Path]) -> None:
        """parse_msg_file should return EmailData with populated fields."""
        from scripts.generate_review_example import parse_msg_file
        
        instructions_path, _ = sample_msg_paths
        email_data = parse_msg_file(instructions_path)
        
        assert email_data.subject is not None
        assert len(email_data.subject) > 0
        assert email_data.sender is not None
        assert email_data.body is not None
    
    def test_parse_msg_file_extracts_docx_attachments(self, sample_msg_paths: tuple[Path, Path]) -> None:
        """parse_msg_file should extract .docx attachments with data."""
        from scripts.generate_review_example import parse_msg_file
        
        instructions_path, _ = sample_msg_paths
        email_data = parse_msg_file(instructions_path)
        
        docx_attachments = [a for a in email_data.attachments if a.is_docx]
        
        assert len(docx_attachments) >= 1
        assert docx_attachments[0].data is not None
        assert len(docx_attachments[0].data) > 0
    
    def test_parse_msg_file_raises_for_nonexistent_file(self) -> None:
        """parse_msg_file should raise FileNotFoundError for missing files."""
        from scripts.generate_review_example import parse_msg_file
        
        with pytest.raises(FileNotFoundError):
            parse_msg_file(Path("/nonexistent/file.msg"))


# =============================================================================
# Tests for select_docx_attachment function
# =============================================================================

class TestSelectDocxAttachment:
    """Tests for selecting .docx attachments from email."""
    
    def test_auto_selects_single_docx(self) -> None:
        """Should auto-select when only one .docx attachment exists."""
        from scripts.generate_review_example import Attachment, select_docx_attachment
        
        attachments = [
            Attachment(filename="image.png", data=b"png"),
            Attachment(filename="contract.docx", data=b"docx"),
        ]
        
        selected = select_docx_attachment(attachments, "Select document:")
        
        assert selected.filename == "contract.docx"
    
    def test_uses_provided_index(self) -> None:
        """Should use preselected_index when provided."""
        from scripts.generate_review_example import Attachment, select_docx_attachment
        
        attachments = [
            Attachment(filename="first.docx", data=b"1"),
            Attachment(filename="second.docx", data=b"2"),
        ]
        
        selected = select_docx_attachment(attachments, "Select:", preselected_index=2)
        
        assert selected.filename == "second.docx"
    
    def test_raises_when_no_docx_attachments(self) -> None:
        """Should raise ValueError when no .docx attachments exist."""
        from scripts.generate_review_example import Attachment, select_docx_attachment
        
        attachments = [
            Attachment(filename="image.png", data=b"png"),
        ]
        
        with pytest.raises(ValueError, match="No .docx attachments found"):
            select_docx_attachment(attachments, "Select:")


# =============================================================================
# Tests for process_comments function
# =============================================================================

class TestProcessComments:
    """Tests for extracting and categorizing comments."""
    
    def test_groups_comments_by_client_prefix(self, sample_msg_paths: tuple[Path, Path]) -> None:
        """Comments starting with 'For {client}' should be in client group."""
        from scripts.generate_review_example import parse_msg_file, process_comments, select_docx_attachment
        
        _, advice_path = sample_msg_paths
        email_data = parse_msg_file(advice_path)
        docx_att = select_docx_attachment(email_data.attachments, "Select:")
        doc = Document(BytesIO(docx_att.data))
        
        categorized = process_comments(doc, client_name="Didimo", counterparty_name="NBC")
        
        assert "client" in categorized
        assert "counterparty" in categorized
        assert len(categorized["client"]) > 0
        
        # All client comments should start with "For Didimo"
        for comment in categorized["client"]:
            assert comment["text"].startswith("For Didimo")
    
    def test_groups_comments_by_counterparty_prefix(self, sample_msg_paths: tuple[Path, Path]) -> None:
        """Comments starting with 'For {counterparty}' should be in counterparty group."""
        from scripts.generate_review_example import parse_msg_file, process_comments, select_docx_attachment
        
        _, advice_path = sample_msg_paths
        email_data = parse_msg_file(advice_path)
        docx_att = select_docx_attachment(email_data.attachments, "Select:")
        doc = Document(BytesIO(docx_att.data))
        
        categorized = process_comments(doc, client_name="Didimo", counterparty_name="NBC")
        
        assert len(categorized["counterparty"]) > 0
        
        # All counterparty comments should start with "For NBC"
        for comment in categorized["counterparty"]:
            assert comment["text"].startswith("For NBC")
    
    def test_includes_paragraph_text_in_comments(self, sample_msg_paths: tuple[Path, Path]) -> None:
        """Each comment should include full paragraph text."""
        from scripts.generate_review_example import parse_msg_file, process_comments, select_docx_attachment
        
        _, advice_path = sample_msg_paths
        email_data = parse_msg_file(advice_path)
        docx_att = select_docx_attachment(email_data.attachments, "Select:")
        doc = Document(BytesIO(docx_att.data))
        
        categorized = process_comments(doc, client_name="Didimo", counterparty_name="NBC")
        
        # Check at least one comment has paragraph_text
        all_comments = categorized["client"] + categorized["counterparty"] + categorized.get("other", [])
        comments_with_para_text = [c for c in all_comments if c.get("paragraph_text")]
        
        assert len(comments_with_para_text) > 0


# =============================================================================
# Tests for process_track_changes function
# =============================================================================

class TestProcessTrackChanges:
    """Tests for extracting tracked insertions and deletions."""
    
    def test_returns_list_of_changes(self, sample_msg_paths: tuple[Path, Path]) -> None:
        """process_track_changes should return a list of change dictionaries."""
        from scripts.generate_review_example import parse_msg_file, process_track_changes, select_docx_attachment
        
        _, advice_path = sample_msg_paths
        email_data = parse_msg_file(advice_path)
        docx_att = select_docx_attachment(email_data.attachments, "Select:")
        doc = Document(BytesIO(docx_att.data))
        
        changes = process_track_changes(doc)
        
        assert isinstance(changes, list)
    
    def test_change_has_required_fields(self, sample_msg_paths: tuple[Path, Path]) -> None:
        """Each change should have type, text, author, paragraph_text."""
        from scripts.generate_review_example import parse_msg_file, process_track_changes, select_docx_attachment
        
        _, advice_path = sample_msg_paths
        email_data = parse_msg_file(advice_path)
        docx_att = select_docx_attachment(email_data.attachments, "Select:")
        doc = Document(BytesIO(docx_att.data))
        
        changes = process_track_changes(doc)
        
        if len(changes) > 0:
            change = changes[0]
            assert "type" in change
            assert change["type"] in ("insertion", "deletion")
            assert "text" in change
            assert "paragraph_text" in change


# =============================================================================
# Tests for markdown generation functions
# =============================================================================

class TestGenerateInstructionsMd:
    """Tests for instructions markdown generation."""
    
    def test_includes_email_metadata(self) -> None:
        """Generated markdown should include From, To, Date, Subject."""
        from scripts.generate_review_example import Attachment, EmailData, generate_instructions_md
        
        email_data = EmailData(
            subject="Review Contract",
            sender="client@example.com",
            recipients="lawyer@example.com",
            date="2025-12-01",
            body="Please review attached.",
            attachments=[Attachment(filename="contract.docx", data=b"")]
        )
        
        markdown = generate_instructions_md(email_data)
        
        assert "client@example.com" in markdown
        assert "lawyer@example.com" in markdown
        assert "2025-12-01" in markdown
        assert "Review Contract" in markdown
    
    def test_includes_email_body(self) -> None:
        """Generated markdown should include email body text."""
        from scripts.generate_review_example import Attachment, EmailData, generate_instructions_md
        
        email_data = EmailData(
            subject="Subject",
            sender="sender@test.com",
            recipients="recipient@test.com",
            date="2025-12-01",
            body="This is the email body with instructions.",
            attachments=[]
        )
        
        markdown = generate_instructions_md(email_data)
        
        assert "This is the email body with instructions" in markdown


class TestGenerateCommentsMd:
    """Tests for comments markdown generation."""
    
    def test_separates_client_and_counterparty_sections(self) -> None:
        """Should have separate sections for client and counterparty comments."""
        from scripts.generate_review_example import generate_comments_md
        
        categorized_comments = {
            "client": [{"text": "For Client: note", "author": "Lawyer", "date": "2025-12-01", 
                       "reference_text": "ref", "paragraph_text": "para"}],
            "counterparty": [{"text": "For Counter: note", "author": "Lawyer", "date": "2025-12-01",
                             "reference_text": "ref", "paragraph_text": "para"}],
            "other": []
        }
        
        markdown = generate_comments_md(categorized_comments, "Client", "Counter")
        
        assert "For Client" in markdown
        assert "For Counter" in markdown
    
    def test_includes_reference_text_and_paragraph(self) -> None:
        """Each comment should show reference text and full paragraph."""
        from scripts.generate_review_example import generate_comments_md
        
        categorized_comments = {
            "client": [{
                "text": "For Client: important note",
                "author": "Lawyer",
                "date": "2025-12-01",
                "reference_text": "the specific phrase",
                "paragraph_text": "This is the full paragraph containing the specific phrase here."
            }],
            "counterparty": [],
            "other": []
        }
        
        markdown = generate_comments_md(categorized_comments, "Client", "Counter")
        
        assert "the specific phrase" in markdown
        assert "This is the full paragraph" in markdown


class TestGenerateTrackChangesMd:
    """Tests for track changes markdown generation."""
    
    def test_separates_insertions_and_deletions(self) -> None:
        """Should have separate sections for insertions and deletions."""
        from scripts.generate_review_example import generate_track_changes_md
        
        changes = [
            {"type": "insertion", "text": "added text", "author": "Lawyer", 
             "date": "2025-12-01", "paragraph_text": "context"},
            {"type": "deletion", "text": "removed text", "author": "Lawyer",
             "date": "2025-12-01", "paragraph_text": "context"}
        ]
        
        markdown = generate_track_changes_md(changes)
        
        assert "Insertion" in markdown or "insertion" in markdown.lower()
        assert "Deletion" in markdown or "deletion" in markdown.lower()


class TestGenerateAdviceNoteMd:
    """Tests for advice note markdown generation."""
    
    def test_includes_email_metadata(self) -> None:
        """Generated markdown should include email metadata."""
        from scripts.generate_review_example import Attachment, EmailData, generate_advice_note_md
        
        email_data = EmailData(
            subject="RE: Review Contract",
            sender="lawyer@example.com",
            recipients="client@example.com",
            date="2025-12-02",
            body="Please find my comments attached.",
            attachments=[]
        )
        
        markdown = generate_advice_note_md(email_data)
        
        assert "lawyer@example.com" in markdown
        assert "client@example.com" in markdown
        assert "RE: Review Contract" in markdown


# =============================================================================
# Tests for main workflow
# =============================================================================

class TestMainWorkflow:
    """Integration tests for the complete workflow."""
    
    def test_generates_all_output_files(
        self, sample_msg_paths: tuple[Path, Path], temp_output_dir: Path
    ) -> None:
        """Main function should generate all 5 output files."""
        from scripts.generate_review_example import generate_review_example
        
        instructions_path, advice_path = sample_msg_paths
        
        generate_review_example(
            incoming_path=instructions_path,
            outgoing_path=advice_path,
            client_name="Didimo",
            counterparty_name="NBC",
            output_dir=temp_output_dir
        )
        
        expected_files = [
            "01_instructions.md",
            "02_original_agreement.md",
            "03_review_comments.md",
            "04_tracked_changes.md",
            "05_advice_note.md"
        ]
        
        for filename in expected_files:
            output_file = temp_output_dir / filename
            assert output_file.exists(), f"Expected {filename} to be created"
            assert output_file.stat().st_size > 0, f"Expected {filename} to have content"
    
    def test_original_agreement_contains_document_text(
        self, sample_msg_paths: tuple[Path, Path], temp_output_dir: Path
    ) -> None:
        """02_original_agreement.md should contain document text."""
        from scripts.generate_review_example import generate_review_example
        
        instructions_path, advice_path = sample_msg_paths
        
        generate_review_example(
            incoming_path=instructions_path,
            outgoing_path=advice_path,
            client_name="Didimo",
            counterparty_name="NBC",
            output_dir=temp_output_dir
        )
        
        original_md = (temp_output_dir / "02_original_agreement.md").read_text(encoding="utf-8")
        
        # Should contain some agreement-related content
        assert len(original_md) > 100
    
    def test_comments_file_has_correct_grouping(
        self, sample_msg_paths: tuple[Path, Path], temp_output_dir: Path
    ) -> None:
        """03_review_comments.md should have For Didimo and For NBC sections."""
        from scripts.generate_review_example import generate_review_example
        
        instructions_path, advice_path = sample_msg_paths
        
        generate_review_example(
            incoming_path=instructions_path,
            outgoing_path=advice_path,
            client_name="Didimo",
            counterparty_name="NBC",
            output_dir=temp_output_dir
        )
        
        comments_md = (temp_output_dir / "03_review_comments.md").read_text(encoding="utf-8")
        
        assert "Didimo" in comments_md
        assert "NBC" in comments_md


# =============================================================================
# Tests for CLI argument parsing
# =============================================================================

class TestCLIArgumentParsing:
    """Tests for command-line argument parsing."""
    
    def test_required_arguments(self) -> None:
        """CLI should require --incoming, --outgoing, --client, --counterparty."""
        from scripts.generate_review_example import create_argument_parser
        
        parser = create_argument_parser()
        
        # Should raise on missing required args
        with pytest.raises(SystemExit):
            parser.parse_args([])
    
    def test_optional_index_arguments(self) -> None:
        """CLI should accept optional --original-index and --edited-index."""
        from scripts.generate_review_example import create_argument_parser
        
        parser = create_argument_parser()
        
        args = parser.parse_args([
            "--incoming", "in.msg",
            "--outgoing", "out.msg",
            "--client", "Client",
            "--counterparty", "Counter",
            "--original-index", "1",
            "--edited-index", "2"
        ])
        
        assert args.original_index == 1
        assert args.edited_index == 2
    
    def test_optional_single_file_flag(self) -> None:
        """CLI should accept --single-file flag."""
        from scripts.generate_review_example import create_argument_parser
        
        parser = create_argument_parser()
        
        args = parser.parse_args([
            "--incoming", "in.msg",
            "--outgoing", "out.msg",
            "--client", "Client",
            "--counterparty", "Counter",
            "--single-file"
        ])
        
        assert args.single_file is True
