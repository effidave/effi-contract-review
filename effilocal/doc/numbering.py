"""Helpers for parsing Word numbering definitions (word/numbering.xml)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, MutableMapping, Sequence
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


@dataclass(frozen=True)
class LevelDefinition:
    """Definition for a single list level in numbering.xml."""

    level: int
    format: str | None
    text: str | None
    start: int
    is_legal: bool
    suffix: str | None = None
    restart: int | None = None


@dataclass(frozen=True)
class LevelOverride:
    """Overrides for a numbering level within a concrete numId."""

    level: int
    start_override: int | None = None
    definition: LevelDefinition | None = None


@dataclass(frozen=True)
class NumberingInstance:
    """Concrete numbering instance (w:num) used by paragraphs."""

    num_id: int
    abstract_num_id: int | None
    overrides: Mapping[int, LevelOverride]


@dataclass(frozen=True)
class NumberingDefinitions:
    """Aggregated numbering metadata for a document."""

    abstract_levels: Mapping[int, Mapping[int, LevelDefinition]]
    instances: Mapping[int, NumberingInstance]

    def get_level(
        self, num_id: int, level: int
    ) -> tuple[
        LevelDefinition | None,
        LevelOverride | None,
        LevelDefinition | None,
    ]:
        """Return effective level definition, override, and base definition."""

        instance = self.instances.get(num_id)
        if instance is None:
            return None, None, None

        override = instance.overrides.get(level)
        override_def = override.definition if override and override.definition else None

        base_def = None
        if instance.abstract_num_id is not None:
            base_def = self.abstract_levels.get(instance.abstract_num_id, {}).get(level)

        effective = override_def or base_def
        return effective, override, base_def


def parse_numbering_xml(xml: str) -> NumberingDefinitions:
    """Parse numbering.xml content into structured numbering metadata."""

    if not xml.strip():
        return NumberingDefinitions(abstract_levels={}, instances={})

    root = ET.fromstring(xml)
    abstract_levels: dict[int, dict[int, LevelDefinition]] = {}
    instances: dict[int, NumberingInstance] = {}

    for abstract in root.findall("w:abstractNum", NS):
        abstract_id = _parse_int(abstract.get(f"{{{W_NS}}}abstractNumId"))
        levels: dict[int, LevelDefinition] = {}
        for lvl in abstract.findall("w:lvl", NS):
            level_def = _parse_level_definition(lvl)
            if level_def is not None:
                levels[level_def.level] = level_def
        if abstract_id is not None and levels:
            abstract_levels[abstract_id] = levels

    for num in root.findall("w:num", NS):
        num_id = _parse_int(num.get(f"{{{W_NS}}}numId"))
        if num_id is None:
            continue

        abstract_num_id = None
        abstract_ref = num.find("w:abstractNumId", NS)
        if abstract_ref is not None:
            abstract_num_id = _parse_int(abstract_ref.get(f"{{{W_NS}}}val"))

        overrides: dict[int, LevelOverride] = {}
        for override_el in num.findall("w:lvlOverride", NS):
            override = _parse_override(override_el)
            if override is not None:
                overrides[override.level] = override

        instances[num_id] = NumberingInstance(
            num_id=num_id,
            abstract_num_id=abstract_num_id,
            overrides=overrides,
        )

    return NumberingDefinitions(abstract_levels=abstract_levels, instances=instances)


_CACHE: MutableMapping[tuple[str, int], NumberingDefinitions] = {}


def load_numbering(docx_path: Path) -> NumberingDefinitions:
    """
    Load numbering metadata for the given .docx.

    Results are cached based on file path and modification timestamp to avoid
    reparsing on repeated calls within the same run.
    """

    docx_path = Path(docx_path)
    if not docx_path.exists():
        return NumberingDefinitions(abstract_levels={}, instances={})

    try:
        mtime_ns = docx_path.stat().st_mtime_ns
    except OSError:
        mtime_ns = 0

    cache_key = (str(docx_path.resolve()), mtime_ns)
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached

    try:
        with ZipFile(docx_path) as archive:
            try:
                xml_bytes = archive.read("word/numbering.xml")
            except KeyError:
                numbering = NumberingDefinitions(abstract_levels={}, instances={})
            else:
                numbering = parse_numbering_xml(xml_bytes.decode("utf-8"))
    except (BadZipFile, OSError):
        numbering = NumberingDefinitions(abstract_levels={}, instances={})

    _CACHE[cache_key] = numbering
    return numbering


def _parse_level_definition(
    element: ET.Element, fallback_level: int | None = None
) -> LevelDefinition | None:
    lvl_val = element.get(f"{{{W_NS}}}ilvl")
    level = _parse_int(lvl_val)
    if level is None:
        level = fallback_level
    if level is None:
        return None

    start = 1
    start_el = element.find("w:start", NS)
    if start_el is not None:
        start = _parse_int(start_el.get(f"{{{W_NS}}}val")) or 1

    num_fmt = None
    num_fmt_el = element.find("w:numFmt", NS)
    if num_fmt_el is not None:
        num_fmt = num_fmt_el.get(f"{{{W_NS}}}val")

    lvl_text = None
    lvl_text_el = element.find("w:lvlText", NS)
    if lvl_text_el is not None:
        lvl_text = lvl_text_el.get(f"{{{W_NS}}}val")

    is_legal = element.find("w:isLgl", NS) is not None

    suffix = None
    suffix_el = element.find("w:suff", NS)
    if suffix_el is not None:
        suffix = suffix_el.get(f"{{{W_NS}}}val")

    restart = None
    restart_el = element.find("w:lvlRestart", NS)
    if restart_el is not None:
        restart = _parse_int(restart_el.get(f"{{{W_NS}}}val"))

    return LevelDefinition(
        level=level,
        format=num_fmt,
        text=lvl_text,
        start=start,
        is_legal=is_legal,
        suffix=suffix,
        restart=restart,
    )


def _parse_override(element: ET.Element) -> LevelOverride | None:
    level = _parse_int(element.get(f"{{{W_NS}}}ilvl"))
    if level is None:
        return None

    start_override = None
    start_el = element.find("w:startOverride", NS)
    if start_el is not None:
        start_override = _parse_int(start_el.get(f"{{{W_NS}}}val"))

    override_def = None
    lvl_el = element.find("w:lvl", NS)
    if lvl_el is not None:
        override_def = _parse_level_definition(lvl_el, fallback_level=level)

    return LevelOverride(level=level, start_override=start_override, definition=override_def)


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def format_ordinals(
    counters: Sequence[int],
    *,
    num_fmt: str | None,
    pattern: str | None,
    is_legal: bool = False,
    placeholder_formats: Sequence[str | None] | None = None,
    placeholder_is_legal: Sequence[bool] | None = None,
    suffix: str | None = None,
) -> str:
    """Render the display label for a numbering entry."""

    if not counters:
        return ""

    fmt = (num_fmt or "decimal").lower()

    if fmt == "bullet":
        glyph = pattern or ""
        return glyph or "•"

    placeholder_formats = placeholder_formats or []
    placeholder_is_legal = placeholder_is_legal or []

    tokens: dict[str, str] = {}
    for index, value in enumerate(counters, start=1):
        level_fmt = fmt
        if index - 1 < len(placeholder_formats):
            candidate = placeholder_formats[index - 1]
            if candidate:
                level_fmt = candidate.lower()

        level_legal = is_legal
        if index - 1 < len(placeholder_is_legal):
            level_legal = level_legal or placeholder_is_legal[index - 1]

        if level_legal:
            level_fmt = "decimal"

        tokens[f"%{index}"] = _format_value(level_fmt, value)

    template = (pattern or "").strip()
    if template:
        rendered = template
        for placeholder in sorted(tokens.keys(), key=len, reverse=True):
            rendered = rendered.replace(placeholder, tokens[placeholder])
        if "%" in rendered:
            rendered = _join_tokens(tokens)
    else:
        if is_legal or len(tokens) > 1:
            rendered = _join_tokens(tokens)
        else:
            rendered = tokens.get("%1", "")

    if suffix:
        suffix_lower = suffix.lower()
        if suffix_lower == "tab":
            rendered += "\t"
        elif suffix_lower == "space":
            rendered += " "

    return rendered


def _join_tokens(tokens: Mapping[str, str]) -> str:
    ordered: list[str] = []
    idx = 1
    while True:
        key = f"%{idx}"
        if key not in tokens:
            break
        ordered.append(tokens[key])
        idx += 1
    return ".".join(ordered)


def _format_value(fmt: str, value: int) -> str:
    if value <= 0:
        return str(value)

    fmt = fmt.lower()
    if fmt == "decimal":
        return str(value)
    if fmt == "lowerletter":
        return _alpha(value).lower()
    if fmt == "upperletter":
        return _alpha(value)
    if fmt == "lowerroman":
        return _roman(value).lower()
    if fmt == "upperroman":
        return _roman(value)
    if fmt in {"ordinal", "ordinaltext"}:
        # Placeholder for future natural language ordinals. For now, fallback.
        return str(value)
    if fmt == "bullet":
        return "•"
    return str(value)


def _alpha(value: int) -> str:
    result = ""
    current = value
    while current > 0:
        current -= 1
        result = chr(ord("A") + (current % 26)) + result
        current //= 26
    return result or "A"


def _roman(value: int) -> str:
    numerals = (
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
    )
    current = value
    result = ""
    for threshold, glyph in numerals:
        while current >= threshold:
            result += glyph
            current -= threshold
    return result or str(value)
