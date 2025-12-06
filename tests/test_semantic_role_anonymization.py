#!/usr/bin/env python3
"""
Tests for Option D: Semantic Role Anonymization.

Instead of using [CLIENT]/[COUNTERPARTY], we use semantic role placeholders
based on the inferred party role:
- [SUPPLIER], [CUSTOMER] for service agreements
- [LICENSOR], [LICENSEE] for license agreements
- [LANDLORD], [TENANT] for lease agreements
- etc.

This preserves semantic meaning for LLM training while still anonymizing
specific company/party names.

Example:
    Before: "For Didimo: The Vendor shall provide services to Company."
    After:  "For [SUPPLIER]: The Vendor shall provide services to Company."
    
Not:    "For [CLIENT]: The Vendor shall provide services to Company."
        (loses semantic meaning)
"""

import sys
from pathlib import Path
from io import BytesIO
from typing import Any
from unittest.mock import patch

import pytest
from docx import Document

# Add project root to path
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# =============================================================================
# Tests for role-based placeholder generation
# =============================================================================

class TestGetRolePlaceholder:
    """Tests for getting the placeholder string from a role."""
    
    def test_supplier_role_becomes_supplier_placeholder(self) -> None:
        """Role 'supplier' should produce placeholder '[SUPPLIER]'."""
        from scripts.generate_review_example import get_role_placeholder
        
        placeholder = get_role_placeholder("supplier")
        assert placeholder == "[SUPPLIER]"
    
    def test_customer_role_becomes_customer_placeholder(self) -> None:
        """Role 'customer' should produce placeholder '[CUSTOMER]'."""
        from scripts.generate_review_example import get_role_placeholder
        
        placeholder = get_role_placeholder("customer")
        assert placeholder == "[CUSTOMER]"
    
    def test_licensor_role_becomes_licensor_placeholder(self) -> None:
        """Role 'licensor' should produce placeholder '[LICENSOR]'."""
        from scripts.generate_review_example import get_role_placeholder
        
        placeholder = get_role_placeholder("licensor")
        assert placeholder == "[LICENSOR]"
    
    def test_licensee_role_becomes_licensee_placeholder(self) -> None:
        """Role 'licensee' should produce placeholder '[LICENSEE]'."""
        from scripts.generate_review_example import get_role_placeholder
        
        placeholder = get_role_placeholder("licensee")
        assert placeholder == "[LICENSEE]"
    
    def test_landlord_role_becomes_landlord_placeholder(self) -> None:
        """Role 'landlord' should produce placeholder '[LANDLORD]'."""
        from scripts.generate_review_example import get_role_placeholder
        
        placeholder = get_role_placeholder("landlord")
        assert placeholder == "[LANDLORD]"
    
    def test_tenant_role_becomes_tenant_placeholder(self) -> None:
        """Role 'tenant' should produce placeholder '[TENANT]'."""
        from scripts.generate_review_example import get_role_placeholder
        
        placeholder = get_role_placeholder("tenant")
        assert placeholder == "[TENANT]"
    
    def test_unknown_role_becomes_party_placeholder(self) -> None:
        """Role 'party' (unknown) should produce placeholder '[PARTY]'."""
        from scripts.generate_review_example import get_role_placeholder
        
        placeholder = get_role_placeholder("party")
        assert placeholder == "[PARTY]"
    
    def test_seller_role_becomes_seller_placeholder(self) -> None:
        """Role 'seller' should produce placeholder '[SELLER]'."""
        from scripts.generate_review_example import get_role_placeholder
        
        placeholder = get_role_placeholder("seller")
        assert placeholder == "[SELLER]"
    
    def test_employer_role_becomes_employer_placeholder(self) -> None:
        """Role 'employer' should produce placeholder '[EMPLOYER]'."""
        from scripts.generate_review_example import get_role_placeholder
        
        placeholder = get_role_placeholder("employer")
        assert placeholder == "[EMPLOYER]"
    
    def test_employee_role_becomes_employee_placeholder(self) -> None:
        """Role 'employee' should produce placeholder '[EMPLOYEE]'."""
        from scripts.generate_review_example import get_role_placeholder
        
        placeholder = get_role_placeholder("employee")
        assert placeholder == "[EMPLOYEE]"


