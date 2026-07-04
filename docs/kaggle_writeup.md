# LaunchForge: Adaptive Multi-Agent Small Business Launch Studio

**Subtitle:** Turning rough small-business ideas into tailored launch packs with agents, MCP tools, skills, privacy controls, and deployable Streamlit UI.

## Problem

Many first-time founders have a business idea but do not know what to do next. A tutoring business, a corner shop, and a Shopify store need very different launch plans. Generic advice like "know your customer" or "market on social media" is not enough when a founder has 24 hours to build and demonstrate something useful.

## Solution

LaunchForge is a Streamlit app that transforms a rough small-business idea into a visual, practical launch pack. The user enters the idea, budget, location, launch timeframe, stage, resources, and optional target customer. The app classifies the business model and generates a tailored dashboard containing a Business Model Canvas, customer personas, offer ladder, pricing table, sales funnel, 30-day roadmap, cashflow forecast, operations checklist, marketing copy, risks, assumptions, and final next actions.

The app supports multiple business categories, with the strongest MVP tailoring for local service, physical retail, and ecommerce businesses.

## Why Agents?

Launch planning is not one task. It combines market segmentation, product packaging, pricing, operations, finance, marketing, and critical review. LaunchForge uses a multi-agent workflow so each specialist has a clear role:

- BusinessClassifierAgent identifies the business model.
- MarketAgent creates target personas.
- OfferAgent designs packages and value proposition.
- PricingAgent creates pricing tiers.
- MarketingAgent creates channels, funnel, and launch copy.
- OperationsAgent creates fulfilment and daily checklists.
- FinanceAgent creates startup costs and a 3-month forecast.
- RoadmapAgent creates the launch plan.
- CriticAgent scores readiness and flags risks.
- VisualPackAgent prepares diagrams and dashboard data.

This architecture makes the output easier to inspect, test, and extend than one monolithic prompt.

## Architecture

The project uses an ADK-style compatibility layer in `agent_runtime.py`: agents expose `name`, `role`, and `run(context)`, and a sequential runner merges outputs into a shared session context. If Google ADK is installed later, the same conceptual boundaries can be wrapped with ADK primitives. The deterministic fallback is intentional: the capstone demo must run without API keys or network dependency.

## Implementation

The repository is written in Python 3.11+ with Streamlit, Pydantic, Pandas, Plotly, and Pytest. Pydantic schemas define the input, classification, personas, offers, pricing, cashflow rows, tasks, and final `LaunchPack`.

The UI is organized into six tabs: Overview, Customers & Offer, Pricing & Finance, Marketing & Operations, Roadmap, and Export. It includes demo buttons for tutoring, corner shop, and Shopify scenarios.

## MCP and Agent Skills

The MCP tool layer includes functions for classification, cashflow forecasting, sales funnel generation, launch task creation, pricing table creation, and export. `server.py` exposes these through FastMCP when available and falls back to a local registry when not.

Reusable skills wrap launch pack assembly, cashflow, funnel, and export logic. Agents call these skills, demonstrating how capabilities can be reused outside the main UI.

## Security and Privacy

LaunchForge does not require or expose API keys. `.env.example` contains placeholders only. Inputs are sanitized and length-capped. A privacy toggle states that ideas are not stored, and the app does not write user inputs to disk unless the user explicitly downloads an export. Generated finance numbers include a disclaimer because they are planning assumptions, not financial advice.

## Example Outputs

For a tutoring business, LaunchForge prioritizes diagnostic sessions, local referrals, testimonials, booking workflow, and WhatsApp/email outreach. For a corner shop, it prioritizes footfall, fast-moving stock, opening hours, suppliers, store layout, and daily cash-up. For Shopify, it prioritizes hero product validation, supplier samples, product-page copy, bundles, content hooks, fulfilment, and conversion metrics.

## Limitations

The MVP uses deterministic templates and keyword classification. It does not perform live market research, legal checks, supplier verification, or accounting advice. The forecasts are intentionally simple and should be reviewed by a human before real spending decisions.

## Future Work

Future versions could add Gemini-powered reasoning, browser research tools, richer business categories, export to Trello/Notion, and encrypted user-owned history.

## Conclusion

LaunchForge demonstrates how agentic architecture can make small-business launch planning more adaptive and actionable. It combines multi-agent orchestration, MCP-style tools, reusable skills, privacy choices, and deployability into a polished capstone-ready MVP.
