"""Business classifier agent."""

from __future__ import annotations

from typing import Any, Dict

from launchforge.agents.base import LaunchForgeAgent
from launchforge.mcp_server.tools import classify_business_model
from launchforge.schemas import BusinessClassification


class BusinessClassifierAgent(LaunchForgeAgent):
    name = "BusinessClassifierAgent"
    role = "Classifies the idea and extracts initial assumptions."

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raw = classify_business_model(context["business_input"].idea)
        classification = BusinessClassification(**raw)
        return {"classification": classification, "business_type": classification.business_type}