# =============================================================================
# Tests for anonymize_text with semantic roles
# =============================================================================

class TestAnonymizeTextWithSemanticRoles:
    """Tests for anonymize_text using semantic role placeholders."""
    
    def test_anonymize_replaces_company_with_role_placeholder(self) -> None:
        """Should replace 'Didimo' with '[SUPPLIER]' when role is 'supplier'."""
        from scripts.generate_review_example import anonymize_text
        
        text = "For Didimo: The Vendor shall provide services."
        
        result = anonymize_text(
            text,
            client_names=["Didimo"],
            counterparty_names=["NBC"],
            client_role="SUPPLIER",
            counterparty_role="CUSTOMER"
        )
        
        assert "[SUPPLIER]" in result
        assert "Didimo" not in result
        assert "Vendor" in result  # Defined term preserved
    
    def test_anonymize_replaces_counterparty_with_role_placeholder(self) -> None:
        """Should replace 'NBC' with '[CUSTOMER]' when role is 'customer'."""
        from scripts.generate_review_example import anonymize_text
        
        text = "For NBC: The Company will pay within 30 days."
        
        result = anonymize_text(
            text,
            client_names=["Didimo"],
            counterparty_names=["NBC"],
            client_role="SUPPLIER",
            counterparty_role="CUSTOMER"
        )
        
        assert "[CUSTOMER]" in result
        assert "NBC" not in result
        assert "Company" in result  # Defined term preserved
    
    def test_anonymize_uses_licensor_licensee_placeholders(self) -> None:
        """Should use [LICENSOR]/[LICENSEE] for license agreements."""
        from scripts.generate_review_example import anonymize_text
        
        text = "Acme Corp grants rights. BigTech receives rights."
        
        result = anonymize_text(
            text,
            client_names=["Acme Corp"],
            counterparty_names=["BigTech"],
            client_role="LICENSOR",
            counterparty_role="LICENSEE"
        )
        
        assert "[LICENSOR]" in result
        assert "[LICENSEE]" in result
        assert "Acme Corp" not in result
        assert "BigTech" not in result
    
    def test_anonymize_preserves_defined_terms(self) -> None:
        """Should NOT replace defined terms like 'Vendor', 'Company'."""
        from scripts.generate_review_example import anonymize_text
        
        text = "The Vendor (Didimo) shall deliver to Company (NBC)."
        
        result = anonymize_text(
            text,
            client_names=["Didimo"],
            counterparty_names=["NBC"],
            client_role="SUPPLIER",
            counterparty_role="CUSTOMER"
        )
        
        # Defined terms MUST be preserved
        assert "Vendor" in result
        assert "Company" in result
        # But company identifiers replaced
        assert "Didimo" not in result
        assert "NBC" not in result
        assert "[SUPPLIER]" in result
        assert "[CUSTOMER]" in result
    
    def test_anonymize_handles_landlord_tenant(self) -> None:
        """Should use [LANDLORD]/[TENANT] for lease agreements."""
        from scripts.generate_review_example import anonymize_text
        
        text = "PropertyCo leases to RetailCo."
        
        result = anonymize_text(
            text,
            client_names=["PropertyCo"],
            counterparty_names=["RetailCo"],
            client_role="LANDLORD",
            counterparty_role="TENANT"
        )
        
        assert "[LANDLORD]" in result
        assert "[TENANT]" in result
    
    def test_default_roles_are_client_counterparty(self) -> None:
        """Default roles should still be 'CLIENT' and 'COUNTERPARTY' for backwards compat."""
        from scripts.generate_review_example import anonymize_text
        
        text = "Acme and BigCorp agree."
        
        # Without specifying roles, should default to CLIENT/COUNTERPARTY
        result = anonymize_text(
            text,
            client_names=["Acme"],
            counterparty_names=["BigCorp"]
        )
        
        assert "[CLIENT]" in result
        assert "[COUNTERPARTY]" in result
    
    def test_anonymize_replaces_full_company_name_with_legal_suffix(self) -> None:
        """Should replace 'NBCUniversal Media, LLC' with '[CUSTOMER]', not just 'NBCUniversal'."""
        from scripts.generate_review_example import anonymize_text
        
        text = 'This Agreement is entered into by NBCUniversal Media, LLC ("Company").'
        
        result = anonymize_text(
            text,
            client_names=["Didimo"],
            counterparty_names=["NBCUniversal Media, LLC", "Company", "NBCUniversal"],
            client_role="SUPPLIER",
            counterparty_role="CUSTOMER"
        )
        
        # The full company name should be replaced
        assert "NBCUniversal Media, LLC" not in result
        assert "[CUSTOMER]" in result
        # Should NOT have leftover ", LLC"
        assert ", LLC" not in result.replace("[CUSTOMER]", "")
    
    def test_anonymize_replaces_inc_suffix(self) -> None:
        """Should replace 'Didimo, Inc.' with '[SUPPLIER]', not just 'Didimo'."""
        from scripts.generate_review_example import anonymize_text
        
        text = 'Didimo, Inc. provides services to Customer.'
        
        result = anonymize_text(
            text,
            client_names=["Didimo, Inc.", "Vendor", "Didimo"],
            counterparty_names=["Customer"],
            client_role="SUPPLIER",
            counterparty_role="CUSTOMER"
        )
        
        # The full company name should be replaced
        assert "Didimo, Inc." not in result
        assert "[SUPPLIER]" in result
        # Should NOT have leftover ", Inc."
        assert ", Inc." not in result


