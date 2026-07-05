"""LaunchForge workflow orchestration."""

from __future__ import annotations

from typing import Any, Dict

from launchforge.adk_runtime import agent_trace_entry, get_runtime_status
from launchforge.agent_registry import agent_registry_as_dicts
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
from launchforge.config import detect_currency, sanitize_text
from launchforge.llm_agents import get_llm_agent_team_status
from launchforge.mcp_server.tools import (
    build_capacity_model,
    build_funnel_model,
    build_pricing_scenarios,
    list_tool_definitions,
    package_dashboard_outputs,
    prioritize_launch_tasks,
    run_red_team_checks,
    score_customer_segments,
    score_offer_fit,
    simulate_cashflow_scenarios,
)
from launchforge.schemas import BusinessInput, LaunchPack, model_to_dict
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
    currency_code, currency_symbol = detect_currency(
        cleaned.idea,
        cleaned.location,
        cleaned.founder_resources,
        cleaned.target_customer,
    )
    return {"business_input": cleaned, "currency_code": currency_code, "currency_symbol": currency_symbol}


def _next_actions(context: Dict[str, Any]) -> list[str]:
    business_type = context["business_type"]
    if business_type == "local_service":
        return ["Create a diagnostic intake form today.", "Message 20 local/referral contacts with the starter offer.", "Book 3 trial sessions and request feedback/testimonials."]
    if business_type == "physical_retail":
        return ["Count footfall at morning, lunch, and evening peaks.", "Build a supplier shortlist for the first 30 core SKUs.", "Mock the front-of-store commuter bundle display."]
    if business_type == "ecommerce":
        return ["Pick one hero product and order samples.", "Create 5 short-form content hooks for validation.", "Draft the Shopify product page with bundle and guarantee."]
    return ["Interview 10 target customers.", "Create a paid pilot offer.", "Track objections and revise the promise."]


def _agent_trace(context: Dict[str, Any], runtime_status: Dict[str, Any]) -> list[dict[str, Any]]:
    team = get_llm_agent_team_status()
    trace = []
    for item in team:
        agent_name = item["name"].replace("_", " ")
        if agent_name in {
            "Finance Simulation Agent",
            "Finance Agent / Finance Simulation Agent",
            "Finance Agent / Finance Agent / Finance Simulation Agent",
        }:
            agent_name = "Finance Agent"
        trace.append(
            {
                "agent": agent_name,
                "status": "completed" if runtime_status["mode"] == "ai-assisted" else "fallback ready",
                "summary": item["latest_output_summary"],
                "mode": runtime_status["mode"],
                "tools_available": item["tools_available"],
                "instruction_summary": item["instruction_summary"],
                "limitations": item["limitations"],
            }
        )
    return trace


def _tool_trace(name: str, output: Any, summary: str) -> Dict[str, Any]:
    count = len(output) if isinstance(output, list) else len(output.keys()) if isinstance(output, dict) else 1
    return {
        "trace_id": f"tool-{name.replace('_', '-')}",
        "type": "tool",
        "name": name,
        "status": "completed",
        "mode": "deterministic",
        "instruction_summary": "Deterministic MCP-style tool call.",
        "tools_called": [],
        "input_summary": "Structured launch-pack context.",
        "output_summary": summary,
        "metrics": {"items": count},
        "visible_reasoning_summary": "Tool output is produced by deterministic, testable Python logic.",
        "limitations": "Tool output depends on assumptions in the current launch pack.",
    }


