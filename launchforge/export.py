"""Markdown and JSON export helpers."""

from __future__ import annotations

import json
from typing import Any, Dict

from pydantic import BaseModel

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
    lines = [
        "# LaunchForge Launch Pack",
        "",
        f"**Business type:** {classification['business_type']}",
        f"**Readiness score:** {data['readiness_score']}/100",
        f"**Break-even month:** {data['breakeven_month']}",
        "",
        "## Business Model Canvas",
    ]
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
        lines.append(f"- **{tier['tier']}**: ${tier['price']} per {tier['unit']} - {tier['rationale']}")
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
