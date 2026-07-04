"""Market and customer agent."""

from __future__ import annotations

from typing import Any, Dict

from launchforge.agents.base import LaunchForgeAgent
from launchforge.sample_data import template_for
from launchforge.schemas import CustomerPersona


class MarketAgent(LaunchForgeAgent):
    name = "MarketAgent"
    role = "Builds target segments and customer personas from the classification."

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        business_type = context["business_type"]
        business_input = context["business_input"]
        personas = [CustomerPersona(**item) for item in template_for(business_type)["personas"]]
        if business_input.target_customer:
            personas[0].segment = business_input.target_customer
            personas[0].buying_trigger = f"Specific need from {business_input.target_customer}."
        return {"personas": personas}
