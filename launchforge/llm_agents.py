"""ADK/LlmAgent construction helpers for registered LaunchForge agents."""

from __future__ import annotations

from typing import Any, Dict

from launchforge.adk_runtime import build_llm_agent, get_runtime_status
from launchforge.agent_registry import AgentDefinition, get_agent_definitions
from launchforge.mcp_server import tools as tool_module


TOOL_FUNCTIONS = {
    name: getattr(tool_module, name)
    for name in [
        "classify_business_model",
        "score_customer_segments",
        "score_offer_fit",
        "build_pricing_scenarios",
        "build_funnel_model",
        "build_capacity_model",
        "simulate_cashflow_scenarios",
        "prioritize_launch_tasks",
        "run_red_team_checks",
        "explain_readiness_score",
        "improve_marketing_message",
        "suggest_next_action",
        "package_dashboard_outputs",
        "export_launch_pack",
    ]
    if hasattr(tool_module, name)
}


def construct_agent_if_configured(definition: AgentDefinition) -> Dict[str, Any]:
    status = get_runtime_status()
    if status["mode"] != "ai-assisted":
        return {"constructed": False, "agent": None, "reason": status["reason"]}
    selected_tools = [TOOL_FUNCTIONS[name] for name in definition.tools_available if name in TOOL_FUNCTIONS]
    try:
        agent = build_llm_agent(
            name=definition.name,
            description=definition.description,
            instruction=definition.instruction,
            tools=selected_tools,
            model=status["model"],
        )
        return {"constructed": True, "agent": agent, "reason": "Constructed ADK LlmAgent."}
    except Exception as exc:  # noqa: BLE001
        return {"constructed": False, "agent": None, "reason": f"ADK construction failed safely: {exc}"}


def get_llm_agent_team_status() -> list[Dict[str, Any]]:
    runtime = get_runtime_status()
    rows = []
    for definition in get_agent_definitions():
        rows.append(
            {
                **definition.as_dict(),
                "mode": runtime["mode"],
                "latest_output_summary": definition.fallback_behaviour if runtime["mode"] == "deterministic-fallback" else "Ready for ADK execution.",
                "limitations": runtime["reason"] if runtime["mode"] == "deterministic-fallback" else "AI-assisted outputs still require founder review.",
            }
        )
    return rows
