"""Operations agent."""

from __future__ import annotations

from typing import Any, Dict

from launchforge.agents.base import LaunchForgeAgent
from launchforge.sample_data import template_for


class OperationsAgent(LaunchForgeAgent):
    name = "OperationsAgent"
    role = "Defines the delivery, fulfilment, supplier, and daily operating checklist."

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"operations_checklist": template_for(context["business_type"])["operations"]}
