"""LaunchForge Copilot with Gemini execution and grounded fallback answers."""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

from launchforge.adk_runtime import get_runtime_status
from launchforge.agent_registry import get_agent_definitions
from launchforge.llm_agents import construct_agent_if_configured
from launchforge.mcp_server.tools import explain_readiness_score, improve_marketing_message, suggest_next_action
from launchforge.platform_knowledge import explain_metric, retrieve_platform_context, search_platform_knowledge
from launchforge.schemas import model_to_dict
from launchforge.security import safe_copilot_input


FALLBACK_LABEL = "COPILOT \u00b7 DETERMINISTIC FALLBACK"
AI_LABEL = "COPILOT \u00b7 AI-ASSISTED"
FALLBACK_AFTER_AI_ERROR_LABEL = "COPILOT \u00b7 FALLBACK AFTER AI ERROR"
WEB_GROUNDED_LABEL = "COPILOT \u00b7 WEB-GROUNDED"
SCOPE_MESSAGE = (
    "I can help explain LaunchForge, the dashboard tabs, agents, tools, readiness score, pricing, "
    "finance, funnel, roadmap, risks, exports, and the current launch pack. Try asking "
    "'What is the Agent Control Room?' or 'What should I do first?'"
)


@dataclass
class CopilotResponse:
    answer: str
    mode: str
    provider: str
    model: str
    tools_or_context_used: List[str]
    safety_status: str
    response_label: str
    blocked: bool = False
    redacted_question: str = ""
    runtime_mode: str = "deterministic-fallback"
    tools_called: List[str] | None = None
    context_used: List[str] | None = None
    error: str | None = None
    fallback_reason: str | None = None
    retrieved_context: Dict[str, Any] | None = None
    sources_used: List[str] | None = None
    citations: List[Dict[str, str]] | None = None
    intent: str | None = None
    trace: Dict[str, Any] | None = None

    def as_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["tools_called"] = self.tools_called or []
        payload["context_used"] = self.context_used or self.tools_or_context_used
        payload["sources_used"] = self.sources_used or []
        payload["citations"] = self.citations or []
        payload["trace"] = self.trace or {}
        return payload


def _plain_pack(pack: Any) -> Dict[str, Any]:
    if hasattr(pack, "model_dump") or hasattr(pack, "dict"):
        return model_to_dict(pack)
    return dict(pack)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _contains_any(text: str, words: List[str]) -> bool:
    return any(word in text for word in words)


def _format_percent(value: Any) -> str:
    try:
        return f"{float(value):.0%}"
    except (TypeError, ValueError):
        return "not available"


def _format_money(symbol: str, value: Any) -> str:
    try:
        return f"{symbol}{float(value):,.0f}"
    except (TypeError, ValueError):
        return "not available"


def _list_sentence(items: List[Any], fallback: str = "not available") -> str:
    cleaned = [_text(item) for item in items if _text(item)]
    return "; ".join(cleaned) if cleaned else fallback


METRIC_ALIASES = {
    "pain": ["pain", "pain score", "pain intensity"],
    "reach": ["reach", "reachability", "access"],
    "urgency": ["urgency", "urgent"],
    "pay": ["pay", "willingness to pay", "ability to pay"],
    "control": ["control", "buyer control", "buying authority"],
    "readiness": ["readiness", "readiness score", "launch readiness"],
    "break_even": ["break-even", "breakeven", "break even"],
    "forecast": ["forecast", "cashflow", "cash flow", "scenario"],
    "confidence": ["confidence", "model confidence", "classification confidence"],
}


METRIC_FIELDS = {
    "pain": "pain_intensity",
    "reach": "reachability",
    "urgency": "urgency",
    "pay": "willingness_to_pay",
    "control": "buyer_control",
}


EXTERNAL_RESEARCH_TERMS = [
    "competitor",
    "competitors",
    "market research",
    "current trends",
    "trends",
    "typical prices",
    "regulations",
    "big companies",
    "shopify product trends",
    "who are my competitors",
]


INTERNAL_LAUNCHFORGE_TERMS = [
    "launchforge",
    "launch pack",
    "dashboard",
    "tab",
    "view",
    "section",
    "agent",
    "agents",
    "mcp",
    "adk",
    "readiness",
    "break-even",
    "breakeven",
    "cashflow",
    "cash flow",
    "funnel",
    "roadmap",
    "pricing",
    "finance",
    "persona",
    "segment",
    "offer",
    "export",
    "kpi",
    "score",
    "current pack",
    "this pack",
]


EXTERNAL_CURRENT_TERMS = [
    "current",
    "latest",
    "today",
    "yesterday",
    "this week",
    "this month",
    "this year",
    "2025",
    "2026",
    "regulation",
    "regulations",
    "legal requirements",
]


BUSINESS_RESEARCH_TERMS = [
    "business",
    "businesses",
    "company",
    "companies",
    "brand",
    "brands",
    "chain",
    "chains",
    "store",
    "stores",
    "shopify",
    "tutor",
    "tutoring",
    "cafe",
    "food",
    "retail",
    "cleaning",
    "barber",
    "gym",
    "ecommerce",
    "e-commerce",
]


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower().replace("&", " and ")).strip()


def _business_type_label(value: str | None) -> str:
    return str(value or "unknown").replace("_", " ").title()


def _metric_from_field(metric: str) -> str:
    return METRIC_FIELDS.get(metric, metric)


def _matched_metrics(question: str) -> List[str]:
    text = _normalise(question)
    matches: List[str] = []
    for metric, aliases in METRIC_ALIASES.items():
        if any(_normalise(alias) in text for alias in aliases):
            matches.append(metric)
    return matches


def _section_mentions(question: str) -> List[str]:
    text = _normalise(question)
    sections = ["overview", "opportunities", "market", "finance", "action plan", "export", "technical view", "product view", "agent control room"]
    return [section for section in sections if section in text]