# =============================================================================
# Tests for generate_yaml_header with semantic roles
# =============================================================================

class TestYamlHeaderSemanticRoles:
    """Tests for YAML header with semantic role identifiers."""
    
    def test_yaml_identifier_uses_role_placeholder(self) -> None:
        """Parties.client.identifier should be '[SUPPLIER]' not '[CLIENT]'."""
        from scripts.generate_review_example import PartyInfo, generate_yaml_header
        
        party_info = PartyInfo(
            client_prefix="Didimo",
            counterparty_prefix="NBC",
            client_defined_term="Vendor",
            counterparty_defined_term="Company",
            original_provided_by="counterparty",
            client_role="supplier",
            counterparty_role="customer"
        )
        
        yaml = generate_yaml_header(
            document_type="test",
            party_info=party_info
        )
        
        # Should use [SUPPLIER] as identifier, not [CLIENT]
        assert '"[SUPPLIER]"' in yaml or "'[SUPPLIER]'" in yaml
        assert '"[CUSTOMER]"' in yaml or "'[CUSTOMER]'" in yaml
    
    def test_yaml_identifier_for_license_agreement(self) -> None:
        """License agreement should have [LICENSOR]/[LICENSEE] identifiers."""
        from scripts.generate_review_example import PartyInfo, generate_yaml_header
        
        party_info = PartyInfo(
            client_prefix="Acme",
            counterparty_prefix="BigCorp",
            client_defined_term="Licensor",
            counterparty_defined_term="Licensee",
            original_provided_by="client",
            client_role="licensor",
            counterparty_role="licensee"
        )
        
        yaml = generate_yaml_header(
            document_type="test",
            party_info=party_info
        )
        
        assert '"[LICENSOR]"' in yaml or "'[LICENSOR]'" in yaml
        assert '"[LICENSEE]"' in yaml or "'[LICENSEE]'" in yaml
    
    def test_yaml_identifier_for_lease_agreement(self) -> None:
        """Lease agreement should have [LANDLORD]/[TENANT] identifiers."""
        from scripts.generate_review_example import PartyInfo, generate_yaml_header
        
        party_info = PartyInfo(
            client_prefix="PropertyCo",
            counterparty_prefix="RetailCo",
            client_defined_term="Landlord",
            counterparty_defined_term="Tenant",
            original_provided_by="counterparty",
            client_role="landlord",
            counterparty_role="tenant"
        )
        
        yaml = generate_yaml_header(
            document_type="test",
            party_info=party_info
        )
        
        assert '"[LANDLORD]"' in yaml or "'[LANDLORD]'" in yaml
        assert '"[TENANT]"' in yaml or "'[TENANT]'" in yaml
    
    def test_yaml_excludes_defined_term(self) -> None:
        """YAML should NOT include the defined_term field (it's redundant)."""
        from scripts.generate_review_example import PartyInfo, generate_yaml_header
        
        party_info = PartyInfo(
            client_prefix="Didimo",
            counterparty_prefix="NBC",
            client_defined_term="Vendor",
            counterparty_defined_term="Company",
            original_provided_by="counterparty",
            client_role="supplier",
            counterparty_role="customer"
        )
        
        yaml = generate_yaml_header(
            document_type="test",
            party_info=party_info
        )
        
        # defined_term is redundant since we replace terms with role placeholders
        assert "defined_term:" not in yaml
    
    def test_yaml_still_includes_role(self) -> None:
        """YAML should still include the role field."""
        from scripts.generate_review_example import PartyInfo, generate_yaml_header
        
        party_info = PartyInfo(
            client_prefix="Didimo",
            counterparty_prefix="NBC",
            client_defined_term="Vendor",
            counterparty_defined_term="Company",
            original_provided_by="counterparty",
            client_role="supplier",
            counterparty_role="customer"
        )
        
        yaml = generate_yaml_header(
            document_type="test",
            party_info=party_info
        )
        
        assert 'role: "supplier"' in yaml
        assert 'role: "customer"' in yaml


