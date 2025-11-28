"""Table-of-contents field tracker for synthesized numbering."""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass
from typing import Any, Optional

from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

from effilocal.doc.trackers.numbering_tracker import NumberingTracker

TOC_TC_PATTERN = re.compile(r"\bTC\s+\"([^\"]+)\"", re.IGNORECASE)
TOC_LEVEL_PATTERN = re.compile(r"\\l\s+(\d+)", re.IGNORECASE)
TOKEN_CANDIDATE_PATTERN = re.compile(r"\(?[A-Za-z0-9IVXLCDMivxlcdm]+\)?")
ROMAN_NUMERAL_MAP = {
    "I": 1,
    "V": 5,
    "X": 10,
    "L": 50,
    "C": 100,
    "D": 500,
    "M": 1000,
}


@dataclass(frozen=True)
class TocSynthesis:
    level: int
    list_payload: dict[str, Any]
    group_id: str


@dataclass(frozen=True)
class TocEntry:
    label: str
    level: int
    ordinal: str
    counters: list[int]
    formats: list[str]
    pattern: str


@dataclass(frozen=True)
class OrdinalParseResult:
    ordinal: str
    counters: list[int]
    formats: list[str]
    pattern: str


@dataclass(frozen=True)
class TokenInfo:
    value: int
    format: str
    prefix: str = ""
    suffix: str = ""


class TocFieldTracker:
    """Synthesize numbering metadata for headings defined via TOC field codes."""

    def __init__(self) -> None:
        self._group_counter = itertools.count(1)
        self._current_group_id: Optional[str] = None
        self._last_top_counter: Optional[int] = None
        self._ordinal_counts: dict[str, int] = {}

    def synthesize(self, paragraph: Paragraph) -> Optional[TocSynthesis]:
        """Synthesize numbering metadata for a paragraph that contains a TOC field."""

        entry = extract_tc_entry(paragraph, TOC_TC_PATTERN, TOC_LEVEL_PATTERN)
        if entry is None:
            return None

        group_id, restart_boundary = self._resolve_group(entry)
        ordinal_snapshot = self._ordinal_counts.get(group_id, 0) + 1
        self._ordinal_counts[group_id] = ordinal_snapshot

        num_id = 0
        abstract_num_id = 0
        num_format = entry.formats[-1] if entry.formats else "unknown"

        list_payload = {
            "num_id": num_id,
            "abstract_num_id": abstract_num_id,
            "level": entry.level,
            "counters": entry.counters,
            "ordinal": entry.ordinal,
            "format": num_format,
            "pattern": entry.pattern,
            "is_legal": len(entry.counters) > 1,
            "restart_boundary": restart_boundary and entry.level == 0,
            "list_instance_id": NumberingTracker._make_instance_id(
                num_id,
                abstract_num_id,
                group_id,
            ),
            "numbering_digest": NumberingTracker._make_numbering_digest(
                num_id=num_id,
                level=entry.level,
                num_fmt=num_format,
                pattern=entry.pattern,
            ),
            "ordinal_at_parse": ordinal_snapshot,
        }

        return TocSynthesis(level=entry.level, list_payload=list_payload, group_id=group_id)

    def reset(self) -> None:
        """Reset the tracker state."""

        self._group_counter = itertools.count(1)
        self._current_group_id = None
        self._last_top_counter = None
        self._ordinal_counts.clear()

    def _resolve_group(self, entry: TocEntry) -> tuple[str, bool]:
        """Return the group id for ``entry`` along with a restart flag."""

        counters = entry.counters
        level = entry.level
        restart = False

        if not counters:
            restart = True
        elif level == 0:
            if self._current_group_id is None:
                restart = True
            elif self._last_top_counter is not None and counters[0] <= self._last_top_counter:
                restart = True
            self._last_top_counter = counters[0]
        else:
            if self._current_group_id is None:
                restart = True

        if restart:
            seq = next(self._group_counter)
            group_id = NumberingTracker._make_group_id(0, seq)
            self._current_group_id = group_id
            self._ordinal_counts[group_id] = 0
            self._last_top_counter = counters[0] if counters and level == 0 else self._last_top_counter
            return group_id, True

        group_id = self._current_group_id or NumberingTracker._make_group_id(
            0, next(self._group_counter)
        )
        self._current_group_id = group_id
        self._ordinal_counts.setdefault(group_id, 0)
        return group_id, False


