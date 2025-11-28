"""Logfire initialization and tracing helpers for effi-local."""

from __future__ import annotations

from contextlib import AbstractContextManager
import os
import threading
from importlib import metadata
from typing import Any, Dict, Sequence

import logfire

__all__ = ["configure_logfire", "get_tracer"]

_CONFIG_LOCK = threading.Lock()
_CONFIGURED = False


def _resolve_version() -> str:
    """Return the installed effi-local version or a sensible fallback."""

    candidates = ("effilocal", "effi-local")
    for name in candidates:
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return os.getenv("EFFI_LOCAL_VERSION", "0.0.0")


_APP_VERSION = _resolve_version()


def configure_logfire(*, force: bool = False) -> None:
    """Configure Logfire once for the current process."""

    global _CONFIGURED
    with _CONFIG_LOCK:
        if _CONFIGURED and not force:
            return

        service_name = os.getenv("LOGFIRE_SERVICE_NAME", "effi-local")
        service_version = os.getenv("LOGFIRE_SERVICE_VERSION", _APP_VERSION) or _APP_VERSION
        environment = os.getenv("LOGFIRE_ENVIRONMENT", "development")
        send_to_logfire = os.getenv("LOGFIRE_SEND_TO_LOGFIRE") or "if-token-present"

        configure_kwargs: Dict[str, Any] = {
            "send_to_logfire": send_to_logfire,
            "service_name": service_name,
            "service_version": service_version,
            "environment": environment,
        }

        min_level = os.getenv("LOGFIRE_MIN_LEVEL")
        if min_level:
            configure_kwargs["min_level"] = min_level

        logfire.configure(**configure_kwargs)
        _CONFIGURED = True


def get_tracer(
    flow: str,
    *,
    doc_id: str | None = None,
    question: str | None = None,
    model: str | None = None,
    tags: Sequence[str] | None = None,
) -> AbstractContextManager[object]:
    """Return a Logfire span context configured with effi-local metadata."""

    configure_logfire()

    attributes: Dict[str, Any] = {
        "flow": flow,
        "version": _APP_VERSION,
    }
    if doc_id:
        attributes["doc_id"] = doc_id
    if question:
        attributes["question"] = question
    if model:
        attributes["model"] = model

    span_tags = ["effi-local", f"flow={flow}"]
    if doc_id:
        span_tags.append(f"doc_id={doc_id}")
    if tags:
        if isinstance(tags, str):
            span_tags.append(tags)
        else:
            span_tags.extend(tags)

    return logfire.span(
        "effi-local {flow}",
        _span_name=f"{flow}.run",
        _tags=span_tags,
        **attributes,
    )


# The following helper is only intended for testing to reset configuration state.
def _reset_for_tests() -> None:
    global _CONFIGURED
    with _CONFIG_LOCK:
        _CONFIGURED = False
