"""
Tests for effilocal.doc module exports.

Verifies that all key classes and functions are properly exported
from the effilocal.doc package for convenient importing.
"""

import pytest


class TestDocModuleImports:
    """Test that effilocal.doc can be imported."""

    def test_import_effilocal_doc(self):
        """The effilocal.doc package should be importable."""
        import effilocal.doc
        assert effilocal.doc is not None

    def test_has_all_attribute(self):
        """The package should define __all__ for explicit exports."""
        import effilocal.doc
        assert hasattr(effilocal.doc, '__all__')
        assert isinstance(effilocal.doc.__all__, list)


class TestClauseLookupExports:
    """Test that clause_lookup module exports are available."""

    def test_clause_lookup_in_all(self):
        """clause_lookup should be listed in __all__."""
        import effilocal.doc
        assert 'clause_lookup' in effilocal.doc.__all__

    def test_can_import_clause_lookup_module(self):
        """Should be able to import clause_lookup submodule."""
        from effilocal.doc import clause_lookup
        assert clause_lookup is not None

    def test_clause_lookup_class_accessible(self):
        """ClauseLookup class should be importable from the module."""
        from effilocal.doc.clause_lookup import ClauseLookup
        assert ClauseLookup is not None

    def test_clause_lookup_class_direct_export(self):
        """ClauseLookup should be directly importable from effilocal.doc."""
        from effilocal.doc import ClauseLookup
        assert ClauseLookup is not None
        # Verify it's the actual class by checking __init__ signature
        import inspect
        sig = inspect.signature(ClauseLookup.__init__)
        assert 'source' in sig.parameters


class TestPartyDetectionExports:
    """Test that party_detection module exports are available."""

    def test_party_detection_in_all(self):
        """party_detection should be listed in __all__."""
        import effilocal.doc
        assert 'party_detection' in effilocal.doc.__all__

    def test_can_import_party_detection_module(self):
        """Should be able to import party_detection submodule."""
        from effilocal.doc import party_detection
        assert party_detection is not None

    def test_party_info_class_accessible(self):
        """PartyInfo class should be importable from the module."""
        from effilocal.doc.party_detection import PartyInfo
        assert PartyInfo is not None

    def test_party_info_class_direct_export(self):
        """PartyInfo should be directly importable from effilocal.doc."""
        from effilocal.doc import PartyInfo
        assert PartyInfo is not None
        # Verify it's the actual dataclass by checking __dataclass_fields__
        assert hasattr(PartyInfo, '__dataclass_fields__')
        assert 'client_defined_term' in PartyInfo.__dataclass_fields__
        assert 'counterparty_defined_term' in PartyInfo.__dataclass_fields__

    def test_extract_defined_party_terms_accessible(self):
        """extract_defined_party_terms function should be importable from the module."""
        from effilocal.doc.party_detection import extract_defined_party_terms
        assert callable(extract_defined_party_terms)

    def test_extract_defined_party_terms_direct_export(self):
        """extract_defined_party_terms should be directly importable from effilocal.doc."""
        from effilocal.doc import extract_defined_party_terms
        assert callable(extract_defined_party_terms)

    def test_extract_company_names_accessible(self):
        """extract_company_names should be importable from the module."""
        from effilocal.doc.party_detection import extract_company_names
        assert callable(extract_company_names)

    def test_extract_company_names_direct_export(self):
        """extract_company_names should be directly importable from effilocal.doc."""
        from effilocal.doc import extract_company_names
        assert callable(extract_company_names)


class TestAnonymizationExports:
    """Test that anonymization module exports are available."""

    def test_anonymization_in_all(self):
        """anonymization should be listed in __all__."""
        import effilocal.doc
        assert 'anonymization' in effilocal.doc.__all__

    def test_can_import_anonymization_module(self):
        """Should be able to import anonymization submodule."""
        from effilocal.doc import anonymization
        assert anonymization is not None

    def test_anonymize_text_function_accessible(self):
        """anonymize_text function should be importable from the module."""
        from effilocal.doc.anonymization import anonymize_text
        assert callable(anonymize_text)

    def test_anonymize_text_function_direct_export(self):
        """anonymize_text should be directly importable from effilocal.doc."""
        from effilocal.doc import anonymize_text
        assert callable(anonymize_text)

    def test_generate_yaml_header_accessible(self):
        """generate_yaml_header should be importable from the module."""
        from effilocal.doc.anonymization import generate_yaml_header
        assert callable(generate_yaml_header)

    def test_generate_yaml_header_direct_export(self):
        """generate_yaml_header should be directly importable from effilocal.doc."""
        from effilocal.doc import generate_yaml_header
        assert callable(generate_yaml_header)


