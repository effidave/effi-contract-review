"""Attachment cue configuration."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Pattern

# Canonical keywords used for schedules/annexes/etc.
ATTACHMENT_KEYWORDS: dict[str, str] = {
    "schedule": "schedule",
    "annex": "annex",
    "appendix": "appendix",
    "exhibit": "exhibit",
    "attachment": "attachment",
}

# Allowed punctuation between keyword/ordinal/title segments.
ATTACHMENT_PUNCTUATION = "-\u2013\u2014:)"


@dataclass(frozen=True)
class AttachmentCue:
    """Regex-based cue for inferring attachment types."""

    attachment_type: str
    pattern: Pattern[str]


ATTACHMENT_PATTERN_CUES: list[AttachmentCue] = [
    AttachmentCue("schedule", re.compile(r"\bschedule\b", re.IGNORECASE)),
    AttachmentCue("annex", re.compile(r"\bannex\b", re.IGNORECASE)),
    AttachmentCue("appendix", re.compile(r"\bappendix\b", re.IGNORECASE)),
    AttachmentCue("exhibit", re.compile(r"\bexhibit\b", re.IGNORECASE)),
    AttachmentCue("attachment", re.compile(r"\battachment\b", re.IGNORECASE)),
]
