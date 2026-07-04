"""LaunchForge workflow orchestration."""

from __future__ import annotations

from typing import Any, Dict

from launchforge.agent_runtime import SequentialAgentRunner
from launchforge.agents import (
    BusinessClassifierAgent,
    CriticAgent,
    FinanceAgent,
    MarketAgent,
    MarketingAgent,
    OfferAgent,
    OperationsAgent,
    PricingAgent,
    RoadmapAgent,
    VisualPackAgent,
)
from launchforge.config import sanitize_text
from launchforge.schemas import BusinessInput, LaunchPack
from launchforge.skills.launch_pack_skill import assemble_launch_pack_skill


def create_initial_context(business_input: BusinessInput | Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(business_input, dict):
        business_input = BusinessInput(**business_input)
    cleaned = BusinessInput(
        idea=sanitize_text(business_input.idea),
        budget=business_input.budget,
        location=sanitize_text(business_input.location, 500),
        founder_resources=sanitize_text(business_input.founder_resources, 1000),
        timeframe=sanitize_text(business_input.timeframe, 200),
        stage=sanitize_text(business_input.stage, 200),
        target_customer=sanitize_text(business_input.target_customer, 500) if business_input.target_customer else None,
        privacy_mode=business_input.privacy_mode,
    )
    return {"business_input": cleaned}


def _next_actions(context: Dict[str, Any]) -> list[str]:
    business_type = context["business_type"]
    if business_type == "local_service":
        return ["Create a diagnostic intake form today.", "Message 20 local/referral contacts with the starter offer.", "Book 3 trial sessions and request feedback/testimonials."]
    if business_type == "physical_retail":
        return ["Count footfall at morning, lunch, and evening peaks.", "Build a supplier shortlist for the first 30 core SKUs.", "Mock the front-of-store commuter bundle display."]
    if business_type == "ecommerce":
        return ["Pick one hero product and order samples.", "Create 5 short-form content hooks for validation.", "Draft the Shopify product page with bundle and guarantee."]
    return ["Interview 10 target customers.", "Create a paid pilot offer.", "Track objections and revise the promise."]


def run_launchforge_workflow(business_input: BusinessInput | Dict[str, Any]) -> LaunchPack:
    context = create_initial_context(business_input)
    runner = SequentialAgentRunner(
        [
            BusinessClassifierAgent(),
            MarketAgent(),
            OfferAgent(),
            PricingAgent(),
            MarketingAgent(),
            OperationsAgent(),
            FinanceAgent(),
            RoadmapAgent(),
            CriticAgent(),
            VisualPackAgent(),
        ]
    )
    session = runner.run(context)
    final = session.context
    final["next_3_actions"] = _next_actions(final)
    pack = assemble_launch_pack_skill(
        input=final["business_input"],
        classification=final["classification"],
        readiness_score=final["readiness_score"],
        readiness_breakdown=final["readiness_breakdown"],
        business_model_canvas=final["business_model_canvas"],
        personas=final["personas"],
        offer_ladder=final["offer_ladder"],
        pricing=final["pricing"],
        sales_funnel=final["sales_funnel"],
        roadmap=final["roadmap"],
        cashflow=final["cashflow"],
        startup_costs=final["startup_costs"],
        breakeven_month=final["breakeven_month"],
        operations_checklist=final["operations_checklist"],
        marketing_messages=final["marketing_messages"],
        risks=final["risks"],
        assumptions=final["assumptions"],
        next_3_actions=final["next_3_actions"],
        critic_notes=final["critic_notes"],
        diagrams=final["diagrams"],
    )
    validate_launch_pack(pack)
    return pack


def validate_launch_pack(pack: LaunchPack) -> bool:
    if not pack.personas:
        raise ValueError("Launch pack must include at least one persona.")
    if len(pack.next_3_actions) != 3:
        raise ValueError("Launch pack must include exactly three next actions.")
    if pack.readiness_score < 0 or pack.readiness_score > 100:
        raise ValueError("Readiness score out of range.")
    return True
