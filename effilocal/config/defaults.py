"""Default values for document operations.

These defaults are used when no explicit value is provided by the user.
They can be overridden via environment variables.
"""
from __future__ import annotations

import os


# Default author for comments and tracked changes
# Can be overridden via EFFI_DEFAULT_AUTHOR environment variable
DEFAULT_AUTHOR = os.environ.get("EFFI_DEFAULT_AUTHOR", "Effi")
DEFAULT_INITIALS = os.environ.get("EFFI_DEFAULT_INITIALS", "EF")

# Authors for review workflow (internal vs external comments)
# These distinguish between client-facing and counterparty-facing comments
DEFAULT_INTERNAL_AUTHOR = os.environ.get("EFFI_INTERNAL_AUTHOR", "Internal Counsel")
DEFAULT_INTERNAL_INITIALS = os.environ.get("EFFI_INTERNAL_INITIALS", "IC")
DEFAULT_EXTERNAL_AUTHOR = os.environ.get("EFFI_EXTERNAL_AUTHOR", "Counterparty Comment")
DEFAULT_EXTERNAL_INITIALS = os.environ.get("EFFI_EXTERNAL_INITIALS", "EC")