# =============================================================================
# Tests for markdown generation with semantic roles
# =============================================================================

class TestMarkdownGenerationSemanticRoles:
    """Tests that generated markdown uses semantic role placeholders."""
    
    def test_comments_md_uses_role_placeholders_in_headers(self) -> None:
        """Comments markdown should use role placeholders in section headers."""
        from scripts.generate_review_example import (
            generate_comments_md,
            PartyInfo
        )
        
        categorized_comments = {
            "client": [{"text": "For Client: note", "author": "L", "date": "2025"}],
            "counterparty": [],
            "other": []
        }
        
        party_info = PartyInfo(
            client_prefix="Didimo",
            counterparty_prefix="NBC",
            client_defined_term="Vendor",
            counterparty_defined_term="Company",
            original_provided_by="counterparty",
            client_role="supplier",
            counterparty_role="customer"
        )
        
        markdown = generate_comments_md(
            categorized_comments,
            client_names=["Didimo"],
            counterparty_names=["NBC"],
            party_info=party_info
        )
        
        # Section headers should use role placeholders
        assert "[SUPPLIER]" in markdown
        assert "[CUSTOMER]" in markdown
    
    def test_track_changes_md_uses_role_placeholders(self) -> None:
        """Track changes markdown should anonymize with role placeholders."""
        from scripts.generate_review_example import (
            generate_track_changes_md,
            PartyInfo,
            ParagraphDiff
        )
        
        party_info = PartyInfo(
            client_prefix="Didimo",
            counterparty_prefix="NBC",
            client_defined_term="Vendor",
            counterparty_defined_term="Company",
            original_provided_by="counterparty",
            client_role="supplier",
            counterparty_role="customer"
        )
        
        diffs = [
            ParagraphDiff(
                before_text="Didimo shall provide services.",
                after_text="Didimo shall provide enhanced services.",
                authors={"Author"},
                dates={"2025-01-01"},
                insertions=["enhanced "],
                deletions=[]
            )
        ]
        
        markdown = generate_track_changes_md(
            diffs,
            client_names=["Didimo"],
            counterparty_names=["NBC"],
            party_info=party_info
        )
        
        # Text should use [SUPPLIER] not [CLIENT]
        assert "[SUPPLIER]" in markdown
        assert "Didimo" not in markdown
    
    def test_instructions_md_uses_role_placeholders(self) -> None:
        """Instructions markdown should anonymize with role placeholders."""
        from scripts.generate_review_example import (
            generate_instructions_md,
            PartyInfo,
            EmailData,
            Attachment
        )
        
        email_data = EmailData(
            subject="Review of Didimo contract with NBC",
            sender="client@example.com",
            recipients="lawyer@example.com",
            date="2025-01-01",
            body="Please review the attached agreement with NBC.",
            attachments=[Attachment(filename="contract.docx", data=b"")]
        )
        
        party_info = PartyInfo(
            client_prefix="Didimo",
            counterparty_prefix="NBC",
            client_defined_term="Vendor",
            counterparty_defined_term="Company",
            original_provided_by="counterparty",
            client_role="supplier",
            counterparty_role="customer"
        )
        
        markdown = generate_instructions_md(
            email_data,
            client_names=["Didimo"],
            counterparty_names=["NBC"],
            party_info=party_info
        )
        
        # Body should use role placeholders
        assert "[SUPPLIER]" in markdown or "[CUSTOMER]" in markdown
        # Company names should be replaced
        assert "Didimo" not in markdown
        assert "NBC" not in markdown


