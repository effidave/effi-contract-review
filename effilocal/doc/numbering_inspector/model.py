from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from lxml import etree

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
}

BULLET_PRIVATE_USE = "\uf0b7"
BULLET_REPLACEMENT = "\u2022"


def normalize_glyphs(value):
    if isinstance(value, str):
        return value.replace(BULLET_PRIVATE_USE, BULLET_REPLACEMENT)
    return value


@dataclass
class ParagraphData:
    idx: int
    para_id: str
    style_id: str
    text: str
    direct_numpr: Optional[dict]


@dataclass
class BindingResult:
    source: str
    num_id: Optional[int]
    ilvl: Optional[int]
    num_restart: bool
    abs_id: Optional[int] = None


@dataclass
class AbstractState:
    counters: list[int]
    prev_level: Optional[int] = None
    last_num_id: Optional[int] = None


@dataclass
class NumberingResult:
    """Container for the numbering data produced per paragraph."""

    row: dict[str, Any]
    debug_row: dict[str, Any] | None = None

    @property
    def rendered_number(self) -> str:
        return self.row.get("rendered_number", "") or ""

    @property
    def num_id(self) -> Optional[int]:
        num_id = self.row.get("numId")
        return int(num_id) if isinstance(num_id, int) else None

    @property
    def abstract_num_id(self) -> Optional[int]:
        abs_id = self.row.get("abstractNumId")
        return int(abs_id) if isinstance(abs_id, int) else None


def build_numbering_maps(num_tree, styles_tree):
    """Return (nums, abstracts, style_numpr) dictionaries for numbering resolution.
    
    If num_tree is None (document has no numbering.xml), returns empty dicts for nums/abstracts.
    """
    if num_tree is None:
        nums = {}
        abstracts = {}
    else:
        nums = _extract_number_definitions(num_tree)
        abstracts = _extract_abstract_definitions(num_tree)
    style_numpr = _resolve_paragraph_style_numbering(styles_tree)
    numbering_style_numpr = _extract_numbering_style_links(styles_tree)
    _apply_num_style_links(abstracts, numbering_style_numpr, nums)
    return nums, abstracts, style_numpr


def build_paragraphs(doc_tree) -> list[ParagraphData]:
    """Return structured paragraph data for every paragraph in the document body."""
    paragraphs: list[ParagraphData] = []
    for idx, para_node in enumerate(doc_tree.xpath("//w:body//w:p", namespaces=NS)):
        para_id = (para_node.xpath("./@w14:paraId", namespaces=NS) or [""])[0]
        style_id = para_style(para_node) or ""
        text = para_text(para_node)
        paragraphs.append(
            ParagraphData(
                idx=idx,
                para_id=para_id,
                style_id=style_id,
                text=text,
                direct_numpr=para_numpr(para_node),
            )
        )
    return paragraphs


def para_text(p):
    return normalize_glyphs("".join(p.xpath(".//w:t/text()", namespaces=NS)).strip())


def para_style(p):
    s = p.xpath("./w:pPr/w:pStyle/@w:val", namespaces=NS)
    return s[0] if s else None


def para_numpr(p):
    npr = p.xpath("./w:pPr/w:numPr", namespaces=NS)
    if not npr:
        return None
    il = npr[0].xpath("./w:ilvl/@w:val", namespaces=NS)
    ni = npr[0].xpath("./w:numId/@w:val", namespaces=NS)
    nr = bool(npr[0].xpath("./w:numRestart", namespaces=NS))
    return {
        "numId": int(ni[0]) if ni else None,
        "ilvl": int(il[0]) if il else 0,
        "numRestart": nr,
    }


def _extract_number_definitions(num_tree):
    nums = {}
    for n in num_tree.xpath("//w:num", namespaces=NS):
        num_id = int(n.xpath("./@w:numId", namespaces=NS)[0])
        abs_id = int(n.xpath("./w:abstractNumId/@w:val", namespaces=NS)[0])
        lvl_overrides = {}
        for override in n.xpath("./w:lvlOverride", namespaces=NS):
            lvl_overrides[int(override.xpath("./@w:ilvl", namespaces=NS)[0])] = (
                _parse_level_override(override)
            )
        nums[num_id] = {"abstractId": abs_id, "lvlOverrides": lvl_overrides}
    return nums


def _parse_level_override(node):
    override = {}
    start_value = node.xpath("./w:startOverride/@w:val", namespaces=NS)
    if start_value:
        override["startOverride"] = int(start_value[0])
    lvl_node = node.xpath("./w:lvl", namespaces=NS)
    if lvl_node:
        level = lvl_node[0]
        pattern = level.xpath("./w:lvlText/@w:val", namespaces=NS)
        fmt = level.xpath("./w:numFmt/@w:val", namespaces=NS)
        override["lvlOverrideDef"] = {
            "pattern": pattern[0] if pattern else None,
            "numFmt": fmt[0] if fmt else None,
        }
    return override


