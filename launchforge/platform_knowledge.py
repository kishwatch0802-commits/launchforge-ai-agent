"""Grounding knowledge for LaunchForge Copilot.

This module is intentionally deterministic. It gives the Copilot a product
dictionary for the dashboard and a compact summary of the current launch pack
without calling external services or storing user input.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from launchforge.schemas import model_to_dict


KnowledgeEntry = Dict[str, Any]


PLATFORM_KNOWLEDGE: Dict[str, KnowledgeEntry] = {
    "overview": {
        "title": "Overview tab",
        "category": "tab",
        "aliases": ["overview", "overview tab", "executive summary", "summary tab", "first tab"],
        "description": "The executive summary of the generated launch pack.",
        "contains": [
            "business type",
            "readiness score",
            "classification evidence",
            "business model canvas",
            "readiness strengths and gaps",
            "risks and next actions",
        ],
        "why_matters": "It lets you understand the overall plan before reviewing specialist details.",
        "when_to_use": "Start here after generating a pack.",
    },
    "agent_control_room": {
        "title": "Agent Control Room",
        "category": "tab",
        "aliases": ["agent control room", "agent studio", "agents tab", "agent trace", "execution trace"],
        "description": "The technical view that shows how LaunchForge built the pack.",
        "contains": [
            "runtime status",
            "LLM agent definitions",
            "MCP-style tool mapping",
            "execution trace",
            "Copilot",
        ],
        "why_matters": "It proves the project separates agents from deterministic tools and records what each layer produced.",
        "when_to_use": "Use it when you want to inspect the agent system, fallback mode, tools, or Copilot grounding.",
    },
    "customers_offer": {
        "title": "Customers & Offer tab",
        "category": "tab",
        "aliases": ["customers", "customers and offer", "customers & offer", "persona", "personas", "offer ladder"],
        "description": "The strategy workspace for deciding who to serve first and what to sell.",
        "contains": ["persona cards", "segment scores", "offer ladder", "offer-fit scores", "package positioning"],
        "why_matters": "A launch plan only becomes practical when the first customer and first offer are specific.",
        "when_to_use": "Use it to choose the first target segment and refine the starter, core, and premium offers.",
    },
    "pricing_finance": {
        "title": "Pricing & Finance tab",
        "category": "tab",
        "aliases": ["pricing", "finance", "pricing and finance", "cashflow", "forecast", "startup costs"],
        "description": "The commercial planning view for pricing, assumptions, and cashflow scenarios.",
        "contains": ["pricing cards", "cashflow chart", "startup cost breakdown", "scenario forecasts", "finance assumptions"],
        "why_matters": "It turns the launch idea into planning numbers without presenting them as guaranteed predictions.",
        "when_to_use": "Use it before spending money, changing price, or deciding how much validation is needed.",
    },
    "marketing_operations": {
        "title": "Marketing & Operations tab",
        "category": "tab",
        "aliases": ["marketing", "operations", "marketing and operations", "funnel", "capacity", "checklist"],
        "description": "The tactical view for finding customers and delivering the offer reliably.",
        "contains": ["sales funnel", "funnel model", "marketing messages", "channel strategy", "operations checklist", "capacity model"],
        "why_matters": "A launch can fail either because leads do not convert or because delivery cannot keep up.",
        "when_to_use": "Use it to improve outreach, fix funnel bottlenecks, and check operational readiness.",
    },
    "roadmap": {
        "title": "Roadmap tab",
        "category": "tab",
        "aliases": ["roadmap", "launch tracker", "execution board", "timeline", "30 day plan", "30-day plan"],
        "description": "The execution board for the first 30 days of launch work.",
        "contains": ["weekly milestones", "day badges", "task outcomes", "priority scores", "dependencies", "risk-reduction notes"],
        "why_matters": "It converts strategy into sequenced actions with visible completion criteria.",
        "when_to_use": "Use it when deciding what to do this week and what depends on earlier validation.",
    },
    "export": {
        "title": "Export tab",
        "category": "tab",
        "aliases": ["export", "download", "markdown", "json", "deliverables", "launch pack deliverables"],
        "description": "The deliverables center for downloading the launch pack.",
        "contains": ["Markdown export", "JSON export", "pack summary", "agent trace", "technical artefacts"],
        "why_matters": "Exports let you submit, share, archive, or inspect the generated pack without automatic persistence.",
        "when_to_use": "Use Markdown for a readable submission and JSON for structured review or downstream tooling.",
    },
    "copilot": {
        "title": "LaunchForge Copilot",
        "category": "assistant",
        "aliases": ["copilot", "assistant", "guide", "help", "chat"],
        "description": "The grounded guide for understanding the platform and the current launch pack.",
        "contains": ["platform explanations", "launch-pack interpretation", "agent/tool explanations", "next-step guidance"],
        "why_matters": "It helps users interpret the dashboard instead of leaving them to decode every artefact alone.",
        "when_to_use": "Ask about tabs, metrics, agents, tools, scores, pricing, finance, funnel, risks, roadmap, or exports.",
    },
    "readiness_score": {
        "title": "Readiness score",
        "category": "metric",
        "aliases": ["readiness", "readiness score", "launch readiness", "validation-ready", "blue progress bar", "progress bar"],
        "description": "A 0 to 100 planning score that estimates how prepared the business is for launch.",
        "contains": ["strengths", "gaps", "stage cap", "validation evidence", "readiness breakdown"],
        "why_matters": "It prevents idea-only businesses from looking more launch-ready than their evidence supports.",
        "when_to_use": "Use it to decide which gaps to close before spending more money.",
    },
    "kpi_cards": {
        "title": "KPI cards",
        "category": "metric",
        "aliases": ["kpi", "kpi cards", "metric cards", "top cards", "dashboard cards"],
        "description": "The top summary cards for business type, readiness, startup cost, break-even, and currency.",
        "contains": ["business type", "readiness", "startup cost", "break-even", "currency"],
        "why_matters": "They give a fast read on classification, risk, cost, and localization before the detailed tabs.",
        "when_to_use": "Use them as the first scan after generating a pack.",
    },
    "business_type": {
        "title": "Business type",
        "category": "metric",
        "aliases": ["business type", "classification", "classified", "business model", "model type"],
        "description": "The category LaunchForge assigns to the idea, such as local service, physical retail, or ecommerce.",
        "contains": ["confidence", "matched signals", "reasoning", "uncertainty notes"],
        "why_matters": "The business type controls which templates, risks, pricing logic, and roadmap actions are used.",
        "when_to_use": "Check it first if the generated pack feels off.",
    },
    "startup_cost": {
        "title": "Estimated startup cost",
        "category": "metric",
        "aliases": ["startup cost", "startup costs", "estimated startup cost", "budget", "cost breakdown"],
        "description": "The upfront cost estimate used for the planning forecast.",
        "contains": ["cost categories", "cashflow inputs", "finance assumptions"],
        "why_matters": "It shows how much cash the plan assumes before revenue starts arriving.",
        "when_to_use": "Use it to decide whether to validate demand before committing spend.",
    },
    "break_even": {
        "title": "Break-even",
        "category": "metric",
        "aliases": ["break-even", "breakeven", "break even", "break-even month", "breakeven month"],
        "description": "The point where cumulative revenue has covered the planned startup and monthly costs.",
        "contains": ["month estimate", "scenario forecasts", "assumptions", "not financial advice disclaimer"],
        "why_matters": "It helps compare downside risk and how quickly the idea might recover its launch costs.",
        "when_to_use": "Use it as a planning signal, not as a guaranteed prediction.",
    },
    "currency": {
        "title": "Currency badge",
        "category": "metric",
        "aliases": ["currency", "currency badge", "pound", "gbp", "dollar", "usd"],
        "description": "The detected currency used consistently in pricing, startup costs, cashflow, and exports.",
        "contains": ["currency code", "currency symbol", "localized prices"],
        "why_matters": "It keeps UK-heavy demos in GBP and avoids mixing symbols across the pack.",
        "when_to_use": "Check it if prices or costs look localized incorrectly.",
    },
    "segment_scores": {
        "title": "Segment scores",
        "category": "technical artefact",
        "aliases": ["segment scores", "customer scores", "persona scores", "recommended first segment"],
        "description": "A scoring model for which customer/persona should be targeted first.",
        "contains": ["pain intensity", "reachability", "urgency", "willingness to pay", "buyer control"],
        "why_matters": "It makes customer selection explicit instead of assuming all audiences are equally good.",
        "when_to_use": "Use it before writing outreach or choosing a marketing channel.",
    },
    "offer_fit_scores": {
        "title": "Offer-fit scores",
        "category": "technical artefact",
        "aliases": ["offer-fit", "offer fit", "offer score", "package score", "offer ladder score"],
        "description": "A score for how well each offer matches customer pain, feasibility, differentiation, and revenue potential.",
        "contains": ["pain match", "delivery feasibility", "differentiation", "revenue potential", "complexity"],
        "why_matters": "It shows whether the offer ladder is attractive and deliverable.",
        "when_to_use": "Use it when deciding whether to simplify, premiumize, or reorder packages.",
    },
    "pricing_scenarios": {
        "title": "Pricing scenarios",
        "category": "technical artefact",
        "aliases": ["pricing scenarios", "low price", "base price", "premium price", "recommended price", "pricing cards"],
        "description": "Low, base, and premium price options for each tier or product bundle.",
        "contains": ["recommended price", "conversion assumption", "margin estimate", "sensitivity note"],
        "why_matters": "It shows price tradeoffs instead of presenting one number as certain.",
        "when_to_use": "Use it to test whether pricing is too low, too high, or missing an upgrade path.",
    },
    "funnel_model": {
        "title": "Funnel model",
        "category": "technical artefact",
        "aliases": ["funnel model", "sales funnel", "conversion funnel", "weakest funnel stage", "bottleneck stage"],
        "description": "A staged conversion model from awareness to first sale or package conversion.",
        "contains": ["stage volume", "conversion rate", "output volume", "bottleneck flag", "improvement recommendation"],
        "why_matters": "It shows where customer acquisition is most likely to leak.",
        "when_to_use": "Use it to decide which channel or message to improve first.",
    },
    "capacity_model": {
        "title": "Capacity model",
        "category": "technical artefact",
        "aliases": ["capacity", "capacity model", "operational bottleneck", "founder hours", "delivery capacity"],
        "description": "An operational model for how many customers, orders, or sessions the founder can handle.",
        "contains": ["available hours", "admin hours", "delivery hours", "maximum customers or orders", "scaling constraint"],
        "why_matters": "It prevents the launch plan from selling more than the operation can deliver.",
        "when_to_use": "Use it before increasing outreach volume or adding a premium offer.",
    },
    "scenario_forecasts": {
        "title": "Scenario forecasts",
        "category": "technical artefact",
        "aliases": ["scenario forecasts", "conservative", "base", "aggressive", "forecast scenarios", "breakeven probability"],
        "description": "Conservative, base, and aggressive 3-month forecasts.",
        "contains": ["monthly revenue", "monthly costs", "net cashflow", "cumulative cashflow", "break-even probability"],
        "why_matters": "It makes uncertainty visible and highlights the assumption that most needs validation.",
        "when_to_use": "Use it before deciding whether the current budget is enough.",
    },
    "cashflow_chart": {
        "title": "Cashflow chart",
        "category": "chart",
        "aliases": ["cashflow chart", "cash flow chart", "revenue chart", "forecast chart", "finance chart"],
        "description": "A planning chart that compares revenue, costs, and cumulative cashflow over the forecast period.",
        "contains": ["revenue", "costs", "net cashflow", "cumulative cashflow", "planning disclaimer"],
        "why_matters": "It turns the Finance Agent assumptions into a visual planning curve.",
        "when_to_use": "Use it to understand how quickly the launch might recover startup costs under the current assumptions.",
    },
    "startup_cost_breakdown": {
        "title": "Startup cost breakdown chart",
        "category": "chart",
        "aliases": ["startup cost chart", "startup cost breakdown", "cost chart", "cost breakdown chart"],
        "description": "A chart showing which launch cost categories make up the estimated startup spend.",
        "contains": ["cost categories", "budget allocation", "upfront spend"],
        "why_matters": "It helps identify which costs should wait until demand is validated.",
        "when_to_use": "Use it before buying tools, stock, samples, or paid promotion.",
    },
    "critic_red_team": {
        "title": "Critic red-team",
        "category": "technical artefact",
        "aliases": ["critic", "critic agent", "red team", "red-team", "risk critic", "risks", "failure modes", "validation tests"],
        "description": "A challenge pass that looks for missing evidence, overconfidence, contradictions, and failure modes.",
        "contains": ["missing evidence", "overconfidence flags", "failure modes", "validation tests", "go/no-go criteria"],
        "why_matters": "It keeps the launch pack honest and prevents premature confidence.",
        "when_to_use": "Use it before spending money or claiming the idea is ready.",
    },
    "roadmap_priority_scores": {
        "title": "Roadmap priority scores",
        "category": "technical artefact",
        "aliases": ["roadmap priority", "priority score", "impact", "effort", "urgency", "risk reduction"],
        "description": "A simple prioritization score for each roadmap task.",
        "contains": ["impact", "effort", "urgency", "dependency", "risk reduction"],
        "why_matters": "It explains why tasks are ordered and which actions reduce risk fastest.",
        "when_to_use": "Use it when choosing the first task or reordering the roadmap.",
    },
    "runtime_modes": {
        "title": "Runtime modes",
        "category": "system",
        "aliases": ["runtime mode", "adk mode", "ai-assisted mode", "deterministic fallback", "fallback mode", "google adk"],
        "description": "LaunchForge can run in deterministic fallback mode or optional AI-assisted ADK mode.",
        "contains": ["ADK availability", "API key availability", "model name", "fallback reason"],
        "why_matters": "The app stays usable without secrets, while still documenting the ADK/LlmAgent path.",
        "when_to_use": "Check it in the Agent Control Room if you want to know whether external LLM reasoning was used.",
    },
    "agents_vs_tools": {
        "title": "Agents vs tools",
        "category": "system",
        "aliases": ["agents vs tools", "difference between agents and tools", "what are agents", "what are tools", "why agents"],
        "description": "Agents are role-specific reasoning units. Tools are deterministic functions that compute structured outputs.",
        "contains": ["agent instructions", "tool access", "execution trace", "MCP-style tool registry"],
        "why_matters": "This separation makes the project inspectable: agents decide and synthesize, tools calculate reliably.",
        "when_to_use": "Use this distinction when explaining the capstone architecture.",
    },
    "dashboard_workflow": {
        "title": "How to use the dashboard",
        "category": "workflow",
        "aliases": ["how do i use this dashboard", "what should i look at first", "where should i start", "how to use", "what should i click"],
        "description": "A practical review order for the LaunchForge pack.",
        "contains": [
            "start with Overview",
            "check Agent Control Room if judging the architecture",
            "review customers and offer",
            "test pricing and finance",
            "use Roadmap for execution",
            "export Markdown or JSON",
        ],
        "why_matters": "The dashboard is dense, so reviewing it in the right order makes the launch plan easier to act on.",
        "when_to_use": "Use this when you are new to LaunchForge or preparing the demo walkthrough.",
    },
}


PLATFORM_KNOWLEDGE.update(
    {
        "pain": {
            "title": "Pain",
            "category": "metric",
            "aliases": ["pain", "pain score", "pain intensity", "customer pain"],
            "description": "Pain measures how strongly the customer feels the problem the launch pack is trying to solve.",
            "contains": ["problem severity", "frustration", "need intensity", "reason to act"],
            "why_matters": "Higher pain usually means the customer is more likely to respond to a focused offer.",
            "when_to_use": "Use it when deciding whether a segment has a problem urgent enough to target first.",
        },
        "reach": {
            "title": "Reach",
            "category": "metric",
            "aliases": ["reach", "reachability", "access", "market to", "find this segment"],
            "description": "Reach measures how easily the founder can find, contact, and market to the segment.",
            "contains": ["channel access", "local access", "online access", "contactability"],
            "why_matters": "A high-pain segment is less useful if the founder cannot reach them cheaply.",
            "when_to_use": "Use it when choosing the first outreach channel or beachhead customer segment.",
        },
        "urgency": {
            "title": "Urgency",
            "category": "metric",
            "aliases": ["urgency", "urgent", "time pressure", "need now"],
            "description": "Urgency measures how soon the customer needs a solution.",
            "contains": ["deadline", "immediacy", "launch timing", "purchase trigger"],
            "why_matters": "Urgent segments are more likely to act during a short launch window.",
            "when_to_use": "Use it when choosing between customers who could buy now versus later.",
        },
        "pay": {
            "title": "Willingness to pay",
            "category": "metric",
            "aliases": ["pay", "willingness to pay", "ability to pay", "price sensitivity"],
            "description": "Pay measures whether the segment is likely and able to pay for the offer at the planned price.",
            "contains": ["budget", "buyer economics", "price acceptance", "margin signal"],
            "why_matters": "A segment may like the offer but still be a weak launch target if payment intent is low.",
            "when_to_use": "Use it when comparing pricing risk across customer segments.",
        },
        "control": {
            "title": "Buyer control",
            "category": "metric",
            "aliases": ["control", "buyer control", "buying authority", "decision control"],
            "description": "Control measures whether the person in the segment can make or strongly influence the buying decision.",
            "contains": ["decision maker", "buying authority", "permission", "purchase control"],
            "why_matters": "Segments with buying control usually convert faster because fewer approvals are needed.",
            "when_to_use": "Use it when deciding whether to target users, buyers, or influencers first.",
        },
        "model_confidence": {
            "title": "Model confidence",
            "category": "metric",
            "aliases": ["confidence", "model confidence", "classification confidence", "94% confident"],
            "description": "Model confidence is LaunchForge's confidence that the classified business type fits the founder brief.",
            "contains": ["matched signals", "classification reasoning", "uncertainty notes"],
            "why_matters": "It tells you how much trust to place in the selected business-type path.",
            "when_to_use": "Use it if the plan appears tailored to the wrong business model.",
        },
        "forecast": {
            "title": "Forecast",
            "category": "metric",
            "aliases": ["forecast", "planning forecast", "cashflow forecast", "scenario model", "scenario forecast"],
            "description": "The forecast is a deterministic planning model of revenue, costs, and cumulative cash over the first months.",
            "contains": ["revenue assumptions", "cost assumptions", "conversion assumptions", "cashflow"],
            "why_matters": "It makes assumptions visible without claiming future results are guaranteed.",
            "when_to_use": "Use it to decide which financial assumption to validate before spending more.",
        },
    }
)


AGENT_KNOWLEDGE: Dict[str, KnowledgeEntry] = {
    "orchestrator_agent": {
        "title": "LaunchForge Orchestrator Agent",
        "category": "agent",
        "aliases": ["orchestrator", "orchestrator agent", "launchforge orchestrator"],
        "description": "Routes the founder input through specialist agents and keeps the launch pack coherent.",
        "contains": ["business context", "routing decisions", "quality checks"],
        "why_matters": "It prevents the pack from becoming disconnected outputs from isolated specialists.",
        "when_to_use": "Inspect it when explaining the end-to-end multi-agent workflow.",
    },
    "business_classifier_agent": {
        "title": "Business Classifier Agent",
        "category": "agent",
        "aliases": ["classifier agent", "business classifier", "classification agent"],
        "description": "Detects the business type, confidence, matched signals, and classification reasoning.",
        "contains": ["business type", "confidence", "matched signals", "uncertainty notes"],
        "why_matters": "Classification drives all downstream tailoring.",
        "when_to_use": "Check it if the pack seems tailored to the wrong model.",
    },
    "market_agent": {
        "title": "Market Strategist Agent",
        "category": "agent",
        "aliases": ["market agent", "market strategist", "customer agent", "persona agent"],
        "description": "Creates personas and scores which segment should be targeted first.",
        "contains": ["personas", "segment scores", "recommended first segment"],
        "why_matters": "It turns a broad idea into a specific first audience.",
        "when_to_use": "Use it before outreach or offer positioning.",
    },
    "offer_agent": {
        "title": "Offer Architect Agent",
        "category": "agent",
        "aliases": ["offer agent", "offer architect", "package agent", "offer ladder agent"],
        "description": "Builds the starter, core, and premium offer ladder and checks offer fit.",
        "contains": ["offer ladder", "deliverables", "success metrics", "offer-fit scores"],
        "why_matters": "It makes the first thing to sell concrete.",
        "when_to_use": "Use it when the offer feels too vague or too hard to deliver.",
    },
    "pricing_agent": {
        "title": "Pricing Analyst Agent",
        "category": "agent",
        "aliases": ["pricing agent", "pricing analyst", "price agent"],
        "description": "Creates pricing tiers and scenario recommendations with rationale and upgrade paths.",
        "contains": ["pricing tiers", "pricing scenarios", "margin assumptions", "sensitivity notes"],
        "why_matters": "It explains why a price exists rather than just listing a number.",
        "when_to_use": "Use it to test whether pricing is too low, too high, or missing a premium option.",
    },
    "marketing_agent": {
        "title": "Growth Marketing Agent",
        "category": "agent",
        "aliases": ["marketing agent", "growth marketing", "funnel agent"],
        "description": "Builds the channel plan, launch messages, and funnel model.",
        "contains": ["channels", "hooks", "social posts", "WhatsApp/email copy", "funnel bottleneck"],
        "why_matters": "It converts positioning into customer acquisition actions.",
        "when_to_use": "Use it when trying to get the first leads or improve conversion.",
    },
    "operations_agent": {
        "title": "Operations Planner Agent",
        "category": "agent",
        "aliases": ["operations agent", "operations planner", "ops agent", "capacity agent"],
        "description": "Creates the delivery workflow, operations checklist, and capacity model.",
        "contains": ["checklist", "capacity model", "bottleneck", "recommended system"],
        "why_matters": "It checks whether the business can actually deliver what it sells.",
        "when_to_use": "Use it before increasing lead flow or accepting more orders.",
    },
    "finance_agent": {
        "title": "Finance Agent / Finance Simulation Agent",
        "category": "agent",
        "aliases": ["finance agent", "finance simulation", "cashflow agent", "forecast agent"],
        "description": "Builds planning forecasts and conservative/base/aggressive cashflow scenarios.",
        "contains": ["startup costs", "revenue assumptions", "cost assumptions", "break-even probability", "key assumption"],
        "why_matters": "It makes the money assumptions visible without pretending they are guaranteed.",
        "when_to_use": "Use it before spending budget or changing prices.",
    },
    "roadmap_agent": {
        "title": "Roadmap Planner Agent",
        "category": "agent",
        "aliases": ["roadmap agent", "roadmap planner", "launch plan agent"],
        "description": "Turns the strategy into 7-day and 30-day execution tasks with priority scores.",
        "contains": ["weekly plan", "day tasks", "priority score", "dependencies"],
        "why_matters": "It gives the founder a realistic order of work.",
        "when_to_use": "Use it when deciding what to do next.",
    },
    "critic_agent": {
        "title": "Risk Critic Agent",
        "category": "agent",
        "aliases": ["critic agent", "risk critic", "red team agent", "red-team agent"],
        "description": "Challenges assumptions, flags missing evidence, and explains readiness gaps.",
        "contains": ["failure modes", "validation tests", "readiness cap", "go/no-go criteria"],
        "why_matters": "It lowers overconfidence and focuses validation work.",
        "when_to_use": "Use it before claiming the idea is ready or spending significant cash.",
    },
    "visual_agent": {
        "title": "Visual Packaging Agent",
        "category": "agent",
        "aliases": ["visual agent", "visual packaging", "dashboard agent", "packaging agent"],
        "description": "Packages outputs for the dashboard and exports.",
        "contains": ["dashboard artefacts", "charts", "export-ready pack"],
        "why_matters": "It turns structured data into a readable product experience.",
        "when_to_use": "Use it when checking whether the pack is submission-ready.",
    },
    "copilot_agent": {
        "title": "LaunchForge Copilot Agent",
        "category": "agent",
        "aliases": ["copilot agent", "launchforge copilot", "assistant agent"],
        "description": "Answers grounded questions about the platform and the current launch pack.",
        "contains": ["platform knowledge retrieval", "launch-pack context", "safety checks", "fallback answers"],
        "why_matters": "It acts as a guide, dictionary, and launch-pack interpreter.",
        "when_to_use": "Use it whenever a dashboard element, agent, metric, or next step is unclear.",
    },
}


DETERMINISTIC_TOOL_KNOWLEDGE: Dict[str, KnowledgeEntry] = {
    "classify_business_model": {
        "title": "classify_business_model",
        "category": "tool",
        "aliases": ["classify_business_model", "classification tool"],
        "description": "Classifies the idea and returns evidence signals.",
        "contains": ["business type", "confidence", "signals"],
        "why_matters": "It gives the agent system a reliable starting point.",
        "when_to_use": "Used by the Business Classifier Agent.",
    },
    "score_customer_segments": {
        "title": "score_customer_segments",
        "category": "tool",
        "aliases": ["score_customer_segments", "segment scoring tool"],
        "description": "Scores personas by pain, reachability, urgency, willingness to pay, and buyer control.",
        "contains": ["segment scores", "recommended first segment"],
        "why_matters": "It makes target-customer choice inspectable.",
        "when_to_use": "Used by the Market Strategist Agent.",
    },
    "score_offer_fit": {
        "title": "score_offer_fit",
        "category": "tool",
        "aliases": ["score_offer_fit", "offer fit tool"],
        "description": "Scores the fit of each offer package.",
        "contains": ["pain match", "feasibility", "differentiation", "revenue potential"],
        "why_matters": "It helps identify the strongest first package.",
        "when_to_use": "Used by the Offer Architect Agent.",
    },
    "build_pricing_scenarios": {
        "title": "build_pricing_scenarios",
        "category": "tool",
        "aliases": ["build_pricing_scenarios", "pricing scenario tool"],
        "description": "Creates low, base, and premium pricing options.",
        "contains": ["recommended price", "conversion rate", "margin", "sensitivity note"],
        "why_matters": "It shows pricing tradeoffs and upgrade paths.",
        "when_to_use": "Used by the Pricing Analyst Agent.",
    },
    "build_funnel_model": {
        "title": "build_funnel_model",
        "category": "tool",
        "aliases": ["build_funnel_model", "funnel model tool"],
        "description": "Models funnel stages, conversion rates, and bottlenecks.",
        "contains": ["stage volumes", "conversion rates", "bottleneck"],
        "why_matters": "It tells the founder where acquisition may leak.",
        "when_to_use": "Used by the Growth Marketing Agent.",
    },
    "build_capacity_model": {
        "title": "build_capacity_model",
        "category": "tool",
        "aliases": ["build_capacity_model", "capacity model tool"],
        "description": "Models founder hours, delivery capacity, and operational bottlenecks.",
        "contains": ["admin hours", "delivery hours", "maximum customers/orders", "scaling constraint"],
        "why_matters": "It checks whether demand can be served.",
        "when_to_use": "Used by the Operations Planner Agent.",
    },
    "simulate_cashflow_scenarios": {
        "title": "simulate_cashflow_scenarios",
        "category": "tool",
        "aliases": ["simulate_cashflow_scenarios", "cashflow scenario tool"],
        "description": "Runs conservative, base, and aggressive cashflow scenarios.",
        "contains": ["monthly revenue", "monthly costs", "break-even probability", "worst-case gap"],
        "why_matters": "It makes financial uncertainty visible.",
        "when_to_use": "Used by the Finance Agent / Finance Simulation Agent.",
    },
    "prioritize_launch_tasks": {
        "title": "prioritize_launch_tasks",
        "category": "tool",
        "aliases": ["prioritize_launch_tasks", "roadmap priority tool"],
        "description": "Scores roadmap tasks by impact, effort, urgency, and risk reduction.",
        "contains": ["priority score", "dependency", "rationale"],
        "why_matters": "It explains the order of the roadmap.",
        "when_to_use": "Used by the Roadmap Planner Agent.",
    },
    "run_red_team_checks": {
        "title": "run_red_team_checks",
        "category": "tool",
        "aliases": ["run_red_team_checks", "red team tool", "critic tool"],
        "description": "Finds missing evidence, overconfidence flags, and failure modes.",
        "contains": ["validation tests", "assumptions to verify", "go/no-go criteria"],
        "why_matters": "It protects against overconfident launch plans.",
        "when_to_use": "Used by the Risk Critic Agent.",
    },
    "explain_readiness_score": {
        "title": "explain_readiness_score",
        "category": "tool",
        "aliases": ["explain_readiness_score", "readiness explanation tool"],
        "description": "Explains the readiness score from strengths, gaps, and validation evidence.",
        "contains": ["score", "strengths", "gaps"],
        "why_matters": "It gives Copilot a grounded answer for readiness questions.",
        "when_to_use": "Used by the Copilot Agent.",
    },
    "improve_marketing_message": {
        "title": "improve_marketing_message",
        "category": "tool",
        "aliases": ["improve_marketing_message", "message improvement tool"],
        "description": "Improves launch copy while staying grounded in the business type.",
        "contains": ["original message", "improved message"],
        "why_matters": "It turns the marketing pack into reusable outreach copy.",
        "when_to_use": "Used by the Copilot Agent.",
    },
    "suggest_next_action": {
        "title": "suggest_next_action",
        "category": "tool",
        "aliases": ["suggest_next_action", "next action tool"],
        "description": "Selects the highest-priority next action from the pack.",
        "contains": ["next action", "action rationale"],
        "why_matters": "It helps the founder move from analysis to execution.",
        "when_to_use": "Used by the Copilot Agent.",
    },
    "package_dashboard_outputs": {
        "title": "package_dashboard_outputs",
        "category": "tool",
        "aliases": ["package_dashboard_outputs", "dashboard packaging tool"],
        "description": "Creates a compact inventory of dashboard artefacts.",
        "contains": ["artefact availability", "dashboard summary"],
        "why_matters": "It helps the UI and export show what was produced.",
        "when_to_use": "Used by the Visual Packaging Agent.",
    },
    "export_launch_pack": {
        "title": "export_launch_pack",
        "category": "tool",
        "aliases": ["export_launch_pack", "export tool"],
        "description": "Exports the launch pack as Markdown or JSON.",
        "contains": ["Markdown", "JSON", "agent trace", "technical artefacts"],
        "why_matters": "It makes the pack portable without automatic persistence.",
        "when_to_use": "Used by the Visual Packaging Agent.",
    },
}


def all_knowledge_entries() -> Dict[str, KnowledgeEntry]:
    """Return every searchable platform, agent, and tool entry."""

    return {**PLATFORM_KNOWLEDGE, **AGENT_KNOWLEDGE, **DETERMINISTIC_TOOL_KNOWLEDGE}


def get_platform_knowledge() -> Dict[str, KnowledgeEntry]:
    """Return the internal product dictionary used by LaunchForge Copilot."""

    return all_knowledge_entries()


def _plain_pack(pack: Any) -> Dict[str, Any]:
    if pack is None:
        return {}
    if hasattr(pack, "model_dump") or hasattr(pack, "dict"):
        return model_to_dict(pack)
    return dict(pack)


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("&", " and ")).strip()


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", _normalise(text)) if len(token) > 2}


def _entry_text(entry: KnowledgeEntry) -> str:
    parts: List[str] = [
        str(entry.get("title", "")),
        str(entry.get("category", "")),
        str(entry.get("description", "")),
        str(entry.get("why_matters", "")),
        str(entry.get("when_to_use", "")),
    ]
    parts.extend(str(alias) for alias in entry.get("aliases", []))
    parts.extend(str(item) for item in entry.get("contains", []))
    return " ".join(parts)


def _score_entry(question: str, question_tokens: set[str], entry: KnowledgeEntry) -> int:
    score = 0
    entry_tokens = _tokens(_entry_text(entry))
    score += len(question_tokens & entry_tokens)
    for alias in entry.get("aliases", []):
        alias_norm = _normalise(str(alias))
        if alias_norm and alias_norm in question:
            score += 8 + len(alias_norm.split())
    title_norm = _normalise(str(entry.get("title", "")))
    if title_norm and title_norm in question:
        score += 10
    return score


def search_platform_knowledge(query: str, limit: int = 5) -> List[KnowledgeEntry]:
    """Search the internal platform knowledge base with deterministic scoring."""

    query_norm = _normalise(query)
    query_tokens = _tokens(query_norm)
    scored: List[Dict[str, Any]] = []
    for key, entry in all_knowledge_entries().items():
        score = _score_entry(query_norm, query_tokens, entry)
        if score >= 2:
            scored.append({"key": key, "score": score, **entry})
    scored.sort(key=lambda row: row["score"], reverse=True)
    return scored[:limit]


def explain_metric(metric_name: str) -> Dict[str, Any]:
    """Return the best metric definition for a LaunchForge dashboard term."""

    query = _normalise(metric_name)
    for key, entry in all_knowledge_entries().items():
        if entry.get("category") != "metric":
            continue
        aliases = [_normalise(str(alias)) for alias in entry.get("aliases", [])]
        if query == key or query == _normalise(str(entry.get("title", ""))) or query in aliases:
            return {"key": key, **entry}
    matches = [entry for entry in search_platform_knowledge(metric_name, limit=3) if entry.get("category") == "metric"]
    return matches[0] if matches else {}


def _business_type_label(value: str | None) -> str:
    if not value:
        return "Unknown"
    return value.replace("_", " ").title()


def _money(symbol: str, value: float) -> str:
    return f"{symbol}{value:,.0f}"


def _weakest_funnel_stage(stages: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    stage_list = list(stages or [])
    bottlenecks = [stage for stage in stage_list if stage.get("bottleneck")]
    return bottlenecks[0] if bottlenecks else (stage_list[-1] if stage_list else {})


def launch_pack_summary(launch_pack: Any) -> Dict[str, Any]:
    """Extract current launch-pack facts for grounded Copilot answers."""

    data = _plain_pack(launch_pack)
    classification = data.get("classification", {}) or {}
    startup_costs = data.get("startup_costs", {}) or {}
    scenario = data.get("scenario_forecasts", {}) or {}
    capacity = data.get("capacity_model", {}) or {}
    critic = data.get("critic_red_team", {}) or {}
    priority_rows = data.get("roadmap_priority_scores", []) or []
    segment_rows = data.get("segment_scores", []) or []
    funnel_stage = _weakest_funnel_stage(data.get("funnel_model", []) or [])
    symbol = data.get("currency_symbol") or ""
    total_startup_cost = float(sum(float(value or 0) for value in startup_costs.values()))
    recommended_segment = next((row for row in segment_rows if row.get("recommended_first_segment")), segment_rows[0] if segment_rows else {})

    return {
        "business_type": classification.get("business_type", "unknown"),
        "business_type_label": _business_type_label(classification.get("business_type", "unknown")),
        "classification_confidence": classification.get("confidence"),
        "matched_signals": classification.get("matched_signals", [])[:5],
        "readiness_score": data.get("readiness_score"),
        "readiness_label": data.get("launch_readiness_label"),
        "readiness_strengths": data.get("readiness_strengths", [])[:4],
        "readiness_gaps": data.get("readiness_gaps", [])[:5],
        "currency_code": data.get("currency_code"),
        "currency_symbol": symbol,
        "startup_cost": total_startup_cost,
        "startup_cost_display": _money(symbol, total_startup_cost) if total_startup_cost else "not available",
        "breakeven_month": data.get("breakeven_month"),
        "next_action": (data.get("next_3_actions", []) or ["Review the Overview tab first."])[0],
        "weakest_funnel_stage": funnel_stage.get("stage_name", "not available"),
        "weakest_funnel_recommendation": funnel_stage.get("improvement_recommendation", ""),
        "capacity_bottleneck": capacity.get("bottleneck", "not available"),
        "capacity_system": capacity.get("recommended_system", ""),
        "breakeven_probability": scenario.get("breakeven_probability"),
        "worst_case_gap": scenario.get("worst_case_gap"),
        "upside_case": scenario.get("upside_case"),
        "key_assumption_to_validate": scenario.get("key_assumption_to_validate"),
        "critic_missing_evidence": critic.get("missing_evidence", [])[:4],
        "critic_validation_tests": critic.get("validation_tests", [])[:4],
        "top_failure_modes": critic.get("top_3_failure_modes", [])[:3],
        "top_roadmap_priority": priority_rows[0] if priority_rows else {},
        "agent_count": len(data.get("agent_registry", []) or []),
        "tool_count": len(data.get("tool_registry", []) or []),
        "runtime_mode": (data.get("runtime_status", {}) or {}).get("mode"),
    }


PLATFORM_RELATED_TOKENS = {
    "launchforge",
    "dashboard",
    "tab",
    "metric",
    "score",
    "readiness",
    "launch",
    "business",
    "agent",
    "tool",
    "workflow",
    "pack",
    "export",
    "price",
    "pricing",
    "finance",
    "cashflow",
    "funnel",
    "roadmap",
    "risk",
    "critic",
    "customer",
    "offer",
    "operation",
    "capacity",
    "scenario",
    "validate",
    "spending",
    "budget",
    "first",
    "next",
    "use",
    "click",
    "explain",
}


def retrieve_platform_context(question: str, launch_pack: Any) -> Dict[str, Any]:
    """Retrieve relevant platform dictionary and launch-pack context.

    This is semantic-lite retrieval: exact aliases get strong weight, and token
    overlap catches related phrasing without needing embeddings.
    """

    question_norm = _normalise(question)
    question_tokens = _tokens(question_norm)
    top_matches = search_platform_knowledge(question, limit=5)
    related = bool(top_matches) or bool(question_tokens & PLATFORM_RELATED_TOKENS)

    return {
        "question": question,
        "matches": top_matches,
        "primary_match": top_matches[0] if top_matches else None,
        "launch_pack": launch_pack_summary(launch_pack),
        "is_platform_related": related,
        "topics": [row["key"] for row in top_matches],
    }

