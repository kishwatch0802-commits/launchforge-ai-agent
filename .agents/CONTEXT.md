# LaunchForge Agent Context

LaunchForge separates LLM-style agents from deterministic tools.

- ADK/LlmAgent definitions live in `launchforge/agent_registry.py` and can be constructed through `launchforge/adk_runtime.py` when Google ADK and `GOOGLE_API_KEY` are configured.
- Deterministic MCP-style tools live in `launchforge/mcp_server/tools.py`.
- The Streamlit Agent Control Room shows runtime status, agent definitions, tool mapping, execution trace, and Copilot fallback mode.
- Public demos must work without API keys and without external calls.
