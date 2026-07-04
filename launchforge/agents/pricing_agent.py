"""Pricing agent."""

from __future__ import annotations

from typing import Any, Dict

from launchforge.agents.base import LaunchForgeAgent
from launchforge.mcp_server.tools import create_pricing_table
from launchforge.schemas import PricingTier, model_to_dict


class PricingAgent(LaunchForgeAgent):
    name = "PricingAgent"
    role = "Creates practical starter pricing and package assumptions."

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        business_input = context["business_input"]
        offer_dicts = [model_to_dict(item) for item in context.get("offer_ladder", [])]
        pricing = [
            PricingTier(**item)
            for item in create_pricing_table(context["business_type"], business_input.budget, offer_dicts)
        ]
        return {"pricing": pricing}
