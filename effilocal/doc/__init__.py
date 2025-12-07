"""Document processing utilities for sprint 1 (placeholders)."""

# Import submodules for attribute access
from effilocal.doc import (
    anonymization,
    clause_lookup,
    direct_docx,
    email_parser,
    hierarchy,
    indexer,
    models,
    numbering,
    party_detection,
    relationships,
    sections,
    styles,
)

# Import key classes and functions for direct access
from effilocal.doc.anonymization import anonymize_text, generate_yaml_header
from effilocal.doc.clause_lookup import ClauseLookup
from effilocal.doc.email_parser import (
    Attachment,
    EmailData,
    EmailMessage,
    MsgParser,
    parse_msg_file,
    select_docx_attachment,
)
from effilocal.doc.party_detection import (
    PartyInfo,
    extract_company_names,
    extract_defined_party_terms,
)

__all__ = [
    # Submodules
    "anonymization",
    "clause_lookup",
    "direct_docx",
    "email_parser",
    "hierarchy",
    "indexer",
    "models",
    "numbering",
    "party_detection",
    "relationships",
    "sections",
    "styles",
    # Classes
    "Attachment",
    "ClauseLookup",
    "EmailData",
    "EmailMessage",
    "MsgParser",
    "PartyInfo",
    # Functions
    "anonymize_text",
    "extract_company_names",
    "extract_defined_party_terms",
    "generate_yaml_header",
    "parse_msg_file",
    "select_docx_attachment",
]

