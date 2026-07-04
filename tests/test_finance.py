from launchforge.mcp_server.tools import build_cashflow_forecast
from launchforge.schemas import BusinessInput
from launchforge.workflow import run_launchforge_workflow


def test_cashflow_forecast_shape():
    forecast = build_cashflow_forecast({"stock": 500, "ads": 100}, monthly_revenue=700, monthly_costs=150, months=3)
    assert forecast["startup_total"] == 600
    assert len(forecast["months"]) == 3
    assert {"month", "revenue", "costs", "net_cashflow", "cumulative_cashflow"} <= set(forecast["months"][0])


def test_finance_agent_creates_cashflow():
    pack = run_launchforge_workflow(
        BusinessInput(
            idea="I want to launch a Shopify store selling affordable gym accessories.",
            budget=2500,
            location="Online",
        )
    )
    assert len(pack.cashflow) == 3
    assert sum(pack.startup_costs.values()) > 0
    assert pack.breakeven_month
