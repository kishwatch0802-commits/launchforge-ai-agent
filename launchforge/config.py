"""Application configuration and lightweight safety helpers."""

from __future__ import annotations

import os
from typing import Any


APP_NAME = "LaunchForge"
APP_TAGLINE = "Adaptive Multi-Agent Small Business Launch Studio"
MAX_INPUT_CHARS = 5_000


def get_google_api_key() -> str | None:
    """Return an optional Gemini key without ever logging or exposing it."""

    return os.getenv("GOOGLE_API_KEY") or None


def sanitize_text(value: Any, max_chars: int = MAX_INPUT_CHARS) -> str:
    """Trim hostile or accidental huge input while preserving normal prose."""

    if value is None:
        return ""
    text = str(value).replace("\x00", " ").strip()
    text = " ".join(text.split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip() + "..."
    return text


def as_money(value: float | int) -> str:
    return f"${float(value):,.0f}"
