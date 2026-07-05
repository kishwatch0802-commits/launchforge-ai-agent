# LaunchForge Agents

LaunchForge now separates real ADK/LlmAgent-style agent definitions from deterministic tools.

- LLM agent definitions live in `launchforge/agent_registry.py`.
- Optional ADK and Gemini runtime detection lives in `launchforge/adk_runtime.py`.
- The interactive Copilot uses `google-genai` for a real Gemini call when `GOOGLE_API_KEY` is configured, and labels the answer AI-assisted only after that call succeeds.
- Deterministic tools live in `launchforge/mcp_server/tools.py`.
- Fallback workflow classes still exist for reliable no-key execution, but they are presented as deterministic fallback/tool orchestration rather than the only agent implementation.
- The Streamlit Agent Control Room shows runtime status, LLM agent definitions, tool mapping, execution trace, and Copilot.

## Registered LLM Agent Team

1. `LaunchForge_Orchestrator_Agent`
2. `Business_Classifier_Agent`
3. `Market_Strategist_Agent`
4. `Offer_Architect_Agent`
5. `Pricing_Analyst_Agent`
6. `Growth_Marketing_Agent`
7. `Operations_Planner_Agent`
8. `Finance_Simulation_Agent`
9. `Roadmap_Planner_Agent`
10. `Risk_Critic_Agent`
11. `Visual_Packaging_Agent`
12. `LaunchForge_Copilot_Agent`

## ADK Mapping

`adk_runtime.py` attempts to import Google ADK's `LlmAgent`, `Runner`, and `InMemorySessionService`, plus `google-genai` for the direct Gemini Copilot path. If Gemini, ADK, or `GOOGLE_API_KEY` is unavailable, LaunchForge reports deterministic fallback mode and continues using reliable tools. Tests never require external API calls.

## Privacy

Agents operate in memory. They do not persist user inputs. Export text is generated only when requested by the user in the UI.
