from __future__ import annotations

import os
from typing import Any, Callable

try:
    import logfire
except ImportError:  # pragma: no cover - logfire optional at runtime
    logfire = None  # type: ignore[assignment]


def _env_enabled() -> bool:
    enabled = os.getenv("LOGFIRE_ENABLE", "")
    return enabled.lower() in {"1", "true", "yes", "on"}


def _ensure_configured() -> None:
    if logfire is None:
        return
    if not logfire.is_configured():
        logfire.configure(send_to_logfire="if-token-present", min_level="info")


def build_emitter(enabled: bool | None = None) -> Callable[[str, dict[str, Any]], None] | None:
    """Return a no-op or Logfire-backed emitter based on availability and toggle."""

    use_logging = _env_enabled() if enabled is None else bool(enabled)
    if not use_logging or logfire is None:
        return None

    _ensure_configured()

    def emit(event: str, payload: dict[str, Any]) -> None:
        logfire.event(event, **payload)

    return emit
