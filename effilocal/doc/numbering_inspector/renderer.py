from __future__ import annotations

from typing import Optional

from .model import (
    AbstractState,
    BindingResult,
    NumberingResult,
    ParagraphData,
    build_paragraphs,
    normalize_glyphs,
)


def apply_fmt(value, fmt):
    if fmt == "decimal":
        return str(value)
    if fmt == "lowerLetter":
        s = ""
        x = value
        while x > 0:
            x, r = divmod(x - 1, 26)
            s = chr(97 + r) + s
        return s
    if fmt == "upperLetter":
        s = ""
        x = value
        while x > 0:
            x, r = divmod(x - 1, 26)
            s = chr(65 + r) + s
        return s
    if fmt in ("lowerRoman", "upperRoman"):
        vals = [
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
        n = value
        out = ""
        for v, sym in vals:
            while n >= v:
                out += sym
                n -= v
        return normalize_glyphs(out if fmt == "upperRoman" else out.lower())
    return ""


def token_numfmt(numbering_model, abs_id, level_index, num_id_for_para):
    abstracts = numbering_model["abstracts"]
    nums = numbering_model["nums"]
    resolved_abs_id = resolve_proxy_abstract(abstracts, abs_id)
    levels = abstracts[resolved_abs_id]["levels"]
    lvl_def = levels.get(level_index)
    base_fmt = lvl_def["numFmt"] if lvl_def else "decimal"
    if num_id_for_para is not None and num_id_for_para in nums:
        ov = nums[num_id_for_para]["lvlOverrides"].get(level_index)
        if ov and ov.get("lvlOverrideDef") and ov["lvlOverrideDef"].get("numFmt"):
            return ov["lvlOverrideDef"]["numFmt"]
    return base_fmt


def render_tokens(numbering_model, abs_id, pattern, counters1based, num_id_for_para):
    s = pattern
    for k in range(1, 10):
        token = f"%{k}"
        if token in s:
            val = counters1based.get(k, 0)
            fmt = token_numfmt(numbering_model, abs_id, k - 1, num_id_for_para)
            s = s.replace(token, apply_fmt(val, fmt))
    return s


def resolve_binding_for_paragraph(
    para: ParagraphData, abstracts, style_numpr
) -> Optional[BindingResult]:
    """Resolve how a paragraph binds to numbering (direct numPr, style, or style-link)."""
    direct = para.direct_numpr
    if direct:
        return BindingResult(
            source="paragraph",
            num_id=direct["numId"],
            ilvl=direct["ilvl"],
            num_restart=direct["numRestart"],
        )

    style_id = para.style_id
    if style_id in style_numpr:
        style_binding = style_numpr[style_id]
        return BindingResult(
            source="style",
            num_id=style_binding["numId"],
            ilvl=style_binding["ilvl"],
            num_restart=style_binding.get("numRestart", False),
        )

    for abs_id, info in abstracts.items():
        il = info["styleLink"].get(style_id)
        if il is not None:
            return BindingResult(source="style-link", num_id=None, ilvl=il, num_restart=False, abs_id=abs_id)

    return None


def effective_level_props(abstracts, nums, abs_id, ilvl, num_id):
    abs_id = resolve_proxy_abstract(abstracts, abs_id)
    lvl = abstracts[abs_id]["levels"][ilvl]
    pattern = lvl["pattern"]
    start = lvl["start"]
    base_numfmt = lvl["numFmt"]
    override_pattern = None
    override_numfmt = None
    override_start = None
    if num_id is not None and num_id in nums:
        ov = nums[num_id]["lvlOverrides"].get(ilvl)
        if ov:
            if "startOverride" in ov:
                override_start = ov["startOverride"]
            if ov.get("lvlOverrideDef"):
                override_pattern = ov["lvlOverrideDef"].get("pattern")
                override_numfmt = ov["lvlOverrideDef"].get("numFmt")
    effective_pattern = override_pattern if override_pattern is not None else pattern
    effective_numfmt = override_numfmt if override_numfmt is not None else base_numfmt
    effective_start = override_start if override_start is not None else start
    return {
        "base_pattern": pattern,
        "base_numFmt": base_numfmt,
        "base_start": start,
        "override_pattern": override_pattern,
        "override_numFmt": override_numfmt,
        "override_start": override_start,
        "effective_pattern": effective_pattern,
        "effective_numFmt": effective_numfmt,
        "effective_start": effective_start,
    }


def resolve_proxy_abstract(abstracts, abs_id):
    visited = set()
    while True:
        proxy = abstracts.get(abs_id, {}).get("proxy")
        if proxy is None or proxy in visited:
            break
        visited.add(proxy)
        abs_id = proxy
    return abs_id


def _build_row_dict(para: ParagraphData, binding: Optional[BindingResult]):
    return {
        "idx": para.idx,
        "paraId": para.para_id,
        "styleId": para.style_id,
        "source": binding.source if binding else "",
        "numId": "",
        "abstractNumId": "",
        "ilvl": "",
        "pattern": "",
        "rendered_number": "",
        "counters": None,
        "num_restart": binding.num_restart if binding else False,
        "prev_level": None,
        "text": para.text,
    }


def _build_debug_row(para: ParagraphData, binding: Optional[BindingResult], num_id_seen_before: bool):
    return {
        "idx": para.idx,
        "paraId": para.para_id,
        "styleId": para.style_id,
        "text": para.text,
        "binding_source": binding.source if binding else "",
        "binding_numId": binding.num_id if binding else None,
        "binding_ilvl": binding.ilvl if binding else None,
        "binding_numRestart": binding.num_restart if binding else False,
        "num_id_seen_before": num_id_seen_before,
        "resolved_numId": "",
        "resolved_ilvl": None,
        "resolved_abstractNumId": "",
        "is_style_linked": False,
        "base_pattern": None,
        "base_numFmt": None,
        "base_start": None,
        "override_start": None,
        "override_pattern": None,
        "override_numFmt": None,
        "effective_pattern": None,
        "effective_numFmt": None,
        "effective_start": None,
        "rendered_number": "",
        "tokens_used": None,
        "formatted_tokens_used": None,
        "counters_before": None,
        "counters_after": None,
        "prevLevel_before": None,
        "prevLevel_after": None,
        "started_new_level": False,
        "incremented_level": False,
        "reason_started": "",
        "descended_from_level": None,
        "reset_levels_from": None,
        "ancestors_touched": [],
    }


class NumberingSession:
    """Stateful processor that emits numbering rows per paragraph."""

    def __init__(
        self,
        nums,
        abstracts,
        style_numpr,
        *,
        debug: bool = False,
        log_event=None,
    ):
        self._nums = nums
        self._abstracts = abstracts
        self._style_numpr = style_numpr
        self._debug_enabled = debug
        self._shared = {abs_id: AbstractState([0] * 9) for abs_id in abstracts.keys()}
        self._seen_num_ids: set[int] = set()
        self._log_event = log_event

    def _log(self, event: str, **fields) -> None:
        if self._log_event is not None:
            self._log_event(event, fields)

    def reset_for_attachment(self) -> None:
        """Attachment transitions do not affect numbering state in the inspector."""
        # Intentionally a no-op: numbering restarts are derived from Word XML data.
        return None

    def process_paragraph(self, para: ParagraphData) -> NumberingResult:
        """Process a single paragraph and return the numbering payload."""

        binding = resolve_binding_for_paragraph(para, self._abstracts, self._style_numpr)
        row = _build_row_dict(para, binding)

        num_id_seen_before = False
        if binding and binding.num_id is not None:
            num_id_seen_before = binding.num_id in self._seen_num_ids

        debug_row = _build_debug_row(para, binding, num_id_seen_before)

        if not binding:
            if para.style_id:
                self._log(
                    "numbering.binding_missing",
                    paraId=para.para_id,
                    styleId=para.style_id,
                    reason="no_binding",
                )
            return NumberingResult(row=row, debug_row=debug_row if self._debug_enabled else None)

        source = binding.source
        num_id = binding.num_id
        ilvl = binding.ilvl
        abs_id = None

        if source in ("paragraph", "style"):
            if num_id is None or num_id not in self._nums:
                self._log(
                    "numbering.binding_missing_numpr",
                    paraId=para.para_id,
                    styleId=para.style_id,
                    numId=num_id,
                    source=source,
                )
                return NumberingResult(
                    row=row,
                    debug_row=debug_row if self._debug_enabled else None,
                )
            abs_id = self._nums[num_id]["abstractId"]
        else:
            abs_id = binding.abs_id

        style_id = para.style_id
        is_style_linked = self._abstracts[abs_id]["styleLink"].get(style_id) == ilvl
        if source == "style" and not is_style_linked:
            self._log(
                "numbering.style_link_mismatch",
                paraId=para.para_id,
                styleId=style_id,
                numId=num_id,
                ilvl=ilvl,
                expected_level=self._abstracts[abs_id]["styleLink"].get(style_id),
            )
            return NumberingResult(row=row, debug_row=debug_row if self._debug_enabled else None)

        effective_abs_id = resolve_proxy_abstract(self._abstracts, abs_id)
        state = self._shared.setdefault(effective_abs_id, AbstractState([0] * 9))
        reset_due_to_new_num = False
        # Note: We don't reset counters when numId changes because different numIds
        # can share the same abstractNumId, and Word continues the counter sequence
        # across them (e.g., numId 10 and 11 both referencing abstractNumId 101).
        if num_id is not None:
            if state.last_num_id is None:
                state.last_num_id = num_id
            elif state.last_num_id != num_id:
                state.last_num_id = num_id
        counters = state.counters
        prev_level = state.prev_level
        counters_before = counters.copy()
        prev_level_before = prev_level

        ancestors_touched = []
        for k in range(0, ilvl):
            if counters[k] == 0:
                base_start = self._abstracts[abs_id]["levels"][k]["start"]
                override_start = None
                if num_id is not None:
                    aov = self._nums[num_id]["lvlOverrides"].get(k)
                    if aov and "startOverride" in aov:
                        override_start = aov["startOverride"]
                final_value = override_start if override_start is not None else base_start
                counters[k] = final_value
                ancestors_touched.append(
                    {
                        "level": k,
                        "was_zero_before": True,
                        "base_start": base_start,
                        "override_start": override_start,
                        "final_value": final_value,
                    }
                )

        props = effective_level_props(self._abstracts, self._nums, abs_id, ilvl, num_id)
        reason_started = ""
        if binding.num_restart:
            reason_started = "numRestart"
        elif reset_due_to_new_num:
            reason_started = "new_numId"
        elif prev_level_before is not None and prev_level_before < ilvl:
            reason_started = "descend_to_deeper_level"
        elif counters[ilvl] == 0:
            reason_started = "ancestor_synthesized" if ancestors_touched else "first_use_level"

        started_new_level = reason_started != ""
        if started_new_level:
            counters[ilvl] = props["effective_start"]
            effective_start = props["effective_start"]
        else:
            counters[ilvl] += 1
            effective_start = None

        reset_levels_from = next((k for k in range(ilvl + 1, 9) if counters_before[k] != 0), None)
        for k in range(ilvl + 1, 9):
            counters[k] = 0
        if reset_levels_from is not None and reset_levels_from > ilvl:
            self._log(
                "numbering.counter_reset",
                paraId=para.para_id,
                styleId=para.style_id,
                numId=num_id,
                ilvl=ilvl,
                reset_from=reset_levels_from,
                reason=reason_started or "reset_levels_from",
            )

        counters_after = counters.copy()
        prev_level_after = ilvl
        state.prev_level = ilvl

        counters1 = {k + 1: counters[k] for k in range(9)}
        numbering_model = {"abstracts": self._abstracts, "nums": self._nums}
        rendered = normalize_glyphs(
            render_tokens(numbering_model, abs_id, props["effective_pattern"], counters1, num_id)
        )
        if props["effective_numFmt"] == "none":
            rendered = ""

        row.update(
            {
                "numId": num_id if num_id is not None else "",
                "abstractNumId": abs_id,
                "ilvl": ilvl,
                "pattern": normalize_glyphs(props["effective_pattern"]),
                "format": props["effective_numFmt"],
                "rendered_number": rendered,
                "counters": counters_after,
                "num_restart": binding.num_restart,
                "prev_level": prev_level_after,
            }
        )

        if num_id is not None:
            self._seen_num_ids.add(num_id)
        if self._debug_enabled:
            debug_row.update(
                {
                    "resolved_numId": num_id if num_id is not None else "",
                    "resolved_ilvl": ilvl,
                    "resolved_abstractNumId": abs_id,
                    "is_style_linked": bool(is_style_linked),
                    "base_pattern": normalize_glyphs(props["base_pattern"]),
                    "base_numFmt": props["base_numFmt"],
                    "base_start": props["base_start"],
                    "override_pattern": props["override_pattern"],
                    "override_numFmt": props["override_numFmt"],
                    "override_start": props["override_start"],
                    "effective_pattern": normalize_glyphs(props["effective_pattern"]),
                    "effective_numFmt": props["effective_numFmt"],
                    "effective_start": effective_start,
                    "rendered_number": rendered,
                    "tokens_used": normalize_glyphs(props["effective_pattern"]),
                    "formatted_tokens_used": rendered,
                    "counters_before": counters_before,
                    "counters_after": counters_after,
                    "prevLevel_before": prev_level_before,
                    "prevLevel_after": prev_level_after,
                    "started_new_level": started_new_level,
                    "incremented_level": not started_new_level,
                    "reason_started": reason_started,
                    "descended_from_level": (
                        prev_level_before if prev_level_before is not None and prev_level_before < ilvl else None
                    ),
                    "reset_levels_from": reset_levels_from,
                    "ancestors_touched": ancestors_touched,
                }
            )

        return NumberingResult(row=row, debug_row=debug_row if self._debug_enabled else None)


def walk_paragraphs(doc, nums, abstracts, style_numpr, debug=False):
    session = NumberingSession(nums, abstracts, style_numpr, debug=debug)
    rows = []
    debug_rows = []
    for para in build_paragraphs(doc):
        result = session.process_paragraph(para)
        rows.append(result.row)
        if debug and result.debug_row:
            debug_rows.append(result.debug_row)
    return rows, debug_rows
