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


def detect_currency(*parts: Any) -> tuple[str, str]:
    """Detect a sensible display currency from user-provided launch context."""

    text = " ".join(str(part or "") for part in parts).lower()
    us_signals = [" usa", " u.s.", "united states", "new york", "california", "dollar", " usd", "$"]
    uk_signals = ["gcse", "a-level", "alevel", "esat", " uk", "london", "sixth form", "parents of gcse", "local area"]
    if any(signal in text for signal in us_signals):
        return "USD", "$"
    if any(signal in text for signal in uk_signals):
        return "GBP", "\u00a3"
    return "GBP", "\u00a3"


def as_money(value: float | int, symbol: str = "\u00a3") -> str:
    amount = float(value)
    if amount.is_integer():
        return f"{symbol}{amount:,.0f}"
    return f"{symbol}{amount:,.2f}"