def _segment_rows(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [dict(row) for row in data.get("segment_scores", []) or []]


def _recommended_segment(data: Dict[str, Any]) -> Dict[str, Any]:
    rows = _segment_rows(data)
    return next((row for row in rows if row.get("recommended_first_segment")), rows[0] if rows else {})


def _entity_candidates(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in _segment_rows(data):
        name = _text(row.get("persona_name"))
        if name:
            key = ("segment", name.lower())
            seen.add(key)
            candidates.append({"type": "segment", "name": name, "data": row})
    for persona in data.get("personas", []) or []:
        name = _text(persona.get("name"))
        if name and ("segment", name.lower()) not in seen:
            candidates.append({"type": "segment", "name": name, "data": persona})
    for offer in data.get("offer_ladder", []) or []:
        name = _text(offer.get("name"))
        if name:
            candidates.append({"type": "offer", "name": name, "data": offer})
    for tier in data.get("pricing", []) or []:
        name = _text(tier.get("tier"))
        if name:
            candidates.append({"type": "pricing", "name": name, "data": tier})
    return candidates


def _matched_entities(question: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    text = _normalise(question)
    matches: List[Dict[str, Any]] = []
    for candidate in _entity_candidates(data):
        name = candidate["name"]
        name_norm = _normalise(name)
        if name_norm and name_norm in text:
            matches.append(candidate)
            continue
        parts = [part for part in name_norm.split() if len(part) > 2]
        if len(parts) >= 2 and all(part in text for part in parts[:2]):
            matches.append(candidate)
    return matches


def _is_competitor_definition(text: str) -> bool:
    return bool(
        re.search(r"\bwhat\s+(is|are)\s+(a\s+|the\s+)?competitors?\b", text)
        or re.search(r"\bwhat\s+does\s+(a\s+|the\s+)?competitor\s+mean\b", text)
    )


def _is_external_general_question(text: str, metrics: List[str], entities: List[Dict[str, Any]]) -> bool:
    if metrics or entities:
        return False
    if _contains_any(text, INTERNAL_LAUNCHFORGE_TERMS):
        return False
    if _is_competitor_definition(text):
        return True
    if _contains_any(text, ["elon musk", "shopify", "tesla", "spacex"]):
        return True
    return bool(re.search(r"^(who|what|where|when)\s+(is|are|was|were)\b", text))


def _is_competitor_research_question(text: str) -> bool:
    if _is_competitor_definition(text):
        return False
    if _contains_any(text, ["who are my competitors", "my competitors", "competitor list", "competitors for"]):
        return True
    if _contains_any(text, ["competitor", "competitors"]):
        return True
    if _contains_any(text, ["big ", "major ", "largest ", "leading "]) and _contains_any(text, BUSINESS_RESEARCH_TERMS):
        return True
    return False


def _is_external_current_question(text: str, metrics: List[str], entities: List[Dict[str, Any]]) -> bool:
    if metrics or entities:
        return False
    if _contains_any(text, ["current pack", "this pack", "current launch pack"]):
        return False
    if _contains_any(text, ["regulation", "regulations", "legal requirements"]):
        return True
    if _contains_any(text, EXTERNAL_CURRENT_TERMS):
        return not _contains_any(text, INTERNAL_LAUNCHFORGE_TERMS)
    return False


def _classify_router_intent(question: str, metrics: List[str], entities: List[Dict[str, Any]]) -> str:
    text = _normalise(question)
    if _is_competitor_definition(text):
        return "external_general"
    if _is_competitor_research_question(text):
        return "competitor_research"
    if _is_external_current_question(text, metrics, entities):
        return "external_current_info"
    if _contains_any(text, EXTERNAL_RESEARCH_TERMS):
        if _contains_any(text, ["competitor", "competitors", "big companies"]):
            return "competitor_research"
        return "market_research"
    if "agent control room" in text:
        return "dashboard_definition"
    if any(metric in metrics for metric in ["break_even", "forecast"]):
        return "finance_explanation"
    if metrics and any(entity.get("type") == "segment" for entity in entities):
        return "segment_explanation"
    if metrics:
        return "metric_explanation"
    if _contains_any(text, ["why", "recommended", "best segment", "target first", "start here"]):
        return "recommendation"
    if _contains_any(text, ["slogan", "tagline", "headline", "write", "draft", "generate", "whatsapp", "email", "social post", "copy"]):
        return "creative_generation"
    if _contains_any(text, ["funnel", "weakest", "bottleneck", "conversion", "lead", "customer acquisition"]):
        return "marketing_question"
    if _contains_any(text, ["finance", "forecast", "cashflow", "cash flow", "break-even", "breakeven", "budget", "assume"]):
        return "finance_explanation"
    if _contains_any(text, ["roadmap", "timeline", "priority", "task", "milestone", "first week", "do first", "do next"]):
        return "roadmap_action"
    if _contains_any(text, ["critic", "risk", "validate", "failure", "red team", "red-team", "flag"]):
        return "critic_question"
    if _contains_any(text, ["agent", "agents", "tool", "tools", "mcp", "adk", "technical", "execution trace", "fallback", "gemini"]):
        return "technical_explanation"
    if _contains_any(text, ["export", "download", "markdown", "json"]):
        return "export_help"
    if _is_external_general_question(text, metrics, entities):
        return "external_general"
    if _contains_any(text, ["tab", "dashboard", "view", "section", "what is"]):
        return "dashboard_definition"
    return "unknown"


def _source_map_for_intent(intent: str, needs_web: bool) -> List[str]:
    if intent == "external_general":
        return ["gemini_general"]
    sources = ["launch_pack", "platform_kb"]
    if needs_web:
        sources.append("web")
    if intent in {"dashboard_definition", "technical_explanation", "export_help"}:
        sources = ["platform_kb", "launch_pack"]
    if intent == "external_current_info":
        sources = ["web", "launch_pack"] if needs_web else ["launch_pack", "platform_kb"]
    return sources


def _build_context_packet(question: str, data: Dict[str, Any], active_section: str | None = None) -> Dict[str, Any]:
    metrics = _matched_metrics(question)
    entities = _matched_entities(question, data)
    intent = _classify_router_intent(question, metrics, entities)
    needs_web = intent in {"competitor_research", "market_research", "external_current_info"}
    platform_entries = search_platform_knowledge(question, limit=5)
    metric_entries = [explain_metric(metric) for metric in metrics]
    segment_entity = next((entity for entity in entities if entity.get("type") == "segment"), None)
    segment = segment_entity.get("data", {}) if segment_entity else {}
    if not segment and intent in {"metric_explanation", "recommendation"}:
        segment = _recommended_segment(data)
    classification = data.get("classification", {}) or {}
    return {
        "question": question,
        "intent": intent,
        "active_section": active_section,
        "matched_metrics": metrics,
        "matched_entities": [{"type": item.get("type"), "name": item.get("name")} for item in entities],
        "platform_entries": platform_entries,
        "metric_entries": metric_entries,
        "launch_pack_extracts": {
            "business_type": classification.get("business_type"),
            "business_type_label": _business_type_label(classification.get("business_type")),
            "readiness_score": data.get("readiness_score"),
            "readiness_label": data.get("launch_readiness_label"),
            "classification_confidence": classification.get("confidence"),
            "segment": segment,
            "recommended_segment": _recommended_segment(data),
            "segment_scores": _segment_rows(data),
            "offer_ladder": data.get("offer_ladder", [])[:3],
            "pricing_scenarios": data.get("pricing_scenarios", [])[:3],
            "cashflow_assumptions": data.get("cashflow_assumptions", {}),
            "scenario_forecasts": data.get("scenario_forecasts", {}),
            "risks": data.get("risks", [])[:3],
            "next_actions": data.get("next_3_actions", [])[:3],
            "agent_trace": data.get("agent_trace", [])[:5],
        },
        "needs_web": needs_web,
        "sources_planned": _source_map_for_intent(intent, needs_web),
    }


def _current_snapshot(summary: Dict[str, Any]) -> str:
    readiness = summary.get("readiness_score")
    readiness_text = f"{readiness}/100" if readiness is not None else "not scored"
    return (
        f"In the current pack, LaunchForge classified the idea as {summary.get('business_type_label', 'Unknown')} "
        f"with readiness {readiness_text}. Startup cost is {summary.get('startup_cost_display', 'not available')}, "
        f"break-even is {summary.get('breakeven_month', 'not available')}, and runtime mode is "
        f"{summary.get('runtime_mode') or 'deterministic-fallback'}."
    )


def _platform_direct_answer(match: Optional[Dict[str, Any]]) -> str:
    if not match:
        return "This is a LaunchForge question, so I will ground the answer in the current pack."
    title = match.get("title")
    return f"{title}: {match.get('description')}"


def _platform_seeing(match: Optional[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    if not match:
        return _current_snapshot(summary)
    contains = _list_sentence(match.get("contains", []))
    return f"It contains: {contains}. {_current_snapshot(summary)}"


def _platform_next_step(match: Optional[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    if not match:
        return f"Start with the Overview tab, then use the Roadmap. Current first action: {summary.get('next_action')}."
    title = _text(match.get("title")).lower()
    if "overview" in title:
        return f"Use it first, then inspect Customers & Offer and Pricing & Finance. Current first action: {summary.get('next_action')}."
    if "agent control" in title or "agent" in title or "tool" in title:
        return "Use it to verify runtime mode, agent definitions, MCP-style tool calls, and execution trace before discussing the capstone architecture."
    if "pricing" in title or "finance" in title or "scenario" in title or "break-even" in title:
        return f"Validate this assumption before spending more: {summary.get('key_assumption_to_validate') or 'customer conversion rate'}."
    if "funnel" in title:
        return f"Improve the weakest stage first: {summary.get('weakest_funnel_stage')}."
    if "critic" in title or "risk" in title or "readiness" in title:
        tests = _list_sentence(summary.get("critic_validation_tests", [])[:2], "run one validation test before spending more")
        return f"Close the evidence gap by running: {tests}."
    if "roadmap" in title:
        top = summary.get("top_roadmap_priority") or {}
        return f"Start with: {top.get('title') or summary.get('next_action')}."
    if "export" in title:
        return "Download Markdown for a readable submission and JSON for structured review or debugging."
    return f"Use it when: {match.get('when_to_use', 'you need to interpret the launch pack')}."


def classify_copilot_intent(question: str) -> str:
    """Small deterministic intent classifier for no-key fallback quality."""

    text = question.lower()
    creative = [
        "slogan",
        "tagline",
        "headline",
        "write",
        "draft",
        "generate",
        "give me",
        "create",
        "whatsapp",
        "email",
        "social post",
        "caption",
        "copy",
        "hook",
        "outreach message",
    ]
    if _contains_any(text, creative):
        return "creative_generation"
    if _contains_any(text, ["what should i do first", "do first", "do next", "next action", "first action", "first week"]):
        return "next_action"
    if _contains_any(text, ["price", "pricing", "premium", "too low", "too high", "charge", "margin"]):
        return "pricing_question"
    if _contains_any(text, ["finance", "forecast", "cashflow", "cash flow", "break-even", "breakeven", "budget", "assume"]):
        return "finance_question"
    if _contains_any(text, ["funnel", "weakest", "bottleneck", "conversion", "first 10 customers", "customer acquisition", "lead", "marketing channel"]):
        return "marketing_question"
    if _contains_any(text, ["roadmap", "timeline", "priority", "task", "milestone", "30 day", "30-day"]):
        return "roadmap_question"
    if _contains_any(text, ["critic", "risk", "validate", "failure", "red team", "red-team", "spending money", "go/no-go", "go no go"]):
        return "critic_question"
    if _contains_any(text, ["agent", "agents", "adk", "gemini", "ai-assisted", "deterministic fallback", "fallback mode", "execution trace"]):
        return "agent_explanation"
    if _contains_any(text, ["tool", "tools", "mcp", "classify_business_model", "simulate_cashflow", "score_customer", "build_funnel"]):
        return "tool_explanation"
    if _contains_any(
        text,
        [
            "overview",
            "tab",
            "kpi",
            "chart",
            "progress bar",
            "metric",
            "dashboard",
            "agent control room",
            "customers & offer",
            "customers and offer",
            "pricing & finance",
            "marketing & operations",
            "export",
            "currency",
            "startup cost",
            "break-even",
            "readiness label",
        ],
    ):
        return "platform_help"
    if _contains_any(
        text,
        [
            "readiness",
            "classification",
            "business type",
            "strength",
            "gap",
            "assumption",
            "persona",
            "offer",
            "capacity",
            "scenario",
            "pack",
            "launch pack",
        ],
    ):
        return "launch_pack_explanation"
    if _contains_any(text, ["launch", "business", "customer", "founder", "validate", "help", "use this"]):
        return "unknown_related"
    return "unrelated"


def _pack_specific_readout(intent: str, data: Dict[str, Any], retrieved: Dict[str, Any], tools_called: List[str]) -> str:
    summary = retrieved["launch_pack"]

    if intent == "launch_pack_explanation":
        result = explain_readiness_score(data)
        tools_called.append("explain_readiness_score")
        strengths = _list_sentence(summary.get("readiness_strengths", [])[:3])
        gaps = _list_sentence(summary.get("readiness_gaps", [])[:4])
        return f"{result['summary']} Strengths: {strengths}. Gaps: {gaps}."

    if intent == "next_action":
        result = suggest_next_action(data)
        tools_called.append("suggest_next_action")
        return result["answer"]

    if intent == "pricing_question":
        pricing = data.get("pricing_scenarios", []) or []
        if pricing:
            first = pricing[0]
            return (
                f"The Pricing Analyst recommends {first.get('recommended_price')} for {first.get('tier')}. "
                f"Why it matters: {first.get('rationale') or first.get('sensitivity_note')}. "
                f"Upgrade logic: {first.get('sensitivity_note', 'test willingness to pay before locking the price')}."
            )
        return "The pricing area explains each package price, what is included, why it exists, when to use it, and the upgrade path."

    if intent == "marketing_question":
        return (
            f"The weakest funnel stage is {summary.get('weakest_funnel_stage')}. "
            f"Recommendation: {summary.get('weakest_funnel_recommendation') or 'review conversion evidence and improve the handoff to the next stage'}."
        )

    if intent == "finance_question":
        return (
            "The Finance Agent / Finance Simulation Agent assumes conservative/base/aggressive scenarios. "
            f"Break-even probability by month 3 is {_format_percent(summary.get('breakeven_probability'))}. "
            f"Worst-case gap is {_format_money(summary.get('currency_symbol') or '', summary.get('worst_case_gap'))}. "
            f"Key assumption to validate: {summary.get('key_assumption_to_validate') or 'customer conversion rate'}."
        )

    if intent == "critic_question":
        tests = _list_sentence(summary.get("critic_validation_tests", [])[:3])
        missing = _list_sentence(summary.get("critic_missing_evidence", [])[:3])
        return f"The Critic Agent / Risk Critic flagged missing evidence: {missing}. Validation tests to run: {tests}."

    if intent == "roadmap_question":
        top = summary.get("top_roadmap_priority") or {}
        return (
            f"The top roadmap priority is {top.get('title', 'not available')} with priority score "
            f"{top.get('priority_score', 'not available')}. Rationale: {top.get('rationale', 'it reduces launch risk quickly')}."
        )

    if intent in {"agent_explanation", "tool_explanation"}:
        return (
            f"This pack has {summary.get('agent_count', 0)} registered LLM agent definitions and "
            f"{summary.get('tool_count', 0)} MCP-style deterministic tools. Agents reason and synthesize; "
            f"tools calculate structured artefacts. Runtime mode is {summary.get('runtime_mode') or 'deterministic-fallback'}."
        )

    return ""


def _business_terms(data: Dict[str, Any]) -> Dict[str, str]:
    idea = (data.get("input", {}) or {}).get("idea", "")
    business_type = (data.get("classification", {}) or {}).get("business_type", "unknown")
    personas = data.get("personas", []) or []
    persona = personas[0] if personas else {}
    value_props = (data.get("business_model_canvas", {}) or {}).get("Value Proposition", [])
    offers = data.get("offer_ladder", []) or []
    return {
        "idea": idea,
        "business_type": business_type,
        "business_label": business_type.replace("_", " ").title(),
        "customer": persona.get("segment") or persona.get("name") or "the first target customer",
        "value": value_props[0] if value_props else "a clear, practical launch promise",
        "offer": (offers[0] or {}).get("name", "starter offer") if offers else "starter offer",
    }


def _generate_slogans(data: Dict[str, Any]) -> str:
    terms = _business_terms(data)
    idea = terms["idea"].lower()
    if "gcse" in idea or "a-level" in idea or "tutor" in idea or "esat" in idea:
        options = [
            "From exam stress to structured progress.",
            "GCSE, A-Level and ESAT prep with a plan.",
            "Confidence for every paper, progress every week.",
            "Maths and Physics tutoring that parents can track.",
            "Clearer concepts. Better habits. Stronger results.",
            "Your next grade starts with a diagnostic plan.",
        ]
        recommended = options[1]
    elif terms["business_type"] == "physical_retail":
        options = [
            "Your daily essentials, right on the route.",
            "Fast stops, fresh picks, local convenience.",
            "Commuter essentials without the detour.",
            "Breakfast, basics and quick wins every morning.",
            "The neighbourhood stop for everyday needs.",
            "Stocked for the rush, ready for the day.",
        ]
        recommended = options[0]
    elif terms["business_type"] == "ecommerce":
        options = [
            "Small gear, stronger sessions.",
            "Training accessories that keep up.",
            "Bundle your basics. Upgrade your workout.",
            "Affordable gym kit, built for consistency.",
            "Everything you need between warm-up and last rep.",
            "Simple training tools for serious routines.",
        ]
        recommended = options[2]
    else:
        options = [
            f"{terms['business_label']} with a clearer first step.",
            "Launch simple. Learn fast. Serve better.",
            "A practical offer for real customer progress.",
            "Start small, prove demand, build momentum.",
            "Clear value, simple delivery, better outcomes.",
        ]
        recommended = options[0]
    numbered = "\n".join(f"{index}. {option}" for index, option in enumerate(options, start=1))
    return (
        f"Direct answer: Here are slogan options grounded in the current {terms['business_label']} launch pack:\n\n"
        f"{numbered}\n\n"
        f"Recommended: {recommended}\n\n"
        f"Why it fits: it connects the offer ({terms['offer']}) to the customer need ({terms['customer']}) without making unsupported claims."
    )


def _generate_whatsapp_message(data: Dict[str, Any], tools_called: List[str]) -> str:
    original = (data.get("marketing_messages", {}).get("whatsapp_email") or [""])[0]
    business_type = data.get("classification", {}).get("business_type", "unknown")
    result = improve_marketing_message(original, business_type)
    tools_called.append("improve_marketing_message")
    return (
        "Direct answer: Here is a WhatsApp/email draft you can use:\n\n"
        f"{result['improved_message']}\n\n"
        "Why it matters: it keeps the ask small, specific, and tied to the current launch offer.\n\n"
        "What to do next: send it to a small validation list first and record replies, objections, and bookings."
    )


def _generate_social_posts(data: Dict[str, Any]) -> str:
    terms = _business_terms(data)
    return (
        "Direct answer: Here are three social post starters:\n\n"
        f"1. Problem post: If {terms['customer']} is struggling with the current goal, I am testing {terms['offer']} this month.\n"
        f"2. Proof-building post: I am opening a small pilot for {terms['offer']} and collecting feedback before scaling.\n"
        f"3. Call-to-action post: Reply 'launch' if you want the first details or want to test the offer.\n\n"
        "Recommended: start with the problem post because it invites replies without over-selling.\n\n"
        "What to do next: post once, send the message directly to warm contacts, and track response rate."
    )


def _creative_fallback(question: str, data: Dict[str, Any], tools_called: List[str]) -> str:
    text = question.lower()
    if _contains_any(text, ["slogan", "tagline", "headline"]):
        return _generate_slogans(data)
    if _contains_any(text, ["whatsapp", "email", "message", "outreach"]):
        return _generate_whatsapp_message(data, tools_called)
    if _contains_any(text, ["social", "post", "caption", "hook", "copy"]):
        return _generate_social_posts(data)
    return _generate_slogans(data)


def _score_phrase(value: Any, scale: str = "/5") -> str:
    if value is None or value == "":
        return "not scored"
    try:
        number = float(value)
        return f"{number:.0f}{scale}" if number.is_integer() else f"{number:.1f}{scale}"
    except (TypeError, ValueError):
        return str(value)


def _metric_label(metric: str) -> str:
    labels = {
        "pain": "pain",
        "reach": "reach",
        "urgency": "urgency",
        "pay": "willingness to pay",
        "control": "buyer control",
        "break_even": "break-even",
        "readiness": "readiness",
        "forecast": "forecast",
        "confidence": "model confidence",
    }
    return labels.get(metric, metric.replace("_", " "))


def _metric_definition(metric: str) -> str:
    entry = explain_metric(metric)
    if entry:
        return str(entry.get("description", ""))
    return f"{_metric_label(metric).title()} is a LaunchForge planning metric used to interpret the current pack."


def _answer_metric_or_segment(packet: Dict[str, Any]) -> str:
    extracts = packet["launch_pack_extracts"]
    metrics = packet.get("matched_metrics") or []
    metric = metrics[0] if metrics else "segment fit"
    segment = extracts.get("segment") or extracts.get("recommended_segment") or {}
    name = segment.get("persona_name") or segment.get("name") or "the recommended segment"
    business_label = extracts.get("business_type_label", "this business")
    field = _metric_from_field(metric)
    score = segment.get(field)
    overall = segment.get("overall_score")
    definition = _metric_definition(metric)
    score_line = ""
    if score is not None:
        score_line = f"For {name}, {_metric_label(metric)} is scored {_score_phrase(score)}."
    elif metric == "readiness":
        score_line = f"The current readiness score is {extracts.get('readiness_score')}/100."
    elif metric == "confidence":
        confidence = extracts.get("classification_confidence")
        score_line = f"The current model confidence is {_format_percent(confidence)}."
    else:
        score_line = f"I do not have a direct {_metric_label(metric)} score for {name}, but I can use the current segment context."
    overall_line = f" Overall segment fit is {_score_phrase(overall)}." if overall is not None else ""
    rationale = segment.get("rationale") or "Use this as a planning signal, not as proof of demand."
    return (
        f"{_metric_label(metric).title()} means: {definition}\n\n"
        f"{score_line}{overall_line}\n\n"
        f"For the {business_label} launch path, this means {rationale}"
    )


def _answer_recommended_segment(packet: Dict[str, Any]) -> str:
    extracts = packet["launch_pack_extracts"]
    entities = packet.get("matched_entities") or []
    segment = extracts.get("segment") or extracts.get("recommended_segment") or {}
    if entities:
        named = entities[0].get("name")
        for row in extracts.get("segment_scores", []):
            if _normalise(row.get("persona_name", "")) == _normalise(named):
                segment = row
                break
    name = segment.get("persona_name") or segment.get("name") or "the recommended segment"
    recommended = "is" if segment.get("recommended_first_segment") else "is not marked as"
    return (
        f"{name} {recommended} the recommended first segment in this launch pack.\n\n"
        f"Score profile: pain {_score_phrase(segment.get('pain_intensity'))}, reach {_score_phrase(segment.get('reachability'))}, "
        f"urgency {_score_phrase(segment.get('urgency'))}, pay {_score_phrase(segment.get('willingness_to_pay'))}, "
        f"control {_score_phrase(segment.get('buyer_control'))}, overall {_score_phrase(segment.get('overall_score'))}.\n\n"
        f"Why: {segment.get('rationale', 'LaunchForge recommends the segment with the best mix of urgency, reachability, buying authority, and fit.')}"
    )


def _answer_finance_context(packet: Dict[str, Any], data: Dict[str, Any]) -> str:
    text = _normalise(packet.get("question", ""))
    extracts = packet["launch_pack_extracts"]
    scenario = extracts.get("scenario_forecasts") or {}
    assumptions = extracts.get("cashflow_assumptions") or {}
    if "break" in text or "breakeven" in text:
        scenarios = scenario.get("scenarios", []) or []
        count = len(scenarios)
        covered = sum(1 for row in scenarios if row.get("break_even_month") != "Beyond 3 months")
        coverage = f"{covered}/{count} modelled scenarios" if count else "the base model"
        return (
            "Break-even here means the point where cumulative cashflow has recovered the planned startup cost and monthly costs. "
            "It is a deterministic planning model, not a guarantee or a real-world probability.\n\n"
            f"In this pack, break-even is shown as {data.get('breakeven_month', 'not available')}; scenario coverage is {coverage}. "
            f"The key assumption to validate is {scenario.get('key_assumption_to_validate', 'customer conversion rate')}."
        )
    revenue = _list_sentence(assumptions.get("revenue", [])[:3])
    costs = _list_sentence(assumptions.get("costs", [])[:3])
    return (
        "The Finance Agent builds planning forecasts from explicit conservative/base/aggressive scenarios, not guarantees.\n\n"
        f"Revenue assumptions: {revenue}.\n\n"
        f"Cost assumptions: {costs}.\n\n"
        f"Key assumption to validate: {scenario.get('key_assumption_to_validate', 'customer conversion rate')}."
    )


def _answer_external_without_web(packet: Dict[str, Any]) -> str:
    text = _normalise(packet.get("question", ""))
    if not _contains_any(text, BUSINESS_RESEARCH_TERMS + ["competitor", "competitors", "market", "trend", "trends", "price", "prices", "regulation", "regulations"]):
        return _answer_external_general_without_ai(packet)
    extracts = packet["launch_pack_extracts"]
    business_label = extracts.get("business_type_label", "this business")
    segment = extracts.get("recommended_segment") or {}
    offer = (extracts.get("offer_ladder") or [{}])[0]
    if _contains_any(text, ["regulation", "regulations", "legal requirements"]):
        return (
            "Live web search was not used/configured, so treat this as general guidance. "
            "I have not searched current regulations and this is not legal advice.\n\n"
            f"For the current {business_label} pack, turn regulation research into a checklist covering licenses, "
            "local authority rules, insurance, customer data handling, health/safety obligations, and any sector-specific rules.\n\n"
            "Practical next step: verify the checklist against official government or local authority sources before spending money or opening."
        )
    return (
        "I can answer from your launch pack, but live web search is not configured in this environment. "
        "I have not searched the web and I will not invent current competitor facts.\n\n"
        f"From the current {business_label} pack, start competitor research around businesses serving "
        f"{segment.get('segment') or segment.get('persona_name') or 'your first target segment'} with an offer similar to "
        f"{offer.get('name', 'your starter offer')}.\n\n"
        "Practical next step: list 5 local/online alternatives your target customer would compare you with, capture their pricing, promise, proof, and acquisition channel, then update your offer or pricing assumptions."
    )


def _answer_external_general_without_ai(packet: Dict[str, Any]) -> str:
    return (
        "That is an external/general question, so LaunchForge should answer it from Gemini general knowledge or live web grounding, "
        "not from the launch pack.\n\n"
        "In this local fallback run, Gemini general answering or live web search is not configured, so I will not guess external facts "
        "from LaunchForge's internal context.\n\n"
        "Ask a launch-pack question for a deterministic answer, or enable GOOGLE_API_KEY to let Copilot answer external/general questions."
    )


def _contextual_fallback_answer(packet: Dict[str, Any], data: Dict[str, Any], retrieved: Dict[str, Any], tools_called: List[str], web_status: Dict[str, Any] | None = None) -> str:
    intent = packet.get("intent", "unknown")
    if intent == "external_general":
        return _answer_external_general_without_ai(packet)
    if intent in {"competitor_research", "market_research", "external_current_info"}:
        return _answer_external_without_web(packet)
    if intent in {"segment_explanation", "metric_explanation"} and (packet.get("matched_metrics") or packet["launch_pack_extracts"].get("segment")):
        return _answer_metric_or_segment(packet)
    if intent == "recommendation":
        return _answer_recommended_segment(packet)
    if intent == "finance_explanation":
        return _answer_finance_context(packet, data)
    if intent == "creative_generation":
        return _creative_fallback(packet.get("question", ""), data, tools_called)

    legacy_intent_map = {
        "dashboard_definition": "platform_help",
        "technical_explanation": "agent_explanation",
        "export_help": "platform_help",
        "marketing_question": "marketing_question",
        "critic_question": "critic_question",
        "roadmap_action": "roadmap_question",
        "unknown": classify_copilot_intent(packet.get("question", "")),
    }
    legacy_intent = legacy_intent_map.get(intent, classify_copilot_intent(packet.get("question", "")))
    return _compose_fallback_answer(legacy_intent, packet.get("question", ""), data, retrieved, tools_called)


def _compose_fallback_answer(intent: str, question: str, data: Dict[str, Any], retrieved: Dict[str, Any], tools_called: List[str]) -> str:
    if intent == "unrelated":
        return SCOPE_MESSAGE
    if intent == "creative_generation":
        return _creative_fallback(question, data, tools_called)

    match = retrieved.get("primary_match")
    summary = retrieved["launch_pack"]
    pack_readout = _pack_specific_readout(intent, data, retrieved, tools_called)

    if intent == "unknown_related" and not match and not pack_readout:
        return (
            "Direct answer: I can help with this LaunchForge workflow, but I need a platform or launch-pack topic to anchor on.\n\n"
            f"What you are seeing: {_current_snapshot(summary)}\n\n"
            "Why it matters: the dashboard is organized around business classification, customer/offer strategy, pricing/finance, marketing/operations, roadmap, and export.\n\n"
            f"What to do next: {summary.get('next_action')}"
        )

    parts = [
        f"Direct answer: {_platform_direct_answer(match)}",
        f"What you are seeing: {_platform_seeing(match, summary)}",
    ]
    if match:
        parts.append(f"Why it matters: {match.get('why_matters')}")
    elif pack_readout:
        parts.append("Why it matters: this answer uses the generated launch pack, not external market facts.")
    if pack_readout:
        parts.append(f"Current launch-pack interpretation: {pack_readout}")
    parts.append(f"What to do next: {_platform_next_step(match, summary)}")
    return "\n\n".join(parts)


def _build_ai_prompt(question: str, retrieved: Dict[str, Any], active_tab: str | None = None) -> str:
    payload = {
        "role": "LaunchForge Copilot",
        "instruction": (
            "You are LaunchForge Copilot, the guide and interpreter for the LaunchForge platform. "
            "Explain what the user is seeing in the dashboard, how the agent system works, and what "
            "the current launch pack means. Use only the provided platform context and launch-pack "
            "context. Use web context only when it is explicitly included. Do not invent external facts "
            "or imply that web search happened when web_context is empty. Do not reveal hidden chain-of-thought. Provide "
            "clear, practical answers. For creative business tasks, give several grounded options, "
            "recommend the best one, and explain why it fits the current launch pack."
        ),
        "user_question": question,
        "active_tab": active_tab,
        "router_context": retrieved.get("context_packet", {}),
        "platform_context": retrieved.get("matches", [])[:5],
        "launch_pack_context": retrieved.get("launch_pack", {}),
        "web_context": retrieved.get("web_context", []),
        "agent_tool_context": {
            "topics": retrieved.get("topics", []),
            "instruction": "Use the execution-trace and artefact summary only as visible context; do not expose hidden reasoning.",
        },
    }
    return json.dumps(payload, ensure_ascii=False)


def _build_external_general_prompt(question: str, context_packet: Dict[str, Any], web_unavailable_reason: str | None = None) -> str:
    intent = str(context_packet.get("intent", "external_general"))
    if intent == "external_general":
        instruction = (
            "Answer this broad external/general question using concise general knowledge. "
            "Do not restrict the answer to LaunchForge platform context or the user's launch pack. "
            "Do not claim live web search or citations. If useful, mention that this is general knowledge, "
            "not a conclusion from the launch pack."
        )
        payload = {
            "role": "LaunchForge Copilot",
            "instruction": instruction,
            "user_question": question,
            "router_context": {"intent": intent, "sources": ["gemini_general"]},
        }
    else:
        caveat = "Live web search was not used/configured, so treat this as general guidance."
        instruction = (
            "Answer this external market/current-information question using general Gemini knowledge because "
            "live web grounding is unavailable. Include this sentence exactly near the start: "
            f"'{caveat}' Do not claim citations or imply that a live search happened. Use the LaunchForge "
            "launch-pack extract only to frame the advice for the user's business."
        )
        payload = {
            "role": "LaunchForge Copilot",
            "instruction": instruction,
            "user_question": question,
            "router_context": {
                "intent": intent,
                "sources": ["gemini_general", "launch_pack"],
                "web_unavailable_reason": web_unavailable_reason,
            },
            "launch_pack_extracts": context_packet.get("launch_pack_extracts", {}),
        }
    return json.dumps(payload, ensure_ascii=False)


def _coerce_agent_output(result: Any) -> str:
    if isinstance(result, str):
        return result.strip()
    if isinstance(result, dict):
        for key in ("answer", "content", "text", "output"):
            if result.get(key):
                return str(result[key]).strip()
    for attr in ("text", "content", "output"):
        if hasattr(result, attr):
            value = getattr(result, attr)
            if value:
                return str(value).strip()
    if hasattr(result, "candidates"):
        try:
            return str(result.candidates[0].content.parts[0].text).strip()
        except Exception:  # noqa: BLE001
            return ""
    return ""


def call_gemini(prompt: str, model: str, api_key: str) -> str:
    """Call Google AI Studio Gemini through google-genai.

    Tests monkeypatch this function; no test performs an external API call.
    """

    from google import genai  # type: ignore

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model, contents=prompt)
    text = _coerce_agent_output(response)
    if not text and hasattr(response, "text"):
        text = str(response.text).strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return text


def web_search_available() -> bool:
    """Return whether Gemini Google Search grounding appears usable locally."""

    if not os.getenv("GOOGLE_API_KEY"):
        return False
    try:
        from google import genai  # type: ignore  # noqa: F401
        from google.genai import types  # type: ignore

        return bool(hasattr(types, "Tool") and hasattr(types, "GoogleSearch"))
    except Exception:  # noqa: BLE001
        return False


def _extract_grounding_citations(response: Any) -> List[Dict[str, str]]:
    citations: List[Dict[str, str]] = []
    try:
        candidates = getattr(response, "candidates", []) or []
        for candidate in candidates:
            metadata = getattr(candidate, "grounding_metadata", None) or getattr(candidate, "groundingMetadata", None)
            chunks = getattr(metadata, "grounding_chunks", None) or getattr(metadata, "groundingChunks", None) or []
            for chunk in chunks:
                web = getattr(chunk, "web", None)
                if web:
                    title = getattr(web, "title", "") or "Source"
                    uri = getattr(web, "uri", "") or ""
                    if uri:
                        citations.append({"title": str(title), "url": str(uri)})
    except Exception:  # noqa: BLE001
        return citations
    return citations


def answer_with_web_grounding(question: str, context_packet: Dict[str, Any], runtime: Dict[str, Any]) -> Dict[str, Any]:
    """Try Gemini Google Search grounding for external/current questions.

    This is optional. If the installed google-genai package or model does not
    support Google Search tools, callers receive an unavailable status instead
    of a crash or a fake search result.
    """

    if not web_search_available():
        return {"available": False, "answer": "", "citations": [], "error": "Live web search is not configured in this environment."}
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"available": False, "answer": "", "citations": [], "error": "GOOGLE_API_KEY is not set."}
    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore

        tool = types.Tool(google_search=types.GoogleSearch())
        config = types.GenerateContentConfig(tools=[tool])
        prompt = json.dumps(
            {
                "instruction": (
                    "Answer the LaunchForge user's external/current question using Google Search grounding. "
                    "Use the launch-pack context to frame the search. Include practical next steps. "
                    "Do not expose API keys or hidden reasoning."
                ),
                "question": question,
                "context_packet": context_packet,
            },
            ensure_ascii=False,
        )
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=runtime.get("model", "gemini-2.5-flash"), contents=prompt, config=config)
        answer = _coerce_agent_output(response)
        if not answer and hasattr(response, "text"):
            answer = str(response.text).strip()
        if not answer:
            raise RuntimeError("Gemini web-grounded response was empty.")
        return {"available": True, "answer": answer, "citations": _extract_grounding_citations(response), "error": None}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "answer": "", "citations": [], "error": f"{type(exc).__name__}: {exc}"}


def _try_adk_assisted_answer(prompt: str) -> Tuple[Optional[str], Optional[str]]:
    definition = next((item for item in get_agent_definitions() if item.name == "LaunchForge_Copilot_Agent"), None)
    if definition is None:
        return None, "Copilot agent definition was not found."
    constructed = construct_agent_if_configured(definition)
    agent = constructed.get("agent")
    if not constructed.get("constructed") or agent is None:
        return None, constructed.get("reason", "ADK Copilot agent could not be constructed.")
    try:
        for method_name in ("run", "invoke", "generate", "respond"):
            method = getattr(agent, method_name, None)
            if callable(method):
                answer = _coerce_agent_output(method(prompt))
                if answer:
                    return answer, None
        if callable(agent):
            answer = _coerce_agent_output(agent(prompt))
            if answer:
                return answer, None
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"
    return None, "ADK agent did not return text."


def _try_ai_assisted_answer(question: str, retrieved: Dict[str, Any], runtime: Dict[str, Any], active_tab: str | None = None) -> Tuple[Optional[str], Optional[str]]:
    if runtime.get("mode") != "ai-assisted":
        return None, None
    prompt = _build_ai_prompt(question, retrieved, active_tab)
    provider = runtime.get("provider")
    if provider == "google-genai-gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None, "GOOGLE_API_KEY disappeared before the Gemini call."
        try:
            return call_gemini(prompt=prompt, model=runtime.get("model", "gemini-2.5-flash"), api_key=api_key), None
        except Exception as exc:  # noqa: BLE001
            return None, f"{type(exc).__name__}: {exc}"
    if provider == "google-adk-gemini":
        return _try_adk_assisted_answer(prompt)
    return None, None


def _try_general_ai_answer(
    question: str,
    context_packet: Dict[str, Any],
    runtime: Dict[str, Any],
    web_unavailable_reason: str | None = None,
) -> Tuple[Optional[str], Optional[str]]:
    if runtime.get("mode") != "ai-assisted":
        return None, None
    prompt = _build_external_general_prompt(question, context_packet, web_unavailable_reason)
    provider = runtime.get("provider")
    if provider == "google-genai-gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None, "GOOGLE_API_KEY disappeared before the Gemini call."
        try:
            return call_gemini(prompt=prompt, model=runtime.get("model", "gemini-2.5-flash"), api_key=api_key), None
        except Exception as exc:  # noqa: BLE001
            return None, f"{type(exc).__name__}: {exc}"
    if provider == "google-adk-gemini":
        return _try_adk_assisted_answer(prompt)
    return None, None


def _response(
    *,
    answer: str,
    mode: str,
    provider: str,
    model: str,
    label: str,
    redacted_question: str,
    tools_called: List[str],
    context_used: List[str],
    safety_status: str,
    runtime_mode: str,
    retrieved: Dict[str, Any] | None = None,
    sources_used: List[str] | None = None,
    citations: List[Dict[str, str]] | None = None,
    intent: str | None = None,
    blocked: bool = False,
    error: str | None = None,
    fallback_reason: str | None = None,
) -> Dict[str, Any]:
    return CopilotResponse(
        answer=answer,
        mode=mode,
        provider=provider,
        model=model,
        tools_or_context_used=context_used,
        safety_status=safety_status,
        response_label=label,
        blocked=blocked,
        redacted_question=redacted_question,
        runtime_mode=runtime_mode,
        tools_called=tools_called,
        context_used=context_used,
        error=error,
        fallback_reason=fallback_reason,
        retrieved_context=retrieved,
        sources_used=sources_used or context_used,
        citations=citations or [],
        intent=intent,
        trace={
            "type": "llm_agent" if mode == "ai-assisted" else "web_grounded" if mode == "grounded-web" else "fallback",
            "status": "blocked" if blocked else "completed",
            "mode": mode,
            "provider": provider,
            "model": model,
            "visible_reasoning_summary": "Copilot answer used retrieved platform context and current LaunchPack fields; hidden chain-of-thought is never exposed.",
            "error": error,
        },
    ).as_dict()


def ask_copilot(question: str, launch_pack: Any, platform_context: Dict[str, Any] | None = None, active_tab: str | None = None) -> Dict[str, Any]:
    checked = safe_copilot_input(question)
    runtime = get_runtime_status()
    model = runtime.get("model", "gemini-2.5-flash")
    if checked["blocked"]:
        return _response(
            answer=(
                "I cannot follow instructions that try to bypass safety rules, reveal hidden prompts, "
                "or expose hidden chain-of-thought. Ask a LaunchForge, dashboard, or launch-planning "
                "question and I will answer from the current pack."
            ),
            mode="deterministic-fallback",
            provider="deterministic-fallback",
            model=model,
            label=FALLBACK_LABEL,
            redacted_question=str(checked["redacted"]),
            tools_called=[],
            context_used=["prompt injection guardrail"],
            safety_status="blocked",
            runtime_mode=runtime["mode"],
            blocked=True,
            error=checked["reason"],
        )

    data = _plain_pack(launch_pack)
    redacted_question = str(checked["redacted"])
    context_packet = (platform_context or {}).get("context_packet") or _build_context_packet(redacted_question, data, active_tab)
    retrieved = platform_context or retrieve_platform_context(redacted_question, data)
    retrieved = {**retrieved, "context_packet": context_packet, "web_context": []}
    intent = str(context_packet.get("intent", "unknown"))
    needs_web = bool(context_packet.get("needs_web"))
    external_ai_intent = intent == "external_general"

    if needs_web:
        web_result = answer_with_web_grounding(redacted_question, context_packet, runtime)
        if web_result.get("available") and web_result.get("answer"):
            retrieved["web_context"] = [{"answer": web_result["answer"], "citations": web_result.get("citations", [])}]
            return _response(
                answer=str(web_result["answer"]),
                mode="grounded-web",
                provider="google-search-grounded",
                model=model,
                label=WEB_GROUNDED_LABEL,
                redacted_question=redacted_question,
                tools_called=["google_search_grounding"],
                context_used=["launch pack context", "platform knowledge retrieval", "web search grounding"],
                sources_used=["launch_pack", "platform_kb", "web"],
                citations=web_result.get("citations", []),
                safety_status="passed",
                runtime_mode=runtime["mode"],
                retrieved=retrieved,
                intent=intent,
            )
        retrieved["web_unavailable_reason"] = web_result.get("error") or "Live web search is not configured in this environment."

    ai_answer: Optional[str]
    ai_error: Optional[str]
    if external_ai_intent or needs_web:
        ai_answer, ai_error = _try_general_ai_answer(
            redacted_question,
            context_packet,
            runtime,
            retrieved.get("web_unavailable_reason"),
        )
    else:
        ai_answer, ai_error = _try_ai_assisted_answer(redacted_question, retrieved, runtime, active_tab)
    if ai_answer:
        if external_ai_intent:
            context_used = ["Gemini general knowledge"]
            sources_used = ["gemini_general"]
        elif needs_web:
            context_used = ["Gemini general knowledge", "launch pack context", "web unavailable notice"]
            sources_used = ["gemini_general", "launch_pack"]
        else:
            context_used = ["platform knowledge retrieval", "launch pack context", runtime.get("provider", "Gemini")]
            sources_used = ["platform_kb", "launch_pack"]
        return _response(
            answer=ai_answer,
            mode="ai-assisted",
            provider=runtime.get("provider", "google-genai-gemini"),
            model=model,
            label=AI_LABEL,
            redacted_question=redacted_question,
            tools_called=[],
            context_used=context_used,
            sources_used=sources_used,
            safety_status="passed",
            runtime_mode=runtime["mode"],
            retrieved=retrieved,
            intent=intent,
        )

    tools_called: List[str] = []
    answer = _contextual_fallback_answer(context_packet, data, retrieved, tools_called, {"error": retrieved.get("web_unavailable_reason")})
    legacy_intent = classify_copilot_intent(redacted_question)
    if legacy_intent == "unrelated" and intent == "unknown":
        context_used = ["scope guardrail", "fallback routing"]
    else:
        context_used = ["platform knowledge retrieval", "launch pack context", "fallback routing", f"intent:{intent}"]
    sources_used = [source for source in context_packet.get("sources_planned", ["launch_pack", "platform_kb"]) if source != "web"]

    if ai_error:
        return _response(
            answer=answer,
            mode="fallback after ai error",
            provider="deterministic-fallback",
            model=model,
            label=FALLBACK_AFTER_AI_ERROR_LABEL,
            redacted_question=redacted_question,
            tools_called=tools_called,
            context_used=context_used,
            sources_used=sources_used,
            safety_status="passed",
            runtime_mode=runtime["mode"],
            retrieved=retrieved,
            intent=intent,
            error=ai_error,
            fallback_reason=ai_error,
        )

    return _response(
        answer=answer,
        mode="deterministic-fallback",
        provider="deterministic-fallback",
        model=model,
        label=FALLBACK_LABEL,
        redacted_question=redacted_question,
        tools_called=tools_called,
        context_used=context_used,
        sources_used=sources_used,
        safety_status="passed",
        runtime_mode=runtime["mode"],
        retrieved=retrieved,
        intent=intent,
        fallback_reason=retrieved.get("web_unavailable_reason"),
    )


def ask_launchforge_copilot(
    question: str,
    launch_pack: Any,
    active_section: str | None = None,
    use_web: bool | None = None,
) -> Dict[str, Any]:
    """Central contextual Copilot router.

    `use_web` can force or disable web routing for tests or future UI toggles.
    The current compatibility response keeps existing mode labels while adding
    router fields such as intent, sources_used, retrieved_context, and citations.
    """

    if use_web is None:
        return ask_copilot(question=question, launch_pack=launch_pack, active_tab=active_section)
    data = _plain_pack(launch_pack)
    packet = _build_context_packet(question, data, active_section)
    if use_web:
        packet["needs_web"] = True
        packet["sources_planned"] = _source_map_for_intent(str(packet.get("intent", "unknown")), True)
    else:
        packet["needs_web"] = False
        packet["sources_planned"] = _source_map_for_intent(str(packet.get("intent", "unknown")), False)
    platform_context = retrieve_platform_context(question, data)
    platform_context = {**platform_context, "context_packet": packet}
    return ask_copilot(question=question, launch_pack=launch_pack, platform_context=platform_context, active_tab=active_section)


def answer_copilot_question(question: str, pack: Any) -> Dict[str, Any]:
    return ask_copilot(question=question, launch_pack=pack)

