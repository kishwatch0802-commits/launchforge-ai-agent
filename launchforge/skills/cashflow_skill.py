"""Cashflow forecasting skill used by the FinanceAgent."""

from __future__ import annotations

from typing import Any, Dict

from launchforge.mcp_server.tools import build_cashflow_forecast


def run_cashflow_skill(startup_costs: Dict[str, float], monthly_revenue: float, monthly_costs: float, months: int = 3) -> Dict[str, Any]:
    """Build a simple deterministic cashflow forecast and break-even estimate."""

    return build_cashflow_forecast(startup_costs, monthly_revenue, monthly_costs, months)
