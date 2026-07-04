"""Base classes for LaunchForge agents."""

from __future__ import annotations

from typing import Any, Dict


class LaunchForgeAgent:
    """Simple ADK-style specialist with a name, role, and run method."""

    name = "BaseAgent"
    role = "Defines a shared interface for LaunchForge specialist agents."

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
