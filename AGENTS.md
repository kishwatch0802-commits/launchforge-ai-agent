# LaunchForge Agents

LaunchForge uses an ADK-style sequential multi-agent architecture. Each agent is a Python class with `name`, `role`, and `run(input_context)` and returns a partial context update.

## Agent Flow

1. `BusinessClassifierAgent`: classifies the idea into a business model and lists assumptions.
2. `MarketAgent`: creates tailored personas and customer segments.
3. `OfferAgent`: builds a staged offer ladder.
4. `PricingAgent`: calls the MCP pricing tool for tiers.
5. `MarketingAgent`: calls the funnel skill and creates launch copy.
6. `OperationsAgent`: creates delivery, supplier, and daily operating checklists.
7. `FinanceAgent`: calls the cashflow skill for the 3-month forecast.
8. `RoadmapAgent`: calls the MCP task tool for the launch roadmap.
9. `CriticAgent`: reviews risk, assumptions, contradictions, and readiness.
10. `VisualPackAgent`: creates dashboard data and Mermaid diagrams.

## ADK Mapping

`agent_runtime.py` mirrors the ADK concepts of agent definitions, a runner, a session context, and events. The fallback runtime is intentionally small so the project remains runnable during a timed capstone.

## Privacy

Agents operate in memory. They do not persist user inputs. Export text is generated only when requested by the user in the UI.