class TestExistingModuleExports:
    """Test that existing modules are still properly exported."""

    def test_direct_docx_in_all(self):
        """direct_docx should remain in __all__."""
        import effilocal.doc
        assert 'direct_docx' in effilocal.doc.__all__

    def test_hierarchy_in_all(self):
        """hierarchy should remain in __all__."""
        import effilocal.doc
        assert 'hierarchy' in effilocal.doc.__all__

    def test_indexer_in_all(self):
        """indexer should remain in __all__."""
        import effilocal.doc
        assert 'indexer' in effilocal.doc.__all__

    def test_models_in_all(self):
        """models should remain in __all__."""
        import effilocal.doc
        assert 'models' in effilocal.doc.__all__

    def test_numbering_in_all(self):
        """numbering should remain in __all__."""
        import effilocal.doc
        assert 'numbering' in effilocal.doc.__all__

    def test_relationships_in_all(self):
        """relationships should remain in __all__."""
        import effilocal.doc
        assert 'relationships' in effilocal.doc.__all__

    def test_sections_in_all(self):
        """sections should remain in __all__."""
        import effilocal.doc
        assert 'sections' in effilocal.doc.__all__

    def test_styles_in_all(self):
        """styles should remain in __all__."""
        import effilocal.doc
        assert 'styles' in effilocal.doc.__all__


class TestDirectImportConvenience:
    """Test convenience of direct imports from effilocal.doc."""

    def test_can_do_combined_import(self):
        """Should be able to import multiple items in one statement."""
        from effilocal.doc import (
            ClauseLookup,
            PartyInfo,
            extract_defined_party_terms,
            anonymize_text,
            generate_yaml_header,
        )
        assert ClauseLookup is not None
        assert PartyInfo is not None
        assert callable(extract_defined_party_terms)
        assert callable(anonymize_text)
        assert callable(generate_yaml_header)

    def test_all_exports_are_strings(self):
        """All items in __all__ should be strings."""
        import effilocal.doc
        for item in effilocal.doc.__all__:
            assert isinstance(item, str), f"{item} should be a string"

    def test_all_exports_are_importable(self):
        """Every item in __all__ should be importable."""
        import effilocal.doc
        for name in effilocal.doc.__all__:
            assert hasattr(effilocal.doc, name), f"{name} should be accessible on effilocal.doc"


class TestNewModulesComplete:
    """Test that all three new modules are fully integrated."""

    def test_all_three_new_modules_in_all(self):
        """All three new modules should be in __all__."""
        import effilocal.doc
        new_modules = ['clause_lookup', 'party_detection', 'anonymization']
        for module in new_modules:
            assert module in effilocal.doc.__all__, f"{module} should be in __all__"

    def test_key_exports_count(self):
        """Should have direct exports for key classes/functions."""
        from effilocal.doc import (
            ClauseLookup,
            PartyInfo,
            extract_defined_party_terms,
            extract_company_names,
            anonymize_text,
            generate_yaml_header,
        )
        # All should be accessible
        exports = [
            ClauseLookup,
            PartyInfo,
            extract_defined_party_terms,
            extract_company_names,
            anonymize_text,
            generate_yaml_header,
        ]
        assert len(exports) == 6
        assert all(e is not None for e in exports)


class TestBackwardsCompatibility:
    """Test that existing import patterns still work."""

    def test_old_import_pattern_direct_docx(self):
        """Existing import pattern for direct_docx should work."""
        from effilocal.doc import direct_docx
        assert direct_docx is not None

    def test_old_import_pattern_hierarchy(self):
        """Existing import pattern for hierarchy should work."""
        from effilocal.doc import hierarchy
        assert hierarchy is not None

    def test_old_import_pattern_models(self):
        """Existing import pattern for models should work."""
        from effilocal.doc import models
        assert models is not None
