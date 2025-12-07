"""
Tests for effilocal.doc.anonymization module.

This module provides functions for anonymizing party names in contract text:
- anonymize_text: Replace party names with role placeholders
- generate_yaml_header: Generate YAML front matter for markdown files
"""

from __future__ import annotations

from typing import Any

import pytest


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def simple_party_info():
    """Create a simple PartyInfo for testing."""
    from effilocal.doc.party_detection import PartyInfo
    
    return PartyInfo(
        client_prefix="Didimo",
        counterparty_prefix="NBC",
        client_defined_term="Vendor",
        counterparty_defined_term="Company",
        original_provided_by="counterparty",
        client_role="supplier",
        counterparty_role="customer",
        client_alternate_names=["Didimo Inc"],
        counterparty_alternate_names=["NBCUniversal"]
    )


@pytest.fixture
def license_party_info():
    """Create PartyInfo for a license agreement."""
    from effilocal.doc.party_detection import PartyInfo
    
    return PartyInfo(
        client_prefix="Acme",
        counterparty_prefix="TechCorp",
        client_defined_term="Licensor",
        counterparty_defined_term="Licensee",
        original_provided_by="client",
        client_role="licensor",
        counterparty_role="licensee"
    )


# =============================================================================
# Tests: anonymize_text - Basic Replacement
# =============================================================================


class TestAnonymizeTextBasic:
    """Basic tests for anonymize_text function."""
    
    def test_replaces_single_client_name(self) -> None:
        """Should replace a single client name with placeholder."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "The Vendor shall provide services."
        result = anonymize_text(text, "Vendor", "", "CLIENT", "COUNTERPARTY")
        
        assert "[CLIENT]" in result
        assert "Vendor" not in result
    
    def test_replaces_single_counterparty_name(self) -> None:
        """Should replace a single counterparty name with placeholder."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "The Company will pay for services."
        result = anonymize_text(text, "", "Company", "CLIENT", "COUNTERPARTY")
        
        assert "[COUNTERPARTY]" in result
        assert "Company" not in result
    
    def test_replaces_both_party_names(self) -> None:
        """Should replace both client and counterparty names."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "The Vendor shall provide services to the Company."
        result = anonymize_text(text, "Vendor", "Company", "CLIENT", "COUNTERPARTY")
        
        assert "[CLIENT]" in result
        assert "[COUNTERPARTY]" in result
        assert "Vendor" not in result
        assert "Company" not in result
    
    def test_handles_empty_text(self) -> None:
        """Should handle empty text gracefully."""
        from effilocal.doc.anonymization import anonymize_text
        
        result = anonymize_text("", "Vendor", "Company")
        
        assert result == ""
    
    def test_handles_empty_names(self) -> None:
        """Should handle empty name lists gracefully."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "Some text without party names."
        result = anonymize_text(text, "", "")
        
        assert result == text
    
    def test_uses_custom_role_labels(self) -> None:
        """Should use custom role labels for placeholders."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "The Vendor shall license to the Licensee."
        result = anonymize_text(text, "Vendor", "Licensee", "LICENSOR", "LICENSEE")
        
        assert "[LICENSOR]" in result
        assert "[LICENSEE]" in result


# =============================================================================
# Tests: anonymize_text - List of Names
# =============================================================================


class TestAnonymizeTextWithLists:
    """Tests for anonymize_text with lists of names."""
    
    def test_replaces_multiple_client_names(self) -> None:
        """Should replace all names in client list."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "Didimo Inc (the Vendor) shall provide services."
        result = anonymize_text(text, ["Didimo Inc", "Vendor"], "")
        
        assert "[CLIENT]" in result
        assert "Didimo" not in result
        assert "Vendor" not in result
    
    def test_replaces_multiple_counterparty_names(self) -> None:
        """Should replace all names in counterparty list."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "NBCUniversal (the Company) will pay."
        result = anonymize_text(text, "", ["NBCUniversal", "Company"])
        
        assert "[COUNTERPARTY]" in result
        assert "NBCUniversal" not in result
        assert "Company" not in result
    
    def test_longer_names_replaced_first(self) -> None:
        """Should replace longer names first to avoid partial replacements."""
        from effilocal.doc.anonymization import anonymize_text
        
        # "Didimo Inc" should be replaced before "Didimo"
        text = "Didimo Inc is the vendor. Didimo will deliver."
        result = anonymize_text(text, ["Didimo", "Didimo Inc"], "")
        
        # Both should be replaced
        assert "Didimo" not in result
        assert result.count("[CLIENT]") == 2


# =============================================================================
# Tests: anonymize_text - Case Sensitivity
# =============================================================================


class TestAnonymizeTextCaseSensitivity:
    """Tests for case-sensitive replacement behavior."""
    
    def test_preserves_lowercase_generic_words(self) -> None:
        """Should NOT replace lowercase 'company' (generic word)."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "a Delaware limited liability company"
        result = anonymize_text(text, "", "Company")
        
        # Lowercase "company" should NOT be replaced
        assert "company" in result
        assert "[COUNTERPARTY]" not in result
    
    def test_replaces_capitalized_defined_term(self) -> None:
        """Should replace capitalized 'Company' (defined term)."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "The Company shall comply."
        result = anonymize_text(text, "", "Company")
        
        assert "[COUNTERPARTY]" in result
        assert "Company" not in result
    
    def test_replaces_allcaps_variant(self) -> None:
        """Should replace ALLCAPS variant of defined term."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "VENDOR OBLIGATIONS: The VENDOR shall..."
        result = anonymize_text(text, "Vendor", "")
        
        # Both "VENDOR" instances should be replaced
        assert "VENDOR" not in result
        assert result.count("[CLIENT]") == 2
    
    def test_adds_allcaps_variants_automatically(self) -> None:
        """Should automatically add ALLCAPS variants."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "The Vendor and VENDOR obligations."
        result = anonymize_text(text, "Vendor", "")
        
        assert "Vendor" not in result
        assert "VENDOR" not in result


# =============================================================================
# Tests: anonymize_text - Or Patterns
# =============================================================================


class TestAnonymizeTextOrPatterns:
    """Tests for handling ("X" or "Y") patterns."""
    
    def test_collapses_or_pattern_same_party(self) -> None:
        """Should collapse ("X" or "Y") to single placeholder when same party."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = '("Company" or "NBCUniversal")'
        result = anonymize_text(text, "", ["Company", "NBCUniversal"])
        
        # Should become single placeholder, not two
        assert result.count("[COUNTERPARTY]") == 1
        assert "or" not in result or '("[COUNTERPARTY]")' in result
    
    def test_handles_curly_quotes_in_or_pattern(self) -> None:
        """Should handle curly quotes in or patterns."""
        from effilocal.doc.anonymization import anonymize_text
        
        # Using curly quotes
        text = '(\u201CCompany\u201D or \u201CNBCUniversal\u201D)'
        result = anonymize_text(text, "", ["Company", "NBCUniversal"])
        
        # Should still collapse
        assert "NBCUniversal" not in result
        assert "Company" not in result


