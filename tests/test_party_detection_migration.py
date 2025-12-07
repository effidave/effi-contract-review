"""
Tests to verify test_party_detection.py uses refactored modules.

These tests ensure that the party detection tests import from
effilocal.doc.party_detection instead of scripts.generate_review_example.
"""

import ast
import pytest
from pathlib import Path


class TestPartyDetectionTestsUseRefactoredModule:
    """Verify test_party_detection.py imports from the correct location."""

    @pytest.fixture
    def test_file_path(self) -> Path:
        """Path to the test_party_detection.py file."""
        return Path(__file__).parent / "test_party_detection.py"

    @pytest.fixture
    def test_file_content(self, test_file_path: Path) -> str:
        """Content of test_party_detection.py."""
        return test_file_path.read_text(encoding="utf-8")

    @pytest.fixture
    def test_file_ast(self, test_file_content: str) -> ast.Module:
        """AST of test_party_detection.py."""
        return ast.parse(test_file_content)

    def test_file_exists(self, test_file_path: Path) -> None:
        """test_party_detection.py should exist."""
        assert test_file_path.exists()

    def test_does_not_import_party_detection_from_scripts(
        self, test_file_content: str
    ) -> None:
        """Party detection functions should NOT be imported from scripts.generate_review_example."""
        # These specific functions should come from effilocal.doc, not the script
        party_detection_functions = [
            "PartyInfo",
            "extract_defined_party_terms",
            "extract_company_names",
            "extract_full_company_names",
            "extract_comment_prefixes",
            "extract_party_from_comment_prefixes",
            "infer_party_role",
            "compute_similarity",
            "match_prefixes_to_parties",
            "get_role_placeholder",
        ]
        
        # Parse each line that imports from scripts.generate_review_example
        import re
        for line in test_file_content.split('\n'):
            if 'from scripts.generate_review_example import' in line:
                # Extract what's being imported on this line
                for func in party_detection_functions:
                    if func in line:
                        assert False, f"{func} should not be imported from scripts.generate_review_example on line: {line.strip()}"

    def test_does_not_import_anonymization_from_scripts(
        self, test_file_content: str
    ) -> None:
        """Anonymization functions should NOT be imported from scripts.generate_review_example."""
        anonymization_functions = [
            "anonymize_text",
            "generate_yaml_header",
        ]
        
        for line in test_file_content.split('\n'):
            if 'from scripts.generate_review_example import' in line:
                for func in anonymization_functions:
                    if func in line:
                        assert False, f"{func} should not be imported from scripts.generate_review_example on line: {line.strip()}"

    def test_imports_party_info_from_effilocal(self, test_file_content: str) -> None:
        """PartyInfo should be imported from effilocal.doc.party_detection."""
        assert "from effilocal.doc.party_detection import" in test_file_content or \
               "from effilocal.doc import" in test_file_content

    def test_imports_extract_functions_from_effilocal(
        self, test_file_content: str
    ) -> None:
        """Extract functions should be imported from effilocal.doc."""
        # Should have effilocal imports for party detection
        assert "effilocal.doc" in test_file_content

    def test_no_script_module_references_in_test_functions(
        self, test_file_ast: ast.Module
    ) -> None:
        """Test function bodies should not reference scripts.generate_review_example."""
        script_refs = []
        
        for node in ast.walk(test_file_ast):
            # Check for attribute access like scripts.generate_review_example.X
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Attribute):
                    if isinstance(node.value.value, ast.Name):
                        if node.value.value.id == "scripts":
                            script_refs.append(ast.dump(node))
            
            # Check for string literals containing the old path
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "scripts.generate_review_example" in node.value:
                    script_refs.append(node.value)
        
        assert len(script_refs) == 0, f"Found references to old script: {script_refs}"


class TestPartyDetectionTestsStillWork:
    """Verify party detection tests still pass after migration."""

    def test_party_info_importable_from_effilocal(self) -> None:
        """PartyInfo should be importable from effilocal.doc.party_detection."""
        from effilocal.doc.party_detection import PartyInfo
        assert PartyInfo is not None

    def test_party_info_has_expected_fields(self) -> None:
        """PartyInfo should have all expected fields."""
        from effilocal.doc.party_detection import PartyInfo
        
        info = PartyInfo(
            client_prefix="Acme",
            counterparty_prefix="Widget",
            client_defined_term="Customer",
            counterparty_defined_term="Supplier",
            original_provided_by="counterparty",
            client_role="customer",
            counterparty_role="supplier",
        )
        
        assert info.client_prefix == "Acme"
        assert info.counterparty_prefix == "Widget"
        assert info.client_defined_term == "Customer"
        assert info.counterparty_defined_term == "Supplier"
        assert info.original_provided_by == "counterparty"
        assert info.client_role == "customer"
        assert info.counterparty_role == "supplier"

    def test_extract_functions_importable_from_effilocal(self) -> None:
        """All extract functions should be importable from effilocal.doc."""
        from effilocal.doc.party_detection import (
            extract_defined_party_terms,
            extract_company_names,
            extract_full_company_names,
            extract_company_to_defined_term_mapping,
            extract_party_alternate_names,
            extract_party_from_comment_prefixes,
            compute_similarity,
            match_prefixes_to_parties,
            infer_party_role,
            get_role_placeholder,
            DEFINED_TERM_TO_ROLE,
        )
        
        assert callable(extract_defined_party_terms)
        assert callable(extract_company_names)
        assert callable(extract_full_company_names)
        assert callable(extract_company_to_defined_term_mapping)
        assert callable(extract_party_alternate_names)
        assert callable(extract_party_from_comment_prefixes)
        assert callable(compute_similarity)
        assert callable(match_prefixes_to_parties)
        assert callable(infer_party_role)
        assert callable(get_role_placeholder)
        assert isinstance(DEFINED_TERM_TO_ROLE, dict)


class TestPartyDetectionTestFileContent:
    """Additional checks on the test file structure."""

    @pytest.fixture
    def test_file_path(self) -> Path:
        """Path to the test_party_detection.py file."""
        return Path(__file__).parent / "test_party_detection.py"

    @pytest.fixture
    def test_file_content(self, test_file_path: Path) -> str:
        """Content of test_party_detection.py."""
        return test_file_path.read_text(encoding="utf-8")

    def test_has_comprehensive_docstring(self, test_file_content: str) -> None:
        """Test file should have a module docstring."""
        assert '"""' in test_file_content[:500]

    def test_imports_pytest(self, test_file_content: str) -> None:
        """Test file should import pytest."""
        assert "import pytest" in test_file_content

    def test_has_test_classes(self, test_file_content: str) -> None:
        """Test file should have test classes."""
        assert "class Test" in test_file_content

    def test_has_multiple_test_methods(self, test_file_content: str) -> None:
        """Test file should have multiple test methods."""
        test_method_count = test_file_content.count("def test_")
        assert test_method_count >= 10, f"Expected at least 10 test methods, found {test_method_count}"
