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

        labels = {
            "revenue": "Revenue",
            "costs": "Costs",
            "cumulative_cashflow": "Cumulative cashflow",
        }
        df = pd.DataFrame(rows)
        long_df = df.melt(id_vars="month", value_vars=["revenue", "costs", "cumulative_cashflow"], var_name="metric", value_name="amount")
        long_df["metric"] = long_df["metric"].map(labels)
        fig = px.line(
            long_df,
            x="month",
            y="amount",
            color="metric",
            markers=True,
            title="3-Month Planning Forecast",
            color_discrete_map={
                "Revenue": "#2f80ed",
                "Costs": "#ef4444",
                "Cumulative cashflow": "#6d5dfc",
            },
        )
        fig.update_traces(line=dict(width=3), marker=dict(size=8))
        fig.update_layout(
            legend_title_text="",
            legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1),
            margin=dict(l=24, r=24, t=70, b=28),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#1f2937"),
            title=dict(font=dict(size=18, color="#111827")),
            xaxis=dict(title="Month", showgrid=False, tickmode="linear", dtick=1),
            yaxis=dict(title="Amount", gridcolor="#e7edf7", zerolinecolor="#94a3b8"),
        )
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
    currency_symbol = context.get("currency_symbol", "£")
    persona_segments = [p.segment for p in personas]
    price_units = [f"{p.tier}: {as_money(p.price, currency_symbol)} / {p.unit}" for p in pricing]
    if business_type == "local_service":
        key_activities = ["Deliver diagnostic and weekly tutoring sessions", "Send parent/student progress updates", "Collect testimonials and referrals"]
        key_resources = ["Maths/Physics subject expertise", "Booking calendar", "Diagnostic checklist and past-paper bank"]
        relationships = ["WhatsApp/email follow-up", "Parent update after sessions", "Referral and testimonial loop"]
        partners = ["School/parent communities", "Local Facebook and WhatsApp groups", "Payment and booking tools"]
    elif business_type == "physical_retail":
        key_activities = ["Manage stock and reorder points", "Optimise shop layout and opening hours", "Run daily cash-up and shrinkage checks"]
        key_resources = ["Station-adjacent premises", "Supplier accounts", "POS, stock sheet, and signage"]
        relationships = ["Fast in-store service", "Loyalty stamp", "Visible opening-week offers"]
        partners = ["Wholesale suppliers", "Local station/community channels", "Payment/POS provider"]
    elif business_type == "ecommerce":
        key_activities = ["Validate product hooks", "Improve Shopify product pages", "Manage supplier quality and fulfilment"]
        key_resources = ["Shopify store", "Product samples", "Content assets and analytics"]
        relationships = ["Email capture", "Review requests", "Post-purchase cross-sell"]
        partners = ["Product suppliers", "Creators/micro-influencers", "Fulfilment and payment providers"]
    else:
        key_activities = ["Validate offer", "Sell pilot", "Measure feedback"]
        key_resources = ["Founder time", "Landing page", "CRM sheet"]
        relationships = ["Fast response", "Clear expectations", "Feedback calls"]
        partners = ["Referral partners", "Launch channels", "Payment tools"]
    return {
        "Customer Segments": persona_segments,
        "Value Propositions": [context.get("value_proposition", "Focused launch offer")],
        "Channels": channels,
        "Customer Relationships": relationships,
        "Revenue Streams": price_units,
        "Key Activities": key_activities,
        "Key Resources": key_resources,
        "Key Partners": partners,
        "Cost Structure": [f"{name}: {as_money(value, currency_symbol)}" for name, value in startup_costs.items()],
    }
