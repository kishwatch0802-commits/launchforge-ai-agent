"""MCP server entry point.

Run with `python -m launchforge.mcp_server.server`. If the official MCP package
is installed, tools are exposed through FastMCP. Otherwise a lightweight local
registry is provided so development and tests still exercise the tool layer.
"""

from __future__ import annotations

from typing import Callable, Dict

from . import tools


try:  # pragma: no cover - optional runtime path.
    from mcp.server.fastmcp import FastMCP  # type: ignore
except Exception:  # noqa: BLE001
    FastMCP = None


class LocalMCPServer:
    """Small MCP-compatible fallback registry for local/demo usage."""

    def __init__(self, name: str):
        self.name = name
        self.registry: Dict[str, Callable] = {}

    def tool(self, fn: Callable | None = None):
        def decorator(func: Callable) -> Callable:
            self.registry[func.__name__] = func
            return func

        return decorator(fn) if fn else decorator

    def run(self) -> None:
        print(f"{self.name} fallback MCP registry loaded: {', '.join(self.registry)}")


def create_server():
    server = FastMCP("LaunchForge MCP") if FastMCP else LocalMCPServer("LaunchForge MCP")
    server.tool()(tools.classify_business_model)
    server.tool()(tools.score_customer_segments)
    server.tool()(tools.score_offer_fit)
    server.tool()(tools.build_pricing_scenarios)
    server.tool()(tools.build_funnel_model)
    server.tool()(tools.build_capacity_model)
    server.tool()(tools.simulate_cashflow_scenarios)
    server.tool()(tools.prioritize_launch_tasks)
    server.tool()(tools.run_red_team_checks)
    server.tool()(tools.explain_readiness_score)
    server.tool()(tools.improve_marketing_message)
    server.tool()(tools.suggest_next_action)
    server.tool()(tools.package_dashboard_outputs)
    server.tool()(tools.build_cashflow_forecast)
    server.tool()(tools.generate_sales_funnel)
    server.tool()(tools.create_launch_tasks)
    server.tool()(tools.create_pricing_table)
    server.tool()(tools.export_launch_pack)
    return server


if __name__ == "__main__":
    create_server().run()
