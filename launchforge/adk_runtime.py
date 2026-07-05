"""Optional Google ADK runtime bridge.

LaunchForge runs without ADK or API keys. When google-adk and GOOGLE_API_KEY are
configured, this module can construct LlmAgent objects for AI-assisted
reasoning. The deterministic tool layer remains the reliable fallback.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List


try:  # pragma: no cover - optional dependency path.
    from google.adk.agents import LlmAgent  # type: ignore
    from google.adk.runners import Runner  # type: ignore
    from google.adk.sessions import InMemorySessionService  # type: ignore
except Exception:  # noqa: BLE001
    LlmAgent = None  # type: ignore
    Runner = None  # type: ignore
    InMemorySessionService = None  # type: ignore

try:  # pragma: no cover - optional dependency path.
    from google import genai as google_genai  # type: ignore
except Exception:  # noqa: BLE001
    google_genai = None  # type: ignore

DEFAULT_MODEL = os.getenv("LAUNCHFORGE_ADK_MODEL", "gemini-2.5-flash")


@dataclass
class RuntimeStatus:
    mode: str
    provider: str
    adk_available: bool
    genai_available: bool
    api_key_available: bool
    model: str
    reason: str


def get_runtime_status() -> Dict[str, Any]:
    adk_available = LlmAgent is not None and Runner is not None and InMemorySessionService is not None
    genai_available = google_genai is not None
    api_key_available = bool(os.getenv("GOOGLE_API_KEY"))
    if api_key_available and genai_available:
        status = RuntimeStatus(
            mode="ai-assisted",
            provider="google-genai-gemini",
            adk_available=adk_available,
            genai_available=True,
            api_key_available=True,
            model=DEFAULT_MODEL,
            reason="GOOGLE_API_KEY and google-genai are configured, so Copilot can call Gemini.",
        )
    elif api_key_available and adk_available:
        status = RuntimeStatus(
            mode="ai-assisted",
            provider="google-adk-gemini",
            adk_available=True,
            genai_available=False,
            api_key_available=True,
            model=DEFAULT_MODEL,
            reason="GOOGLE_API_KEY and Google ADK are configured. Copilot will try ADK execution and fall back safely if unavailable.",
        )
    elif not api_key_available:
        status = RuntimeStatus(
            mode="deterministic-fallback",
            provider="fallback",
            adk_available=adk_available,
            genai_available=genai_available,
            api_key_available=False,
            model=DEFAULT_MODEL,
            reason="GOOGLE_API_KEY is not set, so no external Gemini call is attempted.",
        )
    else:
        status = RuntimeStatus(
            mode="deterministic-fallback",
            provider="fallback",
            adk_available=adk_available,
            genai_available=genai_available,
            api_key_available=True,
            model=DEFAULT_MODEL,
            reason="GOOGLE_API_KEY is set but neither google-genai nor executable Google ADK is available.",
        )
    return asdict(status)


def can_use_adk() -> bool:
    status = get_runtime_status()
    return bool(status["adk_available"] and status["api_key_available"])


def can_call_gemini() -> bool:
    status = get_runtime_status()
    return bool(status["api_key_available"] and status["genai_available"])


def build_llm_agent(name: str, description: str, instruction: str, tools: Iterable[Any] | None = None, model: str = DEFAULT_MODEL) -> Any:
    """Construct an ADK LlmAgent when available.

    The constructor signatures across ADK versions have shifted, so this tries
    the common signatures and raises a clear RuntimeError if construction is not
    possible in the installed environment.
    """

    if LlmAgent is None:
        raise RuntimeError("google-adk LlmAgent is not available.")
    tool_list = list(tools or [])
    try:
        return LlmAgent(name=name, description=description, instruction=instruction, tools=tool_list, model=model)
    except TypeError:
        try:
            return LlmAgent(name=name, instruction=instruction, tools=tool_list, model=model)
        except TypeError as exc:
            raise RuntimeError(f"Installed ADK LlmAgent signature is unsupported: {exc}") from exc


def agent_trace_entry(name: str, tools_called: List[str], output_summary: str, mode: str | None = None) -> Dict[str, Any]:
    runtime = get_runtime_status()
    selected_mode = mode or runtime["mode"]
    return {
        "trace_id": f"llm-{name.lower().replace(' ', '-').replace('_', '-')}",
        "type": "llm_agent",
        "name": name,
        "status": "completed" if selected_mode == "ai-assisted" else "registered",
        "mode": selected_mode,
        "instruction_summary": "Role-specific LlmAgent definition with tool access and deterministic fallback.",
        "tools_called": tools_called,
        "input_summary": "Launch pack context and founder brief.",
        "output_summary": output_summary,
        "metrics": {"tool_count": len(tools_called)},
        "visible_reasoning_summary": "Agent uses structured launch-pack context and reliable tools; hidden chain-of-thought is never exposed.",
        "limitations": runtime["reason"] if selected_mode == "deterministic-fallback" else "LLM output should still be reviewed by the founder.",
    }