# =============================================================================
# Tests for PartyInfo role-to-placeholder integration
# =============================================================================

class TestPartyInfoRolePlaceholder:
    """Tests for getting placeholders from PartyInfo."""
    
    def test_party_info_client_placeholder_property(self) -> None:
        """PartyInfo should have a client_placeholder property."""
        from scripts.generate_review_example import PartyInfo
        
        info = PartyInfo(
            client_prefix="Didimo",
            counterparty_prefix="NBC",
            client_defined_term="Vendor",
            counterparty_defined_term="Company",
            original_provided_by="counterparty",
            client_role="supplier",
            counterparty_role="customer"
        )
        
        assert info.client_placeholder == "[SUPPLIER]"
    
    def test_party_info_counterparty_placeholder_property(self) -> None:
        """PartyInfo should have a counterparty_placeholder property."""
        from scripts.generate_review_example import PartyInfo
        
        info = PartyInfo(
            client_prefix="Didimo",
            counterparty_prefix="NBC",
            client_defined_term="Vendor",
            counterparty_defined_term="Company",
            original_provided_by="counterparty",
            client_role="supplier",
            counterparty_role="customer"
        )
        
        assert info.counterparty_placeholder == "[CUSTOMER]"
    
    def test_party_info_placeholder_for_unknown_role(self) -> None:
        """PartyInfo with unknown role should default to [PARTY]."""
        from scripts.generate_review_example import PartyInfo
        
        info = PartyInfo(
            client_prefix="SomeCo",
            counterparty_prefix="OtherCo",
            client_defined_term="FirstParty",
            counterparty_defined_term="SecondParty",
            original_provided_by="counterparty",
            client_role="party",  # unknown role
            counterparty_role="party"  # unknown role
        )
        
        assert info.client_placeholder == "[PARTY]"
        assert info.counterparty_placeholder == "[PARTY]"


# =============================================================================
# Integration tests
# =============================================================================

