"""
Text anonymization utilities for contract documents.

This module provides functions for anonymizing party names in contract text,
replacing specific company names with generic role placeholders like [SUPPLIER]
or [CUSTOMER] to help LLMs generalize patterns.

Typical usage:
    from effilocal.doc.anonymization import anonymize_text, generate_yaml_header
    from effilocal.doc.party_detection import PartyInfo
    
    # Anonymize text
    result = anonymize_text(
        text="The Vendor shall provide services to the Company.",
        client_names=["Vendor", "Didimo Inc"],
        counterparty_names=["Company", "NBCUniversal"],
        client_role="SUPPLIER",
        counterparty_role="CUSTOMER"
    )
    
    # Generate YAML header
    yaml = generate_yaml_header(
        document_type="review_comments",
        party_info=party_info
    )
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from effilocal.doc.party_detection import PartyInfo


def anonymize_text(
    text: str,
    client_names: str | list[str],
    counterparty_names: str | list[str],
    client_role: str = "CLIENT",
    counterparty_role: str = "COUNTERPARTY"
) -> str:
    """
    Replace party names with generic role placeholders.
    
    This helps the LLM generalize patterns without memorizing specific names.
    Handles special patterns like ("Company" or "NBCUniversal") → ("[CUSTOMER]")
    
    Note: Replacements preserve case distinction:
    - "Company" (defined term with capital) → replaced
    - "COMPANY" (all caps defined term) → replaced  
    - "company" (generic lowercase word) → NOT replaced
    
    This prevents replacing "a Delaware limited liability company" incorrectly.
    
    Args:
        text: Text to anonymize
        client_names: Client name(s) to replace (single string or list of variations)
        counterparty_names: Counterparty name(s) to replace
        client_role: Role label for client (default: "CLIENT")
        counterparty_role: Role label for counterparty (default: "COUNTERPARTY")
        
    Returns:
        Text with party names replaced by role placeholders
    """
    if not text:
        return text
    
    # Normalize to lists
    if isinstance(client_names, str):
        client_names = [client_names] if client_names else []
    if isinstance(counterparty_names, str):
        counterparty_names = [counterparty_names] if counterparty_names else []
    
    def expand_case_variants(names: list[str]) -> list[str]:
        """Add ALLCAPS variants for each name (defined terms often appear in ALLCAPS headings)."""
        expanded = []
        for name in names:
            if name:
                expanded.append(name)
                # Add ALLCAPS variant if not already present
                upper = name.upper()
                if upper != name and upper not in expanded:
                    expanded.append(upper)
        return expanded
    
    # Expand to include ALLCAPS variants
    client_names = expand_case_variants(client_names)
    counterparty_names = expand_case_variants(counterparty_names)
    
    # Quote characters: straight quotes and curly quotes
    quotes = r'["\'\u201C\u201D]'
    
    # First, handle ("X" or "Y") patterns where both names belong to the same party
    # This prevents them from becoming ("[PLACEHOLDER]" or "[PLACEHOLDER]")
    def collapse_or_pattern(names: list[str], placeholder: str) -> None:
        nonlocal text
        # Generate all pairs of names from the list
        for i, name1 in enumerate(names):
            for name2 in names[i+1:]:
                if name1 and name2:
                    # Match ("Name1" or "Name2") or ("Name2" or "Name1") - case sensitive
                    for n1, n2 in [(name1, name2), (name2, name1)]:
                        pattern = rf'\(\s*{quotes}{re.escape(n1)}{quotes}\s+or\s+{quotes}{re.escape(n2)}{quotes}\s*\)'
                        text = re.sub(pattern, f'("{placeholder}")', text)
    
    collapse_or_pattern(client_names, f'[{client_role}]')
    collapse_or_pattern(counterparty_names, f'[{counterparty_role}]')
    
    def make_replacement_pattern(name: str) -> str:
        """Create regex pattern for name replacement.
        
        Uses word boundaries for names ending in word characters,
        but uses lookahead for names ending in punctuation (like 'Inc.')
        """
        escaped = re.escape(name)
        # Names ending in word characters use normal word boundary
        if re.match(r'\w', name[-1]) if name else False:
            return rf'\b{escaped}\b'
        else:
            # Names ending in non-word chars (like period) - use lookahead
            # Match start word boundary but end with lookahead for space/punctuation/end
            return rf'\b{escaped}(?=\s|["\'\(\)]|$)'
    
    # Replace client names (CASE-SENSITIVE)
    # Process longer names first to avoid partial replacements
    # Case-sensitive ensures "Company" is replaced but "company" is not
    for name in sorted(client_names, key=len, reverse=True):
        if name:
            pattern = make_replacement_pattern(name)
            text = re.sub(pattern, f'[{client_role}]', text)
    
    # Replace counterparty names (CASE-SENSITIVE)
    for name in sorted(counterparty_names, key=len, reverse=True):
        if name:
            pattern = make_replacement_pattern(name)
            text = re.sub(pattern, f'[{counterparty_role}]', text)
    
    return text


def generate_yaml_header(
    document_type: str,
    acting_for: str = "client",
    original_provided_by: str = "counterparty",
    extra_fields: dict[str, str] | None = None,
    party_info: "PartyInfo | None" = None
) -> str:
    """
    Generate YAML front matter header for markdown files.
    
    Args:
        document_type: Type of document (e.g., "instructions", "agreement")
        acting_for: Which party we represent ("client")
        original_provided_by: Who provided the original agreement ("client" or "counterparty")
        extra_fields: Additional YAML fields to include
        party_info: Optional PartyInfo for enhanced parties mapping
        
    Returns:
        YAML front matter string with --- delimiters
    """
    # Use party_info.original_provided_by if available
    if party_info:
        original_provided_by = party_info.original_provided_by
    
    lines = [
        "---",
        f"document_type: {document_type}",
        f"acting_for: {acting_for}",
        f"original_provided_by: {original_provided_by}",
    ]
    
    # Add enhanced parties mapping if party_info is provided
    if party_info:
        # Use semantic role placeholders (e.g., [SUPPLIER], [CUSTOMER])
        # instead of generic [CLIENT]/[COUNTERPARTY]
        lines.extend([
            "parties:",
            "  client:",
            f'    identifier: "{party_info.client_placeholder}"',
            f'    role: "{party_info.client_role}"',
            "  counterparty:",
            f'    identifier: "{party_info.counterparty_placeholder}"',
            f'    role: "{party_info.counterparty_role}"',
        ])
    else:
        # Fallback to simple format for backwards compatibility
        lines.extend([
            'our_client: "[CLIENT]"',
            'counterparty: "[COUNTERPARTY]"',
        ])
    
    if extra_fields:
        for key, value in extra_fields.items():
            lines.append(f"{key}: {value}")
    
    lines.append("---")
    lines.append("")
    
    return "\n".join(lines)
