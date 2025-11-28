"""Style aggregation with pluggable semantic strategies."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Protocol


@dataclass
class StyleUsage:
    """Aggregated data for a single Word style."""

    name: str
    count: int = 0
    block_types: Counter[str] = field(default_factory=Counter)
    sample_texts: list[str] = field(default_factory=list)

    def add_block(self, block: Mapping[str, object]) -> None:
        self.count += 1
        block_type = str(block.get("type", "unknown"))
        self.block_types[block_type] += 1
        text = str(block.get("text") or "").strip()
        if text and len(self.sample_texts) < 5:
            self.sample_texts.append(text)

    @property
    def dominant_block_type(self) -> str:
        if not self.block_types:
            return "unknown"
        return self.block_types.most_common(1)[0][0]


class StyleStrategy(Protocol):
    """Strategy interface returning semantic hint scores."""

    name: str

    def score(self, usage: StyleUsage) -> Mapping[str, float]:
        ...


class HeadingKeywordStrategy:
    name = "heading_keyword"

    def score(self, usage: StyleUsage) -> Mapping[str, float]:
        scores: dict[str, float] = {}
        name_lower = usage.name.lower()
        if usage.dominant_block_type == "heading":
            scores["clause_heading"] = scores.get("clause_heading", 0.0) + 1.0
        if "heading" in name_lower:
            scores["clause_heading"] = scores.get("clause_heading", 0.0) + 0.75
        if name_lower.startswith("title"):
            scores["clause_heading"] = scores.get("clause_heading", 0.0) + 0.5
        return scores


class ListPatternStrategy:
    name = "list_pattern"
    _bullet_regex = re.compile(r"^(\d+(\.\d+)*[.)-]?|\(?[a-z]\)|[-•])\s")

    def score(self, usage: StyleUsage) -> Mapping[str, float]:
        scores: dict[str, float] = {}
        name_lower = usage.name.lower()
        if any(token in name_lower for token in ("list", "bullet", "number")):
            scores["list_item"] = scores.get("list_item", 0.0) + 1.0

        for sample in usage.sample_texts:
            if self._bullet_regex.match(sample):
                scores["list_item"] = scores.get("list_item", 0.0) + 0.75
                break
        return scores


class DefinitionCueStrategy:
    name = "definition_cue"

    def score(self, usage: StyleUsage) -> Mapping[str, float]:
        scores: dict[str, float] = {}
        name_lower = usage.name.lower()
        if "definition" in name_lower or "defined" in name_lower:
            scores["definition"] = scores.get("definition", 0.0) + 0.75
        if usage.dominant_block_type != "paragraph":
            return scores

        for sample in usage.sample_texts:
            sample_lower = sample.lower()
            if '" means' in sample_lower or " means " in sample_lower:
                scores["definition"] = scores.get("definition", 0.0) + 1.0
                break
        return scores


DEFAULT_STRATEGIES: tuple[StyleStrategy, ...] = (
    HeadingKeywordStrategy(),
    ListPatternStrategy(),
    DefinitionCueStrategy(),
)

STYLE_TYPE_FALLBACK = {
    "heading": "heading",
    "paragraph": "paragraph",
    "table_cell": "table_cell",
    "image_caption": "image_caption",
}


def analyze_styles(
    blocks: Iterable[Mapping[str, object]],
    *,
    strategies: Iterable[StyleStrategy] | None = None,
) -> dict[str, object]:
    """
    Aggregate style usage statistics with semantic hints.

    Args:
        blocks: Iterable of block dictionaries following block.schema.json.
        strategies: Optional custom strategy list. Defaults to DEFAULT_STRATEGIES.

    Returns:
        Dictionary ready for serialization to ``styles.json``.
    """

    strategy_list = tuple(strategies) if strategies is not None else DEFAULT_STRATEGIES
    usages: dict[str, StyleUsage] = {}

    for block in blocks:
        style_name = str(block.get("style") or "").strip()
        if not style_name:
            style_name = "<unnamed>"
        usage = usages.setdefault(style_name, StyleUsage(name=style_name))
        usage.add_block(block)

    styles_output: list[dict[str, object]] = []
    for usage in sorted(usages.values(), key=lambda u: u.name.lower()):
        hint_scores: dict[str, float] = {}
        for strategy in strategy_list:
            for hint, score in strategy.score(usage).items():
                hint_scores[hint] = hint_scores.get(hint, 0.0) + float(score)

        semantic_hint = None
        if hint_scores:
            semantic_hint = max(hint_scores.items(), key=lambda item: item[1])[0]

        dominant_type = STYLE_TYPE_FALLBACK.get(
            usage.dominant_block_type, "unknown"
        )

        styles_output.append(
            {
                "name": usage.name,
                "type": dominant_type,
                "count": usage.count,
                "semantic_hint": semantic_hint,
                "hint_scores": hint_scores or None,
            }
        )

    return {"styles": styles_output}
