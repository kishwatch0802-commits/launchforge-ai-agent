from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from launchforge.config import APP_TAGLINE, as_money
from launchforge.export import export_json, export_markdown
from launchforge.sample_data import type_label
from launchforge.schemas import BusinessInput, model_to_dict
from launchforge.visuals import cashflow_chart, readiness_score_breakdown
from launchforge.workflow import run_launchforge_workflow


st.set_page_config(page_title="LaunchForge", layout="wide")


DEMO_INPUTS = {
    "Tutoring Demo": "I want to start a tutoring business helping GCSE and A-Level students with Maths, Physics, and admissions tests like ESAT. I want to start locally, keep costs low, and get my first 10 students.",
    "Corner Shop Demo": "I want to open a small corner shop near a train station selling snacks, drinks, essentials, and quick breakfast items for commuters and local residents.",
    "Shopify Demo": "I want to launch a Shopify store selling affordable gym accessories like lifting straps, shaker bottles, resistance bands, and training notebooks.",
}


def ensure_sidebar_defaults() -> None:
    defaults = {
        "idea": "",
        "budget": 1000.0,
        "location": "Online",
        "founder_resources": "",
        "target_customer": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .main .block-container {padding-top: 2rem; max-width: 1220px;}
        .lf-subtitle {font-size: 1.1rem; color: #52616f; margin-top: -0.7rem;}
        .lf-card {
            border: 1px solid #dfe5eb; border-radius: 8px; padding: 1rem;
            background: #ffffff; min-height: 135px; box-shadow: 0 1px 2px rgba(10, 25, 41, 0.04);
        }
        .lf-card h4 {margin: 0 0 0.4rem 0;}
        .lf-small {font-size: 0.88rem; color: #52616f;}
        .lf-stage {
            border-left: 5px solid #1f7a8c; padding: 0.7rem 0.9rem; margin-bottom: 0.65rem;
            background: #f7fbfc; border-radius: 6px;
        }
        .lf-week {
            border-top: 4px solid #bf4342; background: #fffafa; padding: 0.85rem;
            border-radius: 6px; min-height: 210px;
        }
        .lf-canvas {
            border: 1px solid #dfe5eb; border-radius: 8px; padding: 0.8rem;
            background: #fbfcfd; min-height: 150px;
        }
        .lf-canvas h5 {margin: 0 0 0.35rem 0; color: #17324d;}
        .lf-proof {
            border: 1px solid #dfe5eb; border-radius: 8px; padding: 0.85rem;
            background: #f8fafc; min-height: 115px;
        }
        .lf-proof b {color: #17324d;}
        .lf-funnel {
            text-align: center; border: 1px solid #dfe5eb; border-radius: 8px;
            background: #ffffff; padding: 0.75rem; min-height: 82px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_demo(name: str) -> None:
    st.session_state["idea"] = DEMO_INPUTS[name]
    if name == "Tutoring Demo":
        st.session_state["budget"] = 600.0
        st.session_state["location"] = "Local area"
        st.session_state["founder_resources"] = "Strong Maths/Physics knowledge, laptop, evenings and weekends"
        st.session_state["target_customer"] = "Parents of GCSE and A-Level students"
    elif name == "Corner Shop Demo":
        st.session_state["budget"] = 12000.0
        st.session_state["location"] = "Near a train station"
        st.session_state["founder_resources"] = "Retail experience, possible small premises, local supplier contacts"
        st.session_state["target_customer"] = "Commuters and nearby residents"
    else:
        st.session_state["budget"] = 2500.0
        st.session_state["location"] = "Online"
        st.session_state["founder_resources"] = "Shopify basics, gym knowledge, phone for content"
        st.session_state["target_customer"] = "Budget-conscious beginner and intermediate gym users"


def render_canvas(canvas: dict[str, list[str]]) -> None:
    keys = list(canvas.keys())
    for row_start in range(0, len(keys), 3):
        cols = st.columns(3)
        for col, key in zip(cols, keys[row_start : row_start + 3]):
            with col:
                items = "".join(f"<li>{escape(str(item))}</li>" for item in canvas[key])
                st.markdown(f"<div class='lf-canvas'><h5>{escape(key)}</h5><ul>{items}</ul></div>", unsafe_allow_html=True)


def render_personas(pack) -> None:
    cols = st.columns(min(3, len(pack.personas)))
    for col, persona in zip(cols, pack.personas):
        with col:
            st.markdown(
                f"""
                <div class='lf-card'>
                <h4>{escape(persona.name)}</h4>
                <div class='lf-small'>{escape(persona.segment)}</div>
                <p><b>Trigger:</b> {escape(persona.buying_trigger)}</p>
                <p><b>Channels:</b> {escape(", ".join(persona.channels))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_offer_ladder(pack) -> None:
    for index, offer in enumerate(pack.offer_ladder, start=1):
        st.markdown(
            f"""
            <div class='lf-stage'>
            <b>Stage {index}: {escape(offer.name)}</b><br>
            {escape(offer.description)}<br>
            <span class='lf-small'>Ideal for: {escape(offer.ideal_for)} | Success metric: {escape(offer.success_metric)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_capstone_evidence() -> None:
    items = [
        ("Multi-agent", "10 specialist agents coordinated by an ADK-style sequential runner."),
        ("MCP tools", "Classification, pricing, cashflow, funnel, tasks, and export tool functions."),
        ("Agent skills", "Reusable launch pack, cashflow, funnel, and export skills called by agents."),
        ("Security", "No hard-coded keys, sanitized inputs, privacy mode, export-only persistence."),
        ("Deployable", "Runs locally, on Streamlit Community Cloud, or with Docker."),
    ]
    cols = st.columns(len(items))
    for col, (title, text) in zip(cols, items):
        with col:
            st.markdown(f"<div class='lf-proof'><b>{title}</b><br><span class='lf-small'>{text}</span></div>", unsafe_allow_html=True)


def render_funnel(stages: list[str]) -> None:
    cols = st.columns(len(stages))
    for index, (col, stage) in enumerate(zip(cols, stages), start=1):
        with col:
            st.markdown(f"<div class='lf-funnel'><b>{index}</b><br>{escape(stage)}</div>", unsafe_allow_html=True)


def render_roadmap(pack) -> None:
    for week in range(1, 5):
        tasks = [task for task in pack.roadmap if task.week == week]
        with st.container():
            st.subheader(f"Week {week}")
            cols = st.columns(2)
            for col, task in zip(cols * 4, tasks):
                with col:
                    st.markdown(
                        f"<div class='lf-card'><b>Day {task.day}: {escape(task.title)}</b><p>{escape(task.outcome)}</p><span class='lf-small'>{escape(task.category)}</span></div>",
                        unsafe_allow_html=True,
                    )


def main() -> None:
    ensure_sidebar_defaults()
    inject_css()
    st.title("LaunchForge")
    st.markdown(f"<div class='lf-subtitle'>{APP_TAGLINE}</div>", unsafe_allow_html=True)

    with st.sidebar:
        st.header("Founder Input")
        for label in DEMO_INPUTS:
            if st.button(f"Load {label}", use_container_width=True):
                load_demo(label)
        idea = st.text_area("Business idea", key="idea", height=170, placeholder="Describe the business you want to launch...")
        budget = st.number_input("Budget", min_value=0.0, step=100.0, key="budget")
        location = st.text_input("Location or online", key="location")
        founder_resources = st.text_area("Founder skills/resources", key="founder_resources", height=90)
        timeframe = st.selectbox("Target launch timeframe", ["7 days", "14 days", "30 days", "60 days"], index=2)
        stage = st.selectbox("Business stage", ["Idea only", "Testing", "Ready to launch"], index=0)
        target_customer = st.text_input("Optional target customer", key="target_customer")
        privacy_mode = st.toggle("Do not store my business idea", value=True, help="LaunchForge does not write inputs to disk unless you use an export button.")
        generate = st.button("Generate Launch Pack", type="primary", use_container_width=True)
        st.caption("Financial estimates are planning assumptions, not financial advice.")

    if "pack" not in st.session_state and not generate:
        st.info("Load a demo or enter an idea, then generate a launch pack.")
        st.markdown("```mermaid\nflowchart LR\nIdea --> Agents --> LaunchPack\nAgents --> MCPTools[MCP tools]\nLaunchPack --> Exports\n```")
        return

    if generate:
        if not idea.strip():
            st.warning("Enter a business idea or load a demo first.")
            return
        business_input = BusinessInput(
            idea=idea,
            budget=budget,
            location=location,
            founder_resources=founder_resources,
            timeframe=timeframe,
            stage=stage,
            target_customer=target_customer or None,
            privacy_mode=privacy_mode,
        )
        with st.spinner("Running specialist agents..."):
            st.session_state["pack"] = run_launchforge_workflow(business_input)

    pack = st.session_state["pack"]
    type_name = type_label(pack.classification.business_type)
    startup_total = sum(pack.startup_costs.values())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Business Type", type_name)
    c2.metric("Readiness Score", f"{pack.readiness_score}/100")
    c3.metric("Estimated Startup Cost", as_money(startup_total))
    c4.metric("Break-even Month", pack.breakeven_month)
    st.progress(pack.readiness_score / 100)

    tabs = st.tabs(["Overview", "Customers & Offer", "Pricing & Finance", "Marketing & Operations", "Roadmap", "Export"])

    with tabs[0]:
        st.subheader("Capstone Evidence")
        render_capstone_evidence()
        st.subheader("Classification")
        st.write(pack.classification.reasoning)
        st.caption(f"Confidence: {pack.classification.confidence:.0%}")
        st.subheader("Business Model Canvas")
        render_canvas(pack.business_model_canvas)
        st.subheader("Readiness Breakdown")
        st.dataframe(pd.DataFrame(readiness_score_breakdown(pack.readiness_breakdown)), hide_index=True, use_container_width=True)
        st.subheader("Risks & Assumptions")
        risk_cols = st.columns(2)
        with risk_cols[0]:
            st.markdown("**Risks**")
            for risk in pack.risks:
                st.write(f"- {risk}")
        with risk_cols[1]:
            st.markdown("**Assumptions**")
            for assumption in pack.assumptions:
                st.write(f"- {assumption}")

    with tabs[1]:
        st.subheader("Customer Persona Cards")
        render_personas(pack)
        st.subheader("Offer Ladder")
        render_offer_ladder(pack)

    with tabs[2]:
        st.subheader("Pricing Table")
        pricing_rows = [model_to_dict(item) for item in pack.pricing]
        st.dataframe(pd.DataFrame(pricing_rows), hide_index=True, use_container_width=True)
        st.subheader("Cashflow Forecast")
        fig = cashflow_chart(pack.cashflow)
        if hasattr(fig, "to_plotly_json"):
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.pyplot(fig)
        st.caption("Forecasts are illustrative assumptions for planning and should be manually reviewed.")

    with tabs[3]:
        st.subheader("Sales Funnel")
        render_funnel(pack.sales_funnel["stages"])
        st.code(pack.diagrams["sales_funnel"], language="mermaid")
        st.write(" -> ".join(pack.sales_funnel["stages"]))
        st.subheader("Marketing Message Pack")
        for category, messages in pack.marketing_messages.items():
            st.markdown(f"**{category.replace('_', ' ').title()}**")
            for message in messages:
                st.write(f"- {message}")
        st.subheader("Operations Checklist")
        for index, item in enumerate(pack.operations_checklist):
            st.checkbox(item, value=False, key=f"op_{pack.classification.business_type}_{index}")

    with tabs[4]:
        st.subheader("30-Day Launch Roadmap")
        render_roadmap(pack)
        st.subheader("Final Next 3 Actions")
        for index, action in enumerate(pack.next_3_actions, start=1):
            st.success(f"{index}. {action}")

    with tabs[5]:
        st.subheader("Download Launch Pack")
        markdown_export = export_markdown(pack)
        json_export = export_json(pack)
        st.download_button("Download Markdown", markdown_export, "launchforge_launch_pack.md", "text/markdown")
        st.download_button("Download JSON", json_export, "launchforge_launch_pack.json", "application/json")
        st.subheader("Preview")
        st.code(markdown_export[:4000], language="markdown")
        st.caption("Privacy mode: inputs are held in session memory only. Exports are created only when you click a download button.")


if __name__ == "__main__":
    main()
