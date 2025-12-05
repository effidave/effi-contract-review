# Word Numbering System & Implementation

This document explains how Microsoft Word's numbering system works at the OOXML level and how our `NumberingInspector` interprets these signals to render correct clause ordinals.

---

## Understanding Word's Numbering Architecture

Word's numbering system has three key concepts that developers must understand:

### Abstract Numbering Definitions (`abstractNumId`)

An **abstract numbering definition** lives in `numbering.xml` and describes the *format* of a numbering scheme:
- Pattern templates (e.g., `%1.%2` for multi-level like "1.1", "1.2")
- Number formats (`decimal`, `lowerLetter`, `lowerRoman`, etc.)
- Start values for each level
- Indentation and styling

```xml
<w:abstractNum w:abstractNumId="53">
  <w:lvl w:ilvl="0">
    <w:start w:val="1"/>
    <w:numFmt w:val="decimal"/>
    <w:lvlText w:val="%1."/>
  </w:lvl>
  <w:lvl w:ilvl="1">
    <w:start w:val="1"/>
    <w:numFmt w:val="decimal"/>
    <w:lvlText w:val="%1.%2"/>
  </w:lvl>
  <!-- ... more levels ... -->
</w:abstractNum>
```

### Numbering Instances (`numId`)

A **numbering instance** (`<w:num>`) references an abstract definition and optionally applies overrides. Multiple `numId` values can reference the same `abstractNumId`.

**Without overrides** - paragraphs using different `numId`s that share the same `abstractNumId` will share counter state:

```xml
<w:num w:numId="29">
  <w:abstractNumId w:val="53"/>
  <!-- No overrides - continues from previous usage of abstractNumId 53 -->
</w:num>
```

**With startOverride** - explicitly restarts counters at specified values:

```xml
<w:num w:numId="33">
  <w:abstractNumId w:val="53"/>
  <w:lvlOverride w:ilvl="0">
    <w:startOverride w:val="1"/>  <!-- Restart level 0 at 1 -->
  </w:lvlOverride>
  <w:lvlOverride w:ilvl="1">
    <w:startOverride w:val="1"/>  <!-- Restart level 1 at 1 -->
  </w:lvlOverride>
  <!-- ... -->
</w:num>
```

### Counter State Management

By default, paragraphs using the same `abstractNumId` share a single counter state. This allows:
- Clause numbering to continue across sections (1, 2, 3... in body, then 4, 5, 6... in different section)
- Bullet lists to maintain consistent formatting

However, when Word wants numbering to restart (e.g., each Schedule in a contract should have its own clause 1), it creates a new `numId` with `<w:startOverride>` elements.

---

## Real-World Example: Schedule Numbering

In a contract with multiple Schedules, Word creates separate `numId` instances for each Schedule's clause numbering:

| Schedule | numId | abstractNumId | startOverride? | Result |
|----------|-------|---------------|----------------|--------|
| Schedule 5 | 29 | 53 | ❌ No | Clauses 1-11 |
| Schedule 6 | 33 | 53 | ✅ Yes (val="1") | Clauses restart at 1 |

**Why this matters:** Without honoring `startOverride`, Schedule 6's clauses would incorrectly continue from Schedule 5 (12, 13, 14...) instead of restarting at 1.

---

## Implementation: How We Honor Word Signals

The `NumberingSession` in `renderer.py` tracks state per `abstractNumId` and detects when `numId` changes require a restart:

```python
# When numId changes, check for startOverride
if num_id is not None:
    if state.last_num_id is None:
        state.last_num_id = num_id
    elif state.last_num_id != num_id:
        # numId changed - check for startOverride on the new numId
        lvl_overrides = self._nums.get(num_id, {}).get("lvlOverrides", {})
        ov = lvl_overrides.get(ilvl)
        if ov and "startOverride" in ov:
            # Word explicitly says to restart - flag it
            reset_due_to_new_num = True
        state.last_num_id = num_id
```

When `reset_due_to_new_num` is True, we apply `effective_start` (which includes the override value) instead of incrementing.

---

## Debugging Numbering Issues

When clause numbers are wrong, check:

1. **Extract numbering.xml**: `unzip -p document.docx word/numbering.xml | xmllint --format -`

2. **Find the numId** for the problematic paragraph in `blocks.jsonl`:
   ```json
   {"para_idx": 527, "list": {"num_id": 33, "abstract_num_id": 53, "ordinal": "12."}}
   ```

3. **Check for startOverride** in `numbering.xml`:
   ```xml
   <w:num w:numId="33">
     <w:abstractNumId w:val="53"/>
     <w:lvlOverride w:ilvl="0">
       <w:startOverride w:val="1"/>  <!-- Should restart at 1! -->
     </w:lvlOverride>
   </w:num>
   ```

4. **If startOverride exists but isn't honored**, the bug is in our counter management logic.

---

## Sprint 6 – Numbering Tracker Replacement Technical Specification

Replace `effilocal/doc/trackers/numbering_tracker.py` with the stage-based numbering logic from `scripts/new_chat_code_exported.py`, keeping the `AnalysisPipeline` contract intact. The rewrite will follow our Clean Code principles: discrete modules with single responsibilities, well-named data structures, thorough tests, and clear documentation.

## 1. Architecture Overview

### 1.1 Modules

| Module | Responsibility |
| --- | --- |
| `effilocal/doc/numbering_inspector/__init__.py` | Export a cohesive API (`NumberingInspector`) for numbering analysis |
| `effilocal/doc/numbering_inspector/parser.py` | Stage 1 helpers: DOCX part parsing/validation |
| `effilocal/doc/numbering_inspector/model.py` | Stage 2/3 helpers: dataclasses, numbering maps, paragraph normalization |
| `effilocal/doc/numbering_inspector/renderer.py` | Stage 4 helpers: counter management, formatting, debug-row assembly |
| `effilocal/doc/trackers/numbering_tracker.py` | Tracker integrating inspector with pipeline |
| `scripts/new_numbering_cli.py` (optional) | CLI wrapper around shared inspector for debugging |

Each module keeps its public surface minimal, making dependencies explicit and enabling targeted unit tests.

### 1.2 Data Flow

1. `AnalysisPipeline` instantiates `NumberingTracker`.
2. Tracker receives `ParagraphBlock`-style dictionaries, forwards them to `NumberingInspector.process_paragraph`, and receives enriched numbering info.
3. Inspector internally:
   - Parses/loads numbering XML once per document (Stage 1).
   - Builds numbering maps and style inheritance (Stage 2).
   - Normalizes paragraphs into `ParagraphData` instances (Stage 3a) and resolves bindings (Stage 3b).
   - Manages counters/rendered numbers via `CounterManager` (Stage 4).
4. Tracker publishes ordinals, counters, restarts, and digests to downstream consumers.