class TestSemanticRoleIntegration:
    """Integration tests for the complete semantic role workflow."""
    
    def test_full_workflow_service_agreement(self) -> None:
        """Test full workflow for a service agreement (Vendor/Company)."""
        from scripts.generate_review_example import (
            PartyInfo,
            anonymize_text,
            generate_yaml_header,
            infer_party_role
        )
        
        # Simulate party detection
        client_defined_term = "Vendor"
        counterparty_defined_term = "Company"
        
        client_role = infer_party_role(client_defined_term)
        counterparty_role = infer_party_role(counterparty_defined_term)
        
        assert client_role == "supplier"
        assert counterparty_role == "customer"
        
        party_info = PartyInfo(
            client_prefix="Didimo",
            counterparty_prefix="NBC",
            client_defined_term=client_defined_term,
            counterparty_defined_term=counterparty_defined_term,
            original_provided_by="counterparty",
            client_role=client_role,
            counterparty_role=counterparty_role
        )
        
        # Anonymize text using role placeholders
        text = "Didimo shall provide services to NBC according to this agreement."
        result = anonymize_text(
            text,
            client_names=["Didimo"],
            counterparty_names=["NBC"],
            client_role=party_info.client_placeholder.strip("[]"),
            counterparty_role=party_info.counterparty_placeholder.strip("[]")
        )
        
        assert "[SUPPLIER]" in result
        assert "[CUSTOMER]" in result
        assert "Didimo" not in result
        assert "NBC" not in result
        
        # Generate YAML with semantic identifiers
        yaml = generate_yaml_header(
            document_type="test",
            party_info=party_info
        )
        
        assert '"[SUPPLIER]"' in yaml or "'[SUPPLIER]'" in yaml
        assert '"[CUSTOMER]"' in yaml or "'[CUSTOMER]'" in yaml
    
    def test_full_workflow_license_agreement(self) -> None:
        """Test full workflow for a license agreement (Licensor/Licensee)."""
        from scripts.generate_review_example import (
            PartyInfo,
            anonymize_text,
            generate_yaml_header,
            infer_party_role
        )
        
        # Simulate party detection
        client_defined_term = "Licensor"
        counterparty_defined_term = "Licensee"
        
        client_role = infer_party_role(client_defined_term)
        counterparty_role = infer_party_role(counterparty_defined_term)
        
        assert client_role == "licensor"
        assert counterparty_role == "licensee"
        
        party_info = PartyInfo(
            client_prefix="Acme IP",
            counterparty_prefix="BigTech",
            client_defined_term=client_defined_term,
            counterparty_defined_term=counterparty_defined_term,
            original_provided_by="client",
            client_role=client_role,
            counterparty_role=counterparty_role
        )
        
        # Anonymize text using role placeholders
        text = "Acme IP grants to BigTech a license to use the technology."
        result = anonymize_text(
            text,
            client_names=["Acme IP"],
            counterparty_names=["BigTech"],
            client_role=party_info.client_placeholder.strip("[]"),
            counterparty_role=party_info.counterparty_placeholder.strip("[]")
        )
        
        assert "[LICENSOR]" in result
        assert "[LICENSEE]" in result
        assert "Acme IP" not in result
        assert "BigTech" not in result


# =============================================================================
# Tests for generate_mappings_md
# =============================================================================

