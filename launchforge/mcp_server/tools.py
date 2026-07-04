"""LaunchForge MCP tools.

These functions are written as plain Python so the app and tests can call them
locally. `server.py` exposes the same functions through FastMCP when available.
"""

from __future__ import annotations

from typing import Any, Dict, List

from launchforge.config import sanitize_text
from launchforge.sample_data import KEYWORDS, template_for


def classify_business_model(idea: str) -> Dict[str, Any]:
    text = sanitize_text(idea).lower()
    scores: Dict[str, int] = {}
    for business_type, words in KEYWORDS.items():
        scores[business_type] = sum(1 for word in words if word in text)
    # Strong platform/fulfilment signals should beat the generic word "store".
    if any(term in text for term in ["shopify", "ecommerce", "e-commerce", "shipping", "online store"]):
        scores["ecommerce"] = scores.get("ecommerce", 0) + 2
    if any(term in text for term in ["corner shop", "train station", "premises", "footfall"]):
        scores["physical_retail"] = scores.get("physical_retail", 0) + 2
    winner = max(scores, key=scores.get) if scores else "unknown"
    if scores.get(winner, 0) == 0:
        winner = "unknown"
    confidence = min(0.95, 0.45 + (scores.get(winner, 0) * 0.12))
    assumptions = [
        "Founder wants a practical launch plan rather than a long business plan.",
        "The first launch milestone is customer validation and first revenue.",
    ]
    return {
        "business_type": winner,
        "confidence": round(confidence, 2),
        "reasoning": f"Matched {scores.get(winner, 0)} signals for {winner.replace('_', ' ')}.",
        "assumptions": assumptions,
    }


def build_cashflow_forecast(
    startup_costs: Dict[str, float] | float,
    monthly_revenue: float,
    monthly_costs: float,
    months: int = 3,
) -> Dict[str, Any]:
    if isinstance(startup_costs, dict):
        startup_total = float(sum(startup_costs.values()))
    else:
        startup_total = float(startup_costs)
    rows = []
    cumulative = -startup_total
    for month in range(1, months + 1):
        revenue = monthly_revenue * (0.7 + (month * 0.25))
        costs = monthly_costs * (1 + max(0, month - 1) * 0.08)
        net = revenue - costs
        cumulative += net
        rows.append(
            {
                "month": month,
                "revenue": round(revenue, 2),
                "costs": round(costs, 2),
                "net_cashflow": round(net, 2),
                "cumulative_cashflow": round(cumulative, 2),
            }
        )
    breakeven = next((str(r["month"]) for r in rows if r["cumulative_cashflow"] >= 0), "Beyond 3 months")
    return {"startup_total": startup_total, "months": rows, "breakeven_month": breakeven}


def generate_sales_funnel(business_type: str, channels: List[str]) -> Dict[str, Any]:
    if business_type == "local_service":
        stages = ["Local awareness", "Trust proof", "Diagnostic call", "Booked session", "Referral loop"]
    elif business_type == "physical_retail":
        stages = ["Footfall", "Window offer", "Fast purchase", "Loyalty prompt", "Repeat visit"]
    elif business_type == "ecommerce":
        stages = ["Content/ad hook", "Product page", "Offer bundle", "Checkout", "Post-purchase email"]
    else:
        stages = ["Awareness", "Interest", "Offer", "Conversion", "Retention"]
    return {"business_type": business_type, "channels": channels, "stages": stages}


def create_launch_tasks(business_type: str, timeframe: str) -> List[Dict[str, Any]]:
    template = template_for(business_type)
    tasks = [
        ("Clarify the first customer promise", "Strategy"),
        ("Build the minimum sellable offer", "Offer"),
        ("Create proof assets and outreach list", "Marketing"),
        ("Run 10 direct validation conversations", "Sales"),
        ("Set up delivery/fulfilment workflow", "Operations"),
        ("Launch first public campaign", "Marketing"),
        ("Review metrics and fix the bottleneck", "Finance"),
    ]
    if business_type == "physical_retail":
        tasks[1] = ("Map fast-moving stock categories and suppliers", "Operations")
        tasks[3] = ("Count footfall in three time windows", "Validation")
    if business_type == "ecommerce":
        tasks[1] = ("Validate hero product and order samples", "Product")
        tasks[3] = ("Test 5 product hooks with short-form content", "Marketing")
    return [
        {
            "day": min(30, 1 + i * 4),
            "week": min(4, 1 + i // 2),
            "title": title,
            "owner": "Founder",
            "outcome": f"Evidence that {title.lower()} is complete for a {business_type.replace('_', ' ')} launch.",
            "category": category,
        }
        for i, (title, category) in enumerate(tasks + [(item, "Operations") for item in template["operations"][:1]])
    ]


def create_pricing_table(business_type: str, budget: float, offer: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    if business_type == "local_service":
        return [
            {"tier": "Entry", "price": 35, "unit": "diagnostic/session", "includes": ["Assessment", "Action plan"], "rationale": "Low-friction paid trial."},
            {"tier": "Core", "price": 180, "unit": "4-session pack", "includes": ["Weekly sessions", "Progress notes"], "rationale": "Packages recurring delivery."},
            {"tier": "Premium", "price": 420, "unit": "exam sprint", "includes": ["8 sessions", "Past-paper plan"], "rationale": "Urgent outcome with higher support."},
        ]
    if business_type == "physical_retail":
        return [
            {"tier": "Impulse", "price": 3.5, "unit": "bundle", "includes": ["Drink", "Snack"], "rationale": "Fast commuter purchase."},
            {"tier": "Essentials", "price": 12, "unit": "basket", "includes": ["Top-up basics"], "rationale": "Raises average basket size."},
            {"tier": "Weekly Deal", "price": 20, "unit": "basket", "includes": ["Local offer", "Loyalty stamp"], "rationale": "Encourages repeat visits."},
        ]
    if business_type == "ecommerce":
        return [
            {"tier": "Hero", "price": 14.99, "unit": "product", "includes": ["Core accessory", "Guide"], "rationale": "Easy first purchase."},
            {"tier": "Bundle", "price": 39.99, "unit": "kit", "includes": ["3-5 accessories", "Savings"], "rationale": "Improves AOV."},
            {"tier": "Pro Kit", "price": 69.99, "unit": "kit", "includes": ["Premium bundle", "Free shipping"], "rationale": "Anchors value."},
        ]
    base = max(10.0, float(budget) * 0.05)
    return [
        {"tier": "Pilot", "price": round(base, 2), "unit": "offer", "includes": ["Trial outcome"], "rationale": "Validate willingness to pay."},
        {"tier": "Core", "price": round(base * 2.5, 2), "unit": "offer", "includes": ["Main outcome"], "rationale": "Repeatable offer."},
        {"tier": "Premium", "price": round(base * 5, 2), "unit": "offer", "includes": ["Priority support"], "rationale": "Margin option."},
    ]


def export_launch_pack(pack: Dict[str, Any], format: str = "markdown") -> str:
    from launchforge.export import export_json, export_markdown

    if format.lower() == "json":
        return export_json(pack)
    return export_markdown(pack)