def _technical_artifacts(context: Dict[str, Any]) -> Dict[str, Any]:
    personas = [model_to_dict(item) for item in context.get("personas", [])]
    offers = [model_to_dict(item) for item in context.get("offer_ladder", [])]
    pricing = [model_to_dict(item) for item in context.get("pricing", [])]
    roadmap = [model_to_dict(item) for item in context.get("roadmap", [])]
    cashflow = [model_to_dict(item) for item in context.get("cashflow", [])]
    business_type = context["business_type"]

    segment_scores = score_customer_segments(personas, business_type)
    offer_fit_scores = score_offer_fit(offers, business_type)
    pricing_scenarios = build_pricing_scenarios(pricing, business_type, context.get("currency_symbol", "£"))
    funnel_model = build_funnel_model(business_type, context.get("launch_channels", []))
    capacity_model = build_capacity_model(business_type, context["business_input"].founder_resources)
    scenario_forecasts = simulate_cashflow_scenarios(cashflow, context.get("startup_costs", {}), business_type)
    roadmap_priority_scores = prioritize_launch_tasks(roadmap, business_type)
    critic_red_team = run_red_team_checks({**context, "classification": model_to_dict(context["classification"])})

    package_context = {
        "segment_scores": segment_scores,
        "offer_fit_scores": offer_fit_scores,
        "pricing_scenarios": pricing_scenarios,
        "funnel_model": funnel_model,
        "capacity_model": capacity_model,
        "scenario_forecasts": scenario_forecasts,
        "roadmap_priority_scores": roadmap_priority_scores,
        "critic_red_team": critic_red_team,
    }
    dashboard_package = package_dashboard_outputs(package_context)
    traces = [
        _tool_trace("score_customer_segments", segment_scores, "Scored customer/persona fit."),
        _tool_trace("score_offer_fit", offer_fit_scores, "Scored offer ladder fit."),
        _tool_trace("build_pricing_scenarios", pricing_scenarios, "Built low/base/premium pricing scenarios."),
        _tool_trace("build_funnel_model", funnel_model, "Built funnel conversion model and bottleneck flags."),
        _tool_trace("build_capacity_model", capacity_model, "Built operational capacity model."),
        _tool_trace("simulate_cashflow_scenarios", scenario_forecasts, "Simulated conservative/base/aggressive cashflow scenarios."),
        _tool_trace("prioritize_launch_tasks", roadmap_priority_scores, "Scored roadmap priorities."),
        _tool_trace("run_red_team_checks", critic_red_team, "Generated red-team critic findings."),
        _tool_trace("package_dashboard_outputs", dashboard_package, "Packaged dashboard artefact inventory."),
    ]
    return {**package_context, "dashboard_package": dashboard_package, "tool_traces": traces}


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
    runtime_status = get_runtime_status()
    technical = _technical_artifacts(final)
    final.update({key: value for key, value in technical.items() if key != "tool_traces"})
    final["runtime_status"] = runtime_status
    final["agent_registry"] = agent_registry_as_dicts()
    final["tool_registry"] = list_tool_definitions()
    final["agent_trace"] = _agent_trace(final, runtime_status)
    llm_traces = [
        agent_trace_entry(item["agent"], item.get("tools_available", []), item["summary"], runtime_status["mode"])
        for item in final["agent_trace"]
    ]
    final["execution_trace"] = llm_traces + technical["tool_traces"]
    pack = assemble_launch_pack_skill(
        input=final["business_input"],
        currency_code=final["currency_code"],
        currency_symbol=final["currency_symbol"],
        classification=final["classification"],
        readiness_score=final["readiness_score"],
        launch_readiness_label=final["launch_readiness_label"],
        readiness_breakdown=final["readiness_breakdown"],
        readiness_strengths=final["readiness_strengths"],
        readiness_gaps=final["readiness_gaps"],
        business_model_canvas=final["business_model_canvas"],
        personas=final["personas"],
        offer_ladder=final["offer_ladder"],
        pricing=final["pricing"],
        sales_funnel=final["sales_funnel"],
        roadmap=final["roadmap"],
        cashflow=final["cashflow"],
        startup_costs=final["startup_costs"],
        cashflow_assumptions=final["cashflow_assumptions"],
        forecast_disclaimer=final["forecast_disclaimer"],
        breakeven_month=final["breakeven_month"],
        operations_checklist=final["operations_checklist"],
        marketing_messages=final["marketing_messages"],
        risks=final["risks"],
        assumptions=final["assumptions"],
        next_3_actions=final["next_3_actions"],
        critic_notes=final["critic_notes"],
        diagrams=final["diagrams"],
        agent_trace=final["agent_trace"],
        runtime_status=final["runtime_status"],
        agent_registry=final["agent_registry"],
        tool_registry=final["tool_registry"],
        execution_trace=final["execution_trace"],
        segment_scores=final["segment_scores"],
        offer_fit_scores=final["offer_fit_scores"],
        pricing_scenarios=final["pricing_scenarios"],
        funnel_model=final["funnel_model"],
        capacity_model=final["capacity_model"],
        scenario_forecasts=final["scenario_forecasts"],
        roadmap_priority_scores=final["roadmap_priority_scores"],
        critic_red_team=final["critic_red_team"],
        dashboard_package=final["dashboard_package"],
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
    if sum(pack.readiness_breakdown.values()) != pack.readiness_score:
        raise ValueError("Readiness breakdown must sum to readiness score.")
    return True
