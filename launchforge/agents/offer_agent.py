"""Offer design agent."""

from __future__ import annotations

from typing import Any, Dict

from launchforge.agents.base import LaunchForgeAgent
from launchforge.sample_data import template_for
from launchforge.schemas import OfferPackage


class OfferAgent(LaunchForgeAgent):
    name = "OfferAgent"
    role = "Turns the business type into a ladder of sellable offers."

    def _value_proposition(self, business_type: str) -> str:
        if business_type == "local_service":
            return "GCSE and A-Level Maths/Physics tutoring with ESAT/admissions prep, a paid diagnostic assessment, weekly study plan, and parent/student progress updates."
        if business_type == "physical_retail":
            return "A station-adjacent convenience shop for commuters and local residents, focused on breakfast, snacks, drinks, essentials, predictable opening hours, and fast repeat purchases."
        if business_type == "ecommerce":
            return "A focused gym-accessory ecommerce brand using product bundles, fast product-page testing, content-led acquisition, supplier validation, and simple fulfilment."
        return "A validation-first launch offer that tests one customer segment, one promise, one channel, and one paid next step."

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
            "value_proposition": self._value_proposition(context["business_type"]),
        }
