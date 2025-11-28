# Sprint 6 – Numbering Tracker Replacement Technical Specification

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
