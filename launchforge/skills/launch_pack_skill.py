"""High-level launch pack assembly skill.

This skill keeps final pack assembly reusable outside Streamlit, for example
from a notebook, MCP client, or future ADK runner.
"""

from __future__ import annotations

from typing import Any, Dict

from launchforge.schemas import LaunchPack


def assemble_launch_pack_skill(**kwargs: Dict[str, Any]) -> LaunchPack:
    """Validate and assemble a complete LaunchPack Pydantic object."""

    return LaunchPack(**kwargs)
