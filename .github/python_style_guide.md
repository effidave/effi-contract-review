# ** Python Style Guide (Clean Code Edition)**

Use this document as the single source of truth for code generation, refactoring, and reviews.

## 1)  Context

```
You are an experienced software developer and CLEAN Code advocate. Follow this style guide strictly:
- Prefer clarity over cleverness. Small, single-purpose functions.
- Enforce PEP 8, type hints, docstrings (Google or NumPy style).
- No magic numbers/strings: extract constants.
- Handle errors with specific exceptions; never swallow exceptions.
- Write unit tests first/with code (pytest). Aim for simple, deterministic tests.
- Log meaningfully (INFO for high-level flow, DEBUG for details, WARNING/ERROR for problems).
- Avoid duplication (DRY). Extract helpers.
- Keep modules cohesive; keep public APIs small.
- Include docstrings, type hints, and examples.
- Run black, isort, ruff/flake8, mypy, and pytest.
- Prefer dataclasses for simple data containers.
- Default to pure functions; isolate I/O, time, randomness.
- Provide "Good vs Bad" examples when creating new patterns.
```

## 2) Naming & Formatting

* `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants.
* Keep lines <= 100 chars (79–100 acceptable).
* One import per line; order standard library -> third-party -> local, separated by blank lines.

**Bad**

```python
x = 0; import os,sys
class user: pass
```

**Good**

```python
from __future__ import annotations

import os
import sys

MAX_RETRIES = 3

class User:
    ...
```

## 3) Functions: Small & Single-Purpose

* Target <= 20–30 lines.
* Use early returns; minimize nesting; pass explicit parameters.

```python
def is_active(user: User) -> bool:
    return bool(user and user.active)

def handle(user: User) -> bool:
    if not is_active(user):
        return False
    process(user)
    return True
```

## 4) Types & Docstrings (required)

* Use PEP 484 type hints everywhere.
* Public functions/classes must have docstrings (Google or NumPy style).

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Money:
    amount: float
    currency: str

def convert(amount: Money, to_currency: str) -> Money:
    """Convert between currencies.

    Args:
        amount: Source amount and currency.
        to_currency: Target ISO currency code.

    Returns:
        Converted amount with target currency.

    Raises:
        ValueError: If conversion rate is unavailable.
    """
    ...
```

## 5) Errors & Logging

* Catch specific exceptions; keep stack traces with `raise` or `raise from`.
* No silent `except`. Log context that aids debugging.
* Use the `logging` library; configure once (e.g., in `config/logging.py`).

```python
import logging

logger = logging.getLogger(__name__)

def load_config(path: str) -> dict:
    try:
        return _read_yaml(path)
    except FileNotFoundError:
        logger.error("Config not found: %s", path)
        raise
    except YamlError as exc:
        logger.exception("Invalid YAML at %s", path)
        raise ValueError("Invalid configuration") from exc
```

## 6) Constants, Config, and Magic Numbers

* Extract literals to a `constants.py` module or define a local `CONST_NAME` near use.

```python
RETRY_BACKOFF_S = 0.5
MAX_RETRIES = 3
```

## 7) Immutability & Side Effects

* Prefer pure functions; isolate I/O/time/randomness behind thin adapters.
* Use `@dataclass(frozen=True)` for value types when practical.

## 8) Collections & Defensive Coding

* Prefer explicit shapes: `dict[str, Any]` -> better yet, a dedicated dataclass/model.
* Validate inputs at boundaries (API, CLI, file load), not deep inside core logic.

## 9) Testing (pytest)

* One assertion concept per test; follow arrange–act–assert.
* Use fixtures for setup; avoid hidden global state.
* Name tests descriptively.

```python
import pytest

from project_name.pricing import discount

def test_discount_returns_zero_for_non_positive_price() -> None:
    assert discount(0) == 0
    assert discount(-1) == 0

@pytest.mark.parametrize("price, expected", [(100, 10), (50, 5)])
def test_discount_applies_percentage(price: int, expected: int) -> None:
    assert discount(price) == expected
```

## 10) Dependencies & IO Boundaries

* Wrap external services/files in gateways (e.g., `repositories/` modules).
* Use interfaces (protocols/ABCs) to allow testing via fakes.

## 11) Performance & Concurrency (when needed)

* Optimize after profiling (`cProfile`, `time.perf_counter`).
* Prefer `asyncio` for network concurrency, threads for blocking I/O, processes for CPU.
* Keep concurrency at the edges; core logic stays synchronous and testable.

## 12) Security & Safety Basics

* Never log secrets; use env vars or a secrets manager.
* Validate/escape external inputs; rely on strict JSON schemas where possible.
* Pin dependencies; scan with `pip-audit` or `safety`.

## 13) File/Module Guidelines

* Keep modules < 400–500 lines; split by domain where necessary.
* Minimize the public surface: define `__all__` or underscore-prefix internals.

## 14) Linting, Formatting, Typing (tooling)

Example `pyproject.toml` configuration:

```toml
[tool.black]
line-length = 100
target-version = ["py311"]

[tool.isort]
profile = "black"

[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N", "PL", "UP", "B"]
ignore = ["E203"]
target-version = "py311"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_any_generics = true
no_implicit_optional = true
```

## 15) Cross-Platform File Handling

This project runs on Windows. When writing files that will be read by other components (TypeScript extension, other parsers):

### Line Endings
* **Always normalize line endings** when reading files that may have been created on Windows (`\r\n`) vs Unix (`\n`).
* When writing structured files (YAML, JSON, Markdown), prefer explicit `\n` line endings for consistency.
* TypeScript/JavaScript regex patterns like `/^---\n/` will fail on Windows files with `\r\n` endings.

**Example - Reading files safely:**
```python
def read_normalized(path: str) -> str:
    """Read file with normalized line endings."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')
```

**Example - Writing with explicit line endings:**
```python
def write_yaml(path: str, content: str) -> None:
    """Write file with Unix line endings for cross-platform compatibility."""
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
```

### YAML Format Compatibility
* Python's `yaml.dump()` produces lists with **no leading spaces** before `-`:
  ```yaml
  tasks:
  - id: task1
    title: First
  ```
* Some parsers expect **2-space indent** before `-`:
  ```yaml
  tasks:
    - id: task1
      title: First
  ```
* When writing parsers, handle **both formats** to ensure Python ↔ TypeScript interoperability.
* When writing YAML, document which format is produced and ensure consumers can parse it.

### Testing Cross-Platform Compatibility
* Always include tests with **both line ending formats** (`\n` and `\r\n`).
* Include tests with **both YAML indentation styles** (0-space and 2-space list items).
* Test round-trips between Python and TypeScript serialization when both languages interact with the same files.

Adhering to this guide keeps the Effi-Local codebase clean, testable, and maintainable.