# =============================================================================
# Tests: anonymize_text - Word Boundaries
# =============================================================================


class TestAnonymizeTextWordBoundaries:
    """Tests for word boundary handling."""
    
    def test_respects_word_boundaries(self) -> None:
        """Should not replace partial word matches."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "The CompanyName is different from the Company."
        result = anonymize_text(text, "", "Company")
        
        # "CompanyName" should NOT be replaced
        assert "CompanyName" in result
        # "Company" at end should be replaced
        assert "[COUNTERPARTY]" in result
    
    def test_handles_names_with_inc_period(self) -> None:
        """Should handle names ending with Inc. correctly."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "Didimo, Inc. is the vendor. Didimo, Inc. shall provide."
        result = anonymize_text(text, ["Didimo, Inc."], "")
        
        assert "Didimo" not in result
        assert result.count("[CLIENT]") == 2
    
    def test_handles_names_followed_by_punctuation(self) -> None:
        """Should replace names followed by punctuation."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "Vendor, Company, and others."
        result = anonymize_text(text, "Vendor", "Company")
        
        assert "[CLIENT]" in result
        assert "[COUNTERPARTY]" in result


# =============================================================================
# Tests: anonymize_text - Edge Cases
# =============================================================================


class TestAnonymizeTextEdgeCases:
    """Edge case tests for anonymize_text."""
    
    def test_handles_string_instead_of_list(self) -> None:
        """Should accept single string instead of list."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "The Vendor provides services."
        result = anonymize_text(text, "Vendor", "Company")
        
        assert "[CLIENT]" in result
    
    def test_handles_none_in_names(self) -> None:
        """Should handle None gracefully (empty string)."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "The Vendor provides services."
        # Empty string should be treated like no replacement
        result = anonymize_text(text, "Vendor", "")
        
        assert "[CLIENT]" in result
    
    def test_multiple_occurrences(self) -> None:
        """Should replace all occurrences of a name."""
        from effilocal.doc.anonymization import anonymize_text
        
        text = "The Vendor shall. The Vendor will. The Vendor may."
        result = anonymize_text(text, "Vendor", "")
        
        assert result.count("[CLIENT]") == 3
        assert "Vendor" not in result


# =============================================================================
# Tests: generate_yaml_header - Basic
# =============================================================================


class TestGenerateYamlHeaderBasic:
    """Basic tests for generate_yaml_header function."""
    
    def test_generates_yaml_delimiters(self) -> None:
        """Should start and end with --- delimiters."""
        from effilocal.doc.anonymization import generate_yaml_header
        
        result = generate_yaml_header("test_document")
        
        assert result.startswith("---\n")
        assert "\n---\n" in result
    
    def test_includes_document_type(self) -> None:
        """Should include document_type field."""
        from effilocal.doc.anonymization import generate_yaml_header
        
        result = generate_yaml_header("client_instructions")
        
        assert "document_type: client_instructions" in result
    
    def test_includes_acting_for(self) -> None:
        """Should include acting_for field with default."""
        from effilocal.doc.anonymization import generate_yaml_header
        
        result = generate_yaml_header("test")
        
        assert "acting_for: client" in result
    
    def test_includes_original_provided_by(self) -> None:
        """Should include original_provided_by field."""
        from effilocal.doc.anonymization import generate_yaml_header
        
        result = generate_yaml_header("test", original_provided_by="client")
        
        assert "original_provided_by: client" in result
    
    def test_default_original_provided_by(self) -> None:
        """Should default to counterparty for original_provided_by."""
        from effilocal.doc.anonymization import generate_yaml_header
        
        result = generate_yaml_header("test")
        
        assert "original_provided_by: counterparty" in result


# =============================================================================
# Tests: generate_yaml_header - Extra Fields
# =============================================================================


class TestGenerateYamlHeaderExtraFields:
    """Tests for generate_yaml_header with extra fields."""
    
    def test_includes_extra_fields(self) -> None:
        """Should include extra fields in output."""
        from effilocal.doc.anonymization import generate_yaml_header
        
        extra = {"description": '"Test description"', "version": "1.0"}
        result = generate_yaml_header("test", extra_fields=extra)
        
        assert 'description: "Test description"' in result
        assert "version: 1.0" in result
    
    def test_handles_none_extra_fields(self) -> None:
        """Should handle None extra_fields gracefully."""
        from effilocal.doc.anonymization import generate_yaml_header
        
        result = generate_yaml_header("test", extra_fields=None)
        
        # Should not raise, should generate valid header
        assert "document_type: test" in result


# =============================================================================
# Tests: generate_yaml_header - With PartyInfo
# =============================================================================


class TestGenerateYamlHeaderWithPartyInfo:
    """Tests for generate_yaml_header with PartyInfo."""
    
    def test_uses_party_info_original_provided_by(self, simple_party_info) -> None:
        """Should use original_provided_by from PartyInfo."""
        from effilocal.doc.anonymization import generate_yaml_header
        
        result = generate_yaml_header(
            "test",
            original_provided_by="client",  # This should be overridden
            party_info=simple_party_info
        )
        
        # PartyInfo has original_provided_by="counterparty"
        assert "original_provided_by: counterparty" in result
    
    def test_includes_parties_section(self, simple_party_info) -> None:
        """Should include parties section with PartyInfo."""
        from effilocal.doc.anonymization import generate_yaml_header
        
        result = generate_yaml_header("test", party_info=simple_party_info)
        
        assert "parties:" in result
        assert "client:" in result
        assert "counterparty:" in result
    
    def test_includes_client_identifier(self, simple_party_info) -> None:
        """Should include client identifier from PartyInfo."""
        from effilocal.doc.anonymization import generate_yaml_header
        
        result = generate_yaml_header("test", party_info=simple_party_info)
        
        # simple_party_info has client_role="supplier" -> [SUPPLIER]
        assert 'identifier: "[SUPPLIER]"' in result
    
    def test_includes_counterparty_identifier(self, simple_party_info) -> None:
        """Should include counterparty identifier from PartyInfo."""
        from effilocal.doc.anonymization import generate_yaml_header
        
        result = generate_yaml_header("test", party_info=simple_party_info)
        
        # simple_party_info has counterparty_role="customer" -> [CUSTOMER]
        assert 'identifier: "[CUSTOMER]"' in result
    
    def test_includes_role_fields(self, simple_party_info) -> None:
        """Should include role fields from PartyInfo."""
        from effilocal.doc.anonymization import generate_yaml_header
        
        result = generate_yaml_header("test", party_info=simple_party_info)
        
        assert 'role: "supplier"' in result
        assert 'role: "customer"' in result
    
    def test_license_agreement_roles(self, license_party_info) -> None:
        """Should handle license agreement roles correctly."""
        from effilocal.doc.anonymization import generate_yaml_header
        
        result = generate_yaml_header("test", party_info=license_party_info)
        
        assert 'identifier: "[LICENSOR]"' in result
        assert 'identifier: "[LICENSEE]"' in result
        assert 'role: "licensor"' in result
        assert 'role: "licensee"' in result


# =============================================================================
# Tests: generate_yaml_header - Without PartyInfo (Backwards Compatibility)
# =============================================================================


class TestGenerateYamlHeaderWithoutPartyInfo:
    """Tests for generate_yaml_header without PartyInfo (backwards compat)."""
    
    def test_uses_simple_format_without_party_info(self) -> None:
        """Should use simple format when no PartyInfo provided."""
        from effilocal.doc.anonymization import generate_yaml_header
        
        result = generate_yaml_header("test")
        
        assert 'our_client: "[CLIENT]"' in result
        assert 'counterparty: "[COUNTERPARTY]"' in result
    
    def test_no_parties_section_without_party_info(self) -> None:
        """Should NOT include parties section without PartyInfo."""
        from effilocal.doc.anonymization import generate_yaml_header
        
        result = generate_yaml_header("test")
        
        assert "parties:" not in result


# =============================================================================
# Integration Tests
# =============================================================================


class TestAnonymizationIntegration:
    """Integration tests combining anonymization functions."""
    
    def test_full_workflow(self, simple_party_info) -> None:
        """Test full anonymization workflow."""
        from effilocal.doc.anonymization import anonymize_text, generate_yaml_header
        
        # Sample contract text
        text = """
        This Agreement is between NBCUniversal (the Company) and Didimo Inc (the Vendor).
        The Vendor shall provide services to the Company.
        The VENDOR agrees to the terms.
        """
        
        # Anonymize using party info
        client_names = simple_party_info.all_client_names
        counterparty_names = simple_party_info.all_counterparty_names
        client_role = simple_party_info.client_placeholder.strip("[]")
        counterparty_role = simple_party_info.counterparty_placeholder.strip("[]")
        
        result = anonymize_text(
            text, 
            client_names, 
            counterparty_names,
            client_role,
            counterparty_role
        )
        
        # All party names should be replaced
        assert "Didimo" not in result
        assert "Vendor" not in result
        assert "NBCUniversal" not in result
        assert "Company" not in result
        
        # Placeholders should be present
        assert "[SUPPLIER]" in result
        assert "[CUSTOMER]" in result
    
    def test_yaml_header_complete(self, simple_party_info) -> None:
        """Test complete YAML header generation."""
        from effilocal.doc.anonymization import generate_yaml_header
        
        result = generate_yaml_header(
            document_type="review_comments",
            acting_for="client",
            extra_fields={"description": '"Comments addressed to each party"'},
            party_info=simple_party_info
        )
        
        # Should have all required fields
        assert "document_type: review_comments" in result
        assert "acting_for: client" in result
        assert "original_provided_by: counterparty" in result
        assert "parties:" in result
        assert 'description: "Comments addressed to each party"' in result
