"""Offer design agent."""

from __future__ import annotations

from typing import Any, Dict

from launchforge.agents.base import LaunchForgeAgent
from launchforge.sample_data import template_for
from launchforge.schemas import OfferPackage


class OfferAgent(LaunchForgeAgent):
    name = "OfferAgent"
    role = "Turns the business type into a ladder of sellable offers."

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        offers = [
            OfferPackage(
                name=name,
                description=description,
                ideal_for=ideal_for,
                deliverables=deliverables,
                success_metric=success_metric,
            )
            for name, description, ideal_for, deliverables, success_metric in template_for(context["business_type"])["offer"]
        ]
        return {
            "offer_ladder": offers,
            "value_proposition": f"A practical first offer for {context['business_type'].replace('_', ' ')} customers with clear proof and a low-friction next step.",
        }
