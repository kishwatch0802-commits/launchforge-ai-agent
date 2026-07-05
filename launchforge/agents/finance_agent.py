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

    def _assumptions(self, business_type: str) -> Dict[str, list[str]]:
        if business_type == "local_service":
            return {
                "revenue": [
                    "Month 1 assumes 3 paid diagnostics and 1 customer converting into a 4-session pack.",
                    "Month 2 assumes 2 recurring package customers from referrals or local outreach.",
                    "Month 3 assumes one premium exam sprint or equivalent extra weekly sessions.",
                ],
                "costs": [
                    "Costs include booking tools, materials, local outreach, and basic admin.",
                    "Founder labour is not included as a cash cost.",
                ],
                "conversion": [
                    "Diagnostic-to-package conversion is an assumption to validate with the first 10 conversations.",
                    "Testimonials and parent updates are expected to improve conversion after early sessions.",
                ],
            }
        if business_type == "physical_retail":
            return {
                "revenue": [
                    "Revenue assumes modest opening footfall with commuter bundles and local resident baskets.",
                    "Month 2 and 3 growth depends on repeat visits and better stock availability.",
                ],
                "costs": [
                    "Costs include opening stock, fixtures/signage, admin/licences, and launch promotions.",
                    "Rent, wages, and utilities should be added before a real lease decision.",
                ],
                "conversion": [
                    "Average basket and margin assumptions must be validated with footfall counts and supplier quotes.",
                ],
            }
        if business_type == "ecommerce":
            return {
                "revenue": [
                    "Month 1 assumes a small hero-product test with limited paid/content traffic.",
                    "Month 2 assumes bundle testing improves average order value.",
                    "Month 3 assumes one winner is pushed through content or retargeting.",
                ],
                "costs": [
                    "Costs include samples, Shopify/apps, initial inventory, content, and ad testing.",
                    "Founder time, returns, and failed creative tests are not fully costed.",
                ],
                "conversion": [
                    "Conversion rate, AOV, gross margin, and supplier quality must be validated before scaling.",
                ],
            }
        return {
            "revenue": ["Revenue assumes a small paid pilot and modest repeat interest."],
            "costs": ["Costs include validation, basic tools, and launch marketing."],
            "conversion": ["Conversion assumptions should be replaced with real customer evidence."],
        }

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
        assumptions = self._assumptions(business_type)
        assumptions["break_even"] = [
            f"Break-even is the first month where cumulative cashflow becomes non-negative after startup costs. Current estimate: {forecast['breakeven_month']}."
        ]
        return {
            "startup_costs": startup_costs,
            "cashflow": [CashflowMonth(**item) for item in forecast["months"]],
            "breakeven_month": forecast["breakeven_month"],
            "cashflow_assumptions": assumptions,
            "forecast_disclaimer": "Planning forecast only; not financial advice.",
        }
