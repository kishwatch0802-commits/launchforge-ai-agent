"""Roadmap agent."""

from __future__ import annotations

from typing import Any, Dict

from launchforge.agents.base import LaunchForgeAgent
from launchforge.mcp_server.tools import create_launch_tasks
from launchforge.schemas import LaunchTask


class RoadmapAgent(LaunchForgeAgent):
    name = "RoadmapAgent"
    role = "Creates a week-by-week launch plan with concrete tasks."

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        tasks = create_launch_tasks(context["business_type"], context["business_input"].timeframe)
        return {"roadmap": [LaunchTask(**item) for item in tasks]}
