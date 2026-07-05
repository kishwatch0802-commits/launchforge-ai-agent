"""Markdown and JSON export helpers."""

from __future__ import annotations

import json
from typing import Any, Dict

from pydantic import BaseModel

from launchforge.config import as_money
from launchforge.schemas import model_to_dict


def _to_plain(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return model_to_dict(value)
    if isinstance(value, dict):
        return {key: _to_plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    return value


def export_json(pack: Any) -> str:
    return json.dumps(_to_plain(pack), indent=2, ensure_ascii=False)


def export_markdown(pack: Any) -> str:
    data: Dict[str, Any] = _to_plain(pack)
    classification = data["classification"]
    currency_symbol = data.get("currency_symbol", "\u00a3")
    lines = [
        "# LaunchForge Launch Pack",
        "",
        f"**Business type:** {classification['business_type']}",
        f"**Currency:** {data.get('currency_code', 'GBP')} ({currency_symbol})",
        f"**Readiness score:** {data['readiness_score']}/100",
        f"**Readiness label:** {data.get('launch_readiness_label', 'Planning')}",
        f"**Break-even month:** {data['breakeven_month']}",
        "",
        "## Classification Evidence",
    ]
    lines.append(classification["reasoning"])
    lines.extend(f"- {signal}" for signal in classification.get("matched_signals", []))
    if classification.get("uncertainty_notes"):
        lines.append("### Uncertainty Notes")
        lines.extend(f"- {note}" for note in classification["uncertainty_notes"])
    lines.extend(
        [
            "",
            "## Runtime Status",
            f"- Mode: {data.get('runtime_status', {}).get('mode', 'deterministic-fallback')}",
            f"- Provider: {data.get('runtime_status', {}).get('provider', 'fallback')}",
            f"- Model: {data.get('runtime_status', {}).get('model', '')}",
            f"- ADK available: {data.get('runtime_status', {}).get('adk_available', False)}",
            f"- GenAI available: {data.get('runtime_status', {}).get('genai_available', False)}",
            f"- API key available: {data.get('runtime_status', {}).get('api_key_available', False)}",
            f"- Reason: {data.get('runtime_status', {}).get('reason', '')}",
            "",
            "## Agent Trace",
        ]
    )
    for item in data.get("agent_trace", []):
        lines.append(f"- **{item['agent']}** ({item['status']} / {item.get('mode', 'deterministic-fallback')}): {item['summary']}")
    lines.append("")
    lines.append("## Execution Trace Summary")
    for item in data.get("execution_trace", []):
        tools_called = ", ".join(item.get("tools_called") or [])
        lines.append(f"- **{item.get('type')}::{item.get('name')}** [{item.get('mode')}]: {item.get('output_summary')} Tools: {tools_called or 'none'}")
    lines.append("")
    lines.append("## Technical Artefacts")
    lines.append(f"- Segment scores: {len(data.get('segment_scores', []))}")
    lines.append(f"- Offer-fit scores: {len(data.get('offer_fit_scores', []))}")
    lines.append(f"- Pricing scenarios: {len(data.get('pricing_scenarios', []))}")
    lines.append(f"- Funnel model stages: {len(data.get('funnel_model', []))}")
    lines.append(f"- Capacity bottleneck: {data.get('capacity_model', {}).get('bottleneck', '')}")
    lines.append(f"- Break-even probability: {data.get('scenario_forecasts', {}).get('breakeven_probability', 0):.0%}")
    lines.append(f"- Critic readiness cap: {data.get('critic_red_team', {}).get('readiness_cap_reason', '')}")
    lines.extend(
        [
            "",
            "## Readiness Strengths & Gaps",
            "### Strengths",
        ]
    )
    lines.extend(f"- {item}" for item in data.get("readiness_strengths", []))
    lines.append("### Gaps")
    lines.extend(f"- {item}" for item in data.get("readiness_gaps", []))
    lines.extend(
        [
            "",
            "## Business Model Canvas",
        ]
    )
    for key, values in data["business_model_canvas"].items():
        lines.append(f"### {key}")
        lines.extend(f"- {item}" for item in values)
    lines.append("")
    lines.append("## Customer Personas")
    for persona in data["personas"]:
        lines.append(f"### {persona['name']}")
        lines.append(f"- Segment: {persona['segment']}")
        lines.append(f"- Buying trigger: {persona['buying_trigger']}")
        lines.append(f"- Channels: {', '.join(persona['channels'])}")
    lines.append("")
    lines.append("## Offer Ladder")
    for offer in data["offer_ladder"]:
        lines.append(f"- **{offer['name']}**: {offer['description']} Success metric: {offer['success_metric']}")
    lines.append("")
    lines.append("## Pricing")
    for tier in data["pricing"]:
        price = as_money(tier["price"], currency_symbol)
        lines.append(f"- **{tier['tier']}**: {price} per {tier['unit']} - {tier['rationale']} Use when: {tier.get('when_to_use', '')} Upgrade path: {tier.get('upgrade_path', '')}")
    lines.append("")
    lines.append("## Cashflow Assumptions")
    for category, assumptions in data.get("cashflow_assumptions", {}).items():
        lines.append(f"### {category.replace('_', ' ').title()}")
        lines.extend(f"- {assumption}" for assumption in assumptions)
    lines.append("")
    lines.append("## 30-Day Roadmap")
    for task in data["roadmap"]:
        lines.append(f"- Day {task['day']} (Week {task['week']}): {task['title']} -> {task['outcome']}")
    lines.append("")
    lines.append("## Marketing Messages")
    for category, messages in data["marketing_messages"].items():
        lines.append(f"### {category.replace('_', ' ').title()}")
        lines.extend(f"- {message}" for message in messages)
    lines.append("")
    lines.append("## Risks & Assumptions")
    lines.extend(f"- Risk: {risk}" for risk in data["risks"])
    lines.extend(f"- Assumption: {assumption}" for assumption in data["assumptions"])
    lines.append("")
    lines.append("## Next 3 Actions")
    lines.extend(f"{index}. {action}" for index, action in enumerate(data["next_3_actions"], start=1))
    lines.append("")
    lines.append("_Financial estimates are illustrative assumptions for planning, not financial advice._")
    return "\n".join(lines)
