#!/usr/bin/env python3
"""Debug company to defined term regex."""
import re
from docx import Document

# Load actual document
doc = Document(r'C:\Users\DavidSant\effi-contract-review\EL_Precedents\analysis\quick_contract_review\agreement_before.docx')
text = doc.paragraphs[2].text
print(f"Paragraph text: {text[:300]}...")
print(f"\nSpecial chars: {[f'{c!r} (U+{ord(c):04X})' for c in text if ord(c) > 127]}")

suffixes = r'(?:[Ll]td\.?|[Ll]imited|LLP|[Ii]nc\.?|LLC|CIC|[Cc]orp\.?|[Cc]orporation|PLC|plc|S\.?A\.?|GmbH|B\.?V\.?|N\.?V\.?)'

# Pattern to match: "Company Name, LLC ... ("DefinedTerm")"
pattern = re.compile(
    rf'([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*)*)\s*,?\s*{suffixes}'  # Company name with suffix
    rf'[^()]*'  # Skip jurisdiction/description
    rf'\(\s*["\']([A-Z][A-Za-z]+)["\']'  # First quoted defined term in parentheses
    rf'(?:\s+or\s+["\'][A-Za-z]+["\'])?'  # Optional "or Alias"
    rf'\s*\)'  # Close paren
)

print("\nTesting pattern...")
matches = pattern.findall(text)
print(f"Matches: {matches}")

# Try with Unicode curly quotes
print("\nTrying with curly quotes...")
curly_pattern = re.compile(
    rf'([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*)*),?\s*{suffixes}'  # Company + suffix
    rf'[^()]*'  # Skip description
    rf'\(["""\x27]([A-Z][A-Za-z]+)["""\x27]'  # Defined term with various quote types
)
matches2 = curly_pattern.findall(text)
print(f"Curly quote matches: {matches2}")