class TestGenerateMappingsMd:
    """Tests for the mappings markdown generation."""
    
    def test_generate_mappings_md_has_yaml_header(self) -> None:
        """Mappings file should have YAML frontmatter."""
        from scripts.generate_review_example import generate_mappings_md, PartyInfo
        
        party_info = PartyInfo(
            client_prefix="Didimo",
            counterparty_prefix="NBC",
            client_defined_term="Vendor",
            counterparty_defined_term="Company",
            original_provided_by="counterparty",
            client_role="supplier",
            counterparty_role="customer"
        )
        
        result = generate_mappings_md(
            party_info,
            client_names=["Didimo", "Vendor"],
            counterparty_names=["NBC", "Company"]
        )
        
        assert result.startswith("---")
        assert "document_type: mappings" in result
    
    def test_generate_mappings_md_includes_role_placeholders(self) -> None:
        """Mappings should show the role-based placeholders."""
        from scripts.generate_review_example import generate_mappings_md, PartyInfo
        
        party_info = PartyInfo(
            client_prefix="Didimo",
            counterparty_prefix="NBC",
            client_defined_term="Vendor",
            counterparty_defined_term="Company",
            original_provided_by="counterparty",
            client_role="supplier",
            counterparty_role="customer"
        )
        
        result = generate_mappings_md(
            party_info,
            client_names=["Didimo", "Vendor"],
            counterparty_names=["NBC", "Company"]
        )
        
        assert "[SUPPLIER]" in result
        assert "[CUSTOMER]" in result
    
    def test_generate_mappings_md_lists_all_replaced_names(self) -> None:
        """Mappings should list all name variations that are replaced."""
        from scripts.generate_review_example import generate_mappings_md, PartyInfo
        
        party_info = PartyInfo(
            client_prefix="Didimo",
            counterparty_prefix="NBC",
            client_defined_term="Vendor",
            counterparty_defined_term="Company",
            original_provided_by="counterparty",
            client_role="supplier",
            counterparty_role="customer"
        )
        
        result = generate_mappings_md(
            party_info,
            client_names=["Didimo", "Vendor"],
            counterparty_names=["NBC", "Company"]
        )
        
        # Check client names are listed
        assert "`Didimo`" in result
        assert "`Vendor`" in result
        
        # Check counterparty names are listed
        assert "`NBC`" in result
        assert "`Company`" in result
    
    def test_generate_mappings_md_shows_original_provider(self) -> None:
        """Mappings should indicate who provided the original agreement."""
        from scripts.generate_review_example import generate_mappings_md, PartyInfo
        
        party_info = PartyInfo(
            client_prefix="Didimo",
            counterparty_prefix="NBC",
            client_defined_term="Vendor",
            counterparty_defined_term="Company",
            original_provided_by="counterparty",
            client_role="supplier",
            counterparty_role="customer"
        )
        
        result = generate_mappings_md(
            party_info,
            client_names=["Didimo", "Vendor"],
            counterparty_names=["NBC", "Company"]
        )
        
        assert "counterparty" in result
        assert "original agreement" in result.lower()
    
    def test_generate_mappings_md_deduplicates_names(self) -> None:
        """Mappings should deduplicate repeated names."""
        from scripts.generate_review_example import generate_mappings_md, PartyInfo
        
        party_info = PartyInfo(
            client_prefix="Vendor",
            counterparty_prefix="Company",
            client_defined_term="Vendor",  # Same as prefix
            counterparty_defined_term="Company",  # Same as prefix
            original_provided_by="client",
            client_role="supplier",
            counterparty_role="customer"
        )
        
        result = generate_mappings_md(
            party_info,
            client_names=["Vendor", "Vendor"],  # Duplicates
            counterparty_names=["Company", "Company"]  # Duplicates
        )
        
        # Count occurrences of the backticked names (only in the list sections)
        # Each should appear exactly once in the replacement list
        client_section = result.split("## Counterparty Replacements")[0]
        assert client_section.count("- `Vendor`") == 1
    
    def test_generate_mappings_md_includes_roles_table(self) -> None:
        """Mappings should have a table showing party roles."""
        from scripts.generate_review_example import generate_mappings_md, PartyInfo
        
        party_info = PartyInfo(
            client_prefix="Acme",
            counterparty_prefix="BigCorp",
            client_defined_term="Licensor",
            counterparty_defined_term="Licensee",
            original_provided_by="counterparty",
            client_role="licensor",
            counterparty_role="licensee"
        )
        
        result = generate_mappings_md(
            party_info,
            client_names=["Acme", "Licensor"],
            counterparty_names=["BigCorp", "Licensee"]
        )
        
        # Check table headers
        assert "| Party | Role | Placeholder |" in result
        # Check roles are in the table
        assert "licensor" in result
        assert "licensee" in result
        assert "[LICENSOR]" in result
        assert "[LICENSEE]" in result
