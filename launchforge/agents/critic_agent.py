"""Critic and readiness agent."""

from __future__ import annotations

from typing import Any, Dict, List

from launchforge.agents.base import LaunchForgeAgent
from launchforge.sample_data import template_for


class CriticAgent(LaunchForgeAgent):
    name = "CriticAgent"
    role = "Reviews contradictions, assumptions, risk, and launch readiness."

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        business_input = context["business_input"]
        score = 35
        breakdown = {
            "Clarity": 15 if len(business_input.idea) > 40 else 8,
            "Budget realism": 15 if business_input.budget >= 500 else 8,
            "Customer specificity": 15 if business_input.target_customer else 10,
            "Offer readiness": 20 if context.get("offer_ladder") else 0,
            "Operational readiness": 15 if context.get("operations_checklist") else 0,
            "Financial model": 15 if context.get("cashflow") else 0,
        }
        score = min(95, sum(breakdown.values()))
        risks: List[str] = list(template_for(context["business_type"])["risks"])
        assumptions = list(context["classification"].assumptions)
        assumptions.append(f"Budget provided is treated as available launch cash: {business_input.budget:.0f}.")
        notes = [
            "Readiness is a planning score, not a guarantee of success.",
            "Validate demand before committing to irreversible spend.",
        ]
        if business_input.stage == "Idea only":
            risks.append("The idea is pre-validation; first tasks should prove demand before scaling.")
        return {
            "readiness_score": int(score),
            "readiness_breakdown": breakdown,
            "risks": risks,
            "assumptions": assumptions,
            "critic_notes": notes,
        }
