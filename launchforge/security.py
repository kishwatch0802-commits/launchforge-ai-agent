"""Security helpers for agent and Copilot inputs."""

from __future__ import annotations

import re
from typing import Dict

from launchforge.config import sanitize_text


PROMPT_INJECTION_PATTERNS = [
    r"ignore (all )?(previous|above) instructions",
    r"reveal (your )?(system|developer) prompt",
    r"show (hidden )?(chain[- ]of[- ]thought|reasoning)",
    r"bypass (the )?(safety|rules|guardrails)",
    r"act as (an )?unrestricted",
    r"developer mode",
]

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
API_KEY_RE = re.compile(r"\b(?:AIza[0-9A-Za-z_-]{20,}|sk-[0-9A-Za-z_-]{20,}|xox[baprs]-[0-9A-Za-z-]{20,})\b")


def detect_prompt_injection(text: str) -> bool:
    cleaned = sanitize_text(text, 1500).lower()
    return any(re.search(pattern, cleaned) for pattern in PROMPT_INJECTION_PATTERNS)


def redact_pii(text: str) -> str:
    redacted = EMAIL_RE.sub("[redacted-email]", text)
    redacted = PHONE_RE.sub("[redacted-phone]", redacted)
    redacted = API_KEY_RE.sub("[redacted-secret]", redacted)
    return redacted


def safe_copilot_input(text: str, max_chars: int = 1200) -> Dict[str, object]:
    sanitized = sanitize_text(text, max_chars)
    redacted = redact_pii(sanitized)
    blocked = detect_prompt_injection(redacted)
    return {
        "original_length": len(str(text or "")),
        "sanitized": sanitized,
        "redacted": redacted,
        "blocked": blocked,
        "reason": "Prompt injection pattern detected." if blocked else "",
    }
