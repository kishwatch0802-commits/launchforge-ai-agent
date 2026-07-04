"""Visual data and chart helpers for LaunchForge."""

from __future__ import annotations

from typing import Any, Dict, List

from launchforge.config import as_money
from launchforge.schemas import CashflowMonth, model_to_dict


def mermaid_agent_architecture() -> str:
    return """flowchart LR
    UI[Streamlit UI] --> Runtime[ADK-style Sequential Runner]
    Runtime --> C[Classifier Agent]
    C --> M[Market Agent]
    M --> O[Offer Agent]
    O --> P[Pricing Agent]
    P --> MK[Marketing Agent]
    MK --> OPS[Operations Agent]
    OPS --> F[Finance Agent]
    F --> R[Roadmap Agent]
    R --> CR[Critic Agent]
    CR --> V[Visual Pack Agent]
    V --> Pack[Launch Pack Export]
    MK -. uses .-> MCP[MCP Tool Layer]
    F -. uses .-> MCP
    P -. uses .-> MCP
"""


def mermaid_sales_funnel(funnel: Dict[str, Any]) -> str:
    stages = funnel.get("stages", [])
    if not stages:
        return "flowchart TD\n    A[Awareness] --> B[Conversion]"
    lines = ["flowchart TD"]
    safe_ids = []
    for index, stage in enumerate(stages):
        node_id = f"S{index + 1}"
        safe_ids.append(node_id)
        lines.append(f'    {node_id}["{stage}"]')
    for left, right in zip(safe_ids, safe_ids[1:]):
        lines.append(f"    {left} --> {right}")
    return "\n".join(lines)


def cashflow_chart(cashflow: List[CashflowMonth]):
    """Return a Plotly figure when installed; otherwise a Matplotlib figure."""

    rows = [model_to_dict(item) for item in cashflow]
    try:
        import pandas as pd
        import plotly.express as px

        df = pd.DataFrame(rows)
        long_df = df.melt(id_vars="month", value_vars=["revenue", "costs", "cumulative_cashflow"], var_name="metric", value_name="amount")
        fig = px.line(long_df, x="month", y="amount", color="metric", markers=True, title="3-Month Cashflow Forecast")
        fig.update_layout(legend_title_text="", margin=dict(l=20, r=20, t=50, b=20))
        return fig
    except Exception:  # noqa: BLE001
        import matplotlib.pyplot as plt

        months = [row["month"] for row in rows]
        fig, ax = plt.subplots()
        ax.plot(months, [row["revenue"] for row in rows], label="Revenue")
        ax.plot(months, [row["costs"] for row in rows], label="Costs")
        ax.plot(months, [row["cumulative_cashflow"] for row in rows], label="Cumulative")
        ax.set_title("3-Month Cashflow Forecast")
        ax.legend()
        return fig


def readiness_score_breakdown(breakdown: Dict[str, int]) -> List[Dict[str, Any]]:
    return [{"area": key, "points": value} for key, value in breakdown.items()]


def business_model_canvas_data(context: Dict[str, Any]) -> Dict[str, List[str]]:
    business_type = context["business_type"]
    personas = context.get("personas", [])
    pricing = context.get("pricing", [])
    channels = context.get("launch_channels", [])
    startup_costs = context.get("startup_costs", {})
    persona_segments = [p.segment for p in personas]
    price_units = [f"{p.tier}: {as_money(p.price) if p.price >= 100 else '$' + str(p.price)} / {p.unit}" for p in pricing]
    if business_type == "local_service":
        key_activities = ["Deliver repeatable sessions", "Collect testimonials", "Run local outreach"]
        key_resources = ["Founder expertise", "Booking calendar", "Diagnostic checklist"]
    elif business_type == "physical_retail":
        key_activities = ["Manage stock and suppliers", "Optimise layout", "Run daily cash-up"]
        key_resources = ["Premises", "Supplier accounts", "POS and stock sheet"]
    elif business_type == "ecommerce":
        key_activities = ["Test product hooks", "Manage supplier quality", "Improve product pages"]
        key_resources = ["Shopify store", "Samples", "Content assets"]
    else:
        key_activities = ["Validate offer", "Sell pilot", "Measure feedback"]
        key_resources = ["Founder time", "Landing page", "CRM sheet"]
    return {
        "Customer Segments": persona_segments,
        "Value Propositions": [context.get("value_proposition", "Focused launch offer")],
        "Channels": channels,
        "Customer Relationships": ["Fast response", "Clear expectations", "Proof through outcomes"],
        "Revenue Streams": price_units,
        "Key Activities": key_activities,
        "Key Resources": key_resources,
        "Key Partners": ["Suppliers or referral partners", "Local/community channels", "Payment/booking tools"],
        "Cost Structure": [f"{name}: {as_money(value)}" for name, value in startup_costs.items()],
    }