def _extract_abstract_definitions(num_tree):
    abstracts = {}
    for abstract in num_tree.xpath("//w:abstractNum", namespaces=NS):
        abs_id = int(abstract.xpath("./@w:abstractNumId", namespaces=NS)[0])
        levels, style_link = _parse_abstract_levels(abstract)
        num_style_link = (abstract.xpath("./w:numStyleLink/@w:val", namespaces=NS) or [None])[
            0
        ]
        abstracts[abs_id] = {"levels": levels, "styleLink": style_link, "numStyleLink": num_style_link}
    return abstracts


def _parse_abstract_levels(abstract):
    levels = {}
    style_link = {}
    for lvl in abstract.xpath("./w:lvl", namespaces=NS):
        ilvl = int(lvl.xpath("./@w:ilvl", namespaces=NS)[0])
        pattern = normalize_glyphs((lvl.xpath("./w:lvlText/@w:val", namespaces=NS) or [""])[0])
        fmt = (lvl.xpath("./w:numFmt/@w:val", namespaces=NS) or ["decimal"])[0]
        start = int((lvl.xpath("./w:start/@w:val", namespaces=NS) or ["1"])[0])
        paragraph_style = lvl.xpath("./w:pStyle/@w:val", namespaces=NS)
        levels[ilvl] = {
            "pattern": pattern,
            "numFmt": fmt,
            "start": start,
            "pStyle": paragraph_style[0] if paragraph_style else None,
        }
        if paragraph_style:
            style_link[paragraph_style[0]] = ilvl
    return levels, style_link


def _resolve_paragraph_style_numbering(styles_tree):
    direct_map, based_on_map = _collect_paragraph_style_info(styles_tree)
    style_numpr = {}
    all_style_ids = set(based_on_map) | set(direct_map)
    for style_id in all_style_ids:
        resolved = _resolve_style_chain(style_id, direct_map, based_on_map)
        if resolved:
            style_numpr[style_id] = resolved
    return style_numpr


def _collect_paragraph_style_info(styles_tree):
    direct_style_numpr = {}
    style_based_on = {}
    for style in styles_tree.xpath("//w:style[@w:type='paragraph']", namespaces=NS):
        style_id = style.xpath("./@w:styleId", namespaces=NS)[0]
        base = style.xpath("./w:basedOn/@w:val", namespaces=NS)
        if base:
            style_based_on[style_id] = base[0]
        numpr = style.xpath("./w:pPr/w:numPr", namespaces=NS)
        if numpr:
            info = _parse_style_numpr(numpr[0])
            if info:
                direct_style_numpr[style_id] = info
    return direct_style_numpr, style_based_on


def _parse_style_numpr(numpr_node):
    ilvl = numpr_node.xpath("./w:ilvl/@w:val", namespaces=NS)
    num_id = numpr_node.xpath("./w:numId/@w:val", namespaces=NS)
    restart = bool(numpr_node.xpath("./w:numRestart", namespaces=NS))
    info = {}
    if num_id:
        info["numId"] = int(num_id[0])
    if ilvl:
        info["ilvl"] = int(ilvl[0])
    if restart:
        info["numRestart"] = True
    return info


def _resolve_style_chain(style_id, direct_style_numpr, style_based_on):
    visited = set()
    current = style_id
    resolved = {}
    while current and current not in visited:
        visited.add(current)
        data = direct_style_numpr.get(current)
        if data:
            if "numId" in data and "numId" not in resolved:
                resolved["numId"] = data["numId"]
            if "ilvl" in data and "ilvl" not in resolved:
                resolved["ilvl"] = data["ilvl"]
            if data.get("numRestart") and "numRestart" not in resolved:
                resolved["numRestart"] = True
            if "numId" in resolved and "ilvl" in resolved:
                break
        current = style_based_on.get(current)
    num_id = resolved.get("numId")
    if num_id is None:
        return None
    ilvl = resolved.get("ilvl", 0)
    return {"numId": num_id, "ilvl": ilvl, "numRestart": resolved.get("numRestart", False)}


def _extract_numbering_style_links(styles_tree):
    numbering_style_numpr = {}
    for style in styles_tree.xpath("//w:style[@w:type='numbering']", namespaces=NS):
        style_id = style.xpath("./@w:styleId", namespaces=NS)[0]
        numpr = style.xpath("./w:pPr/w:numPr", namespaces=NS)
        if numpr:
            ilvl = numpr[0].xpath("./w:ilvl/@w:val", namespaces=NS)
            num_id = numpr[0].xpath("./w:numId/@w:val", namespaces=NS)
            if num_id:
                numbering_style_numpr[style_id] = {
                    "numId": int(num_id[0]),
                    "ilvl": int(ilvl[0]) if ilvl else 0,
                }
    return numbering_style_numpr


def _apply_num_style_links(abstracts, numbering_style_numpr, nums):
    for abs_id, info in abstracts.items():
        style_link_val = info.get("numStyleLink")
        if style_link_val and style_link_val in numbering_style_numpr:
            num_id_for_style = numbering_style_numpr[style_link_val]["numId"]
            if num_id_for_style in nums:
                info["proxy"] = nums[num_id_for_style]["abstractId"]
