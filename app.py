from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from launchforge.config import APP_TAGLINE, as_money
from launchforge.copilot_agent import answer_copilot_question
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
        :root {
            --lf-navy: #0b1020;
            --lf-navy-2: #111936;
            --lf-purple: #6d5dfc;
            --lf-blue: #2f80ed;
            --lf-cyan: #22d3ee;
            --lf-ink: #111827;
            --lf-muted: #65758b;
            --lf-border: #dfe7f5;
            --lf-panel: #ffffff;
            --lf-soft: #f6f8ff;
            --lf-success: #16a34a;
            --lf-success-soft: #dcfce7;
            --lf-warning: #b45309;
            --lf-warning-soft: #fef3c7;
            --lf-danger: #dc2626;
            --lf-danger-soft: #fee2e2;
        }
        .stApp {background: radial-gradient(circle at top left, #eef3ff 0%, #f8faff 36%, #ffffff 78%);}
        .main .block-container {padding-top: 1.2rem; max-width: 1320px;}
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #080d1c 0%, #141b3c 52%, #241447 100%);
            border-right: 1px solid rgba(255,255,255,0.08);
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"] p {color: rgba(255,255,255,0.86) !important;}
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {color: #ffffff !important;}
        [data-testid="stSidebar"] textarea,
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: rgba(255,255,255,0.08) !important;
            color: #ffffff !important;
            border-color: rgba(255,255,255,0.16) !important;
            border-radius: 12px !important;
        }
        [data-testid="stSidebar"] textarea::placeholder,
        [data-testid="stSidebar"] input::placeholder {color: rgba(255,255,255,0.48) !important;}
        [data-testid="stSidebar"] button {
            border-radius: 12px !important;
            border: 1px solid rgba(255,255,255,0.14) !important;
            background: rgba(255,255,255,0.08) !important;
            color: #ffffff !important;
            font-weight: 650 !important;
        }
        [data-testid="stSidebar"] button[kind="primary"],
        [data-testid="stSidebar"] .stButton:last-of-type button {
            background: linear-gradient(135deg, #6d5dfc 0%, #2f80ed 100%) !important;
            border: 0 !important;
            box-shadow: 0 14px 30px rgba(69, 89, 255, 0.32) !important;
        }
        [data-testid="stSidebar"] hr {border-color: rgba(255,255,255,0.12);}
        .lf-sidebar-brand {
            border: 1px solid rgba(255,255,255,0.14); border-radius: 18px;
            background: linear-gradient(135deg, rgba(109,93,252,0.28), rgba(34,211,238,0.13));
            padding: 1rem; margin: 0.4rem 0 1rem 0;
            box-shadow: 0 18px 42px rgba(0,0,0,0.22);
        }
        .lf-sidebar-brand h2 {margin: 0; color: #ffffff; font-size: 1.4rem;}
        .lf-sidebar-brand p {margin: 0.25rem 0 0 0; color: rgba(255,255,255,0.72); font-size: 0.86rem;}
        .lf-sidebar-group {
            color: rgba(255,255,255,0.66); text-transform: uppercase; letter-spacing: 0.08em;
            font-size: 0.72rem; font-weight: 760; margin: 1rem 0 0.45rem 0;
        }
        div[data-testid="stTabs"] button {
            border-radius: 999px !important;
            padding: 0.55rem 1rem !important;
            color: #4b5870 !important;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            background: #111936 !important;
            color: #ffffff !important;
            box-shadow: 0 10px 26px rgba(17,25,54,0.16);
        }
        div[data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 0.35rem;
            background: rgba(255,255,255,0.72);
            border: 1px solid var(--lf-border);
            border-radius: 999px;
            padding: 0.35rem;
            box-shadow: 0 14px 34px rgba(23, 38, 84, 0.06);
        }
        div[data-testid="stMetric"] {
            background: #ffffff; border: 1px solid #dfe5f2; border-radius: 14px;
            padding: 1rem 1.05rem; box-shadow: 0 12px 30px rgba(23, 38, 84, 0.07);
        }
        .lf-hero {
            position: relative; overflow: hidden;
            background:
                radial-gradient(circle at 82% 12%, rgba(34,211,238,0.34), transparent 26%),
                radial-gradient(circle at 58% 110%, rgba(109,93,252,0.44), transparent 28%),
                linear-gradient(135deg, #081122 0%, #172554 48%, #5b21b6 100%);
            color: #ffffff; border-radius: 22px; padding: 1.55rem 1.65rem; margin-bottom: 1rem;
            box-shadow: 0 24px 70px rgba(31, 59, 115, 0.28);
            border: 1px solid rgba(255,255,255,0.15);
        }
        .lf-hero:after {
            content: ""; position: absolute; right: -80px; top: -80px; width: 220px; height: 220px;
            background: rgba(255,255,255,0.08); border-radius: 50%;
        }
        .lf-hero h1 {font-size: 2.55rem; margin: 0; letter-spacing: 0; line-height: 1.05;}
        .lf-subtitle {font-size: 1rem; color: #d8e2ff; margin-top: 0.25rem;}
        .lf-badges {display: flex; gap: 0.55rem; flex-wrap: wrap; margin-top: 0.9rem;}
        .lf-badge {
            display: inline-block; border: 1px solid rgba(255,255,255,0.24); border-radius: 999px;
            padding: 0.38rem 0.65rem; background: rgba(255,255,255,0.12); color: #ffffff; font-size: 0.85rem;
        }
        .lf-kpi {
            position: relative; overflow: hidden;
            border: 1px solid var(--lf-border); border-radius: 18px; padding: 1.05rem 1.1rem;
            background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
            min-height: 126px; box-shadow: 0 16px 38px rgba(23, 38, 84, 0.08);
        }
        .lf-kpi:before {content: ""; position: absolute; left: 0; top: 0; right: 0; height: 4px; background: linear-gradient(90deg, var(--lf-purple), var(--lf-blue), var(--lf-cyan));}
        .lf-kpi-label {font-size: 0.78rem; color: #60708a; text-transform: uppercase; letter-spacing: 0.04em;}
        .lf-kpi-value {font-size: 1.55rem; font-weight: 760; color: #111827; margin-top: 0.25rem;}
        .lf-kpi-note {font-size: 0.86rem; color: #60708a; margin-top: 0.25rem;}
        .lf-card {
            border: 1px solid var(--lf-border); border-radius: 18px; padding: 1.05rem;
            background: #ffffff; min-height: 138px; box-shadow: 0 14px 34px rgba(23, 38, 84, 0.07);
        }
        .lf-card h4 {margin: 0 0 0.45rem 0; color: var(--lf-ink); line-height: 1.18;}
        .lf-card p {color: #334155;}
        .lf-copilot-answer {white-space: pre-wrap; line-height: 1.55;}
        .lf-small {font-size: 0.88rem; color: #52616f;}
        .lf-section {
            margin: 1.35rem 0 0.75rem 0;
            display: flex; align-items: end; justify-content: space-between; gap: 1rem;
        }
        .lf-section h3 {margin: 0; color: var(--lf-ink); font-size: 1.15rem;}
        .lf-section p {margin: 0.2rem 0 0 0; color: var(--lf-muted); font-size: 0.92rem;}
        .lf-eyebrow {
            display: inline-block; color: #4f46e5; background: #eef2ff;
            padding: 0.22rem 0.5rem; border-radius: 999px; font-size: 0.72rem;
            font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase;
        }
        .lf-chip {
            display: inline-block; margin: 0.2rem 0.28rem 0.2rem 0; padding: 0.42rem 0.58rem;
            border-radius: 999px; background: #eef4ff; color: #24407a; border: 1px solid #d7e5ff; font-size: 0.86rem;
        }
        .lf-stage {
            position: relative;
            border: 1px solid #ded8ff; padding: 1.05rem; margin-bottom: 0.7rem;
            background: linear-gradient(180deg, #ffffff 0%, #f8f7ff 100%);
            border-radius: 18px; box-shadow: 0 16px 34px rgba(91,63,214,0.10);
            min-height: 310px;
        }
        .lf-stage-number {
            display: inline-flex; align-items: center; justify-content: center;
            width: 34px; height: 34px; border-radius: 12px; color: #ffffff;
            background: linear-gradient(135deg, #5b3fd6, #2f80ed); font-weight: 800;
            box-shadow: 0 10px 20px rgba(91,63,214,0.24);
        }
        .lf-canvas {
            border: 1px solid var(--lf-border); border-radius: 18px; padding: 1rem;
            background: linear-gradient(180deg, #ffffff 0%, #fbfcff 100%);
            min-height: 185px; box-shadow: 0 12px 28px rgba(23, 38, 84, 0.06);
        }
        .lf-canvas h5 {margin: 0 0 0.45rem 0; color: #17324d; font-size: 0.98rem;}
        .lf-canvas ul {margin-left: 1rem; padding-left: 0;}
        .lf-proof {
            border: 1px solid var(--lf-border); border-radius: 16px; padding: 0.85rem;
            background: #f8fafc; min-height: 108px; box-shadow: 0 8px 22px rgba(23, 38, 84, 0.05);
        }
        .lf-proof b {color: #17324d;}
        .lf-funnel {
            position: relative; text-align: center; border: 1px solid #dbe7ff; border-radius: 18px;
            background: linear-gradient(180deg, #ffffff 0%, #f2f7ff 100%);
            padding: 0.95rem; min-height: 112px;
            box-shadow: 0 14px 32px rgba(23, 38, 84, 0.08);
        }
        .lf-funnel b {display: inline-flex; align-items: center; justify-content: center; width: 30px; height: 30px; border-radius: 10px; background: #111936; color: #ffffff; margin-bottom: 0.35rem;}
        .lf-day {
            display: inline-block; min-width: 48px; text-align: center; color: #ffffff;
            background: linear-gradient(135deg, #1f3b73, #5b3fd6); border-radius: 10px;
            padding: 0.35rem 0.5rem; font-weight: 700; margin-bottom: 0.45rem;
        }
        .lf-agent {
            border: 1px solid var(--lf-border); border-radius: 16px; padding: 0.9rem;
            background: #ffffff; min-height: 148px; box-shadow: 0 12px 30px rgba(23, 38, 84, 0.06);
        }
        .lf-status {display: inline-block; font-size: 0.72rem; color: #065f46; background: #d1fae5; border: 1px solid #a7f3d0; border-radius: 999px; padding: 0.22rem 0.5rem; font-weight: 750;}
        .lf-action {
            background: linear-gradient(135deg, #ecfeff 0%, #f5f3ff 100%);
            border: 1px solid #cfe9ff; border-radius: 18px; padding: 1rem; min-height: 130px;
            box-shadow: 0 14px 34px rgba(23, 38, 84, 0.07);
        }
        .lf-section-note {color: #60708a; margin-top: -0.2rem;}
        .lf-price {font-size: 2rem; font-weight: 850; color: #1f3b73; letter-spacing: 0;}
        .lf-list {margin: 0.35rem 0 0 1rem; padding: 0;}
        .lf-list li {margin-bottom: 0.25rem;}
        .lf-arrow {text-align: center; color: #5b3fd6; font-weight: 800; font-size: 1.2rem; padding-top: 2rem;}
        .lf-disclaimer {border-left: 4px solid #f59e0b; background: #fffbeb; padding: 0.7rem 0.9rem; border-radius: 12px; color: #7c4a03;}
        .lf-chart-panel {
            border: 1px solid var(--lf-border); border-radius: 18px; padding: 0.8rem;
            background: #ffffff; box-shadow: 0 14px 34px rgba(23, 38, 84, 0.06);
        }
        .lf-roadmap-week {
            border: 1px solid var(--lf-border); border-radius: 20px; padding: 1rem;
            background: rgba(255,255,255,0.78); box-shadow: 0 14px 32px rgba(23, 38, 84, 0.06);
            margin-bottom: 1rem;
        }
        .lf-download-card {
            border: 1px solid #d8e2ff; border-radius: 20px; padding: 1.1rem;
            background: linear-gradient(135deg, #ffffff 0%, #f4f7ff 100%);
            box-shadow: 0 14px 34px rgba(23, 38, 84, 0.08);
        }
        @media (max-width: 900px) {
            .lf-hero h1 {font-size: 1.8rem;}
        }
        /* Final product polish overrides: restrained premium dashboard shell. */
        .stApp {background: #edf2f7;}
        .main .block-container {max-width: 1240px; padding-top: 1rem; padding-bottom: 8.5rem;}
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #070b16 0%, #0d1427 54%, #15102b 100%);
            box-shadow: 12px 0 36px rgba(15,23,42,0.14);
        }
        [data-testid="stSidebar"] section {padding-top: 0.75rem;}
        [data-testid="stSidebar"] textarea,
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            min-height: 2.55rem !important;
            background: rgba(255,255,255,0.095) !important;
            border: 1px solid rgba(199,210,254,0.18) !important;
        }
        [data-testid="stSidebar"] button {
            min-height: 2.35rem !important;
            box-shadow: none !important;
        }
        .lf-sidebar-brand {
            border-radius: 16px; padding: 0.9rem;
            background: linear-gradient(145deg, rgba(37,99,235,0.20), rgba(124,58,237,0.18));
            box-shadow: 0 18px 40px rgba(0,0,0,0.18);
        }
        .lf-sidebar-brand h2 {font-size: 1.25rem;}
        .lf-sidebar-group {margin-top: 0.9rem; margin-bottom: 0.35rem; color: rgba(226,232,240,0.76);}
        .lf-sidebar-chip {
            display: inline-flex; align-items: center; gap: 0.35rem;
            border: 1px solid rgba(147,197,253,0.22); border-radius: 999px;
            background: rgba(15,23,42,0.42); color: #dbeafe;
            padding: 0.34rem 0.58rem; font-size: 0.76rem; font-weight: 700;
            margin-bottom: 0.4rem;
        }
        .lf-hero {
            border-radius: 18px; padding: 1.05rem 1.2rem; margin-bottom: 0.75rem;
            background: linear-gradient(135deg, #0b1224 0%, #172554 58%, #3b1d82 100%);
            box-shadow: 0 18px 46px rgba(15,23,42,0.18);
        }
        .lf-hero:after {display: none;}
        .lf-hero h1 {font-size: 2rem;}
        .lf-subtitle {font-size: 0.92rem;}
        .lf-badges {gap: 0.4rem; margin-top: 0.65rem;}
        .lf-badge {font-size: 0.76rem; padding: 0.28rem 0.52rem;}
        .lf-kpi {
            border-radius: 14px; padding: 0.78rem 0.82rem; min-height: 96px;
            box-shadow: 0 9px 24px rgba(15,23,42,0.055);
            background: #ffffff;
        }
        .lf-kpi:before {height: 3px;}
        .lf-kpi-label {font-size: 0.68rem;}
        .lf-kpi-value {font-size: 1.25rem; line-height: 1.16;}
        .lf-kpi-note {font-size: 0.78rem;}
        .lf-card,
        .lf-agent,
        .lf-proof,
        .lf-canvas,
        .lf-download-card,
        .lf-roadmap-week {
            border-radius: 14px;
            box-shadow: 0 10px 28px rgba(15,23,42,0.055);
        }
        .lf-card {min-height: auto; padding: 0.88rem;}
        .lf-agent {min-height: auto; padding: 0.82rem;}
        .lf-proof {min-height: auto;}
        .lf-canvas {min-height: 148px;}
        .lf-stage {min-height: 250px; border-radius: 14px; padding: 0.88rem;}
        .lf-price {font-size: 1.55rem;}
        .lf-section {margin: 1rem 0 0.55rem 0;}
        .lf-section h3 {font-size: 1.05rem;}
        .lf-section p {font-size: 0.84rem;}
        .lf-chip {font-size: 0.78rem; padding: 0.3rem 0.48rem;}
        .lf-status {font-size: 0.67rem; padding: 0.18rem 0.46rem;}
        .lf-readiness-shell {
            margin-top: 0.75rem; display: grid; grid-template-columns: 1fr auto; gap: 0.75rem; align-items: center;
        }
        .lf-scorebar {
            height: 0.55rem; border-radius: 999px; background: #e5eaf3; overflow: hidden;
            border: 1px solid #d8e0ee;
        }
        .lf-scorebar > span {
            display: block; height: 100%; border-radius: 999px;
            background: linear-gradient(90deg, #2563eb, #7c3aed);
        }
        .lf-scorebar-label {
            display: flex; justify-content: space-between; gap: 0.75rem;
            font-size: 0.78rem; color: #52616f; margin-bottom: 0.25rem;
        }
        .lf-mini-flow {
            display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 0.5rem;
        }
        .lf-flow-step {
            background: #ffffff; border: 1px solid var(--lf-border); border-radius: 14px;
            padding: 0.7rem; min-height: 84px; box-shadow: 0 8px 22px rgba(15,23,42,0.05);
        }
        .lf-flow-step b {display: block; color: #172554; margin-bottom: 0.2rem;}
        .lf-lane-title {
            display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid #e5eaf3; padding-bottom: 0.45rem; margin-bottom: 0.65rem;
        }
        .lf-trace-event {
            border-left: 3px solid #2563eb; background: #ffffff;
            border-radius: 12px; border-top: 1px solid var(--lf-border);
            border-right: 1px solid var(--lf-border); border-bottom: 1px solid var(--lf-border);
            padding: 0.78rem; margin-bottom: 0.55rem; box-shadow: 0 8px 20px rgba(15,23,42,0.045);
        }
        .lf-trace-step {
            display: inline-flex; width: 26px; height: 26px; align-items: center; justify-content: center;
            border-radius: 8px; background: #172554; color: #ffffff; font-size: 0.75rem; font-weight: 800;
            margin-right: 0.35rem;
        }
        .lf-roadmap-board {display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.75rem;}
        .lf-roadmap-column {
            border: 1px solid var(--lf-border); border-radius: 16px;
            background: rgba(255,255,255,0.76); padding: 0.75rem;
        }
        .lf-roadmap-card {
            background: #ffffff; border: 1px solid #e1e8f5; border-radius: 12px;
            padding: 0.72rem; margin-top: 0.55rem; box-shadow: 0 8px 22px rgba(15,23,42,0.05);
        }
        .lf-check-tile {
            display: flex; gap: 0.6rem; align-items: flex-start;
            background: #ffffff; border: 1px solid var(--lf-border); border-radius: 12px;
            padding: 0.72rem; margin-bottom: 0.55rem; box-shadow: 0 8px 20px rgba(15,23,42,0.045);
        }
        .lf-checkmark {
            flex: 0 0 auto; width: 22px; height: 22px; border-radius: 999px;
            display: inline-flex; align-items: center; justify-content: center;
            color: #065f46; background: #dcfce7; font-weight: 900; font-size: 0.78rem;
        }
        .lf-copilot-dock {
            position: sticky; bottom: 0.75rem; z-index: 50;
            border: 1px solid #d7dff0; border-radius: 18px;
            background: rgba(255,255,255,0.94); backdrop-filter: blur(10px);
            box-shadow: 0 22px 60px rgba(15,23,42,0.18);
            padding: 0.8rem 0.95rem; margin-top: 1.25rem;
        }
        .lf-copilot-dock h4 {margin: 0; color: #172554;}
        .lf-copilot-dock p {margin: 0.15rem 0 0 0; color: #64748b; font-size: 0.84rem;}
        .lf-copilot-response {
            border: 1px solid #dbe7ff; border-radius: 14px; background: #f8fbff;
            padding: 0.85rem; margin-bottom: 0.75rem;
        }
        @media (max-width: 980px) {
            .lf-mini-flow, .lf-roadmap-board {grid-template-columns: repeat(2, minmax(0, 1fr));}
        }
        @media (max-width: 680px) {
            .lf-mini-flow, .lf-roadmap-board {grid-template-columns: 1fr;}
            .main .block-container {padding-left: 0.8rem; padding-right: 0.8rem;}
        }
        /* Reference-inspired refinements: flatter sidebar, icon tiles, semantic tone. */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #05070d 0%, #0a0e1a 55%, #0d0a17 100%);
        }
        .lf-kpi {display: flex; gap: 0.7rem; align-items: flex-start;}
        .lf-kpi-body {flex: 1 1 auto; min-width: 0;}
        .lf-icon-tile {
            flex: 0 0 auto; width: 34px; height: 34px; border-radius: 10px;
            display: inline-flex; align-items: center; justify-content: center;
            font-weight: 800; font-size: 0.92rem; color: #ffffff;
            background: linear-gradient(135deg, var(--lf-blue), var(--lf-purple));
        }
        .lf-icon-tile.tone-success {background: var(--lf-success); box-shadow: 0 8px 18px rgba(22,163,74,0.28);}
        .lf-icon-tile.tone-warning {background: var(--lf-warning); box-shadow: 0 8px 18px rgba(180,83,9,0.28);}
        .lf-icon-tile.tone-danger {background: var(--lf-danger); box-shadow: 0 8px 18px rgba(220,38,38,0.24);}
        .lf-icon-tile.tone-neutral {background: linear-gradient(135deg, #64748b, #334155);}
        .lf-kpi-note.tone-success {color: var(--lf-success); font-weight: 650;}
        .lf-kpi-note.tone-warning {color: var(--lf-warning); font-weight: 650;}
        .lf-kpi-note.tone-danger {color: var(--lf-danger); font-weight: 650;}
        .lf-status-dot {
            display: inline-block; width: 8px; height: 8px; border-radius: 999px;
            margin-right: 0.4rem; background: #64748b; box-shadow: 0 0 0 3px rgba(100,116,139,0.18);
        }
        .lf-status-dot.is-live {background: #22c55e; box-shadow: 0 0 0 3px rgba(34,197,94,0.22);}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_product_css() -> None:
    """Premium product-shell styling for the user-facing Product View.

    Kept separate from inject_css() so the technical dashboard is untouched.
    """

    st.markdown(
        """
        <style>
        /* ---------- Product View: shell ---------- */
        .lf-topbar {
            display: flex; align-items: center; justify-content: space-between; gap: 1rem;
            background: linear-gradient(120deg, #0a1024 0%, #111a3a 60%, #171334 100%);
            border: 1px solid rgba(148,163,184,0.14);
            border-radius: 16px; padding: 0.7rem 1.15rem; margin-bottom: 1rem;
            box-shadow: 0 18px 46px rgba(15,23,42,0.20);
        }
        .lf-topbar-brand {display: flex; align-items: center; gap: 0.6rem;}
        .lf-topbar-logo {
            width: 34px; height: 34px; border-radius: 10px; flex: 0 0 auto;
            display: inline-flex; align-items: center; justify-content: center;
            font-weight: 900; color: #fff; font-size: 1rem;
            background: linear-gradient(135deg, #6d5dfc, #2f80ed);
            box-shadow: 0 8px 18px rgba(69,89,255,0.35);
        }
        .lf-topbar-brand b {color: #ffffff; font-size: 1.02rem; letter-spacing: 0.01em; line-height: 1;}
        .lf-topbar-brand span {color: #9fb0d6; font-size: 0.74rem; display: block; margin-top: 2px;}
        .lf-topbar-title {color: #eaf0ff; font-weight: 800; letter-spacing: 0.12em; font-size: 0.86rem; text-transform: uppercase;}
        .lf-topbar-right {display: flex; align-items: center; gap: 0.5rem;}
        .lf-pill {
            display: inline-flex; align-items: center; gap: 0.4rem;
            border: 1px solid rgba(148,163,184,0.28); border-radius: 999px;
            background: rgba(255,255,255,0.06); color: #dbe6ff;
            padding: 0.32rem 0.62rem; font-size: 0.76rem; font-weight: 700;
        }
        .lf-pill .dot {width: 8px; height: 8px; border-radius: 999px; background: #22c55e; box-shadow: 0 0 0 3px rgba(34,197,94,0.22);}
        .lf-pill.amber .dot {background: #f59e0b; box-shadow: 0 0 0 3px rgba(245,158,11,0.22);}

        /* ---------- Product View: section nav (sidebar radio) ---------- */
        .lf-pv-nav-label {color: rgba(226,232,240,0.7); text-transform: uppercase; letter-spacing: 0.09em; font-size: 0.7rem; font-weight: 800; margin: 0.6rem 0 0.3rem 0;}
        [data-testid="stSidebar"] div[role="radiogroup"] {gap: 0.2rem;}
        [data-testid="stSidebar"] div[role="radiogroup"] label {
            border-radius: 12px; padding: 0.35rem 0.55rem; margin: 0;
            transition: background 0.15s ease;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover {background: rgba(255,255,255,0.06);}

        /* Product View sidebar form contrast: dark text on light controls, light labels on dark shell. */
        [data-testid="stSidebar"] div[data-testid="stTextArea"] textarea,
        [data-testid="stSidebar"] div[data-testid="stTextInput"] input,
        [data-testid="stSidebar"] div[data-testid="stNumberInput"] input,
        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: #ffffff !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            border: 1px solid rgba(203,213,225,0.9) !important;
            box-shadow: 0 8px 22px rgba(15,23,42,0.14) !important;
        }
        [data-testid="stSidebar"] div[data-testid="stTextArea"] textarea::placeholder,
        [data-testid="stSidebar"] div[data-testid="stTextInput"] input::placeholder,
        [data-testid="stSidebar"] div[data-testid="stNumberInput"] input::placeholder {
            color: #94a3b8 !important;
            -webkit-text-fill-color: #94a3b8 !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] *,
        [data-testid="stSidebar"] [data-baseweb="select"] input {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: rgba(226,232,240,0.9) !important;
        }

        /* ---------- Product View: hero score + KPIs ---------- */
        .lf-pv-grid {display: grid; grid-template-columns: 1.15fr 1fr; gap: 1rem;}
        .lf-panel {
            background: #ffffff; border: 1px solid #e3e9f5; border-radius: 18px;
            padding: 1.1rem 1.2rem; box-shadow: 0 14px 34px rgba(23,38,84,0.07);
        }
        .lf-panel-title {display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.65rem;}
        .lf-panel-title h3 {margin: 0; font-size: 1.02rem; color: #0f1b3d; font-weight: 800;}
        .lf-panel-title .lf-tag {font-size: 0.72rem; color: #5b6b88; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;}
        .lf-gauge-wrap {display: flex; flex-direction: column; align-items: center; text-align: center; padding: 0.2rem 0 0.1rem;}
        .lf-gauge-label {margin-top: 0.15rem; font-size: 0.9rem; color: #52627f;}
        .lf-gauge-chip {
            margin-top: 0.5rem; display: inline-block; padding: 0.32rem 0.8rem; border-radius: 999px;
            font-weight: 800; font-size: 0.9rem;
        }
        .lf-gauge-chip.success {background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0;}
        .lf-gauge-chip.warning {background: #fef3c7; color: #b45309; border: 1px solid #fde68a;}
        .lf-gauge-chip.danger {background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca;}

        .lf-mini-metrics {display: grid; grid-template-columns: 1fr 1fr; gap: 0.7rem;}
        .lf-mini {
            background: linear-gradient(180deg,#ffffff,#fbfcff); border: 1px solid #e3e9f5;
            border-radius: 14px; padding: 0.75rem 0.85rem; box-shadow: 0 8px 22px rgba(23,38,84,0.05);
        }
        .lf-mini .k {font-size: 0.72rem; color: #61718d; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 700;}
        .lf-mini .v {font-size: 1.35rem; font-weight: 850; color: #0f1b3d; margin-top: 0.15rem; line-height: 1.05;}
        .lf-mini .n {font-size: 0.78rem; color: #61718d; margin-top: 0.15rem;}
        .lf-mini .n.success {color: #15803d; font-weight: 700;}
        .lf-mini .n.warning {color: #b45309; font-weight: 700;}
        .lf-mini .n.danger {color: #b91c1c; font-weight: 700;}

        /* ---------- Insights / lists ---------- */
        .lf-ins {display: flex; gap: 0.6rem; align-items: flex-start; padding: 0.5rem 0; border-bottom: 1px dashed #e7edf7;}
        .lf-ins:last-child {border-bottom: 0;}
        .lf-ins .ic {flex: 0 0 auto; width: 24px; height: 24px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; font-size: 0.78rem; font-weight: 900; color: #fff;}
        .lf-ins .ic.op {background: linear-gradient(135deg,#2563eb,#6d5dfc);}
        .lf-ins .ic.warn {background: #f59e0b;}
        .lf-ins .ic.risk {background: #ef4444;}
        .lf-ins .tx {color: #24324f; font-size: 0.9rem; line-height: 1.4;}
        .lf-ins .tx b {color: #0f1b3d;}

        /* ---------- Cards row ---------- */
        .lf-pv-card {
            background: #ffffff; border: 1px solid #e3e9f5; border-radius: 16px;
            padding: 0.9rem 1rem; box-shadow: 0 10px 26px rgba(23,38,84,0.06); height: 100%;
        }
        .lf-pv-card .eyebrow {font-size: 0.7rem; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; color: #6d5dfc;}
        .lf-pv-card h4 {margin: 0.25rem 0 0.35rem 0; color: #0f1b3d; font-size: 1rem;}
        .lf-pv-card p {margin: 0.2rem 0; color: #33415c; font-size: 0.88rem; line-height: 1.42;}
        .lf-pv-card .num {font-size: 1.6rem; font-weight: 850; color: #17347a;}
        .lf-pv-badge {display:inline-block; padding: 0.2rem 0.5rem; border-radius: 999px; font-size: 0.72rem; font-weight: 800; background: #eef2ff; color: #4338ca; border: 1px solid #dbe2ff;}
        .lf-pv-badge.first {background: #dcfce7; color: #15803d; border-color: #bbf7d0;}

        .lf-step {
            display:flex; gap: 0.65rem; align-items: flex-start;
            background:#ffffff; border:1px solid #e3e9f5; border-radius: 14px; padding: 0.8rem 0.9rem;
            box-shadow: 0 8px 22px rgba(23,38,84,0.05); height: 100%;
        }
        .lf-step .no {flex:0 0 auto; width: 30px; height: 30px; border-radius: 10px; color:#fff; font-weight: 900; display:inline-flex; align-items:center; justify-content:center; background: linear-gradient(135deg,#5b3fd6,#2f80ed);}
        .lf-step .bd h4 {margin:0 0 0.15rem 0; color:#0f1b3d; font-size: 0.94rem;}
        .lf-step .bd p {margin:0; color:#4b5a76; font-size: 0.83rem;}

        .lf-risk {
            display:flex; gap: 0.6rem; align-items:flex-start;
            background:#fff; border:1px solid #f3d9d9; border-left: 4px solid #ef4444; border-radius: 12px;
            padding: 0.72rem 0.85rem; box-shadow: 0 8px 20px rgba(23,38,84,0.05); height: 100%;
        }
        .lf-risk.watch {border-left-color:#f59e0b; border-color:#f5e4c3;}
        .lf-risk .bd p {margin:0; color:#3a2f2f; font-size: 0.86rem; line-height: 1.4;}
        .lf-risk .bd b {display:block; color:#0f1b3d; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.15rem;}

        /* ---------- Copilot panel (persistent right column) ---------- */
        div[data-testid="stHorizontalBlock"]:has(.lf-copilot-marker) > div[data-testid="column"]:last-child > div[data-testid="stVerticalBlock"] {
            position: sticky; top: 4.2rem; align-self: flex-start;
        }
        .lf-cop {
            background: linear-gradient(180deg,#0d1430 0%, #121a3c 55%, #171436 100%);
            border: 1px solid rgba(148,163,184,0.16); border-radius: 18px;
            padding: 0.95rem 1rem 0.6rem; box-shadow: 0 20px 50px rgba(15,23,42,0.25);
        }
        .lf-cop-head {display:flex; align-items:center; gap: 0.55rem; margin-bottom: 0.7rem;}
        .lf-cop-head .av {width: 30px; height: 30px; border-radius: 9px; background: linear-gradient(135deg,#6d5dfc,#22d3ee); display:inline-flex; align-items:center; justify-content:center; color:#fff; font-weight:900; font-size: 0.85rem;}
        .lf-cop-head b {color:#ffffff; font-size: 0.96rem; line-height:1;}
        .lf-cop-head span {color:#9fb0d6; font-size: 0.72rem;}
        .lf-cop-bubble {
            background: rgba(255,255,255,0.06); border: 1px solid rgba(148,163,184,0.14);
            border-radius: 12px; padding: 0.6rem 0.7rem; margin-bottom: 0.55rem;
            color: #e6edff; font-size: 0.85rem; line-height: 1.48; white-space: pre-wrap;
        }
        .lf-cop-bubble .who {display:block; color:#8fd3ff; font-size: 0.68rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.2rem;}
        .lf-cop-bubble.you {background: linear-gradient(135deg,#2f56c9,#4338ca); border-color: transparent; color:#eef2ff;}
        .lf-cop-bubble.you .who {color:#cdd9ff;}
        .lf-cop-meta {color:#8595bb; font-size: 0.7rem; margin: 0.1rem 0 0.4rem;}
        .lf-cop-agents {border-top: 1px solid rgba(148,163,184,0.14); margin-top: 0.35rem; padding-top: 0.55rem;}
        .lf-cop-agents .hd {color:#9fb0d6; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 800; margin-bottom: 0.4rem;}
        .lf-agent-row {display:flex; align-items:center; justify-content:space-between; padding: 0.28rem 0;}
        .lf-agent-row .nm {display:flex; align-items:center; gap:0.45rem; color:#dbe6ff; font-size: 0.8rem;}
        .lf-agent-row .nm .d {width:8px; height:8px; border-radius:999px; background:#22c55e; box-shadow:0 0 0 3px rgba(34,197,94,0.18);}
        .lf-agent-row .nm .d.ready {background:#38bdf8; box-shadow:0 0 0 3px rgba(56,189,248,0.18);}
        .lf-agent-row .nm .d.mon {background:#f59e0b; box-shadow:0 0 0 3px rgba(245,158,11,0.18);}
        .lf-agent-row .st {color:#9fb0d6; font-size: 0.72rem; font-weight: 700;}

        /* Scope buttons/inputs inside the copilot column to the dark theme */
        div[data-testid="stHorizontalBlock"]:has(.lf-copilot-marker) > div[data-testid="column"]:last-child .stButton button {
            background: rgba(255,255,255,0.08); color:#eaf0ff; border: 1px solid rgba(148,163,184,0.22);
            border-radius: 10px; font-size: 0.78rem; font-weight: 600; padding: 0.3rem 0.5rem; box-shadow:none;
        }
        div[data-testid="stHorizontalBlock"]:has(.lf-copilot-marker) > div[data-testid="column"]:last-child .stButton button:hover {
            border-color: #6d5dfc; color:#fff;
        }
        div[data-testid="stHorizontalBlock"]:has(.lf-copilot-marker) > div[data-testid="column"]:last-child .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #6d5dfc 0%, #2f80ed 100%) !important;
            color: #ffffff !important;
            border: 0 !important;
            box-shadow: 0 12px 24px rgba(69,89,255,0.28) !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.lf-copilot-marker) > div[data-testid="column"]:last-child .stButton button[kind="primary"]:hover {
            background: linear-gradient(135deg, #5b4bea 0%, #2563eb 100%) !important;
            color: #ffffff !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.lf-copilot-marker) > div[data-testid="column"]:last-child div[data-testid="stTextInput"] input {
            background: rgba(255,255,255,0.08); color:#fff; border:1px solid rgba(148,163,184,0.22); border-radius: 10px;
        }
        div[data-testid="stHorizontalBlock"]:has(.lf-copilot-marker) > div[data-testid="column"]:last-child div[data-testid="stTextInput"] input::placeholder {color: rgba(226,232,240,0.5);}

        @media (max-width: 1100px) {
            .lf-pv-grid {grid-template-columns: 1fr;}
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


def money(pack, value: float) -> str:
    return as_money(value, pack.currency_symbol)


def section_header(title: str, eyebrow: str = "", note: str = "") -> None:
    eyebrow_html = f"<span class='lf-eyebrow'>{escape(eyebrow)}</span>" if eyebrow else ""
    note_html = f"<p>{escape(note)}</p>" if note else ""
    st.markdown(
        f"""
        <div class='lf-section'>
            <div>
                {eyebrow_html}
                <h3>{escape(title)}</h3>
                {note_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_bar(label: str, value: float, max_value: float = 100, note: str = "") -> None:
    pct = 0 if max_value <= 0 else max(0, min(100, (value / max_value) * 100))
    display_value = round(value, 1) if value % 1 else int(value)
    suffix = "/" + str(int(max_value)) if max_value != 100 else "%"
    st.markdown(
        f"""
        <div>
            <div class='lf-scorebar-label'>
                <span>{escape(label)}</span>
                <b>{escape(str(display_value))}{escape(suffix)}</b>
            </div>
            <div class='lf-scorebar'><span style='width:{pct:.0f}%'></span></div>
            <div class='lf-small'>{escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, note: str = "", icon: str = "", tone: str = "") -> None:
    tone_class = f" tone-{tone}" if tone else ""
    icon_html = f"<div class='lf-icon-tile{tone_class}'>{escape(str(icon))}</div>" if icon else ""
    st.markdown(
        f"""
        <div class='lf-kpi'>
            {icon_html}
            <div class='lf-kpi-body'>
                <div class='lf-kpi-label'>{escape(str(label))}</div>
                <div class='lf-kpi-value'>{escape(str(value))}</div>
                <div class='lf-kpi-note{tone_class}'>{escape(str(note))}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pipeline_map() -> None:
    steps = [
        ("Founder Input", "brief, budget, stage"),
        ("Orchestrator", "routes context"),
        ("Specialists", "market, offer, finance"),
        ("MCP Tools", "structured artefacts"),
        ("Risk Critic", "caps confidence"),
        ("Launch Pack", "dashboard + export"),
    ]
    cards = "".join(
        f"<div class='lf-flow-step'><b>{escape(title)}</b><span class='lf-small'>{escape(note)}</span></div>"
        for title, note in steps
    )
    st.markdown(f"<div class='lf-mini-flow'>{cards}</div>", unsafe_allow_html=True)


def render_hero(pack, type_name: str, startup_total: float) -> None:
    st.markdown(
        f"""
        <div class='lf-hero'>
            <h1>LaunchForge</h1>
            <div class='lf-subtitle'>{APP_TAGLINE}</div>
            <div class='lf-badges'>
                <span class='lf-badge'>{escape(type_name)}</span>
                <span class='lf-badge'>Adaptive execution pack</span>
                <span class='lf-badge'>{escape(pack.launch_readiness_label)}</span>
                <span class='lf-badge'>{escape(pack.currency_code)} {escape(pack.currency_symbol)}</span>
                <span class='lf-badge'>{escape(pack.input.stage)}</span>
                <span class='lf-badge'>{escape(pack.runtime_status.get('mode', 'deterministic-fallback'))}</span>
            </div>
            <div class='lf-readiness-shell'>
                <div>
                    <div class='lf-scorebar-label'><span>Launch readiness</span><b>{pack.readiness_score}/100</b></div>
                    <div class='lf-scorebar'><span style='width:{pack.readiness_score}%'></span></div>
                </div>
                <span class='lf-badge'>{escape(pack.runtime_status.get('provider', 'fallback'))}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(5)
    readiness_tone = "success" if pack.readiness_score >= 70 else "warning" if pack.readiness_score >= 40 else "danger"
    confidence_tone = "success" if pack.classification.confidence >= 0.7 else "warning" if pack.classification.confidence >= 0.4 else "danger"
    kpis = [
        ("Business Type", type_name, f"{pack.classification.confidence:.0%} confidence", "◆", confidence_tone),
        ("Readiness", f"{pack.readiness_score}/100", pack.launch_readiness_label, "%", readiness_tone),
        ("Startup Cost", money(pack, startup_total), "Planning estimate", pack.currency_symbol, "neutral"),
        ("Break-even", str(pack.breakeven_month), "Cumulative cashflow", "#", "neutral"),
        ("Currency", pack.currency_code, pack.currency_symbol, pack.currency_symbol, "neutral"),
    ]
    for col, (label, value, note, icon, tone) in zip(cols, kpis):
        with col:
            render_metric_card(label, str(value), str(note), icon=icon, tone=tone)


def render_chips(items: list[str]) -> None:
    chips = "".join(f"<span class='lf-chip'>{escape(item)}</span>" for item in items)
    st.markdown(chips, unsafe_allow_html=True)


def render_agent_trace(pack) -> None:
    cols = st.columns(5, gap="small")
    for index, item in enumerate(pack.agent_trace):
        with cols[index % 5]:
            st.markdown(
                f"""
                <div class='lf-agent'>
                    <div class='lf-status'>{escape(item.get('status', 'completed').title())}</div>
                    <h4>{escape(item.get('agent', 'Agent'))}</h4>
                    <div class='lf-small'>{escape(item.get('summary', 'Completed specialist step.'))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_canvas(canvas: dict[str, list[str]]) -> None:
    keys = list(canvas.keys())
    for row_start in range(0, len(keys), 3):
        cols = st.columns(3, gap="medium")
        for col, key in zip(cols, keys[row_start : row_start + 3]):
            with col:
                items = "".join(f"<li>{escape(str(item))}</li>" for item in canvas[key])
                st.markdown(f"<div class='lf-canvas'><h5>{escape(key)}</h5><ul>{items}</ul></div>", unsafe_allow_html=True)


def render_personas(pack) -> None:
    cols = st.columns(min(3, len(pack.personas)), gap="medium")
    for col, persona in zip(cols, pack.personas):
        with col:
            st.markdown(
                f"""
                <div class='lf-card'>
                    <span class='lf-eyebrow'>Persona</span>
                    <h4>{escape(persona.name)}</h4>
                    <div class='lf-small'>{escape(persona.segment)}</div>
                    <p><b>Pain</b><br>{escape(persona.pains[0] if persona.pains else 'Needs a better option')}</p>
                    <p><b>Goal</b><br>{escape(persona.goals[0] if persona.goals else 'Make progress quickly')}</p>
                    <p><b>Trigger</b><br>{escape(persona.buying_trigger)}</p>
                    <div>{''.join(f"<span class='lf-chip'>{escape(channel)}</span>" for channel in persona.channels)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_offer_ladder(pack) -> None:
    cols = st.columns([1, 0.12, 1, 0.12, 1], gap="small")
    for index, offer in enumerate(pack.offer_ladder[:3]):
        with cols[index * 2]:
            deliverables = "".join(f"<li>{escape(item)}</li>" for item in offer.deliverables)
            st.markdown(
                f"""
                <div class='lf-stage'>
                <div class='lf-stage-number'>{index + 1}</div>
                <h4>{escape(offer.name)}</h4>
                <p>{escape(offer.description)}</p>
                <ul class='lf-list'>{deliverables}</ul>
                <span class='lf-small'>Metric: {escape(offer.success_metric)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if index < 2:
            with cols[index * 2 + 1]:
                st.markdown("<div class='lf-arrow'>&rarr;</div>", unsafe_allow_html=True)


def render_capstone_evidence() -> None:
    items = [
        ("LLM agents", "12 registered ADK/LlmAgent-style specialists with no-key fallback."),
        ("MCP tools", "Structured tools for scoring, scenarios, funnels, capacity, critique, and export."),
        ("Skills", "Reusable Python skills plus .agents policies for repeatable agent behaviours."),
        ("Security", "Prompt-injection checks, PII redaction, privacy mode, and env-only keys."),
        ("Deployable", "Runs locally, on Streamlit Community Cloud, or with Docker."),
    ]
    cols = st.columns(len(items), gap="small")
    for col, (title, text) in zip(cols, items):
        with col:
            st.markdown(f"<div class='lf-proof'><b>{title}</b><br><span class='lf-small'>{text}</span></div>", unsafe_allow_html=True)


def render_funnel(stages: list[str]) -> None:
    if len(stages) == 5:
        cols = st.columns([1, 0.11, 1, 0.11, 1, 0.11, 1, 0.11, 1], gap="small")
        for index, stage in enumerate(stages):
            with cols[index * 2]:
                st.markdown(f"<div class='lf-funnel'><b>{index + 1}</b><br>{escape(stage)}</div>", unsafe_allow_html=True)
            if index < len(stages) - 1:
                with cols[(index * 2) + 1]:
                    st.markdown("<div class='lf-arrow'>&rarr;</div>", unsafe_allow_html=True)
    else:
        cols = st.columns(len(stages))
        for index, (col, stage) in enumerate(zip(cols, stages), start=1):
            with col:
                st.markdown(f"<div class='lf-funnel'><b>{index}</b><br>{escape(stage)}</div>", unsafe_allow_html=True)


def render_pricing_cards(pack) -> None:
    cols = st.columns(min(3, len(pack.pricing)), gap="medium")
    for col, tier in zip(cols, pack.pricing):
        with col:
            includes = "".join(f"<li>{escape(item)}</li>" for item in tier.includes)
            st.markdown(
                f"""
                <div class='lf-card'>
                    <span class='lf-eyebrow'>Pricing Tier</span>
                    <h4>{escape(tier.tier)}</h4>
                    <div class='lf-price'>{money(pack, tier.price)}</div>
                    <div class='lf-small'>per {escape(tier.unit)}</div>
                    <ul class='lf-list'>{includes}</ul>
                    <p><b>Why:</b> {escape(tier.rationale)}</p>
                    <p><b>Use when:</b> {escape(tier.when_to_use)}</p>
                    <p><b>Upgrade:</b> {escape(tier.upgrade_path)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_assumption_cards(pack) -> None:
    cols = st.columns(4, gap="small")
    for col, key in zip(cols, ["revenue", "costs", "conversion", "break_even"]):
        assumptions = pack.cashflow_assumptions.get(key, [])
        with col:
            items = "".join(f"<li>{escape(item)}</li>" for item in assumptions)
            st.markdown(
                f"<div class='lf-card'><h4>{escape(key.replace('_', ' ').title())}</h4><ul class='lf-list'>{items}</ul></div>",
                unsafe_allow_html=True,
            )


def render_agent_system_summary(pack) -> None:
    status = pack.runtime_status
    cols = st.columns(4, gap="small")
    mode_tone = "success" if status.get("mode") == "ai-assisted" else "neutral"
    items = [
        ("Runtime Mode", status.get("mode", "deterministic-fallback"), status.get("reason", ""), "M", mode_tone),
        ("Provider", status.get("provider", "fallback"), "Copilot runtime provider", "P", "neutral"),
        ("Model", status.get("model", "gemini-2.5-flash"), "Selected Gemini model", "G", "neutral"),
        ("API Key", "Present" if status.get("api_key_available") else "Not set", "No key required for demo", "K", "success" if status.get("api_key_available") else "warning"),
    ]
    for col, (label, value, note, icon, tone) in zip(cols, items):
        with col:
            render_metric_card(label, value, note, icon=icon, tone=tone)
    cols = st.columns(4, gap="small")
    items = [
        ("ADK Available", "Yes" if status.get("adk_available") else "No", "Optional LlmAgent bridge", "A", "success" if status.get("adk_available") else "warning"),
        ("GenAI Available", "Yes" if status.get("genai_available") else "No", "Direct Gemini Copilot path", "G", "success" if status.get("genai_available") else "warning"),
        ("Trace Events", str(len(pack.execution_trace)), "LLM agent and tool events", "T", "neutral"),
        ("Last Copilot", st.session_state.get("copilot_answer", {}).get("provider", "Not asked"), st.session_state.get("copilot_answer", {}).get("mode", "Ask Copilot to populate"), "C", "neutral"),
    ]
    for col, (label, value, note, icon, tone) in zip(cols, items):
        with col:
            render_metric_card(label, value, note, icon=icon, tone=tone)


def render_artefact_chips(pack) -> None:
    names = [
        "Segment Scores",
        "Offer Fit",
        "Pricing Scenarios",
        "Funnel Model",
        "Capacity Model",
        "Scenario Forecasts",
        "Red-Team Critique",
        "Roadmap Priorities",
    ]
    render_chips(names)


def render_segment_scores(pack) -> None:
    cols = st.columns(min(3, len(pack.segment_scores)), gap="medium")
    for col, row in zip(cols, pack.segment_scores):
        with col:
            badge = "Recommended first" if row.get("recommended_first_segment") else "Secondary segment"
            score = float(row.get("overall_score", 0) or 0)
            score_pct = max(0, min(100, score / 5 * 100))
            st.markdown(
                f"""
                <div class='lf-card'>
                    <span class='lf-eyebrow'>{escape(badge)}</span>
                    <h4>{escape(row.get('persona_name', 'Segment'))}</h4>
                    <div class='lf-scorebar-label'><span>Overall segment fit</span><b>{score:.1f}/5</b></div>
                    <div class='lf-scorebar'><span style='width:{score_pct:.0f}%'></span></div>
                    <p>{escape(row.get('rationale', ''))}</p>
                    <div>
                        <span class='lf-chip'>Pain {row.get('pain_intensity')}</span>
                        <span class='lf-chip'>Reach {row.get('reachability')}</span>
                        <span class='lf-chip'>Urgency {row.get('urgency')}</span>
                        <span class='lf-chip'>Pay {row.get('willingness_to_pay')}</span>
                        <span class='lf-chip'>Control {row.get('buyer_control')}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_offer_fit_scores(pack) -> None:
    cols = st.columns(min(3, len(pack.offer_fit_scores)), gap="medium")
    for col, row in zip(cols, pack.offer_fit_scores):
        with col:
            score = float(row.get("overall_offer_score", 0) or 0)
            score_pct = max(0, min(100, score / 5 * 100))
            st.markdown(
                f"""
                <div class='lf-card'>
                    <span class='lf-eyebrow'>Offer Fit</span>
                    <h4>{escape(row.get('offer_name', 'Offer'))}</h4>
                    <div class='lf-scorebar-label'><span>Overall offer fit</span><b>{score:.1f}/5</b></div>
                    <div class='lf-scorebar'><span style='width:{score_pct:.0f}%'></span></div>
                    <p>{escape(row.get('rationale', ''))}</p>
                    <div>
                        <span class='lf-chip'>Pain {row.get('customer_pain_match')}</span>
                        <span class='lf-chip'>Feasible {row.get('delivery_feasibility')}</span>
                        <span class='lf-chip'>Diff {row.get('differentiation')}</span>
                        <span class='lf-chip'>Revenue {row.get('revenue_potential')}</span>
                        <span class='lf-chip'>Complexity {row.get('operational_complexity')}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_pricing_scenarios(pack) -> None:
    cols = st.columns(min(3, len(pack.pricing_scenarios)), gap="medium")
    for col, row in zip(cols, pack.pricing_scenarios):
        with col:
            st.markdown(
                f"""
                <div class='lf-card'>
                    <span class='lf-eyebrow'>Scenario</span>
                    <h4>{escape(row.get('tier', 'Tier'))}</h4>
                    <div class='lf-price'>{escape(str(row.get('recommended_price', '')))}</div>
                    <p>{escape(row.get('sensitivity_note', ''))}</p>
                    <div>
                        <span class='lf-chip'>Low {money(pack, row.get('low_price', 0))}</span>
                        <span class='lf-chip'>Base {money(pack, row.get('base_price', 0))}</span>
                        <span class='lf-chip'>Premium {money(pack, row.get('premium_price', 0))}</span>
                    </div>
                    <p><b>Conversion:</b> {row.get('expected_conversion_rate', 0):.0%} | <b>Margin:</b> {row.get('estimated_margin', 0):.0%}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_scenario_forecasts(pack) -> None:
    scenario_data = pack.scenario_forecasts.get("scenarios", [])
    if scenario_data:
        try:
            import plotly.express as px

            rows = []
            for scenario in scenario_data:
                for month, value in enumerate(scenario["cumulative_cashflow"], start=1):
                    rows.append({"scenario": scenario["scenario"].title(), "month": month, "cumulative_cashflow": value})
            fig = px.line(pd.DataFrame(rows), x="month", y="cumulative_cashflow", color="scenario", markers=True, title="Scenario Cumulative Cashflow")
            fig.update_traces(line=dict(width=3), marker=dict(size=8))
            fig.update_layout(height=330, legend=dict(orientation="h", y=1.08, x=1, xanchor="right"), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.dataframe(pd.DataFrame(scenario_data), hide_index=True, use_container_width=True)
    cols = st.columns(4, gap="medium")
    cards = [
        ("Break-even Probability", f"{pack.scenario_forecasts.get('breakeven_probability', 0):.0%}", "Scenarios breaking even by month 3"),
        ("Worst-case Gap", money(pack, pack.scenario_forecasts.get("worst_case_gap", 0)), "Lowest cumulative cash position"),
        ("Upside Case", str(pack.scenario_forecasts.get("upside_case", "n/a")).title(), pack.scenario_forecasts.get("key_assumption_to_validate", "")),
        ("Validate First", str(pack.scenario_forecasts.get("key_assumption_to_validate", "conversion rate")), "Key assumption"),
    ]
    for col, (label, value, note) in zip(cols, cards):
        with col:
            render_metric_card(label, value, note)


def render_funnel_model(pack) -> None:
    rows = pack.funnel_model
    cols = st.columns(min(3, len(rows)), gap="small")
    for index, row in enumerate(rows):
        with cols[index % len(cols)]:
            bottleneck = "Bottleneck" if row.get("bottleneck") else "Stage"
            st.markdown(
                f"""
                <div class='lf-card'>
                    <span class='lf-eyebrow'>{escape(bottleneck)}</span>
                    <h4>{escape(row.get('stage_name', 'Stage'))}</h4>
                    <div class='lf-price'>{row.get('conversion_rate', 0):.0%}</div>
                    <p>{escape(row.get('stage_objective', ''))}</p>
                    <p><b>{row.get('starting_volume')}</b> in &rarr; <b>{row.get('output_volume')}</b> out</p>
                    <p>{escape(row.get('improvement_recommendation', ''))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_capacity_model(pack) -> None:
    capacity = pack.capacity_model
    cols = st.columns(4, gap="small")
    metrics = [
        ("Weekly Hours", capacity.get("founder_hours_available_per_week", 0), "Founder capacity"),
        ("Admin Hours", capacity.get("admin_hours_required", 0), "Weekly overhead"),
        ("Delivery Hours", capacity.get("delivery_hours_required", 0), "Fulfilment load"),
        ("Max Volume", capacity.get("max_customers_or_orders_per_week", 0), "Weekly customers/orders"),
    ]
    for col, (label, value, note) in zip(cols, metrics):
        with col:
            st.markdown(f"<div class='lf-kpi'><div class='lf-kpi-label'>{escape(label)}</div><div class='lf-kpi-value'>{escape(str(value))}</div><div class='lf-kpi-note'>{escape(note)}</div></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class='lf-card'>
            <span class='lf-eyebrow'>Operational Bottleneck</span>
            <h4>{escape(capacity.get('bottleneck', ''))}</h4>
            <p><b>Risk:</b> {escape(capacity.get('operational_risk', ''))}</p>
            <p><b>Recommended system:</b> {escape(capacity.get('recommended_system', ''))}</p>
            <p><b>Scaling constraint:</b> {escape(capacity.get('scaling_constraint', ''))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_red_team(pack) -> None:
    critic = pack.critic_red_team
    cols = st.columns(3, gap="medium")
    for col, key in zip(cols, ["missing_evidence", "top_3_failure_modes", "validation_tests"]):
        with col:
            items = "".join(f"<li>{escape(item)}</li>" for item in critic.get(key, []))
            st.markdown(f"<div class='lf-card'><span class='lf-eyebrow'>Critic</span><h4>{escape(key.replace('_', ' ').title())}</h4><ul class='lf-list'>{items}</ul></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='lf-disclaimer'>{escape(critic.get('readiness_cap_reason', ''))}</div>", unsafe_allow_html=True)


def render_roadmap_priorities(pack) -> None:
    for row in pack.roadmap_priority_scores:
        st.markdown(
            f"""
            <div class='lf-card'>
                <div class='lf-day'>Day {row.get('day')}</div>
                <h4>{escape(row.get('title', 'Task'))}</h4>
                <div>
                    <span class='lf-chip'>Priority {row.get('priority_score')}</span>
                    <span class='lf-chip'>Impact {row.get('impact')}</span>
                    <span class='lf-chip'>Effort {row.get('effort')}</span>
                    <span class='lf-chip'>Urgency {row.get('urgency')}</span>
                    <span class='lf-chip'>Risk reduction {row.get('risk_reduction')}</span>
                </div>
                <p><b>Dependency:</b> {escape(str(row.get('dependency', 'None')))}</p>
                <p>{escape(row.get('rationale', ''))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_execution_trace(pack) -> None:
    for index, event in enumerate(pack.execution_trace, start=1):
        type_label = "LLM Agent" if event.get("type") == "llm_agent" else "Tool"
        tools = ", ".join(event.get("tools_called") or [])
        st.markdown(
            f"""
            <div class='lf-trace-event'>
                <span class='lf-trace-step'>{index}</span>
                <span class='lf-eyebrow'>{escape(type_label)} / {escape(str(event.get('mode', '')))}</span>
                <h4>{escape(str(event.get('name', 'Trace Event')))}</h4>
                <p><b>Status:</b> {escape(str(event.get('status', '')))} &nbsp; <b>Tools:</b> {escape(tools or 'None')}</p>
                <p><b>Output:</b> {escape(str(event.get('output_summary', '')))}</p>
                <p><b>Visible reasoning:</b> {escape(str(event.get('visible_reasoning_summary', '')))}</p>
                <p class='lf-small'>{escape(str(event.get('limitations', '')))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_copilot_panel(pack) -> None:
    st.session_state.setdefault("copilot_question_text", "")
    st.markdown(
        """
        <div class='lf-card'>
            <span class='lf-eyebrow'>Platform Guide</span>
            <h4>Ask about the dashboard, agents, tools, or this launch pack</h4>
            <p>Copilot can define tabs and metrics, explain agent/tool behaviour, interpret readiness, finance, funnel, roadmap, risks, and suggest what to review next. Fallback mode uses platform knowledge and current launch-pack data without external calls.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    quick_questions = [
        "What is the Overview tab?",
        "How do I use this dashboard?",
        "What is the Agent Control Room?",
        "What are agents vs tools?",
        "Why is my readiness score?",
        "What should I do first?",
        "Which funnel stage is weakest?",
        "What did the Critic Agent flag?",
    ]
    cols = st.columns(4, gap="small")
    for index, question in enumerate(quick_questions):
        with cols[index % 4]:
            if st.button(question, use_container_width=True, key=f"quick_v2_{question}"):
                st.session_state["copilot_question_text"] = question
    question = st.text_input(
        "Ask LaunchForge Copilot",
        key="copilot_question_text",
        placeholder="Ask about tabs, KPI cards, agents, tools, readiness, pricing, finance, funnel, roadmap, risks, or exports...",
    )
    if st.button("Ask Copilot", type="primary", use_container_width=True):
        st.session_state["copilot_answer"] = answer_copilot_question(question, pack)
    answer = st.session_state.get("copilot_answer")
    if answer:
        status = "Blocked" if answer.get("blocked") else "Answered"
        tools = ", ".join(answer.get("tools_called") or ["None"])
        context_used = ", ".join(answer.get("context_used") or ["fallback routing"])
        response_label = answer.get("response_label") or f"Copilot - {answer.get('mode', 'deterministic-fallback')}"
        provider = answer.get("provider", "fallback")
        model = answer.get("model", "")
        fallback_reason = answer.get("fallback_reason") or answer.get("error") or "None"
        st.markdown(
            f"""
            <div class='lf-card'>
                <span class='lf-eyebrow'>{escape(response_label)} - {escape(status)}</span>
                <h4>Grounded response</h4>
                <p class='lf-copilot-answer'>{escape(answer.get('answer', ''))}</p>
                <p class='lf-small'><b>Provider:</b> {escape(provider)}<br><b>Model:</b> {escape(model)}<br><b>Tools called:</b> {escape(tools)}<br><b>Context used:</b> {escape(context_used)}<br><b>Fallback reason:</b> {escape(fallback_reason)}<br><b>Question:</b> {escape(str(answer.get('redacted_question', '')))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_global_copilot_bar(pack) -> None:
    st.session_state.setdefault("global_copilot_question_text", "")
    answer = st.session_state.get("global_copilot_answer") or st.session_state.get("copilot_answer")
    if answer:
        status = "Blocked" if answer.get("blocked") else "Answered"
        mode = answer.get("mode", "deterministic-fallback")
        mode_label = "AI-assisted" if mode == "ai-assisted" else "Deterministic fallback"
        if mode == "fallback after ai error":
            mode_label = "Fallback after AI error"
        tools = ", ".join(answer.get("tools_called") or ["None"])
        context_used = ", ".join(answer.get("context_used") or ["fallback routing"])
        provider = answer.get("provider", "fallback")
        st.markdown(
            f"""
            <div class='lf-copilot-response'>
                <span class='lf-eyebrow'>Copilot / {escape(mode_label)} / {escape(status)}</span>
                <p class='lf-copilot-answer'>{escape(answer.get('answer', ''))}</p>
                <p class='lf-small'><b>Provider:</b> {escape(provider)} &nbsp; <b>Tools:</b> {escape(tools)} &nbsp; <b>Context:</b> {escape(context_used)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class='lf-copilot-dock'>
            <h4>LaunchForge Copilot</h4>
            <p>Ask LaunchForge Copilot about this dashboard, the agents, or your launch pack...</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns([6, 1.2], gap="small")
    with cols[0]:
        question = st.text_input(
            "Ask LaunchForge Copilot anywhere",
            key="global_copilot_question_text",
            label_visibility="collapsed",
            placeholder="Ask about readiness, finance assumptions, the agent trace, funnel bottlenecks, or next actions...",
        )
    with cols[1]:
        if st.button("Ask", type="primary", use_container_width=True, key="global_copilot_ask"):
            if question.strip():
                st.session_state["global_copilot_answer"] = answer_copilot_question(question, pack)
                st.session_state["copilot_answer"] = st.session_state["global_copilot_answer"]


def render_agent_control_room(pack) -> None:
    section_header("Runtime Status", "ADK Runtime", "LaunchForge uses ADK/LlmAgent definitions when configured and deterministic fallback otherwise.")
    render_agent_system_summary(pack)
    section_header("Architecture Flow", "Control Centre", "Founder input moves through orchestrated agents, deterministic tools, critic review, and exportable artefacts.")
    render_pipeline_map()
    st.markdown(
        """
        <div class='lf-card'>
            <span class='lf-eyebrow'>Why Agents?</span>
            <p>LaunchForge uses agents because launching a business requires separate specialist decisions: customer selection, offer design, pricing, marketing, operations, finance, roadmap planning, and critical review. A single generic assistant tends to flatten these decisions. LaunchForge separates reasoning into specialist agents, gives them reliable tools, and records what each agent produced.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_header("LLM Agent Team", "Agent Studio", "Registered ADK/LlmAgent definitions and their fallback status.")
    agent_cols = st.columns(3, gap="medium")
    for index, agent in enumerate(pack.agent_trace):
        with agent_cols[index % 3]:
            st.markdown(
                f"""
                <div class='lf-card'>
                    <span class='lf-eyebrow'>{escape(str(agent.get('mode', 'deterministic-fallback')))}</span>
                    <h4>{escape(str(agent.get('agent', 'Agent')))}</h4>
                    <p><b>Instruction:</b> {escape(str(agent.get('instruction_summary', '')))}</p>
                    <p><b>Tools:</b> {escape(', '.join(agent.get('tools_available') or []))}</p>
                    <p><b>Latest output:</b> {escape(str(agent.get('summary', '')))}</p>
                    <p class='lf-small'>{escape(str(agent.get('limitations', '')))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    section_header("Tool / Skill Layer", "MCP-style Tools", "Deterministic functions compute reliable artefacts that agents can call.")
    tool_cols = st.columns(3, gap="medium")
    for index, tool in enumerate(pack.tool_registry):
        with tool_cols[index % 3]:
            st.markdown(
                f"""
                <div class='lf-card'>
                    <span class='lf-eyebrow'>Tool</span>
                    <h4>{escape(tool.get('tool_name', 'tool'))}</h4>
                    <p>{escape(tool.get('computes', ''))}</p>
                    <p class='lf-small'>Used by: {escape(tool.get('used_by', ''))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    section_header("Execution Trace", "Trace", "LLM agent definitions and deterministic tool calls are deliberately separate.")
    render_execution_trace(pack)
    section_header("LaunchForge Copilot", "Grounded Q&A", "Ask questions about the platform, dashboard elements, agents, tools, and current launch pack. Fallback mode works without API keys.")
    render_copilot_panel(pack)


def render_next_actions(pack) -> None:
    cols = st.columns(3, gap="medium")
    for index, (col, action) in enumerate(zip(cols, pack.next_3_actions), start=1):
        with col:
            st.markdown(
                f"<div class='lf-action'><div class='lf-day'>{index}</div><h4>{escape(action)}</h4></div>",
                unsafe_allow_html=True,
            )


def render_roadmap(pack) -> None:
    columns_html = []
    for week in range(1, 5):
        tasks = [task for task in pack.roadmap if task.week == week]
        cards = "".join(
            f"""
            <div class='lf-roadmap-card'>
                <div class='lf-day'>Day {task.day}</div>
                <h4>{escape(task.title)}</h4>
                <p>{escape(task.outcome)}</p>
                <span class='lf-chip'>{escape(task.category)}</span>
            </div>
            """
            for task in tasks
        )
        columns_html.append(
            f"""
            <div class='lf-roadmap-column'>
                <span class='lf-eyebrow'>Week {week}</span>
                {cards}
            </div>
            """
        )
    st.markdown(f"<div class='lf-roadmap-board'>{''.join(columns_html)}</div>", unsafe_allow_html=True)


# =====================================================================
# PRODUCT VIEW (new primary, user-facing dashboard)
# =====================================================================

PRODUCT_SECTIONS = ["Overview", "Opportunities", "Market", "Finance", "Action Plan", "Export"]


def _tone_for(score: float) -> str:
    if score >= 70:
        return "success"
    if score >= 40:
        return "warning"
    return "danger"


def _gauge_svg(score: int, tone: str) -> str:
    palette = {
        "success": ("#16a34a", "#22c55e"),
        "warning": ("#d97706", "#f59e0b"),
        "danger": ("#dc2626", "#ef4444"),
    }
    c1, c2 = palette.get(tone, ("#2563eb", "#6d5dfc"))
    score = max(0, min(100, int(score)))
    return (
        f"<svg viewBox='0 0 220 128' width='240' height='140' role='img' aria-label='Business potential {score} percent'>"
        "<defs><linearGradient id='lf-gauge' x1='0' y1='0' x2='1' y2='0'>"
        f"<stop offset='0' stop-color='{c1}'/><stop offset='1' stop-color='{c2}'/>"
        "</linearGradient></defs>"
        "<path d='M18 110 A 92 92 0 0 1 202 110' fill='none' stroke='#e6ebf5' stroke-width='18' stroke-linecap='round'/>"
        f"<path d='M18 110 A 92 92 0 0 1 202 110' fill='none' stroke='url(#lf-gauge)' stroke-width='18' stroke-linecap='round' pathLength='100' stroke-dasharray='{score} 100'/>"
        f"<text x='110' y='98' text-anchor='middle' font-size='42' font-weight='800' fill='#0f1b3d'>{score}%</text>"
        "<text x='110' y='120' text-anchor='middle' font-size='12.5' fill='#52627f'>out of 100</text>"
        "</svg>"
    )


def render_topbar(pack) -> None:
    status = pack.runtime_status
    is_ai = status.get("mode") == "ai-assisted"
    pill_class = "" if is_ai else "amber"
    mode_label = "AI-assisted" if is_ai else "Guided fallback"
    provider = escape(str(status.get("provider", "fallback")))
    st.markdown(
        f"""
        <div class='lf-topbar'>
            <div class='lf-topbar-brand'>
                <span class='lf-topbar-logo'>LF</span>
                <div><b>LaunchForge</b><span>Business Launch Command Centre</span></div>
            </div>
            <div class='lf-topbar-title'>Your AI Business Co-Pilot</div>
            <div class='lf-topbar-right'>
                <span class='lf-pill {pill_class}'><span class='dot'></span>{mode_label} · {provider}</span>
                <span class='lf-pill'>{escape(pack.currency_code)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_topbar_static() -> None:
    """Topbar for the pre-generation landing state (no pack yet)."""
    st.markdown(
        """
        <div class='lf-topbar'>
            <div class='lf-topbar-brand'>
                <span class='lf-topbar-logo'>LF</span>
                <div><b>LaunchForge</b><span>Business Launch Command Centre</span></div>
            </div>
            <div class='lf-topbar-title'>Your AI Business Co-Pilot</div>
            <div class='lf-topbar-right'>
                <span class='lf-pill amber'><span class='dot'></span>Awaiting brief</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_business_score_card(pack, type_name: str) -> None:
    tone = _tone_for(pack.readiness_score)
    html = (
        "<div class='lf-panel'>"
        "<div class='lf-panel-title'><h3>Business Potential Score</h3><span class='lf-tag'>Launch readiness</span></div>"
        "<div class='lf-gauge-wrap'>"
        f"{_gauge_svg(pack.readiness_score, tone)}"
        f"<div class='lf-gauge-chip {tone}'>{escape(pack.launch_readiness_label)}</div>"
        f"<div class='lf-gauge-label'>{escape(type_name)} / {pack.classification.confidence:.0%} confident this is the right model</div>"
        "</div>"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)
    return
    st.markdown(
        f"""
        <div class='lf-panel'>
            <div class='lf-panel-title'><h3>Business Potential Score</h3><span class='lf-tag'>Launch readiness</span></div>
            <div class='lf-gauge-wrap'>
                {_gauge_svg(pack.readiness_score, tone)}
                <div class='lf-gauge-chip {tone}'>{escape(pack.launch_readiness_label)}</div>
                <div class='lf-gauge-label'>{escape(type_name)} · {pack.classification.confidence:.0%} confident this is the right model</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insights_panel(pack) -> None:
    rows: list[tuple[str, str, str]] = []
    for strength in pack.readiness_strengths[:3]:
        rows.append(("op", "&#9650;", strength))
    for gap in pack.readiness_gaps[:2]:
        rows.append(("warn", "!", gap))
    if pack.risks:
        rows.append(("risk", "!", pack.risks[0]))
    body = "".join(
        f"<div class='lf-ins'><span class='ic {cls}'>{icon}</span><span class='tx'>{escape(text)}</span></div>"
        for cls, icon, text in rows
    )
    st.markdown(
        f"""
        <div class='lf-panel'>
            <div class='lf-panel-title'><h3>Key Insights &amp; Opportunities</h3><span class='lf-tag'>What matters now</span></div>
            {body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_strip(pack, type_name: str, startup_total: float) -> None:
    confidence = pack.classification.confidence
    conf_tone = "success" if confidence >= 0.7 else "warning" if confidence >= 0.4 else "danger"
    first_segment = _first_segment_name(pack)
    cards = [
        ("Startup budget", money(pack, startup_total), "Planning estimate", ""),
        ("Break-even", f"Month {escape(str(pack.breakeven_month))}", "From cashflow model", ""),
        ("Model confidence", f"{confidence:.0%}", type_name, conf_tone),
        ("Target first", first_segment, "Recommended segment", "success"),
    ]
    html = "".join(
        f"<div class='lf-mini'><div class='k'>{escape(k)}</div><div class='v'>{v}</div><div class='n {tone}'>{escape(n)}</div></div>"
        for k, v, n, tone in cards
    )
    st.markdown(f"<div class='lf-mini-metrics' style='grid-template-columns:repeat(4,1fr);'>{html}</div>", unsafe_allow_html=True)


def _first_segment_name(pack) -> str:
    for row in pack.segment_scores:
        if row.get("recommended_first_segment"):
            return str(row.get("persona_name", "Primary segment"))
    if pack.segment_scores:
        return str(pack.segment_scores[0].get("persona_name", "Primary segment"))
    if pack.personas:
        return pack.personas[0].name
    return "Primary segment"


def _cumulative_forecast_fig(pack):
    try:
        import plotly.express as px

        rows = [{"Month": m.month, "Cumulative cash": m.cumulative_cashflow} for m in pack.cashflow]
        fig = px.area(pd.DataFrame(rows), x="Month", y="Cumulative cash", markers=True)
        fig.update_traces(line=dict(width=3, color="#2563eb"), marker=dict(size=7, color="#6d5dfc"), fillcolor="rgba(45,128,237,0.12)")
        fig.update_layout(
            height=250, margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#eef2f9"),
        )
        return fig
    except Exception:
        return None


def render_forecast_panel(pack, *, compact: bool = False) -> None:
    st.markdown(
        "<div class='lf-panel-title'><h3>Forecasted cash position</h3><span class='lf-tag'>Planning model</span></div>",
        unsafe_allow_html=True,
    )
    fig = _cumulative_forecast_fig(pack)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.dataframe(pd.DataFrame([model_to_dict(m) for m in pack.cashflow]), hide_index=True, use_container_width=True)
    scen = pack.scenario_forecasts
    scenarios = scen.get("scenarios", []) or []
    modelled_count = len(scenarios)
    if modelled_count:
        break_even_count = sum(1 for scenario in scenarios if scenario.get("break_even_month") != "Beyond 3 months")
        break_even_display = f"{break_even_count}/{modelled_count} scenarios"
    else:
        break_even_display = "Base model only"
    total_rev = sum(m.revenue for m in pack.cashflow)
    total_cost = sum(m.costs for m in pack.cashflow)
    cards = [
        ("Projected revenue", money(pack, total_rev), "Sum over forecast window"),
        ("Projected costs", money(pack, total_cost), "Sum over forecast window"),
        ("Break-even month", f"Month {escape(str(pack.breakeven_month))}", "Cumulative cash turns positive"),
        ("Scenario break-even", break_even_display, "Across deterministic planning scenarios; not a real-world probability"),
    ]
    html = "".join(
        f"<div class='lf-mini'><div class='k'>{escape(k)}</div><div class='v'>{v}</div><div class='n'>{escape(n)}</div></div>"
        for k, v, n in cards
    )
    st.markdown(f"<div class='lf-mini-metrics' style='grid-template-columns:repeat(4,1fr);'>{html}</div>", unsafe_allow_html=True)
    if not compact:
        st.markdown(
            f"<div class='lf-disclaimer' style='margin-top:0.7rem;'>{escape(pack.forecast_disclaimer)} These figures are planning assumptions, not financial advice.</div>",
            unsafe_allow_html=True,
        )


def render_action_plan_panel(pack, *, full: bool = False) -> None:
    st.markdown(
        "<div class='lf-panel-title'><h3>Your next moves</h3><span class='lf-tag'>Do these first</span></div>",
        unsafe_allow_html=True,
    )
    steps = "".join(
        f"<div class='lf-step'><span class='no'>{i}</span><div class='bd'><h4>{escape(action)}</h4><p>Highest-leverage step from your launch plan.</p></div></div>"
        for i, action in enumerate(pack.next_3_actions, start=1)
    )
    st.markdown(
        f"<div class='lf-mini-metrics' style='grid-template-columns:repeat(3,1fr);'>{steps}</div>",
        unsafe_allow_html=True,
    )


def render_risks_panel(pack) -> None:
    st.markdown(
        "<div class='lf-panel-title'><h3>Risks &amp; watch-outs</h3><span class='lf-tag'>Handle early</span></div>",
        unsafe_allow_html=True,
    )
    cards = []
    for risk in pack.risks[:3]:
        cards.append(f"<div class='lf-risk'><div class='bd'><b>Risk</b><p>{escape(risk)}</p></div></div>")
    for assumption in pack.assumptions[:2]:
        cards.append(f"<div class='lf-risk watch'><div class='bd'><b>Assumption to test</b><p>{escape(assumption)}</p></div></div>")
    st.markdown(
        f"<div class='lf-mini-metrics' style='grid-template-columns:repeat(3,1fr);'>{''.join(cards)}</div>",
        unsafe_allow_html=True,
    )


def render_copilot_overlay(pack) -> None:
    st.session_state.setdefault("pv_last_q", "")
    # Marker enables the sticky + dark-theme scoping CSS for this column.
    st.markdown("<div class='lf-copilot-marker'></div>", unsafe_allow_html=True)

    answer = st.session_state.get("copilot_answer")
    conversation = (
        "<div class='lf-cop-bubble'><span class='who'>Co-Pilot</span>"
        "I've analysed your idea. Ask me anything, or tap a suggestion below.</div>"
    )
    meta_html = ""
    if answer:
        last_q = st.session_state.get("pv_last_q") or answer.get("redacted_question", "")
        if last_q:
            conversation += f"<div class='lf-cop-bubble you'><span class='who'>You</span>{escape(str(last_q))}</div>"
        conversation += f"<div class='lf-cop-bubble'><span class='who'>Co-Pilot</span>{escape(str(answer.get('answer', '')))}</div>"
        mode = answer.get("mode", "deterministic-fallback")
        mode_label = "AI-assisted" if mode == "ai-assisted" else "Guided fallback"
        meta_html = f"<div class='lf-cop-meta'>{escape(mode_label)} · provider: {escape(str(answer.get('provider', 'fallback')))}</div>"

        if mode == "ai-assisted":
            mode_label = "AI-assisted"
        elif mode == "grounded-web":
            mode_label = "Web-grounded"
        elif mode == "fallback after ai error":
            mode_label = "Fallback after AI error"
        else:
            mode_label = "Guided fallback"
        sources = ", ".join(str(item).replace("_", " ").title() for item in (answer.get("sources_used") or answer.get("context_used") or []))
        citations = answer.get("citations") or []
        citation_links = " ".join(
            f"<a href='{escape(str(item.get('url', '')))}' target='_blank'>{escape(str(item.get('title', 'Source')))}</a>"
            for item in citations
            if item.get("url")
        )
        citation_html = f"<br><b>Citations:</b> {citation_links}" if citation_links else ""
        fallback_reason = answer.get("fallback_reason")
        fallback_html = f"<br><span>{escape(str(fallback_reason))}</span>" if fallback_reason else ""
        meta_html = (
            f"<div class='lf-cop-meta'>{escape(mode_label)} / provider: {escape(str(answer.get('provider', 'fallback')))}"
            f"<br><b>Sources:</b> {escape(sources or 'Launch Pack, Platform Kb')}{citation_html}{fallback_html}</div>"
        )

    completed = sum(1 for a in pack.agent_trace if str(a.get("status", "completed")).lower() == "completed")
    agents = [
        ("Market Analyst", "Active", ""),
        ("Offer Architect", "Ready", "ready"),
        ("Financial Modeler", "Ready", "ready"),
        ("Risk Critic", "Monitoring", "mon"),
    ]
    agent_rows = "".join(
        f"<div class='lf-agent-row'><span class='nm'><span class='d {dot}'></span>{escape(name)}</span><span class='st'>{escape(state)}</span></div>"
        for name, state, dot in agents
    )

    st.markdown(
        f"""
        <div class='lf-cop'>
            <div class='lf-cop-head'>
                <span class='av'>&#9673;</span>
                <div><b>Your Co-Pilot</b><br><span>LaunchForge strategist</span></div>
            </div>
            {conversation}
            {meta_html}
            <div class='lf-cop-agents'>
                <div class='hd'>Agent status · {completed} specialists ran</div>
                {agent_rows}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    prompts = [
        "What should I do first?",
        "What's my biggest risk?",
        "Who should I target?",
        "Write me a slogan",
        "Explain my forecast",
        "My first week plan",
    ]
    pcols = st.columns(2, gap="small")
    for i, prompt in enumerate(prompts):
        with pcols[i % 2]:
            if st.button(prompt, key=f"pv_quick_{i}", use_container_width=True):
                st.session_state["pv_last_q"] = prompt
                st.session_state["copilot_answer"] = answer_copilot_question(prompt, pack)
                st.rerun()

    question = st.text_input(
        "Ask your Co-Pilot",
        key="pv_copilot_input",
        label_visibility="collapsed",
        placeholder="Ask your Co-Pilot anything…",
    )
    if st.button("Ask Co-Pilot", key="pv_ask", type="primary", use_container_width=True):
        if question.strip():
            st.session_state["pv_last_q"] = question
            st.session_state["copilot_answer"] = answer_copilot_question(question, pack)
            st.rerun()


def render_compact_founder_brief_editor(has_pack: bool) -> bool:
    """Compact, collapsible founder brief inside the sidebar. Returns whether Generate was clicked."""

    st.markdown("<div class='lf-pv-nav-label'>Founder brief</div>", unsafe_allow_html=True)
    with st.expander("Edit founder brief", expanded=not has_pack):
        cols = st.columns(3, gap="small")
        preset_names = list(DEMO_INPUTS.keys())
        for col, label in zip(cols, preset_names):
            with col:
                short = label.replace(" Demo", "")
                if st.button(short, use_container_width=True, key=f"preset_{label}"):
                    load_demo(label)
                    st.rerun()
        st.text_area("Business idea", key="idea", height=120, placeholder="Describe the business you want to launch…")
        bc = st.columns(2, gap="small")
        with bc[0]:
            st.number_input("Budget", min_value=0.0, step=100.0, key="budget")
        with bc[1]:
            st.text_input("Location / online", key="location")
        st.text_area("Skills & resources", key="founder_resources", height=70)
        sc = st.columns(2, gap="small")
        with sc[0]:
            st.selectbox("Timeframe", ["7 days", "14 days", "30 days", "60 days"], index=2, key="pv_timeframe")
        with sc[1]:
            st.selectbox("Stage", ["Idea only", "Testing", "Ready to launch"], index=0, key="pv_stage")
        st.text_input("Target customer (optional)", key="target_customer")
        st.toggle("Do not store my idea", value=True, key="pv_privacy",
                  help="Inputs stay in session memory; nothing is written to disk unless you export.")
        return st.button("Generate Launch Pack", type="primary", use_container_width=True, key="pv_generate")


def render_product_overview(pack, type_name: str, startup_total: float) -> None:
    grid = st.columns([1.15, 1], gap="large")
    with grid[0]:
        render_business_score_card(pack, type_name)
    with grid[1]:
        render_insights_panel(pack)
    st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)
    render_kpi_strip(pack, type_name, startup_total)
    st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)
    moves = st.columns(2, gap="large")
    with moves[0]:
        render_first_moves_customer(pack)
    with moves[1]:
        render_first_moves_offer(pack)
    st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)
    render_forecast_panel(pack, compact=True)
    st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)
    render_action_plan_panel(pack)
    st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)
    render_risks_panel(pack)


def render_first_moves_customer(pack) -> None:
    seg = None
    for row in pack.segment_scores:
        if row.get("recommended_first_segment"):
            seg = row
            break
    if seg is None and pack.segment_scores:
        seg = pack.segment_scores[0]
    name = escape(str(seg.get("persona_name", "Your first customers"))) if seg else "Your first customers"
    reason = escape(str(seg.get("rationale", ""))) if seg else "Focus on the audience with the most urgent pain."
    st.markdown(
        f"<div class='lf-pv-card'><span class='eyebrow'>Who to target first</span>"
        f"<h4>{name} <span class='lf-pv-badge first'>Start here</span></h4><p>{reason}</p></div>",
        unsafe_allow_html=True,
    )


def render_first_moves_offer(pack) -> None:
    offer = pack.offer_ladder[0] if pack.offer_ladder else None
    name = escape(offer.name) if offer else "Entry offer"
    desc = escape(offer.description) if offer else "A low-friction first offer to win early customers."
    st.markdown(
        f"<div class='lf-pv-card'><span class='eyebrow'>What to sell first</span>"
        f"<h4>{name} <span class='lf-pv-badge'>Beachhead offer</span></h4><p>{desc}</p></div>",
        unsafe_allow_html=True,
    )


def render_product_opportunities(pack) -> None:
    section_header("Best customer segments", "Where the opportunity is strongest", "Ranked by pain, reachability, willingness to pay, and buyer control.")
    render_segment_scores(pack)
    section_header("Your offer ladder", "What to sell, in order", "Start with a low-friction entry offer and grow into premium outcomes.")
    render_offer_ladder(pack)
    section_header("Offer fit", "How strong each offer is", "Scored on pain match, feasibility, differentiation, and revenue.")
    render_offer_fit_scores(pack)


def render_product_market(pack, type_name: str) -> None:
    section_header("Who you're selling to", "Customer personas", "The people most likely to buy first, and what triggers them.")
    render_personas(pack)
    section_header("First-segment recommendation", "Beachhead", "Concentrate limited budget on the highest-intent audience.")
    render_first_moves_customer(pack)
    section_header("Sales funnel", "How customers reach you", "The journey from first contact to repeat customer.")
    render_funnel(pack.sales_funnel["stages"])


def render_product_finance(pack) -> None:
    render_forecast_panel(pack)
    section_header("Where the startup budget goes", "Budget allocation", "How your initial launch budget is split across categories.")
    cost_rows = [{"category": key, "amount": value} for key, value in pack.startup_costs.items()]
    try:
        import plotly.express as px

        fig = px.pie(pd.DataFrame(cost_rows), names="category", values="amount", hole=0.5)
        fig.update_traces(textposition="inside", textinfo="percent+label", marker=dict(line=dict(color="#ffffff", width=2)))
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.dataframe(pd.DataFrame(cost_rows), hide_index=True, use_container_width=True)
    section_header("Pricing you can start with", "Pricing tiers", "Simple, defensible starting prices with room to grow.")
    render_pricing_cards(pack)


def render_product_action_plan(pack) -> None:
    render_action_plan_panel(pack, full=True)
    section_header("Your 30-day roadmap", "Week by week", "A milestone board that turns the plan into daily action.")
    render_roadmap(pack)
    section_header("Risks & watch-outs", "Handle these early", "Practical risks and assumptions to validate before scaling.")
    render_risks_panel(pack)


def render_product_export(pack) -> None:
    section_header("Take your launch pack with you", "Export centre", "Download a portable launch pack to share or keep working on.")
    markdown_export = export_markdown(pack)
    json_export = export_json(pack)
    ec = st.columns(2, gap="large")
    with ec[0]:
        st.markdown(
            "<div class='lf-pv-card'><span class='eyebrow'>Markdown</span><h4>Launch pack (readable)</h4>"
            "<p>A narrative pack for your notes, a co-founder, or an advisor.</p></div>",
            unsafe_allow_html=True,
        )
        st.download_button("Download Markdown", markdown_export, "launchforge_launch_pack.md", "text/markdown", use_container_width=True)
    with ec[1]:
        st.markdown(
            "<div class='lf-pv-card'><span class='eyebrow'>JSON</span><h4>Structured data</h4>"
            "<p>Machine-readable pack with every figure, assumption, and step.</p></div>",
            unsafe_allow_html=True,
        )
        st.download_button("Download JSON", json_export, "launchforge_launch_pack.json", "application/json", use_container_width=True)
    with st.expander("Preview the Markdown pack"):
        st.code(markdown_export[:4000], language="markdown")
    st.caption("Privacy mode keeps inputs in session memory only. Exports are created just when you click download.")


def render_product_view(pack, section: str, type_name: str, startup_total: float) -> None:
    render_topbar(pack)
    content, copilot = st.columns([2.55, 1], gap="large")
    with content:
        if section == "Overview":
            render_product_overview(pack, type_name, startup_total)
        elif section == "Opportunities":
            render_product_opportunities(pack)
        elif section == "Market":
            render_product_market(pack, type_name)
        elif section == "Finance":
            render_product_finance(pack)
        elif section == "Action Plan":
            render_product_action_plan(pack)
        elif section == "Export":
            render_product_export(pack)
        else:
            render_product_overview(pack, type_name, startup_total)
    with copilot:
        render_copilot_overlay(pack)


def render_technical_view(pack, type_name: str, startup_total: float) -> None:
    """The original technical dashboard, preserved as the Advanced View."""

    render_hero(pack, type_name, startup_total)

    tabs = st.tabs(["Overview", "Agent Control Room", "Customers & Offer", "Pricing & Finance", "Marketing & Operations", "Roadmap", "Export"])

    with tabs[0]:
        section_header("Agent System Summary", "Runtime", "Current ADK availability, fallback mode, and technical artefacts.")
        render_agent_system_summary(pack)
        section_header("Agent Pipeline", "Command Flow", "Founder input becomes a launch pack through agents, tools, and critic review.")
        render_pipeline_map()
        render_artefact_chips(pack)
        section_header("How LaunchForge Built This Pack", "Agent Trace", "Specialist agents completed a sequential launch-planning workflow.")
        render_agent_trace(pack)
        section_header("Capstone Evidence", "Kaggle Signals", "The dashboard visibly demonstrates the required agentic concepts.")
        render_capstone_evidence()
        section_header("Classification Evidence", "Adaptive Routing", f"Detected {type_name} with {pack.classification.confidence:.0%} confidence.")
        st.write(pack.classification.reasoning)
        render_chips(pack.classification.matched_signals)
        if pack.classification.uncertainty_notes:
            st.warning(" ".join(pack.classification.uncertainty_notes))
        section_header("Business Model Canvas", "Execution Model", "Nine operating-system tiles for how this business will create and capture value.")
        render_canvas(pack.business_model_canvas)
        section_header("Readiness Breakdown", "Critic Agent", "Score components sum to the final readiness score.")
        breakdown_df = pd.DataFrame(readiness_score_breakdown(pack.readiness_breakdown))
        try:
            import plotly.express as px

            fig = px.bar(breakdown_df, x="points", y="area", orientation="h", text="points", color="points", color_continuous_scale="Blues")
            fig.update_layout(showlegend=False, coloraxis_showscale=False, margin=dict(l=10, r=10, t=15, b=10), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            fig.update_traces(marker_line_width=0, textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.dataframe(breakdown_df, hide_index=True, use_container_width=True)
        section_header("Strengths & Gaps", "Readiness", "What is working now, and what must be validated before scaling.")
        sg_cols = st.columns(2)
        with sg_cols[0]:
            st.markdown("**Strengths**")
            render_chips(pack.readiness_strengths)
        with sg_cols[1]:
            st.markdown("**Gaps**")
            render_chips(pack.readiness_gaps)
        section_header("Next 3 Actions", "Priority Queue", "The highest-leverage next moves from the agent workflow.")
        render_next_actions(pack)
        section_header("Risks & Assumptions", "Critic Notes", "Planning constraints that should be checked manually.")
        risk_cols = st.columns(2)
        with risk_cols[0]:
            for risk in pack.risks:
                st.markdown(f"<div class='lf-card'><b>Risk</b><p>{escape(risk)}</p></div>", unsafe_allow_html=True)
        with risk_cols[1]:
            for assumption in pack.assumptions:
                st.markdown(f"<div class='lf-card'><b>Assumption</b><p>{escape(assumption)}</p></div>", unsafe_allow_html=True)

    with tabs[1]:
        render_agent_control_room(pack)

    with tabs[2]:
        section_header("Segment Scores", "Market Strategist Agent", "Customer segments scored by urgency, reachability, willingness to pay, and buyer control.")
        render_segment_scores(pack)
        section_header("Customer Persona Cards", "Market Agent", "Target segments translated into launch-ready buying triggers.")
        render_personas(pack)
        section_header("Offer-Fit Scores", "Offer Architect Agent", "Offer packages scored by pain match, feasibility, differentiation, revenue, and complexity.")
        render_offer_fit_scores(pack)
        section_header("Offer Ladder", "Offer Agent", "A staged product ladder from low-friction entry to premium outcome.")
        render_offer_ladder(pack)

    with tabs[3]:
        section_header("Pricing Strategy", "Pricing Agent", "Packages, rationale, use cases, and upgrade paths.")
        render_pricing_cards(pack)
        section_header("Pricing Scenarios", "Pricing Analyst Agent", "Low, base, and premium price sensitivity for each tier.")
        render_pricing_scenarios(pack)
        with st.expander("View pricing data table"):
            pricing_rows = [model_to_dict(item) for item in pack.pricing]
            st.dataframe(pd.DataFrame(pricing_rows), hide_index=True, use_container_width=True)
        section_header("Scenario Forecasts", "Finance Agent / Finance Simulation Agent", "Conservative, base, and aggressive forecasts with break-even probability.")
        render_scenario_forecasts(pack)
        section_header("Cashflow Forecast", "Finance Agent", "A planning forecast, not a guarantee.")
        fig = cashflow_chart(pack.cashflow)
        if hasattr(fig, "to_plotly_json"):
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.pyplot(fig)
        st.markdown(f"<div class='lf-disclaimer'>{escape(pack.forecast_disclaimer)} Forecasts are illustrative assumptions for planning and should be manually reviewed.</div>", unsafe_allow_html=True)
        section_header("Startup Cost Breakdown", "Launch Budget", "Where the initial launch budget is being allocated.")
        cost_rows = [{"category": key, "amount": value} for key, value in pack.startup_costs.items()]
        try:
            import plotly.express as px

            fig = px.pie(pd.DataFrame(cost_rows), names="category", values="amount", hole=0.45)
            fig.update_traces(textposition="inside", textinfo="percent+label", marker=dict(line=dict(color="#ffffff", width=2)))
            fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.dataframe(pd.DataFrame(cost_rows), hide_index=True, use_container_width=True)
        section_header("Forecast Assumptions", "Model Inputs", "Revenue, cost, conversion, and break-even assumptions made visible.")
        render_assumption_cards(pack)

    with tabs[4]:
        section_header("Sales Funnel", "Marketing Agent", "A connected acquisition-to-retention journey.")
        render_funnel(pack.sales_funnel["stages"])
        st.caption("Funnel shown as a visual execution sequence; Mermaid remains available in exports/docs, not exposed here.")
        section_header("Funnel Conversion Model", "Growth Marketing Agent", "Stage volumes, conversion rates, bottleneck flags, and recommendations.")
        render_funnel_model(pack)
        section_header("Marketing Message Pack", "Launch Copy", "Tactical messaging cards for the first launch push.")
        msg_cols = st.columns(len(pack.marketing_messages))
        for col, (category, messages) in zip(msg_cols, pack.marketing_messages.items()):
            with col:
                items = "".join(f"<li>{escape(message)}</li>" for message in messages)
                st.markdown(f"<div class='lf-card'><h4>{escape(category.replace('_', ' ').title())}</h4><ul class='lf-list'>{items}</ul></div>", unsafe_allow_html=True)
        section_header("Operations Checklist", "Operations Agent", "Execution checks before launch activity turns into delivery.")
        op_cols = st.columns(2)
        for index, item in enumerate(pack.operations_checklist):
            with op_cols[index % 2]:
                st.markdown(
                    f"""
                    <div class='lf-check-tile'>
                        <span class='lf-checkmark'>&#10003;</span>
                        <div>
                            <span class='lf-status'>Planned</span>
                            <p>{escape(item)}</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        section_header("Capacity Model", "Operations Planner Agent", "Founder capacity, operational bottleneck, and scaling constraint.")
        render_capacity_model(pack)

    with tabs[5]:
        section_header("30-Day Launch Roadmap", "Roadmap Agent", "A milestone board with natural completion criteria.")
        render_roadmap(pack)
        section_header("Priority Scores", "Roadmap Planner Agent", "Roadmap tasks scored by impact, urgency, effort, and risk reduction.")
        render_roadmap_priorities(pack)
        section_header("Risk Critic Red-Team", "Risk Critic Agent", "Missing evidence, failure modes, validation tests, and readiness cap.")
        render_red_team(pack)
        section_header("Final Next 3 Actions", "Immediate Execution", "The first decisions and actions to complete after this pack.")
        render_next_actions(pack)

    with tabs[6]:
        section_header("Launch Pack Deliverables", "Export Centre", "Package the agent output into portable Markdown or JSON.")
        deliverable_cols = st.columns(3, gap="medium")
        deliverables = [
            ("Launch Pack Ready", "Markdown", "Narrative pack for Kaggle writeup, demo review, and founder handoff."),
            ("Structured Data Ready", "JSON", "Machine-readable launch pack with currency, assumptions, agent trace, and roadmap."),
            ("Technical Trace Ready", "Agent Evidence", "Runtime status, ADK-style agents, MCP-style tools, skills, and execution trace."),
        ]
        for col, (title, badge, copy) in zip(deliverable_cols, deliverables):
            with col:
                st.markdown(
                    f"<div class='lf-download-card'><span class='lf-eyebrow'>{escape(badge)}</span><h4>{escape(title)}</h4><p>{escape(copy)}</p></div>",
                    unsafe_allow_html=True,
                )
        markdown_export = export_markdown(pack)
        json_export = export_json(pack)
        st.download_button("Download Markdown", markdown_export, "launchforge_launch_pack.md", "text/markdown")
        st.download_button("Download JSON", json_export, "launchforge_launch_pack.json", "application/json")
        st.subheader("Preview")
        st.code(markdown_export[:4000], language="markdown")
        st.caption("Privacy mode: inputs are held in session memory only. Exports are created only when you click a download button.")

    render_global_copilot_bar(pack)


def main() -> None:
    ensure_sidebar_defaults()
    inject_css()
    inject_product_css()

    st.session_state.setdefault("view_mode", "Product")

    with st.sidebar:
        st.markdown(
            """
            <div class='lf-sidebar-brand'>
                <h2>LaunchForge</h2>
                <p>Adaptive multi-agent launch command centre</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div class='lf-pv-nav-label'>View</div>", unsafe_allow_html=True)
        view_mode = st.radio(
            "View mode",
            ["Product", "Technical"],
            horizontal=True,
            key="view_mode",
            label_visibility="collapsed",
            help="Product View is the user-facing dashboard. Technical View is the advanced agent control room.",
        )

        section = "Overview"
        if view_mode == "Product":
            st.markdown("<div class='lf-pv-nav-label'>Sections</div>", unsafe_allow_html=True)
            section = st.radio(
                "Section",
                PRODUCT_SECTIONS,
                key="pv_section",
                label_visibility="collapsed",
            )

        generate = render_compact_founder_brief_editor("pack" in st.session_state)

        sidebar_pack = st.session_state.get("pack")
        sidebar_mode = sidebar_pack.runtime_status.get("mode", "not generated") if sidebar_pack else "not generated"
        sidebar_provider = sidebar_pack.runtime_status.get("provider", "fallback") if sidebar_pack else "fallback"
        dot_class = "is-live" if sidebar_pack else ""
        st.markdown(
            f"<div class='lf-sidebar-chip'><span class='lf-status-dot {dot_class}'></span>{escape(sidebar_mode)} / {escape(sidebar_provider)}</div>",
            unsafe_allow_html=True,
        )
        st.caption("Financial estimates are planning assumptions, not financial advice.")

    if "pack" not in st.session_state and not generate:
        render_topbar_static()
        st.info("Load a demo or describe your idea in the Founder brief, then generate your launch pack.")
        render_capstone_evidence()
        return

    if generate:
        idea = st.session_state.get("idea", "")
        if not idea.strip():
            st.warning("Enter a business idea or load a demo first.")
            return
        business_input = BusinessInput(
            idea=idea,
            budget=float(st.session_state.get("budget", 1000.0)),
            location=st.session_state.get("location", "Online"),
            founder_resources=st.session_state.get("founder_resources", ""),
            timeframe=st.session_state.get("pv_timeframe", "30 days"),
            stage=st.session_state.get("pv_stage", "Idea only"),
            target_customer=st.session_state.get("target_customer") or None,
            privacy_mode=bool(st.session_state.get("pv_privacy", True)),
        )
        with st.spinner("Running specialist agents..."):
            st.session_state["pack"] = run_launchforge_workflow(business_input)

    pack = st.session_state["pack"]
    type_name = type_label(pack.classification.business_type)
    startup_total = sum(pack.startup_costs.values())

    if view_mode == "Technical":
        render_technical_view(pack, type_name, startup_total)
    else:
        render_product_view(pack, section, type_name, startup_total)


if __name__ == "__main__":
    main()

