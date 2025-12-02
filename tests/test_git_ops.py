"""Tests for git operations module."""

from __future__ import annotations

import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from effilocal.util.git_ops import (
    CommitInfo,
    auto_commit,
    generate_commit_message,
    get_effi_commits,
    get_file_history,
    get_repo_root,
    has_changes,
    is_git_repo,
)


@pytest.fixture
def temp_git_repo() -> Path:
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path, check=True, capture_output=True
        )
        
        yield repo_path


@pytest.fixture
def repo_with_file(temp_git_repo: Path) -> tuple[Path, Path]:
    """Create a repo with an initial committed file."""
    repo_path = temp_git_repo
    file_path = repo_path / "test.txt"
    file_path.write_text("Initial content")
    
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path, check=True, capture_output=True
    )
    
    return repo_path, file_path


class TestIsGitRepo:
    """Tests for is_git_repo function."""

    def test_valid_repo(self, temp_git_repo: Path):
        """Test detection of valid git repo."""
        assert is_git_repo(temp_git_repo) is True

    def test_not_a_repo(self):
        """Test non-repo directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert is_git_repo(Path(tmpdir)) is False


class TestGetRepoRoot:
    """Tests for get_repo_root function."""

    def test_find_root(self, temp_git_repo: Path):
        """Test finding repo root."""
        root = get_repo_root(temp_git_repo)
        assert root is not None
        # Compare resolved paths to handle Windows short path names
        assert root.resolve() == temp_git_repo.resolve()

    def test_find_root_from_subdir(self, temp_git_repo: Path):
        """Test finding repo root from subdirectory."""
        subdir = temp_git_repo / "subdir"
        subdir.mkdir()
        
        root = get_repo_root(subdir)
        assert root is not None
        # Compare resolved paths to handle Windows short path names
        assert root.resolve() == temp_git_repo.resolve()

    def test_no_root_outside_repo(self):
        """Test that None is returned outside a repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = get_repo_root(Path(tmpdir))
            assert root is None


class TestHasChanges:
    """Tests for has_changes function."""

    def test_no_changes_after_commit(self, repo_with_file: tuple[Path, Path]):
        """Test no changes reported after clean commit."""
        repo_path, file_path = repo_with_file
        assert has_changes(repo_path) is False

    def test_has_changes_after_modify(self, repo_with_file: tuple[Path, Path]):
        """Test changes detected after file modification."""
        repo_path, file_path = repo_with_file
        file_path.write_text("Modified content")
        assert has_changes(repo_path) is True

    def test_has_changes_specific_file(self, repo_with_file: tuple[Path, Path]):
        """Test changes for specific file."""
        repo_path, file_path = repo_with_file
        other_file = repo_path / "other.txt"
        other_file.write_text("New file")
        
        # file_path has no changes
        assert has_changes(repo_path, files=[file_path]) is False
        # other_file has changes
        assert has_changes(repo_path, files=[other_file]) is True


class TestAutoCommit:
    """Tests for auto_commit function."""

    def test_commit_new_file(self, repo_with_file: tuple[Path, Path]):
        """Test committing a new file."""
        repo_path, _ = repo_with_file
        new_file = repo_path / "new.txt"
        new_file.write_text("New content")
        
        commit_hash = auto_commit(repo_path, "Add new file", files=[new_file])
        
        assert commit_hash is not None
        assert len(commit_hash) == 40  # Full SHA

    def test_no_commit_when_no_changes(self, repo_with_file: tuple[Path, Path]):
        """Test that no commit happens when there are no changes."""
        repo_path, _ = repo_with_file
        
        commit_hash = auto_commit(repo_path, "Empty commit")
        
        assert commit_hash is None

    def test_commit_message_used(self, repo_with_file: tuple[Path, Path]):
        """Test that provided commit message is used."""
        repo_path, file_path = repo_with_file
        file_path.write_text("Modified")
        
        message = "[effi] test: custom message"
        auto_commit(repo_path, message, files=[file_path])
        
        # Check commit message
        result = subprocess.run(
            ["git", "log", "-1", "--format=%s"],
            cwd=repo_path, capture_output=True, text=True, check=True
        )
        assert result.stdout.strip() == message


