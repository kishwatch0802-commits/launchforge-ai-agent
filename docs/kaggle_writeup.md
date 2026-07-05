# LaunchForge: Adaptive Multi-Agent Small Business Launch Studio

**Subtitle:** Turning rough small-business ideas into tailored launch packs with ADK/LlmAgent-style agents, MCP tools, skills, privacy controls, and a deployable Streamlit dashboard.

## Problem

Many first-time founders have a business idea but do not know what to do next. A tutoring business, a corner shop, and a Shopify store need very different launch plans. Generic advice like "know your customer" or "market on social media" is not enough when a founder has 24 hours to build and demonstrate something useful.

## Solution

LaunchForge is a Streamlit app that transforms a rough small-business idea into a visual, practical launch pack. The user enters the idea, budget, location, launch timeframe, stage, resources, and optional target customer. The app classifies the business model and generates a tailored dashboard containing KPI cards, Agent Control Room, execution trace, classification evidence chips, Business Model Canvas, customer personas, offer ladder, pricing scenarios, sales funnel model, 30-day roadmap, capacity model, cashflow scenarios, forecast assumptions, operations checklist, marketing copy, risks, assumptions, and final next actions.

The app supports multiple business categories, with the strongest MVP tailoring for local service, physical retail, and ecommerce businesses.

## Why Agents?

Launch planning is not one task. It combines customer selection, offer packaging, pricing, operations, finance, marketing, roadmap planning, and critical review. A single generic assistant tends to flatten those decisions into advice. LaunchForge separates the work into specialist agents, gives them reliable tools, and records what each agent produced.

The registered LLM agent team includes an Orchestrator, Business Classifier, Market Strategist, Offer Architect, Pricing Analyst, Growth Marketing, Operations Planner, Finance Simulation, Roadmap Planner, Risk Critic, Visual Packaging, and LaunchForge Copilot Agent. The deterministic Python classes from the MVP still exist, but they are presented as fallback orchestration and reliable tool execution, not as the only agent implementation.

## Architecture

LaunchForge is built as a three-layer system:

1. Deterministic MCP-style tools compute reliable structured outputs such as classification, segment scores, offer-fit scores, pricing scenarios, funnel conversion rates, capacity models, cashflow simulations, roadmap priorities, critic checks, Copilot helper answers, and exports.
2. ADK/LlmAgent-style agent definitions live in `agent_registry.py` and can be constructed through `adk_runtime.py` when Google ADK and `GOOGLE_API_KEY` are configured. The runtime also detects `google-genai`; Copilot uses it for the real Gemini call when available and reports whether it is in `ai-assisted`, `fallback after ai error`, or `deterministic-fallback` mode.
3. The Streamlit dashboard visualizes the launch pack, technical artefacts, Agent Control Room, Copilot, and exports.

This keeps the capstone honest: deterministic tools do the repeatable calculations, while the ADK/LlmAgent layer is the reasoning and synthesis boundary when configured. Tests never require external API calls.

## Implementation

The repository is written in Python 3.11+ with Streamlit, Pydantic, Pandas, Plotly, and Pytest. Pydantic schemas define the input, classification, personas, offers, pricing, cashflow rows, tasks, technical artefacts, execution trace, and final `LaunchPack`.

The UI is organized into dashboard tabs: Overview, Agent Control Room, Customers & Offer, Pricing & Finance, Marketing & Operations, Roadmap, and Export. It includes demo buttons for tutoring, corner shop, and Shopify scenarios. The Agent Control Room shows runtime status, LLM agent definitions, tool mapping, execution trace, and Copilot.

## MCP and Agent Skills

The MCP tool layer includes functions for classification, segment scoring, offer-fit scoring, pricing scenarios, funnel modelling, capacity modelling, cashflow scenario simulation, roadmap prioritisation, red-team checks, readiness explanation, marketing improvement, next action selection, dashboard packaging, and export. `server.py` exposes these through FastMCP when available and falls back to a local registry when not.

Reusable Python skills wrap launch pack assembly, cashflow, funnel, and export logic. The `.agents/skills` directory also documents agent skills for launch-pack validation, pricing scenario analysis, growth funnel design, finance simulation review, red-team critique, and outreach drafting.

## Security and Privacy

LaunchForge does not require or expose API keys. `.env.example` contains placeholders only, and optional `GOOGLE_API_KEY` is read only from the environment. Inputs are sanitized and length-capped. Copilot checks for prompt-injection phrases, refuses requests to reveal hidden prompts or chain-of-thought, redacts email, phone, and API-key-like strings, and falls back safely if Gemini errors. A privacy toggle states that ideas are not stored, and the app does not write user inputs to disk unless the user explicitly downloads an export. Generated finance numbers include a disclaimer because they are planning assumptions, not financial advice.

## Example Outputs

For a tutoring business, LaunchForge prioritizes GCSE/A-Level/ESAT diagnostic sessions, local referrals, testimonials, booking workflow, parent/student progress updates, and WhatsApp/email outreach. The readiness score is deliberately capped below launch-ready levels when there is no validation or proof. For a corner shop, it prioritizes footfall, fast-moving stock, opening hours, suppliers, store layout, opening-week bundles, and daily cash-up. For Shopify, it prioritizes hero product validation, supplier samples, product-page copy, bundles, content hooks, fulfilment, AOV, gross margin, and conversion metrics.

## Limitations

The public demo uses deterministic fallback outputs unless Google ADK and an API key are configured. It does not perform live market research, legal checks, supplier verification, or accounting advice. The forecasts are intentionally simple and should be reviewed by a human before real spending decisions.

## Future Work

Future versions could add deeper Gemini-powered synthesis, browser research tools, richer business categories, export to Trello/Notion, and encrypted user-owned history.

## Conclusion

LaunchForge demonstrates how agentic architecture can make small-business launch planning more adaptive and actionable. It combines ADK/LlmAgent-style agents, deterministic MCP tools, reusable skills, Copilot, execution traces, privacy choices, and deployability into a polished capstone-ready MVP.
