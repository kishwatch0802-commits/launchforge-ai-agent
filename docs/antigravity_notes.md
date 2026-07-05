# Antigravity Notes

Use Antigravity in the capstone video/writeup as the development environment for inspecting and improving the agent workflow.

Suggested video beats:

1. Open the repository in Antigravity.
2. Inspect `launchforge/agent_registry.py` and `launchforge/adk_runtime.py` to show the ADK/LlmAgent-style agent layer.
3. Inspect `launchforge/workflow.py` to show how deterministic fallback orchestration produces the same launch-pack artefacts without secrets.
4. Jump into `launchforge/mcp_server/tools.py` to show MCP-style tools for scoring, scenarios, funnel, capacity, critique, and export.
5. Open `.agents/skills/` to show the reusable agent skill policies.
6. Run `pytest` inside the terminal.
7. Run `streamlit run app.py`.
8. Generate the three demo launch packs and open the Agent Control Room.

Narration:

"I used Antigravity as the agentic development environment to inspect the repository, refactor the agent workflow, run tests, and verify the Streamlit demo. It made the multi-agent structure easier to navigate because each agent, MCP tool, and skill is separated into a clear file."
