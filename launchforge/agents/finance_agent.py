"""Finance agent."""

from __future__ import annotations

from typing import Any, Dict

from launchforge.agents.base import LaunchForgeAgent
from launchforge.schemas import CashflowMonth
from launchforge.skills.cashflow_skill import run_cashflow_skill


class FinanceAgent(LaunchForgeAgent):
    name = "FinanceAgent"
    role = "Builds a simple launch-budget forecast and break-even estimate."

    def _startup_costs(self, business_type: str, budget: float) -> Dict[str, float]:
        if business_type == "physical_retail":
            return {"Initial stock": budget * 0.45, "Signage/fixtures": budget * 0.2, "Licences/admin": budget * 0.15, "Launch promotions": budget * 0.1}
        if business_type == "ecommerce":
            return {"Samples": budget * 0.2, "Shopify/apps": budget * 0.12, "Initial inventory": budget * 0.38, "Content/ads test": budget * 0.2}
        if business_type == "local_service":
            return {"Booking/tools": budget * 0.15, "Local marketing": budget * 0.25, "Materials": budget * 0.2, "Insurance/admin": budget * 0.1}
        return {"Validation": budget * 0.25, "Tools": budget * 0.2, "Marketing": budget * 0.25}

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        business_input = context["business_input"]
        business_type = context["business_type"]
        budget = max(float(business_input.budget), 100.0)
        startup_costs = self._startup_costs(business_type, budget)
        if business_type == "physical_retail":
            monthly_revenue, monthly_costs = budget * 0.9, budget * 0.45
        elif business_type == "ecommerce":
            monthly_revenue, monthly_costs = budget * 0.7, budget * 0.32
        elif business_type == "local_service":
            monthly_revenue, monthly_costs = budget * 0.55, budget * 0.12
        else:
            monthly_revenue, monthly_costs = budget * 0.45, budget * 0.18
        forecast = run_cashflow_skill(startup_costs, monthly_revenue, monthly_costs, months=3)
        return {
            "startup_costs": startup_costs,
            "cashflow": [CashflowMonth(**item) for item in forecast["months"]],
            "breakeven_month": forecast["breakeven_month"],
        }
