"""
Tests for generate_review_example.py integration with refactored modules.

These tests verify that generate_review_example.py correctly uses the
refactored modules from effilocal.doc instead of duplicated local functions.
"""

import pytest
import sys
from pathlib import Path
from io import BytesIO
from unittest.mock import patch, MagicMock

# Ensure project root is in path
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


class TestScriptImportsFromRefactoredModules:
    """Test that the script imports from the correct refactored modules."""

    def test_script_is_importable(self):
        """The generate_review_example script should be importable."""
        # Import the script as a module
        import scripts.generate_review_example as script
        assert script is not None

    def test_imports_party_info_from_effilocal(self):
        """Script should use PartyInfo from effilocal.doc.party_detection."""
        import scripts.generate_review_example as script
        from effilocal.doc.party_detection import PartyInfo
        
        # Check that script.PartyInfo is the same as the one from effilocal
        assert script.PartyInfo is PartyInfo

    def test_imports_extract_defined_party_terms_from_effilocal(self):
        """Script should use extract_defined_party_terms from effilocal.doc."""
        import scripts.generate_review_example as script
        from effilocal.doc.party_detection import extract_defined_party_terms
        
        assert script.extract_defined_party_terms is extract_defined_party_terms

    def test_imports_extract_company_names_from_effilocal(self):
        """Script should use extract_company_names from effilocal.doc."""
        import scripts.generate_review_example as script
        from effilocal.doc.party_detection import extract_company_names
        
        assert script.extract_company_names is extract_company_names

    def test_imports_extract_full_company_names_from_effilocal(self):
        """Script should use extract_full_company_names from effilocal.doc."""
        import scripts.generate_review_example as script
        from effilocal.doc.party_detection import extract_full_company_names
        
        assert script.extract_full_company_names is extract_full_company_names

    def test_imports_extract_company_to_defined_term_mapping_from_effilocal(self):
        """Script should use extract_company_to_defined_term_mapping from effilocal.doc."""
        import scripts.generate_review_example as script
        from effilocal.doc.party_detection import extract_company_to_defined_term_mapping
        
        assert script.extract_company_to_defined_term_mapping is extract_company_to_defined_term_mapping

    def test_imports_extract_party_alternate_names_from_effilocal(self):
        """Script should use extract_party_alternate_names from effilocal.doc."""
        import scripts.generate_review_example as script
        from effilocal.doc.party_detection import extract_party_alternate_names
        
        assert script.extract_party_alternate_names is extract_party_alternate_names

    def test_imports_compute_similarity_from_effilocal(self):
        """Script should use compute_similarity from effilocal.doc."""
        import scripts.generate_review_example as script
        from effilocal.doc.party_detection import compute_similarity
        
        assert script.compute_similarity is compute_similarity

    def test_imports_match_prefixes_to_parties_from_effilocal(self):
        """Script should use match_prefixes_to_parties from effilocal.doc."""
        import scripts.generate_review_example as script
        from effilocal.doc.party_detection import match_prefixes_to_parties
        
        assert script.match_prefixes_to_parties is match_prefixes_to_parties

    def test_imports_infer_party_role_from_effilocal(self):
        """Script should use infer_party_role from effilocal.doc."""
        import scripts.generate_review_example as script
        from effilocal.doc.party_detection import infer_party_role
        
        assert script.infer_party_role is infer_party_role

    def test_imports_get_role_placeholder_from_effilocal(self):
        """Script should use get_role_placeholder from effilocal.doc."""
        import scripts.generate_review_example as script
        from effilocal.doc.party_detection import get_role_placeholder
        
        assert script.get_role_placeholder is get_role_placeholder


class TestScriptImportsAnonymizationFromRefactoredModules:
    """Test that anonymization functions are imported from the correct module."""

    def test_imports_anonymize_text_from_effilocal(self):
        """Script should use anonymize_text from effilocal.doc.anonymization."""
        import scripts.generate_review_example as script
        from effilocal.doc.anonymization import anonymize_text
        
        assert script.anonymize_text is anonymize_text

    def test_imports_generate_yaml_header_from_effilocal(self):
        """Script should use generate_yaml_header from effilocal.doc.anonymization."""
        import scripts.generate_review_example as script
        from effilocal.doc.anonymization import generate_yaml_header
        
        assert script.generate_yaml_header is generate_yaml_header


