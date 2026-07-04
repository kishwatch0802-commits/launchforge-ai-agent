"""Visual pack agent."""

from __future__ import annotations

from typing import Any, Dict

from launchforge.agents.base import LaunchForgeAgent
from launchforge.visuals import business_model_canvas_data, mermaid_agent_architecture, mermaid_sales_funnel


class VisualPackAgent(LaunchForgeAgent):
    name = "VisualPackAgent"
    role = "Produces diagram strings and dashboard-ready visual data."

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        canvas = business_model_canvas_data(context)
        diagrams = {
            "agent_architecture": mermaid_agent_architecture(),
            "sales_funnel": mermaid_sales_funnel(context["sales_funnel"]),
        }
        return {"business_model_canvas": canvas, "diagrams": diagrams}