class TestGenerateCommitMessage:
    """Tests for generate_commit_message function."""

    def test_analyze_action(self):
        """Test message for analyze action."""
        msg = generate_commit_message("analyze", {"document_name": "contract.docx"})
        assert "[effi]" in msg
        assert "analyze" in msg
        assert "contract.docx" in msg

    def test_edit_action(self):
        """Test message for edit action."""
        msg = generate_commit_message("edit", {"document_name": "doc.docx", "changes": "updated clause 5"})
        assert "[effi]" in msg
        assert "edit" in msg
        assert "updated clause 5" in msg

    def test_checkpoint_action(self):
        """Test message for checkpoint action."""
        msg = generate_commit_message("checkpoint", {"document_name": "doc.docx", "note": "milestone reached"})
        assert "[effi]" in msg
        assert "checkpoint" in msg
        assert "milestone reached" in msg

    def test_save_action(self):
        """Test message for save action."""
        msg = generate_commit_message("save", {"document_name": "doc.docx"})
        assert "[effi]" in msg
        assert "save" in msg


class TestGetFileHistory:
    """Tests for get_file_history function."""

    def test_empty_history(self, temp_git_repo: Path):
        """Test history for non-existent file."""
        history = get_file_history(temp_git_repo, temp_git_repo / "nonexistent.txt")
        assert history == []

    def test_single_commit(self, repo_with_file: tuple[Path, Path]):
        """Test history with single commit."""
        repo_path, file_path = repo_with_file
        history = get_file_history(repo_path, file_path)
        
        assert len(history) == 1
        assert isinstance(history[0], CommitInfo)
        assert "Initial commit" in history[0].message

    def test_multiple_commits(self, repo_with_file: tuple[Path, Path]):
        """Test history with multiple commits."""
        repo_path, file_path = repo_with_file
        
        # Add more commits
        for i in range(3):
            file_path.write_text(f"Content {i}")
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", f"Update {i}"],
                cwd=repo_path, check=True, capture_output=True
            )
        
        history = get_file_history(repo_path, file_path)
        
        assert len(history) == 4  # Initial + 3 updates

    def test_max_commits_limit(self, repo_with_file: tuple[Path, Path]):
        """Test max_commits parameter."""
        repo_path, file_path = repo_with_file
        
        # Add many commits
        for i in range(10):
            file_path.write_text(f"Content {i}")
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", f"Update {i}"],
                cwd=repo_path, check=True, capture_output=True
            )
        
        history = get_file_history(repo_path, file_path, max_commits=5)
        
        assert len(history) == 5


class TestGetEffiCommits:
    """Tests for get_effi_commits function."""

    def test_filter_effi_commits(self, repo_with_file: tuple[Path, Path]):
        """Test filtering commits by effi prefix."""
        repo_path, file_path = repo_with_file
        
        # Add mixed commits
        for i, msg in enumerate([
            "[effi] save: doc1.docx",
            "Regular commit",
            "[effi] analyze: doc2.docx",
            "Another regular",
        ]):
            file_path.write_text(f"Content {i}")
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", msg],
                cwd=repo_path, check=True, capture_output=True
            )
        
        effi_commits = get_effi_commits(repo_path)
        
        # Filter to only include effi commits
        effi_commits = [c for c in effi_commits if "[effi]" in c.message]
        assert len(effi_commits) == 2
        for commit in effi_commits:
            assert "[effi]" in commit.message


class TestCommitInfo:
    """Tests for CommitInfo dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.now()
        info = CommitInfo(
            hash="abc123def456",
            short_hash="abc123d",
            author="Test User",
            date=now,
            message="Test commit"
        )
        
        d = info.to_dict()
        
        assert d["hash"] == "abc123def456"
        assert d["short_hash"] == "abc123d"
        assert d["author"] == "Test User"
        assert d["message"] == "Test commit"
        assert "date" in d
