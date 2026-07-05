"""Critic and readiness agent."""

from __future__ import annotations

from typing import Any, Dict, List

from launchforge.agents.base import LaunchForgeAgent
from launchforge.sample_data import template_for


class CriticAgent(LaunchForgeAgent):
    name = "CriticAgent"
    role = "Reviews contradictions, assumptions, risk, and launch readiness."

    def _label(self, score: int) -> str:
        if score >= 82:
            return "Launch-ready"
        if score >= 68:
            return "Validation-ready"
        if score >= 55:
            return "Promising but unvalidated"
        return "Needs validation"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        business_input = context["business_input"]
        stage = business_input.stage.lower()
        breakdown = {
            "Idea clarity": 14 if len(business_input.idea) > 80 else 10,
            "Customer focus": 12 if business_input.target_customer else 9,
            "Offer design": 13 if context.get("offer_ladder") else 0,
            "Channel practicality": 11 if context.get("launch_channels") else 0,
            "Operations plan": 9 if context.get("operations_checklist") else 0,
            "Financial assumptions": 9 if context.get("cashflow_assumptions") else 0,
            "Validation proof": 6 if stage == "testing" else 0,
            "Launch assets": 7 if stage == "ready to launch" else 0,
        }
        complexity_adjustment = {"local_service": 0, "physical_retail": -4, "ecommerce": -2}.get(context["business_type"], -3)
        if complexity_adjustment:
            breakdown["Model complexity adjustment"] = complexity_adjustment
        base_score = sum(breakdown.values())
        if stage == "idea only":
            score = min(base_score, 72)
        elif stage == "testing":
            score = min(max(base_score + 5, 60), 82)
        elif stage == "ready to launch":
            score = min(max(base_score + 12, 72), 90)
        else:
            score = min(base_score, 84)
        if not business_input.target_customer:
            score = min(score, 74)
        if stage == "idea only":
            score = min(score, 72)
        if sum(breakdown.values()) != score:
            difference = score - sum(breakdown.values())
            breakdown["Stage adjustment"] = difference
        risks: List[str] = list(template_for(context["business_type"])["risks"])
        assumptions = list(context["classification"].assumptions)
        assumptions.append(f"Budget provided is treated as available launch cash: {context['currency_symbol']}{business_input.budget:.0f}.")
        strengths = [
            "Clear customer group and business model.",
            "Offer ladder gives a low-friction entry point plus upgrade paths.",
            "Launch channels match the detected business type.",
        ]
        gaps = [
            "No validated demand yet.",
            "No testimonials, reviews, or existing sales are included in the input.",
            "No proven lead list or conversion rate yet.",
        ]
        if context["business_type"] == "local_service":
            strengths.append("Low startup cost and founder expertise make a first tutoring launch practical.")
            gaps.append("Booking process, safeguarding note, and parent follow-up still need to be created.")
        elif context["business_type"] == "physical_retail":
            strengths.append("Location and commuter/resident use cases give concrete validation targets.")
            gaps.append("Supplier quotes, footfall counts, waste, and shrinkage assumptions still need proof.")
        elif context["business_type"] == "ecommerce":
            strengths.append("Niche product bundle gives clear product-page and content tests.")
            gaps.append("Supplier quality, fulfilment timing, and conversion rate still need validation.")
        notes = [
            "Readiness is a planning score, not a guarantee of success.",
            "Validate demand before committing to irreversible spend.",
        ]
        if business_input.stage == "Idea only":
            risks.append("The idea is pre-validation; first tasks should prove demand before scaling.")
        return {
            "readiness_score": int(score),
            "launch_readiness_label": self._label(int(score)),
            "readiness_breakdown": breakdown,
            "readiness_strengths": strengths,
            "readiness_gaps": gaps,
            "risks": risks,
            "assumptions": assumptions,
            "critic_notes": notes,
        }