def extract_tc_entry(
    paragraph: Paragraph,
    tc_pattern: re.Pattern[str],
    level_pattern: re.Pattern[str],
) -> Optional[TocEntry]:
    """Extract TOC ordinal information from ``paragraph`` using the supplied patterns."""
    instr_nodes = paragraph._p.findall(".//" + qn("w:instrText"))
    if not instr_nodes:
        return None

    raw_instr = " ".join(node.text or "" for node in instr_nodes)
    match = tc_pattern.search(raw_instr)
    if not match:
        return None

    label = match.group(1).strip()
    parsed = parse_ordinal_prefix(label)
    if parsed is None or not parsed.counters:
        return None

    level_match = level_pattern.search(raw_instr)
    if level_match:
        try:
            level = max(int(level_match.group(1)) - 1, 0)
        except ValueError:
            level = max(len(parsed.counters) - 1, 0)
    else:
        level = max(len(parsed.counters) - 1, 0)

    return TocEntry(
        label=label,
        level=level,
        ordinal=parsed.ordinal,
        counters=parsed.counters,
        formats=parsed.formats,
        pattern=parsed.pattern,
    )


def parse_ordinal_prefix(label: str) -> Optional[OrdinalParseResult]:
    """Parse the numeric/roman/alphabetic counters that prefix a TOC label."""
    working = label.replace("\t", " ").replace("\u00a0", " ").strip()
    if not working:
        return None

    matches = list(TOKEN_CANDIDATE_PATTERN.finditer(working))
    for idx, match in enumerate(matches):
        token_info = parse_token(match.group(0))
        if token_info is None:
            continue

        start_idx = extend_prefix_start(working, match.start())
        token_infos: list[TokenInfo] = [token_info]
        spans: list[tuple[int, int]] = [match.span()]
        pos = match.end()

        for next_match in matches[idx + 1 :]:
            between = working[pos:next_match.start()]
            if between and any(ch not in " .)\t\u00a0-" for ch in between):
                break
            next_info = parse_token(next_match.group(0))
            if next_info is None:
                break
            token_infos.append(next_info)
            spans.append(next_match.span())
            pos = next_match.end()

        while pos < len(working) and working[pos] in ".])":
            pos += 1

        ordinal = working[start_idx:pos].strip()
        counters = [info.value for info in token_infos]
        formats = [info.format for info in token_infos]

        cursor = start_idx
        pattern_parts: list[str] = []
        for token_index, (span_start, span_end) in enumerate(spans):
            pattern_parts.append(working[cursor:span_start])
            pattern_parts.append(token_infos[token_index].prefix)
            pattern_parts.append(f"%{token_index + 1}")
            pattern_parts.append(token_infos[token_index].suffix)
            cursor = span_end
        pattern_parts.append(working[cursor:pos])
        pattern = "".join(pattern_parts).strip()

        return OrdinalParseResult(
            ordinal=ordinal,
            counters=counters,
            formats=formats,
            pattern=pattern,
        )

    return None


def extend_prefix_start(text: str, token_start: int) -> int:
    """Extend the slice backwards to include alphabetic prefixes for numbering."""
    idx = token_start
    while idx > 0 and text[idx - 1].isspace():
        idx -= 1
    word_start = idx
    while word_start > 0 and text[word_start - 1].isalpha():
        word_start -= 1
    prefix = text[word_start:token_start]
    if prefix and prefix.strip() and all(ch.isalpha() or ch.isspace() for ch in prefix):
        return word_start
    return token_start


def parse_token(token: str) -> Optional[TokenInfo]:
    """Parse an individual numbering token (decimal, roman, alphabetic)."""
    prefix = ""
    suffix = ""
    stripped = token
    if stripped.startswith("(") and stripped.endswith(")"):
        prefix = "("
        suffix = ")"
        stripped = stripped[1:-1]

    if not stripped:
        return None
    if stripped.isdigit():
        return TokenInfo(int(stripped), "decimal", prefix, suffix)
    if len(stripped) == 1 and stripped.isalpha():
        value = ord(stripped.lower()) - 96
        if 1 <= value <= 26:
            fmt = "upperLetter" if stripped.isupper() else "lowerLetter"
            return TokenInfo(value, fmt, prefix, suffix)
        return None
    roman_value = roman_to_int(stripped)
    if roman_value is not None:
        fmt = "upperRoman" if stripped.isupper() else "lowerRoman"
        return TokenInfo(roman_value, fmt, prefix, suffix)
    return None


def roman_to_int(token: str) -> Optional[int]:
    """Convert a roman numeral token to an integer."""
    if not token:
        return None
    upper = token.upper()
    if not all(ch in ROMAN_NUMERAL_MAP for ch in upper):
        return None

    total = 0
    prev_value = 0
    for ch in reversed(upper):
        value = ROMAN_NUMERAL_MAP[ch]
        if value < prev_value:
            total -= value
        else:
            total += value
            prev_value = value

    if total <= 0:
        return None

    if int_to_roman(total) != upper:
        return None
    return total


def int_to_roman(value: int) -> str:
    """Convert an integer to an uppercase roman numeral."""
    numerals = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]
    result: list[str] = []
    remaining = value
    for magnitude, glyph in numerals:
        while remaining >= magnitude:
            result.append(glyph)
            remaining -= magnitude
    return "".join(result)
