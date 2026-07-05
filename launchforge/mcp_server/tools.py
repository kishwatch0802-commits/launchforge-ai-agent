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
    matched_signals: List[str] = []
    uncertainty_notes: List[str] = []
    if winner == "local_service":
        if any(term in text for term in ["tutor", "tuition"]):
            matched_signals.append("Tutoring implies founder-led service delivery.")
        if any(term in text for term in ["gcse", "a-level", "a level", "esat", "maths", "physics"]):
            matched_signals.append("GCSE/A-Level/ESAT and subject language indicate education services.")
        if any(term in text for term in ["local", "locally", "near me"]):
            matched_signals.append("Local launch points to referral and neighbourhood acquisition.")
        if any(term in text for term in ["students", "first 10", "clients"]):
            matched_signals.append("Goal of first students/clients implies appointment-based service delivery.")
        if not matched_signals:
            matched_signals.append("Service keywords suggest a founder-delivered local offer.")
    elif winner == "physical_retail":
        if any(term in text for term in ["corner shop", "barber", "cafe", "shop"]):
            matched_signals.append("The idea depends on a physical customer-facing location.")
        if any(term in text for term in ["snacks", "drinks", "essentials", "breakfast", "stock"]):
            matched_signals.append("Stock and product-category language points to retail operations.")
        if any(term in text for term in ["train station", "commuters", "footfall"]):
            matched_signals.append("Commuter/footfall language indicates location-led demand.")
        if any(term in text for term in ["local residents", "opening", "hours"]):
            matched_signals.append("Local residents and opening-hours assumptions matter to the model.")
    elif winner == "ecommerce":
        if any(term in text for term in ["shopify", "online store", "ecommerce", "e-commerce"]):
            matched_signals.append("Shopify/online-store language indicates ecommerce infrastructure.")
        if any(term in text for term in ["accessories", "product", "bottles", "bands", "notebooks"]):
            matched_signals.append("A product catalogue and niche accessories require product validation.")
        if any(term in text for term in ["shipping", "fulfilment", "store"]):
            matched_signals.append("Store and fulfilment signals point to conversion and delivery operations.")
        matched_signals.append("Content, product-page, and bundle testing are likely launch levers.")
    else:
        matched_signals.append("The idea has enough launch intent to build a validation plan.")
        uncertainty_notes.append("Business model is not strongly signalled; validate category before spending.")
    if scores.get(winner, 0) <= 2 and winner != "unknown":
        uncertainty_notes.append("Classification is based on limited signals; review before using for high-stakes decisions.")
    confidence = min(0.95, 0.58 + (len(matched_signals) * 0.08) + (scores.get(winner, 0) * 0.02))
    assumptions = [
        "Founder wants a practical launch plan rather than a long business plan.",
        "The first launch milestone is customer validation and first revenue.",
    ]
    reasoning = {
        "local_service": "LaunchForge classifies this as a local service because the idea is centred on founder-led tutoring, named exam outcomes, local acquisition, and a target of securing the first students.",
        "physical_retail": "LaunchForge classifies this as physical retail because success depends on location, stock categories, footfall, opening hours, and repeat purchases from commuters and local residents.",
        "ecommerce": "LaunchForge classifies this as ecommerce because the idea is an online product store with a catalogue, product-page conversion, supplier validation, fulfilment, and content-led acquisition.",
    }.get(winner, "LaunchForge could not find enough strong category signals, so it built a validation-first launch plan.")
    return {
        "business_type": winner,
        "confidence": round(confidence, 2),
        "matched_signals": matched_signals,
        "reasoning": reasoning,
        "uncertainty_notes": uncertainty_notes,
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
    plans = {
        "local_service": [
            (1, 1, "Define the diagnostic offer", "A clear diagnostic-session offer is written with price, duration, target student, and promised next step.", "Offer"),
            (5, 1, "Build proof assets", "A one-page offer sheet, WhatsApp message, and diagnostic form are ready to send to parents/students.", "Marketing"),
            (9, 2, "Create the first lead list", "At least 30 local parents, schools, groups, or referral contacts are listed with outreach status.", "Sales"),
            (13, 2, "Run 10 validation conversations", "At least 10 parents/students have been contacted and objections, price reactions, and urgent exam needs are recorded.", "Validation"),
            (17, 3, "Set up booking and policies", "Booking calendar, cancellation rules, safeguarding note, and parent update template are ready before the first paid session.", "Operations"),
            (23, 4, "Launch referral loop", "First students are asked for feedback, testimonials, and one warm referral after a useful session.", "Growth"),
            (30, 4, "Review conversion and retention", "Lead source, diagnostic bookings, paid package conversions, and next-week follow-ups are reviewed.", "Finance"),
        ],
        "physical_retail": [
            (1, 1, "Map commuter demand windows", "Morning, lunch, and evening footfall counts are recorded with notes on commuter and resident buying moments.", "Validation"),
            (5, 1, "Build the opening stock list", "A first 30-SKU list is grouped by snacks, drinks, essentials, breakfast, and emergency convenience items.", "Operations"),
            (9, 2, "Collect supplier quotes", "At least 3 supplier options are compared for price, delivery frequency, minimum order, and payment terms.", "Operations"),
            (13, 2, "Design the opening-week bundle", "A commuter breakfast/snack bundle is priced with a target average basket and margin assumption.", "Offer"),
            (18, 3, "Sketch shop layout", "Entrance, counter, fast-mover shelves, queue flow, and impulse purchase zones are mapped.", "Operations"),
            (24, 4, "Prepare local promotion", "Window signage, Google Maps listing, station leaflet, and local resident offer are ready.", "Marketing"),
            (30, 4, "Lock daily operating checklist", "Opening, replenishment, cash-up, reorder, waste, and shrinkage checks are documented.", "Operations"),
        ],
        "ecommerce": [
            (1, 1, "Choose the hero product shortlist", "Three gym accessory candidates are scored by margin, supplier reliability, content potential, and shipping simplicity.", "Product"),
            (5, 1, "Order or validate samples", "Supplier samples or proof of quality are requested before committing to inventory or ad spend.", "Operations"),
            (9, 2, "Draft the Shopify product page", "Hero product copy, bundle anchor, FAQ, guarantee, and product photos checklist are ready.", "Conversion"),
            (13, 2, "Build the content test plan", "Five short-form hooks and two creator/outreach angles are queued for product validation.", "Marketing"),
            (18, 3, "Define fulfilment and returns", "Packaging, delivery estimate, returns policy, and customer support response rules are documented.", "Operations"),
            (24, 4, "Launch landing page and waitlist", "Email capture, launch discount, bundle option, and analytics tracking are live.", "Launch"),
            (30, 4, "Review conversion metrics", "Traffic, add-to-cart rate, conversion rate, AOV, and gross margin are reviewed before scaling spend.", "Finance"),
        ],
    }
    selected = plans.get(
        business_type,
        [
            (1, 1, "Clarify the first paid promise", "The pilot offer states the customer, outcome, scope, price, and validation question.", "Offer"),
            (7, 1, "Interview target customers", "Ten target customers have been interviewed and common objections are recorded.", "Validation"),
            (14, 2, "Build the delivery checklist", "The founder can deliver the first paid pilot without improvising every step.", "Operations"),
            (21, 3, "Launch direct outreach", "The first outreach list is contacted with a simple call to action.", "Sales"),
            (30, 4, "Review launch evidence", "Paid interest, objections, conversion rate, and next experiment are documented.", "Finance"),
        ],
    )
    return [
        {"day": day, "week": week, "title": title, "owner": "Founder", "outcome": outcome, "category": category}
        for day, week, title, outcome, category in selected
    ]


def create_pricing_table(business_type: str, budget: float, offer: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    if business_type == "local_service":
        return [
            {"tier": "Entry Diagnostic", "price": 35, "unit": "diagnostic session", "includes": ["45-minute assessment", "Gap report", "Parent/student action plan"], "rationale": "Reduces buyer friction while still proving willingness to pay.", "when_to_use": "Use as the first paid step for parents who are unsure.", "upgrade_path": "Convert into the 4-session weekly package after the action plan."},
            {"tier": "Core Weekly Package", "price": 180, "unit": "4-session pack", "includes": ["Weekly tutoring", "Practice tasks", "Progress notes"], "rationale": "Creates predictable recurring delivery and a clear monthly commitment.", "when_to_use": "Use for students with a stable GCSE/A-Level revision need.", "upgrade_path": "Upgrade to Exam Sprint when mocks or admissions tests are close."},
            {"tier": "Premium Exam Sprint", "price": 420, "unit": "8-session sprint", "includes": ["8 sessions", "Mock/past-paper plan", "Parent update", "Priority scheduling"], "rationale": "Premium support for urgent outcomes where planning and feedback matter.", "when_to_use": "Use before mocks, ESAT/admissions tests, or final exam windows.", "upgrade_path": "Continue into weekly maintenance after the sprint."},
        ]
    if business_type == "physical_retail":
        return [
            {"tier": "Commuter Bundle", "price": 3.5, "unit": "opening bundle", "includes": ["Drink", "Breakfast snack", "Counter display"], "rationale": "Creates a fast, visible reason to stop during peak footfall.", "when_to_use": "Use at morning commute and station-facing signage.", "upgrade_path": "Add a loyalty stamp after the second visit."},
            {"tier": "Essentials Basket", "price": 12, "unit": "average basket", "includes": ["Milk/bread/eggs", "Top-up essentials", "Impulse item"], "rationale": "Targets a realistic local-resident basket with repeat weekly demand.", "when_to_use": "Use for residents avoiding a supermarket trip.", "upgrade_path": "Bundle into weekly household deals."},
            {"tier": "Opening Week Deal", "price": 20, "unit": "promoted basket", "includes": ["Core staples", "Snack/drink add-on", "Loyalty prompt"], "rationale": "Tests basket size and margin assumptions during the first promotional week.", "when_to_use": "Use in launch week to learn best-selling categories.", "upgrade_path": "Turn winners into permanent shelf bundles."},
        ]
    if business_type == "ecommerce":
        return [
            {"tier": "Starter Product", "price": 14.99, "unit": "hero product", "includes": ["One core accessory", "Usage guide", "Guarantee"], "rationale": "Low enough for a first purchase while testing product-page conversion.", "when_to_use": "Use for cold traffic and creator content tests.", "upgrade_path": "Upsell into the Starter Bundle on product page or cart."},
            {"tier": "Starter Bundle", "price": 39.99, "unit": "3-5 item kit", "includes": ["Accessory bundle", "Savings anchor", "Training checklist"], "rationale": "Improves average order value and differentiates generic products.", "when_to_use": "Use when one hero product gets clicks but AOV is low.", "upgrade_path": "Offer Pro Kit with free shipping threshold."},
            {"tier": "Pro Kit", "price": 69.99, "unit": "premium bundle", "includes": ["Premium bundle", "Free shipping", "Bonus notebook"], "rationale": "Anchors margin and gives serious buyers a higher-value option.", "when_to_use": "Use for retargeting and email campaigns.", "upgrade_path": "Follow with replacement/cross-sell emails."},
        ]
    base = max(10.0, float(budget) * 0.05)
    return [
        {"tier": "Pilot", "price": round(base, 2), "unit": "offer", "includes": ["Trial outcome"], "rationale": "Validate willingness to pay."},
        {"tier": "Core", "price": round(base * 2.5, 2), "unit": "offer", "includes": ["Main outcome"], "rationale": "Repeatable offer."},
        {"tier": "Premium", "price": round(base * 5, 2), "unit": "offer", "includes": ["Priority support"], "rationale": "Margin option."},
    ]


def score_customer_segments(personas: List[Dict[str, Any]], business_type: str) -> List[Dict[str, Any]]:
    """Score customer personas by pain, reachability, urgency, willingness to pay, and buyer control."""

    rows = []
    for index, persona in enumerate(personas):
        name = persona.get("name", f"Segment {index + 1}")
        text = " ".join(str(value) for value in persona.values()).lower()
        if business_type == "local_service" and ("parent" in text or "priya" in text):
            scores = (5, 4, 5, 5, 5)
        elif business_type == "local_service":
            scores = (4, 3, 4, 3, 2)
        elif business_type == "physical_retail" and "commuter" in text:
            scores = (4, 5, 5, 4, 4)
        elif business_type == "ecommerce" and ("starter" in text or "beginner" in text):
            scores = (4, 4, 4, 4, 4)
        else:
            scores = (4, 3, 3, 3, 3)
        pain, reach, urgency, willingness, control = scores
        overall = round((pain + reach + urgency + willingness + control) / 5, 2)
        rows.append(
            {
                "segment": persona.get("segment", name),
                "persona_name": name,
                "pain_intensity": pain,
                "reachability": reach,
                "urgency": urgency,
                "willingness_to_pay": willingness,
                "buyer_control": control,
                "overall_score": overall,
                "rationale": f"{name} is scored on urgency, accessibility, buying authority, and fit for the {business_type.replace('_', ' ')} launch path.",
                "recommended_first_segment": False,
            }
        )
    if rows:
        best = max(range(len(rows)), key=lambda i: rows[i]["overall_score"])
        rows[best]["recommended_first_segment"] = True
    return rows


def score_offer_fit(offers: List[Dict[str, Any]], business_type: str) -> List[Dict[str, Any]]:
    """Score offers by pain match, feasibility, differentiation, revenue, and complexity."""

    results = []
    for index, offer in enumerate(offers):
        name = offer.get("name", f"Offer {index + 1}")
        if business_type == "local_service":
            base = [(5, 5, 4, 3, 2), (5, 4, 4, 4, 3), (5, 3, 5, 5, 4)]
        elif business_type == "physical_retail":
            base = [(4, 5, 3, 3, 2), (5, 4, 4, 4, 3), (4, 4, 4, 4, 3)]
        elif business_type == "ecommerce":
            base = [(4, 4, 3, 3, 2), (5, 4, 4, 5, 3), (4, 3, 4, 5, 4)]
        else:
            base = [(4, 4, 3, 3, 3)] * 3
        pain, feasibility, differentiation, revenue, complexity = base[min(index, len(base) - 1)]
        overall = round((pain + feasibility + differentiation + revenue + (6 - complexity)) / 5, 2)
        results.append(
            {
                "offer_name": name,
                "customer_pain_match": pain,
                "delivery_feasibility": feasibility,
                "differentiation": differentiation,
                "revenue_potential": revenue,
                "operational_complexity": complexity,
                "overall_offer_score": overall,
                "rationale": f"{name} balances customer urgency with operational complexity for a {business_type.replace('_', ' ')} launch.",
            }
        )
    return results


def build_pricing_scenarios(pricing: List[Dict[str, Any]], business_type: str, currency_symbol: str = "£") -> List[Dict[str, Any]]:
    """Create low/base/premium pricing scenarios and sensitivity notes for each tier."""

    scenarios = []
    for index, tier in enumerate(pricing):
        base_price = float(tier.get("price", 0))
        if business_type == "physical_retail":
            conversion, margin = [0.48, 0.34, 0.22][min(index, 2)], [0.32, 0.38, 0.42][min(index, 2)]
        elif business_type == "ecommerce":
            conversion, margin = [0.035, 0.025, 0.014][min(index, 2)], [0.45, 0.52, 0.58][min(index, 2)]
        else:
            conversion, margin = [0.32, 0.22, 0.12][min(index, 2)], [0.82, 0.86, 0.88][min(index, 2)]
        scenarios.append(
            {
                "tier": tier.get("tier", f"Tier {index + 1}"),
                "low_price": round(base_price * 0.85, 2),
                "base_price": round(base_price, 2),
                "premium_price": round(base_price * 1.18, 2),
                "expected_conversion_rate": conversion,
                "estimated_margin": margin,
                "sensitivity_note": "If conversion is weak, improve proof/positioning before discounting.",
                "recommended_price": f"{currency_symbol}{base_price:,.0f}" if base_price >= 100 else f"{currency_symbol}{base_price:,.2f}",
                "rationale": tier.get("rationale", "Base price is the recommended first test point."),
            }
        )
    return scenarios


def build_funnel_model(business_type: str, channels: List[str]) -> List[Dict[str, Any]]:
    """Build a stage-by-stage conversion model and identify the likely bottleneck."""

    if business_type == "local_service":
        model = [
            ("Awareness leads", 100, 0.35, "Generate local/referral awareness", False, "Post in parent groups and ask for warm introductions."),
            ("Trust proof replies", 35, 0.34, "Convert interest into diagnostic conversations", True, "Add testimonials, credentials, and a clear diagnostic promise."),
            ("Diagnostic calls", 12, 0.42, "Book paid first sessions", False, "Offer 2-3 scheduling windows and a simple payment link."),
            ("Booked sessions", 5, 0.40, "Convert sessions to packages", False, "Send parent update and 4-week plan after the session."),
            ("Package conversions", 2, 1.00, "Retain and ask for referrals", False, "Request testimonial and one warm referral."),
        ]
    elif business_type == "physical_retail":
        model = [
            ("Daily footfall", 250, 0.28, "Turn passers-by into store entries", False, "Use window signage and commuter bundle prompts."),
            ("Store entries", 70, 0.62, "Create fast purchase moments", False, "Keep fast movers at entrance/counter."),
            ("Purchases", 43, 0.38, "Raise basket size", True, "Bundle breakfast/snacks with essentials."),
            ("Repeat prompts", 16, 0.50, "Start loyalty habit", False, "Use stamp cards and visible weekly deals."),
            ("Repeat visits", 8, 1.00, "Build weekly rhythm", False, "Track repeat purchase items and reorder points."),
        ]
    elif business_type == "ecommerce":
        model = [
            ("Content/ad visitors", 1000, 0.12, "Earn product-page clicks", False, "Test hooks around budget gym kit outcomes."),
            ("Product page views", 120, 0.18, "Get add-to-cart intent", True, "Improve product proof, images, guarantee, and bundle anchor."),
            ("Add to carts", 22, 0.45, "Reduce checkout friction", False, "Add shipping clarity and payment trust signals."),
            ("Purchases", 10, 0.30, "Increase AOV and email capture", False, "Promote starter bundle and free-shipping threshold."),
            ("Repeat/cross-sell", 3, 1.00, "Drive second purchase", False, "Send review request and companion-product email."),
        ]
    else:
        model = [
            ("Awareness", 100, 0.25, "Find first interested users", False, "Use direct outreach."),
            ("Interest", 25, 0.30, "Validate urgency", True, "Ask for a paid pilot."),
            ("Conversion", 8, 1.00, "Deliver the first paid result", False, "Track feedback."),
        ]
    rows = []
    for stage_name, starting, rate, objective, bottleneck, recommendation in model:
        output = round(starting * rate, 2)
        rows.append(
            {
                "stage_name": stage_name,
                "starting_volume": starting,
                "conversion_rate": rate,
                "output_volume": output,
                "stage_objective": objective,
                "bottleneck": bottleneck,
                "improvement_recommendation": recommendation,
            }
        )
    return rows


def build_capacity_model(business_type: str, founder_resources: str = "") -> Dict[str, Any]:
    """Estimate practical weekly capacity and the operational bottleneck."""

    if business_type == "local_service":
        return {
            "founder_hours_available_per_week": 12,
            "admin_hours_required": 3,
            "delivery_hours_required": 8,
            "max_customers_or_orders_per_week": 8,
            "bottleneck": "Founder tutoring hours and parent follow-up time.",
            "operational_risk": "Scheduling, safeguarding, and parent communication can become inconsistent.",
            "recommended_system": "Booking calendar, diagnostic template, parent update template, and cancellation/safeguarding policy.",
            "scaling_constraint": "One-to-one session capacity until group sessions or associate tutors are added.",
        }
    if business_type == "physical_retail":
        return {
            "founder_hours_available_per_week": 55,
            "admin_hours_required": 9,
            "delivery_hours_required": 46,
            "max_customers_or_orders_per_week": 900,
            "bottleneck": "Opening hours, stock replenishment, and supplier reliability.",
            "operational_risk": "Stockouts, waste, shrinkage, or slow queues reduce trust.",
            "recommended_system": "Daily opening/cash-up checklist, reorder points, supplier sheet, and waste/shrinkage log.",
            "scaling_constraint": "Founder coverage and working capital for inventory.",
        }
    if business_type == "ecommerce":
        return {
            "founder_hours_available_per_week": 18,
            "admin_hours_required": 6,
            "delivery_hours_required": 10,
            "max_customers_or_orders_per_week": 80,
            "bottleneck": "Supplier quality, fulfilment delay, and customer support response time.",
            "operational_risk": "Bad samples or slow shipping can hurt conversion and reviews.",
            "recommended_system": "Sample QA checklist, fulfilment SOP, returns policy, and support templates.",
            "scaling_constraint": "Supplier lead time and cash tied in inventory.",
        }
    return {
        "founder_hours_available_per_week": 10,
        "admin_hours_required": 3,
        "delivery_hours_required": 5,
        "max_customers_or_orders_per_week": 10,
        "bottleneck": "Validation bandwidth.",
        "operational_risk": "Unclear delivery process.",
        "recommended_system": "Simple intake, delivery, and feedback checklist.",
        "scaling_constraint": "Founder time.",
    }


def simulate_cashflow_scenarios(cashflow: List[Dict[str, Any]], startup_costs: Dict[str, float], business_type: str) -> Dict[str, Any]:
    """Generate conservative/base/aggressive 3-month cashflow scenarios."""

    base_revenue = [float(row["revenue"]) for row in cashflow]
    base_costs = [float(row["costs"]) for row in cashflow]
    startup_total = float(sum(startup_costs.values()))
    scenario_specs = {
        "conservative": (0.72, 1.12, "Slower conversion and slightly higher launch costs."),
        "base": (1.00, 1.00, "Current planning assumptions."),
        "aggressive": (1.28, 0.95, "Better conversion and tighter cost control."),
    }
    scenarios = []
    for name, (rev_mult, cost_mult, assumption) in scenario_specs.items():
        revenues = [round(value * rev_mult, 2) for value in base_revenue]
        costs = [round(value * cost_mult, 2) for value in base_costs]
        net = [round(rev - cost, 2) for rev, cost in zip(revenues, costs)]
        cumulative = []
        total = -startup_total
        for value in net:
            total += value
            cumulative.append(round(total, 2))
        break_even = next((str(index + 1) for index, value in enumerate(cumulative) if value >= 0), "Beyond 3 months")
        scenarios.append(
            {
                "scenario": name,
                "assumptions": [assumption],
                "month_1_revenue": revenues[0],
                "month_2_revenue": revenues[1],
                "month_3_revenue": revenues[2],
                "month_1_costs": costs[0],
                "month_2_costs": costs[1],
                "month_3_costs": costs[2],
                "net_cashflow_by_month": net,
                "cumulative_cashflow": cumulative,
                "break_even_month": break_even,
                "risk_note": "Scenario is a planning model, not a guarantee.",
            }
        )
    break_even_count = sum(1 for scenario in scenarios if scenario["break_even_month"] != "Beyond 3 months")
    worst_case_gap = min(value for scenario in scenarios for value in scenario["cumulative_cashflow"])
    upside_case = max(scenarios, key=lambda item: item["cumulative_cashflow"][-1])
    key_assumption = {
        "local_service": "diagnostic-to-package conversion",
        "physical_retail": "average basket and supplier margin",
        "ecommerce": "product-page conversion and gross margin",
    }.get(business_type, "paid conversion rate")
    return {
        "scenarios": scenarios,
        "breakeven_probability": break_even_count / len(scenarios),
        "worst_case_gap": round(worst_case_gap, 2),
        "upside_case": upside_case["scenario"],
        "key_assumption_to_validate": key_assumption,
    }


def prioritize_launch_tasks(roadmap: List[Dict[str, Any]], business_type: str) -> List[Dict[str, Any]]:
    """Score roadmap tasks by impact, effort, urgency, and risk reduction."""

    rows = []
    for index, task in enumerate(roadmap):
        category = str(task.get("category", "")).lower()
        impact = 5 if index < 2 or "validation" in category else 4
        urgency = 5 if task.get("day", 30) <= 13 else 3
        effort = 2 if task.get("day", 30) <= 9 else 3
        risk_reduction = 5 if category in {"validation", "operations", "finance"} else 3
        priority = impact + urgency + risk_reduction - effort
        rows.append(
            {
                "day": task.get("day"),
                "title": task.get("title"),
                "impact": impact,
                "effort": effort,
                "urgency": urgency,
                "dependency": "Founder availability" if index > 0 else "None",
                "priority_score": priority,
                "rationale": f"This task is early because it reduces {business_type.replace('_', ' ')} launch uncertainty.",
                "risk_reduction": risk_reduction,
            }
        )
    return rows


def run_red_team_checks(pack_context: Dict[str, Any]) -> Dict[str, Any]:
    """Run deterministic critic checks for contradictions, missing evidence, and go/no-go criteria."""

    business_type = pack_context.get("business_type") or pack_context.get("classification", {}).get("business_type", "unknown")
    base_missing = ["No validated demand yet.", "No proven conversion rate yet.", "No testimonials/reviews included in the input."]
    if business_type == "local_service":
        missing = base_missing + ["No parent conversion proof.", "No booking/safeguarding system yet.", "Founder capacity is a likely bottleneck."]
        failures = ["Parents do not trust the offer quickly enough.", "Founder cannot consistently schedule and follow up.", "Diagnostics do not convert into packages."]
        validation = ["Contact 10 parents/students and record objections.", "Run 3 paid diagnostics.", "Ask first customers for testimonial/referral."]
        cap = "Idea-only tutoring is capped below launch-ready until demand, testimonials, and booking workflow are proven."
    elif business_type == "physical_retail":
        missing = base_missing + ["Supplier quotes are unverified.", "Footfall and average basket are not proven."]
        failures = ["Stock mix misses commuter demand.", "Supplier terms crush margins.", "Waste/shrinkage erodes profit."]
        validation = ["Count footfall in 3 time windows.", "Get 3 supplier quotes.", "Mock opening-week basket and margin."]
        cap = "Retail readiness is capped until footfall, supplier costs, and margin assumptions are checked."
    elif business_type == "ecommerce":
        missing = base_missing + ["Supplier sample quality unverified.", "Product-page conversion is unknown."]
        failures = ["Generic products fail to convert.", "Supplier delays hurt reviews.", "Paid traffic spends before proof."]
        validation = ["Order samples.", "Test 5 content hooks.", "Measure add-to-cart and conversion on product page."]
        cap = "Ecommerce readiness is capped until product quality, positioning, and conversion are validated."
    else:
        missing = base_missing
        failures = ["Category is unclear.", "Offer is not validated.", "Founder over-invests before proof."]
        validation = ["Interview 10 target customers.", "Sell one paid pilot.", "Record objections."]
        cap = "Readiness is capped until the business model is validated."
    return {
        "contradiction_checks": ["No hard contradiction found in generated pack.", "Financial outputs are labelled as planning assumptions."],
        "missing_evidence": missing,
        "overconfidence_flags": ["Forecasts are not market proof.", "Readiness score is a planning heuristic."],
        "top_3_failure_modes": failures[:3],
        "readiness_cap_reason": cap,
        "validation_tests": validation[:3],
        "assumptions_to_verify": missing[:4],
        "go_no_go_criteria": ["At least 10 validation conversations complete.", "First paid intent or sale recorded.", "Operations checklist ready before scaling spend."],
    }


def explain_readiness_score(pack: Dict[str, Any]) -> Dict[str, Any]:
    """Explain readiness score using strengths, gaps, and score components."""

    score = pack.get("readiness_score", 0)
    strengths = pack.get("readiness_strengths", [])
    gaps = pack.get("readiness_gaps", [])
    return {
        "score": score,
        "summary": f"Readiness is {score}/100 because strengths include {', '.join(strengths[:2])}; the main gaps are {', '.join(gaps[:3])}. The score is capped by validation evidence, not by effort.",
    }


def improve_marketing_message(message: str, business_type: str) -> Dict[str, Any]:
    """Improve a launch message while keeping it grounded in the business type."""

    prefix = {
        "local_service": "Quick note for parents:",
        "physical_retail": "Opening-week local offer:",
        "ecommerce": "Launch list perk:",
    }.get(business_type, "Launch update:")
    return {
        "original_message": message,
        "improved_message": f"{prefix} {message} Reply if you want the first available slot or launch discount.",
    }


def suggest_next_action(pack: Dict[str, Any]) -> Dict[str, Any]:
    """Return the highest-priority next action from the current launch pack."""

    actions = pack.get("next_3_actions", [])
    action = actions[0] if actions else "Interview 10 target customers before spending more."
    return {"answer": f"Do this first: {action}", "action": action}


def package_dashboard_outputs(pack_context: Dict[str, Any]) -> Dict[str, Any]:
    """Create a compact dashboard artefact inventory for UI and export."""

    keys = [
        "segment_scores",
        "offer_fit_scores",
        "pricing_scenarios",
        "funnel_model",
        "capacity_model",
        "scenario_forecasts",
        "roadmap_priority_scores",
        "critic_red_team",
    ]
    return {
        "artefacts": [{"name": key, "available": bool(pack_context.get(key))} for key in keys],
        "summary": "Dashboard package includes scoring, scenario modelling, capacity, funnel, priority, and critic artefacts.",
    }


def list_tool_definitions() -> List[Dict[str, Any]]:
    """Return visible MCP-style tool metadata for Agent Control Room."""

    mapping = [
        ("classify_business_model", "Classifies business type and evidence signals.", "Business Classifier Agent"),
        ("score_customer_segments", "Scores customer/persona fit.", "Market Strategist Agent"),
        ("score_offer_fit", "Scores offer ladder fit.", "Offer Architect Agent"),
        ("build_pricing_scenarios", "Builds low/base/premium pricing scenarios.", "Pricing Analyst Agent"),
        ("build_funnel_model", "Models conversion stages and bottlenecks.", "Growth Marketing Agent"),
        ("build_capacity_model", "Models operational capacity and bottlenecks.", "Operations Planner Agent"),
        ("simulate_cashflow_scenarios", "Runs conservative/base/aggressive forecasts.", "Finance Agent / Finance Simulation Agent"),
        ("prioritize_launch_tasks", "Scores roadmap task priority.", "Roadmap Planner Agent"),
        ("run_red_team_checks", "Finds missing evidence and failure modes.", "Risk Critic Agent"),
        ("explain_readiness_score", "Explains readiness score from pack data.", "Copilot Agent"),
        ("improve_marketing_message", "Improves launch message copy.", "Copilot Agent"),
        ("suggest_next_action", "Selects the first action.", "Copilot Agent"),
        ("package_dashboard_outputs", "Packages artefact inventory.", "Visual Packaging Agent"),
        ("export_launch_pack", "Exports Markdown or JSON.", "Visual Packaging Agent"),
    ]
    return [{"tool_name": name, "computes": computes, "used_by": used_by} for name, computes, used_by in mapping]


def export_launch_pack(pack: Dict[str, Any], format: str = "markdown") -> str:
    from launchforge.export import export_json, export_markdown

    if format.lower() == "json":
        return export_json(pack)
    return export_markdown(pack)