class TestNoLocalDefinitions:
    """Test that the script doesn't define functions locally that should be imported."""

    def test_no_local_party_info_class(self):
        """Script should not define its own PartyInfo class."""
        import scripts.generate_review_example as script
        import inspect
        
        # Get the module where PartyInfo is defined
        source_file = inspect.getfile(script.PartyInfo)
        
        # It should be from effilocal.doc.party_detection, not the script itself
        assert "party_detection" in source_file
        assert "generate_review_example" not in source_file

    def test_no_local_anonymize_text_function(self):
        """Script should not define its own anonymize_text function."""
        import scripts.generate_review_example as script
        import inspect
        
        source_file = inspect.getfile(script.anonymize_text)
        
        assert "anonymization" in source_file
        assert "generate_review_example" not in source_file

    def test_no_local_generate_yaml_header_function(self):
        """Script should not define its own generate_yaml_header function."""
        import scripts.generate_review_example as script
        import inspect
        
        source_file = inspect.getfile(script.generate_yaml_header)
        
        assert "anonymization" in source_file
        assert "generate_review_example" not in source_file

    def test_no_local_extract_defined_party_terms_function(self):
        """Script should not define its own extract_defined_party_terms."""
        import scripts.generate_review_example as script
        import inspect
        
        source_file = inspect.getfile(script.extract_defined_party_terms)
        
        assert "party_detection" in source_file
        assert "generate_review_example" not in source_file


class TestScriptFunctionalityWithRefactoredModules:
    """Test that the script's functionality works with refactored modules."""

    def test_party_info_can_be_instantiated(self):
        """PartyInfo from script should be instantiable with expected fields."""
        import scripts.generate_review_example as script
        
        party_info = script.PartyInfo(
            client_defined_term="Customer",
            client_prefix="For Customer",
            client_alternate_names=["Acme Corp"],
            counterparty_defined_term="Supplier",
            counterparty_prefix="For Supplier",
            counterparty_alternate_names=["Widget Inc"],
            original_provided_by="counterparty",
        )
        
        assert party_info.client_defined_term == "Customer"
        assert party_info.counterparty_defined_term == "Supplier"
        assert party_info.original_provided_by == "counterparty"

    def test_anonymize_text_works_via_script(self):
        """anonymize_text imported in script should work correctly."""
        import scripts.generate_review_example as script
        
        text = "Acme Corp shall pay Widget Inc."
        result = script.anonymize_text(
            text,
            client_names=["Acme Corp"],
            counterparty_names=["Widget Inc"],
            client_role="CUSTOMER",
            counterparty_role="SUPPLIER",
        )
        
        assert "[CUSTOMER]" in result
        assert "[SUPPLIER]" in result
        assert "Acme Corp" not in result
        assert "Widget Inc" not in result

    def test_generate_yaml_header_works_via_script(self):
        """generate_yaml_header imported in script should work correctly."""
        import scripts.generate_review_example as script
        
        header = script.generate_yaml_header(
            document_type="Service Agreement",
            acting_for="Client",
        )
        
        assert "---" in header
        assert "document_type: Service Agreement" in header
        assert "acting_for: Client" in header

    def test_infer_party_role_works_via_script(self):
        """infer_party_role imported in script should work correctly."""
        import scripts.generate_review_example as script
        
        assert script.infer_party_role("Customer") == "customer"
        assert script.infer_party_role("Supplier") == "supplier"
        assert script.infer_party_role("Licensor") == "licensor"

    def test_get_role_placeholder_works_via_script(self):
        """get_role_placeholder imported in script should work correctly."""
        import scripts.generate_review_example as script
        
        assert script.get_role_placeholder("customer") == "[CUSTOMER]"
        assert script.get_role_placeholder("supplier") == "[SUPPLIER]"


class TestScriptModuleAttributes:
    """Test that the script module has the expected attributes."""

    def test_has_all_required_party_detection_functions(self):
        """Script should have all party detection functions accessible."""
        import scripts.generate_review_example as script
        
        required_attrs = [
            "PartyInfo",
            "extract_defined_party_terms",
            "extract_company_names",
            "extract_full_company_names",
            "extract_company_to_defined_term_mapping",
            "extract_party_alternate_names",
            "compute_similarity",
            "match_prefixes_to_parties",
            "infer_party_role",
            "get_role_placeholder",
        ]
        
        for attr in required_attrs:
            assert hasattr(script, attr), f"Script should have {attr}"

    def test_has_all_required_anonymization_functions(self):
        """Script should have all anonymization functions accessible."""
        import scripts.generate_review_example as script
        
        required_attrs = [
            "anonymize_text",
            "generate_yaml_header",
        ]
        
        for attr in required_attrs:
            assert hasattr(script, attr), f"Script should have {attr}"

    def test_script_still_has_other_functions(self):
        """Script should still have its other non-refactored functions."""
        import scripts.generate_review_example as script
        
        # Functions that should remain in the script
        remaining_functions = [
            "parse_msg_file",
            "select_docx_attachment",
            "categorize_comments_by_prefix",
            "process_track_changes",
            "detect_and_confirm_parties",
            "generate_instructions_md",
            "generate_original_agreement_md",
            "generate_comments_md",
            "generate_review_example",
        ]
        
        for func in remaining_functions:
            assert hasattr(script, func), f"Script should still have {func}"
