from __future__ import annotations

import json
import math
import re
import tempfile
from html import escape
from typing import Any, Dict, List, Tuple

import gradio as gr
import plotly.graph_objects as go

from launchforge.adk_runtime import get_runtime_status
from launchforge.business_plan_export import generate_business_plan_docx, generate_business_plan_markdown
from launchforge.copilot_agent import ask_launchforge_copilot
from launchforge.export import export_json, export_markdown
from launchforge.sample_data import type_label
from launchforge.schemas import BusinessInput, model_to_dict
from launchforge.workflow import run_launchforge_workflow


SECTIONS = ["Overview", "Opportunity", "Market", "Finance", "Action Plan", "Export"]


DEMO_PRESETS = {
    "tutoring": {
        "idea": "I want to start a local tutoring business helping school students improve their confidence and grades through personalised lessons, structured practice, and regular parent updates.",
        "budget": 600,
        "location": "Local area",
        "resources": "Subject knowledge, evening/weekend availability, existing parent network.",
        "timeframe": "30 days",
        "stage": "Idea only",
        "target": "Parents of school students",
    },
    "corner_shop": {
        "idea": "I want to open a small corner shop near a train station selling snacks, drinks, essentials, and quick breakfast items for commuters and local residents.",
        "budget": 12000,
        "location": "Near a train station",
        "resources": "Potential premises, retail experience, ability to source local suppliers.",
        "timeframe": "60 days",
        "stage": "Testing",
        "target": "Commuters and local residents",
    },
    "shopify": {
        "idea": "I want to launch a Shopify store selling affordable gym accessories like lifting straps, shaker bottles, resistance bands, and training notebooks.",
        "budget": 1800,
        "location": "Online",
        "resources": "Basic Shopify knowledge, fitness content ideas, evenings for fulfilment and customer support.",
        "timeframe": "30 days",
        "stage": "Idea only",
        "target": "Budget-conscious gym users",
    },
}


CSS = """
:root {
  --lf-bg: #060812;
  --lf-bg-2: #070b18;
  --lf-panel: rgba(255,255,255,0.065);
  --lf-card: rgba(255,255,255,0.088);
  --lf-card-strong: rgba(255,255,255,0.13);
  --lf-line: rgba(120,160,255,0.25);
  --lf-line-strong: rgba(34,211,238,0.45);
  --lf-blue: #4f7cff;
  --lf-cyan: #22d3ee;
  --lf-purple: #8b5cf6;
  --lf-green: #22c55e;
  --lf-amber: #f59e0b;
  --lf-red: #ef4444;
  --lf-text: #f8fafc;
  --lf-secondary: #cbd5e1;
  --lf-muted: #94a3b8;
  --lf-very-muted: #64748b;
  --lf-input: rgba(15,23,42,0.92);
}

html,
body,
gradio-app,
.gradio-container {
  overflow-x: hidden !important;
}

body, .gradio-container {
  background:
    radial-gradient(circle at 12% 8%, rgba(79,124,255,0.30), transparent 30%),
    radial-gradient(circle at 78% 12%, rgba(139,92,246,0.24), transparent 28%),
    linear-gradient(135deg, #060812 0%, #071024 46%, #09091a 100%) !important;
  color: var(--lf-text) !important;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}

.gradio-container {
  max-width: none !important;
}

#lf-root {
  width: min(100%, 1720px);
  max-width: 1720px;
  margin: 0 auto;
  box-sizing: border-box;
  overflow-x: hidden !important;
  padding: 0 10px;
}

#lf-root .lf-app-grid,
.lf-app-grid {
  display: grid !important;
  grid-template-columns: minmax(220px, 280px) minmax(0, 1fr) minmax(300px, 400px) !important;
  gap: 14px !important;
  width: 100% !important;
  max-width: 100% !important;
  overflow-x: hidden !important;
  align-items: flex-start !important;
  box-sizing: border-box !important;
}

#lf-root .lf-app-grid > *,
.lf-app-grid > * {
  min-width: 0 !important;
  box-sizing: border-box !important;
}

@media (max-width: 1120px) {
  #lf-root .lf-app-grid,
  .lf-app-grid {
    grid-template-columns: 1fr !important;
  }

  .lf-left-rail,
  .lf-main-canvas,
  .lf-copilot-panel {
    width: 100% !important;
    max-width: 100% !important;
    position: relative !important;
    top: auto !important;
  }
}

#lf-root,
#lf-root * {
  color-scheme: dark;
}

#lf-root p,
#lf-root span,
#lf-root li,
#lf-root td,
#lf-root th,
#lf-root label,
#lf-root summary,
#lf-root .prose,
#lf-root .md,
#lf-root .markdown,
#lf-root .token,
#lf-root .output-class {
  color: var(--lf-secondary) !important;
}

#lf-root strong,
#lf-root b,
#lf-root h1,
#lf-root h2,
#lf-root h3,
#lf-root h4 {
  color: var(--lf-text) !important;
}

#lf-root .block,
#lf-root .form,
#lf-root .wrap,
#lf-root .container,
#lf-root .panel,
#lf-root .input-container,
#lf-root .block.svelte-vt1mxs,
#lf-root [data-testid="block-info"],
#lf-root [data-testid="block-label"] {
  background: rgba(255,255,255,0.035) !important;
  border-color: rgba(120,160,255,0.18) !important;
  color: var(--lf-text) !important;
}

#lf-root [data-testid="block-info"],
#lf-root [data-testid="block-label"],
#lf-root .label,
#lf-root .info {
  color: var(--lf-muted) !important;
}

.lf-left-rail,
.lf-main-canvas,
.lf-copilot-panel {
  border: 1px solid var(--lf-line) !important;
  background: linear-gradient(180deg, rgba(255,255,255,0.075), rgba(255,255,255,0.035)) !important;
  box-shadow: 0 22px 80px rgba(0,0,0,0.32), inset 0 1px 0 rgba(255,255,255,0.08) !important;
  backdrop-filter: blur(18px);
  border-radius: 24px !important;
  box-sizing: border-box !important;
  min-width: 0 !important;
  max-width: 100% !important;
  overflow-x: hidden !important;
}

.lf-left-rail {
  padding: 18px !important;
  flex: 0 1 280px !important;
}

.lf-main-canvas {
  padding: 18px !important;
  flex: 1 1 auto !important;
}

.lf-copilot-panel {
  padding: 16px !important;
  position: sticky;
  top: 12px;
  max-height: 96vh;
  overflow-y: auto !important;
  width: 100% !important;
  max-width: min(420px, 100%) !important;
  flex: 0 1 400px !important;
  display: flex !important;
  flex-direction: column !important;
  flex-wrap: nowrap !important;
  align-items: stretch !important;
  gap: 12px !important;
}

.lf-copilot-panel,
.lf-copilot-panel *,
.lf-copilot-panel .block,
.lf-copilot-panel .wrap,
.lf-copilot-panel .form,
.lf-copilot-panel .container,
.lf-copilot-panel .input-container {
  box-sizing: border-box !important;
  max-width: 100% !important;
  min-width: 0 !important;
}

.lf-copilot-panel .block,
.lf-copilot-panel .wrap,
.lf-copilot-panel .form,
.lf-copilot-panel .container,
.lf-copilot-panel .input-container {
  overflow-x: hidden !important;
}

.lf-copilot-panel > *,
.lf-copilot-panel > .block,
.lf-copilot-panel > .form,
.lf-copilot-panel > .wrap {
  width: 100% !important;
  max-width: 100% !important;
  flex: 0 0 auto !important;
  align-self: stretch !important;
}

.lf-copilot-panel textarea,
.lf-copilot-panel input,
.lf-copilot-panel button {
  width: 100% !important;
  max-width: 100% !important;
}

.lf-copilot-panel .lf-quick-row {
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  gap: 8px !important;
  width: 100% !important;
  max-width: 100% !important;
  overflow-x: hidden !important;
}

.lf-copilot-panel .lf-quick-row > *,
.lf-copilot-panel .lf-quick-row .block {
  width: 100% !important;
  min-width: 0 !important;
  max-width: 100% !important;
}

.lf-export-actions {
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  gap: 10px !important;
  width: 100% !important;
}

.lf-export-actions > *,
.lf-export-actions button {
  width: 100% !important;
  min-width: 0 !important;
  box-sizing: border-box !important;
}

.lf-plan-preview {
  max-height: 520px;
  overflow: auto;
  background: #f8fafc !important;
  color: #0f172a !important;
  border: 1px solid rgba(15,23,42,0.10);
  border-radius: 18px;
  padding: 26px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.85);
}

#lf-root .lf-plan-preview,
#lf-root .lf-plan-preview * {
  color: #0f172a !important;
}

.lf-plan-preview h1,
.lf-plan-preview h2,
.lf-plan-preview h3 {
  color: #0f172a !important;
  letter-spacing: 0;
}

.lf-plan-preview h1 {
  font-size: 1.45rem;
  margin: 0 0 12px;
}

.lf-plan-preview h2 {
  font-size: 1.05rem;
  margin: 22px 0 8px;
  padding-top: 14px;
  border-top: 1px solid #dbe4f0;
}

.lf-plan-preview h3 {
  font-size: 0.92rem;
  margin: 16px 0 6px;
  color: #1e3a8a !important;
}

.lf-plan-preview p,
.lf-plan-preview li {
  color: #334155 !important;
  font-size: 0.86rem;
  line-height: 1.55;
}

.lf-plan-preview ul {
  margin: 8px 0 12px 18px;
  padding: 0;
}

.lf-plan-preview table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 0.78rem;
  color: #0f172a !important;
}

.lf-plan-preview th {
  background: #e0e7ff !important;
  color: #172554 !important;
  text-align: left;
}

.lf-plan-preview th,
.lf-plan-preview td {
  border: 1px solid #cbd5e1;
  padding: 7px 8px;
  vertical-align: top;
}

.lf-plan-preview a {
  color: #2563eb !important;
}

.lf-plan-preview code,
.lf-plan-preview pre {
  background: #e2e8f0 !important;
  color: #0f172a !important;
}

.lf-brand {
  padding: 4px 2px 14px;
  border-bottom: 1px solid rgba(255,255,255,0.12);
  margin-bottom: 14px;
}

.lf-logo {
  font-size: 1.55rem;
  font-weight: 850;
  letter-spacing: -0.04em;
  background: linear-gradient(90deg, #ffffff, #22d3ee 42%, #8b5cf6);
  -webkit-background-clip: text;
  color: transparent;
}

.lf-subtle {
  color: var(--lf-muted) !important;
  font-size: 0.78rem;
  line-height: 1.35;
}

.lf-status-chip,
.lf-chip,
.lf-mini-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  border: 1px solid rgba(34,211,238,0.32);
  background: rgba(34,211,238,0.10);
  color: #ccfbff;
  padding: 6px 10px;
  font-size: 0.74rem;
  font-weight: 750;
  letter-spacing: 0.02em;
}

.lf-mini-chip {
  padding: 4px 8px;
  border-color: rgba(139,92,246,0.35);
  background: rgba(139,92,246,0.12);
  color: #ddd6fe;
}

.lf-nav {
  display: grid;
  gap: 8px;
  margin: 12px 0 18px;
}

.lf-nav-item {
  border: 1px solid rgba(120,160,255,0.18);
  background: rgba(255,255,255,0.05);
  color: var(--lf-secondary) !important;
  padding: 9px 11px;
  border-radius: 14px;
  font-size: 0.78rem;
  font-weight: 700;
}

.lf-nav-item.active {
  border-color: rgba(34,211,238,0.52);
  color: var(--lf-text) !important;
  box-shadow: 0 0 28px rgba(34,211,238,0.16), inset 3px 0 0 rgba(34,211,238,0.92);
  background: linear-gradient(90deg, rgba(79,124,255,0.28), rgba(139,92,246,0.20));
}

.lf-command-heading {
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--lf-muted) !important;
  margin: 14px 0 8px;
  font-weight: 850;
}

.lf-hero {
  border: 1px solid rgba(34,211,238,0.26);
  border-radius: 24px;
  padding: 22px;
  background:
    linear-gradient(120deg, rgba(79,124,255,0.28), rgba(139,92,246,0.18) 55%, rgba(34,211,238,0.10)),
    rgba(255,255,255,0.06);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.10), 0 18px 60px rgba(0,0,0,0.24);
  margin-bottom: 14px;
}

.lf-hero-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 14px;
  align-items: center;
}

.lf-title {
  margin: 0;
  font-size: clamp(2.15rem, 5vw, 4.2rem);
  line-height: 0.92;
  letter-spacing: -0.08em;
  font-weight: 900;
  background: linear-gradient(90deg, #ffffff, #dff6ff 36%, #22d3ee 62%, #a78bfa);
  -webkit-background-clip: text;
  color: transparent;
}

.lf-kpi-grid,
.lf-card-grid,
.lf-three-grid,
.lf-two-grid {
  display: grid;
  gap: 12px;
}

.lf-kpi-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); margin: 12px 0; }
.lf-card-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.lf-three-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.lf-two-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }

.lf-card,
.lf-kpi,
.lf-module,
.lf-action-card,
.lf-risk-card {
  border: 1px solid var(--lf-line);
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255,255,255,0.09), rgba(255,255,255,0.045));
  box-shadow: 0 14px 44px rgba(0,0,0,0.22), inset 0 1px 0 rgba(255,255,255,0.08);
  padding: 15px;
  overflow: hidden;
}

.lf-kpi {
  min-height: 102px;
}

.lf-label {
  color: var(--lf-muted) !important;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 850;
  margin-bottom: 7px;
}

.lf-value {
  color: var(--lf-text) !important;
  font-size: 1.55rem;
  font-weight: 900;
  letter-spacing: -0.04em;
  line-height: 1.05;
}

.lf-note {
  color: var(--lf-secondary) !important;
  font-size: 0.78rem;
  line-height: 1.35;
  margin-top: 8px;
}

.lf-section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 18px 0 10px;
}

.lf-section-title h2 {
  margin: 0;
  font-size: 1.1rem;
  letter-spacing: -0.03em;
  color: var(--lf-text) !important;
}

.lf-gauge-wrap {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 14px;
}

.lf-gauge {
  width: 124px;
  height: 124px;
}

.lf-gauge text {
  font-family: Inter, sans-serif;
  fill: #ffffff;
  font-weight: 900;
}

.lf-bar {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255,255,255,0.10);
  margin-top: 10px;
}

.lf-bar-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #4f7cff, #22d3ee);
}

.lf-persona-name,
.lf-module-title {
  color: var(--lf-text) !important;
  font-weight: 850;
  letter-spacing: -0.025em;
  font-size: 1rem;
  margin-bottom: 6px;
}

.lf-stage {
  width: 30px;
  height: 30px;
  border-radius: 12px;
  display: inline-grid;
  place-items: center;
  background: linear-gradient(135deg, rgba(79,124,255,0.95), rgba(139,92,246,0.9));
  color: #ffffff;
  font-weight: 900;
  margin-bottom: 10px;
}

.lf-list {
  margin: 8px 0 0;
  padding-left: 16px;
  color: var(--lf-secondary) !important;
  font-size: 0.82rem;
  line-height: 1.45;
}

.lf-list li {
  color: var(--lf-secondary) !important;
}

.lf-risk-card {
  border-color: rgba(245,158,11,0.28);
  background: linear-gradient(180deg, rgba(245,158,11,0.10), rgba(255,255,255,0.045));
}

.lf-action-card {
  border-color: rgba(34,197,94,0.28);
  background: linear-gradient(180deg, rgba(34,197,94,0.10), rgba(255,255,255,0.045));
}

.lf-funnel-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.lf-funnel-stage {
  border: 1px solid rgba(34,211,238,0.22);
  border-radius: 16px;
  padding: 12px;
  background: rgba(34,211,238,0.07);
}

.lf-funnel-stage.bottleneck {
  border-color: rgba(245,158,11,0.54);
  background: rgba(245,158,11,0.10);
}

.lf-table {
  width: 100%;
  border-collapse: collapse;
  color: var(--lf-secondary) !important;
  font-size: 0.8rem;
}

.lf-table th,
.lf-table td {
  border-bottom: 1px solid rgba(255,255,255,0.09);
  padding: 9px 6px;
  text-align: left;
}

.lf-table th {
  color: var(--lf-muted) !important;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  font-size: 0.68rem;
}

.lf-finance-section,
.lf-finance-section * {
  color: var(--lf-secondary) !important;
}

.lf-finance-section .lf-label,
.lf-finance-section .lf-table th {
  color: #bfdbfe !important;
}

.lf-finance-section .lf-value,
.lf-finance-section .lf-module-title,
.lf-finance-section strong,
.lf-finance-section b {
  color: var(--lf-text) !important;
}

.lf-finance-section .lf-note,
.lf-finance-section .lf-list,
.lf-finance-section .lf-list li,
.lf-finance-section .lf-table td {
  color: #dbeafe !important;
}

.lf-finance-section .lf-card,
.lf-finance-section .lf-kpi,
.lf-finance-section .lf-risk-card {
  background: linear-gradient(180deg, rgba(15,23,42,0.86), rgba(30,41,59,0.52)) !important;
  border-color: rgba(96,165,250,0.26) !important;
}

.lf-runtime-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 10px;
}

.lf-runtime-cell {
  border: 1px solid rgba(120,160,255,0.18);
  border-radius: 13px;
  padding: 8px;
  background: rgba(15,23,42,0.58);
}

.lf-runtime-cell .lf-label {
  font-size: 0.62rem;
  margin-bottom: 4px;
}

.lf-runtime-cell .lf-note {
  margin-top: 0;
  font-size: 0.76rem;
}

.lf-export-preview {
  white-space: pre-wrap;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.76rem;
  color: var(--lf-secondary) !important;
  max-height: 260px;
  overflow: auto;
}

.lf-copilot-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.lf-copilot-title strong {
  color: var(--lf-text) !important;
  font-size: 1.04rem;
}

.lf-meta-card {
  border: 1px solid rgba(120,160,255,0.20);
  border-radius: 16px;
  padding: 10px;
  background: rgba(255,255,255,0.055);
  color: var(--lf-secondary) !important;
  font-size: 0.78rem;
  line-height: 1.4;
}

.lf-meta-card,
.lf-meta-card * {
  color: var(--lf-secondary) !important;
}

.lf-meta-card strong {
  color: var(--lf-text) !important;
}

.gradio-container button.primary,
.gradio-container .primary {
  background: linear-gradient(135deg, #4f7cff, #8b5cf6) !important;
  border: 1px solid rgba(34,211,238,0.38) !important;
  color: white !important;
  box-shadow: 0 10px 32px rgba(79,124,255,0.25) !important;
}

#lf-root button,
.gradio-container button {
  border-radius: 14px !important;
  border-color: rgba(120,160,255,0.25) !important;
  background: rgba(255,255,255,0.075) !important;
  color: var(--lf-text) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), 0 8px 22px rgba(0,0,0,0.18) !important;
}

#lf-root button:hover,
.gradio-container button:hover {
  border-color: rgba(34,211,238,0.48) !important;
  background: rgba(79,124,255,0.16) !important;
  color: #ffffff !important;
}

#lf-root .lf-quick-btn button,
#lf-root .lf-demo-btn button {
  background: linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.055)) !important;
  border: 1px solid rgba(148,163,184,0.25) !important;
  color: var(--lf-text) !important;
  min-height: 36px !important;
  font-weight: 750 !important;
}

#lf-root .lf-quick-btn button:hover,
#lf-root .lf-demo-btn button:hover {
  background: linear-gradient(135deg, rgba(79,124,255,0.28), rgba(139,92,246,0.20)) !important;
  border-color: rgba(34,211,238,0.45) !important;
}

#lf-root input,
#lf-root textarea,
#lf-root select,
#lf-root [contenteditable="true"],
.gradio-container input,
.gradio-container textarea,
.gradio-container select {
  background: var(--lf-input) !important;
  color: var(--lf-text) !important;
  border-color: rgba(120,160,255,0.25) !important;
  border-radius: 14px !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.05) !important;
}

#lf-root input::placeholder,
#lf-root textarea::placeholder,
.gradio-container input::placeholder,
.gradio-container textarea::placeholder {
  color: var(--lf-muted) !important;
  opacity: 1 !important;
}

#lf-root input:focus,
#lf-root textarea:focus,
#lf-root select:focus {
  border-color: rgba(34,211,238,0.58) !important;
  box-shadow: 0 0 0 3px rgba(34,211,238,0.12), inset 0 1px 0 rgba(255,255,255,0.05) !important;
}

.gradio-container label,
.gradio-container .wrap .label {
  color: var(--lf-secondary) !important;
}

#lf-root .dropdown,
#lf-root .dropdown *,
#lf-root .multiselect,
#lf-root .multiselect *,
#lf-root [role="listbox"],
#lf-root [role="listbox"] *,
#lf-root [role="option"],
#lf-root [role="option"] * {
  background-color: rgba(15,23,42,0.98) !important;
  color: var(--lf-text) !important;
  border-color: rgba(120,160,255,0.25) !important;
}

.tabs {
  background: rgba(255,255,255,0.035) !important;
  border-radius: 18px !important;
  border: 1px solid rgba(120,160,255,0.16) !important;
}

#lf-root .tabs,
#lf-root .tabitem,
#lf-root .tab-nav,
#lf-root .tab-nav button,
#lf-root [role="tablist"],
#lf-root [role="tabpanel"] {
  background: rgba(255,255,255,0.025) !important;
  border-color: rgba(120,160,255,0.16) !important;
}

.tab-nav button,
#lf-root [role="tab"] {
  color: var(--lf-secondary) !important;
  font-weight: 750 !important;
  background: rgba(255,255,255,0.045) !important;
  border-radius: 12px !important;
}

.tab-nav button.selected,
#lf-root [role="tab"][aria-selected="true"] {
  color: var(--lf-text) !important;
  border-color: #22d3ee !important;
  background: linear-gradient(135deg, rgba(79,124,255,0.22), rgba(139,92,246,0.16)) !important;
  box-shadow: 0 0 22px rgba(34,211,238,0.10) !important;
}

.lf-copilot-panel .message-wrap,
.lf-copilot-panel .message,
.lf-copilot-panel .bubble-wrap,
.lf-copilot-panel .bubble,
.lf-copilot-panel .chatbot,
.lf-copilot-panel [data-testid="bot"],
.lf-copilot-panel [data-testid="user"] {
  background: rgba(255,255,255,0.055) !important;
  color: var(--lf-text) !important;
  border-color: rgba(120,160,255,0.18) !important;
}

.lf-copilot-panel .message-wrap *,
.lf-copilot-panel .message *,
.lf-copilot-panel .bubble *,
.lf-copilot-panel .chatbot * {
  color: var(--lf-secondary) !important;
}

.lf-copilot-panel .user,
.lf-copilot-panel .user *,
.lf-copilot-panel [data-testid="user"],
.lf-copilot-panel [data-testid="user"] * {
  color: var(--lf-text) !important;
}

#lf-root .lf-export-file,
#lf-root .lf-export-file *,
#lf-root .file-preview,
#lf-root .file-preview *,
#lf-root .file,
#lf-root .file *,
#lf-root .download,
#lf-root .download *,
#lf-root .upload,
#lf-root .upload * {
  background: rgba(15,23,42,0.82) !important;
  color: var(--lf-secondary) !important;
  border-color: rgba(120,160,255,0.20) !important;
}

#lf-root .lf-export-file {
  max-height: 190px !important;
  overflow: auto !important;
  border-radius: 18px !important;
  border: 1px solid rgba(120,160,255,0.22) !important;
  background: linear-gradient(180deg, rgba(15,23,42,0.86), rgba(15,23,42,0.64)) !important;
}

#lf-root .lf-export-file label,
#lf-root .lf-export-file span,
#lf-root .lf-export-file p,
#lf-root .file-preview label,
#lf-root .file-preview span,
#lf-root .file-preview p {
  color: var(--lf-secondary) !important;
}

#lf-root .lf-export-file a,
#lf-root .file-preview a,
#lf-root .download a {
  color: #bfdbfe !important;
}

#lf-root .empty,
#lf-root .placeholder,
#lf-root .secondary-wrap {
  background: rgba(15,23,42,0.68) !important;
  color: var(--lf-muted) !important;
  border-color: rgba(120,160,255,0.18) !important;
}

gradio-app,
.gradio-container .block,
.gradio-container .wrap,
.gradio-container .form,
.gradio-container .container,
.gradio-container .panel,
.gradio-container .input-container,
.gradio-container .padded,
.gradio-container .auto-margin,
.gradio-container .hide,
.gradio-container .flex,
.gradio-container .full {
  background: rgba(255,255,255,0.035) !important;
  color: var(--lf-text) !important;
  border-color: rgba(120,160,255,0.18) !important;
}

.gradio-container .block label,
.gradio-container .block span,
.gradio-container .block p,
.gradio-container .wrap label,
.gradio-container .wrap span,
.gradio-container .wrap p {
  color: var(--lf-secondary) !important;
}

.gradio-container .chatbot,
.gradio-container .chatbot *,
.gradio-container .messages,
.gradio-container .messages *,
.gradio-container .message,
.gradio-container .message *,
.gradio-container .bubble,
.gradio-container .bubble *,
.gradio-container .block:has(.chatbot),
.gradio-container .block:has([aria-label="Command channel"]) {
  background: rgba(15,23,42,0.72) !important;
  color: var(--lf-secondary) !important;
  border-color: rgba(120,160,255,0.20) !important;
}

.gradio-container .block:has(textarea),
.gradio-container .block:has(input),
.gradio-container .wrap:has(textarea),
.gradio-container .wrap:has(input) {
  background: rgba(15,23,42,0.54) !important;
  border-radius: 16px !important;
  border: 1px solid rgba(120,160,255,0.18) !important;
}

.gradio-container .block:has(.file-preview),
.gradio-container .block:has(.download),
.gradio-container .block:has(.upload),
.gradio-container .lf-export-file {
  min-height: 0 !important;
  max-height: 190px !important;
  background: rgba(15,23,42,0.76) !important;
}

@media (max-width: 1180px) {
  .lf-kpi-grid, .lf-card-grid, .lf-three-grid, .lf-two-grid, .lf-funnel-row {
    grid-template-columns: 1fr 1fr;
  }
  .lf-hero-grid { grid-template-columns: 1fr; }
}

@media (max-width: 760px) {
  .lf-kpi-grid, .lf-card-grid, .lf-three-grid, .lf-two-grid, .lf-funnel-row {
    grid-template-columns: 1fr;
  }
}
"""


def _safe(value: Any) -> str:
    return escape(str(value or ""), quote=True)


def _plain_list(items: List[Any], limit: int | None = None) -> List[str]:
    selected = items[:limit] if limit else items
    return [_safe(item) for item in selected if str(item or "").strip()]


def _pack_dict(pack: Any) -> Dict[str, Any]:
    if not pack:
        return {}
    if isinstance(pack, dict):
        return pack
    return model_to_dict(pack)


def _business_label(data: Dict[str, Any]) -> str:
    return type_label((data.get("classification") or {}).get("business_type", "unknown"))


def _money(data: Dict[str, Any], value: Any) -> str:
    symbol = data.get("currency_symbol") or "GBP "
    try:
        return f"{symbol}{float(value):,.0f}"
    except (TypeError, ValueError):
        return "not available"


def _confidence(data: Dict[str, Any]) -> int:
    try:
        return int(round(float((data.get("classification") or {}).get("confidence", 0)) * 100))
    except (TypeError, ValueError):
        return 0


def _recommended_segment(data: Dict[str, Any]) -> Dict[str, Any]:
    rows = data.get("segment_scores") or []
    return next((row for row in rows if row.get("recommended_first_segment")), rows[0] if rows else {})


def _status_chip(text: str, kind: str = "cyan") -> str:
    return f"<span class='lf-mini-chip'>{_safe(text)}</span>"


def render_sidebar_nav(active_section: str = "Overview") -> str:
    active = active_section if active_section in SECTIONS else "Overview"
    items = "".join(
        f"<div class='lf-nav-item {'active' if section == active else ''}'>{_safe(section)}</div>"
        for section in SECTIONS
    )
    return f"<div class='lf-nav'>{items}</div>"


def set_active_section(section: str) -> Tuple[str, str]:
    selected = section if section in SECTIONS else "Overview"
    return selected, render_sidebar_nav(selected)


def render_runtime_status_card(status: Dict[str, Any] | None = None) -> str:
    runtime = status or get_runtime_status()
    api_key = "Present" if runtime.get("api_key_available") else "Missing"
    genai = "Yes" if runtime.get("genai_available") else "No"
    adk = "Yes" if runtime.get("adk_available") else "No"
    mode = runtime.get("mode", "deterministic-fallback")
    provider = runtime.get("provider", "fallback")
    model = runtime.get("model", "gemini-2.5-flash")
    reason = runtime.get("reason", "")
    return f"""
    <div class="lf-meta-card">
      <strong>Runtime status</strong>
      <div class="lf-runtime-grid">
        <div class="lf-runtime-cell"><div class="lf-label">Mode</div><div class="lf-note">{_safe(mode)}</div></div>
        <div class="lf-runtime-cell"><div class="lf-label">Provider</div><div class="lf-note">{_safe(provider)}</div></div>
        <div class="lf-runtime-cell"><div class="lf-label">API key</div><div class="lf-note">{_safe(api_key)}</div></div>
        <div class="lf-runtime-cell"><div class="lf-label">GenAI</div><div class="lf-note">{_safe(genai)}</div></div>
        <div class="lf-runtime-cell"><div class="lf-label">ADK</div><div class="lf-note">{_safe(adk)}</div></div>
        <div class="lf-runtime-cell"><div class="lf-label">Model</div><div class="lf-note">{_safe(model)}</div></div>
      </div>
      <div class="lf-note">{_safe(reason)}</div>
    </div>
    """


def _section(title: str, note: str = "") -> str:
    note_html = f"<span class='lf-subtle'>{_safe(note)}</span>" if note else ""
    return f"<div class='lf-section-title'><h2>{_safe(title)}</h2>{note_html}</div>"


def _list_html(items: List[Any], limit: int | None = None) -> str:
    values = _plain_list(items, limit)
    if not values:
        return "<p class='lf-note'>No items available yet.</p>"
    return "<ul class='lf-list'>" + "".join(f"<li>{item}</li>" for item in values) + "</ul>"


def _inline_markdown(text: Any) -> str:
    rendered = escape(str(text or ""))
    rendered = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", rendered)
    if rendered.startswith("_") and rendered.endswith("_") and len(rendered) > 2:
        rendered = f"<em>{rendered[1:-1]}</em>"
    return rendered


def _markdown_to_document_html(markdown: str) -> str:
    """Render a small, safe subset of Markdown as a readable document preview."""

    lines = markdown.splitlines()
    output: List[str] = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("# "):
            output.append(f"<h1>{_inline_markdown(line[2:])}</h1>")
            index += 1
            continue
        if line.startswith("## "):
            output.append(f"<h2>{_inline_markdown(line[3:])}</h2>")
            index += 1
            continue
        if line.startswith("### "):
            output.append(f"<h3>{_inline_markdown(line[4:])}</h3>")
            index += 1
            continue
        if line.startswith("- "):
            items: List[str] = []
            while index < len(lines) and lines[index].strip().startswith("- "):
                items.append(f"<li>{_inline_markdown(lines[index].strip()[2:])}</li>")
                index += 1
            output.append("<ul>" + "".join(items) + "</ul>")
            continue
        if line.startswith("|") and "|" in line[1:]:
            table_rows: List[List[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                raw_cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                if raw_cells and not all(set(cell) <= {"-", ":", " "} for cell in raw_cells):
                    table_rows.append(raw_cells)
                index += 1
            if table_rows:
                headers = table_rows[0]
                body = table_rows[1:]
                header_html = "".join(f"<th>{_inline_markdown(cell)}</th>" for cell in headers)
                body_html = "".join(
                    "<tr>" + "".join(f"<td>{_inline_markdown(cell)}</td>" for cell in row) + "</tr>"
                    for row in body
                )
                output.append(f"<table><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table>")
            continue
        output.append(f"<p>{_inline_markdown(line)}</p>")
        index += 1
    return "\n".join(output)


def _gauge(score: int) -> str:
    score = max(0, min(100, int(score or 0)))
    radius = 48
    circumference = 2 * math.pi * radius
    offset = circumference * (1 - score / 100)
    color = "#22c55e" if score >= 75 else "#f59e0b" if score >= 55 else "#ef4444"
    return f"""
    <svg class="lf-gauge" viewBox="0 0 120 120" role="img" aria-label="Readiness score {score}">
      <defs>
        <filter id="glow"><feGaussianBlur stdDeviation="3.5" result="coloredBlur"/><feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <circle cx="60" cy="60" r="{radius}" stroke="rgba(255,255,255,0.12)" stroke-width="12" fill="none"/>
      <circle cx="60" cy="60" r="{radius}" stroke="{color}" stroke-width="12" fill="none" stroke-linecap="round"
        stroke-dasharray="{circumference:.2f}" stroke-dashoffset="{offset:.2f}" transform="rotate(-90 60 60)" filter="url(#glow)"/>
      <text x="60" y="57" text-anchor="middle" font-size="26">{score}</text>
      <text x="60" y="76" text-anchor="middle" font-size="11" fill="rgba(226,232,255,0.62)">/100</text>
    </svg>
    """


def _placeholder() -> str:
    return """
    <div class="lf-hero">
      <div class="lf-hero-grid">
        <div>
          <div class="lf-status-chip">Awaiting founder brief</div>
          <h1 class="lf-title">LaunchForge</h1>
          <p class="lf-subtle">Generate a launch pack to activate the holographic business command centre.</p>
        </div>
        <div class="lf-card">
          <div class="lf-label">System State</div>
          <div class="lf-value">Standby</div>
          <div class="lf-note">Choose a demo preset or enter your own founder brief, then press Generate Launch Pack.</div>
        </div>
      </div>
    </div>
    """


def render_topbar(pack: Any) -> str:
    data = _pack_dict(pack)
    if not data:
        return ""
    runtime = data.get("runtime_status") or {}
    classification = data.get("classification") or {}
    chips = " ".join(
        [
            _status_chip(_business_label(data)),
            _status_chip(data.get("launch_readiness_label", "Planning")),
            _status_chip(f"{data.get('currency_code', 'GBP')} {data.get('currency_symbol', '')}".strip()),
            _status_chip(runtime.get("mode", "deterministic-fallback")),
        ]
    )
    return f"""
    <div class="lf-hero">
      <div class="lf-hero-grid">
        <div>
          <div>{chips}</div>
          <h1 class="lf-title">LaunchForge</h1>
          <p class="lf-subtle">AI Business Launch Command Centre. Specialist agents, deterministic tools, and Copilot guidance fused into one launch operating system.</p>
        </div>
        <div class="lf-gauge-wrap">
          {_gauge(int(data.get("readiness_score", 0)))}
          <div>
            <div class="lf-label">Generated Status</div>
            <div class="lf-value">Launch Pack Online</div>
            <div class="lf-note">{_safe(_business_label(data))} detected with {_confidence(data)}% model confidence.</div>
          </div>
        </div>
      </div>
    </div>
    """


def render_overview(pack: Any) -> str:
    data = _pack_dict(pack)
    if not data:
        return _placeholder()
    classification = data.get("classification") or {}
    segment = _recommended_segment(data)
    startup_total = sum((data.get("startup_costs") or {}).values())
    risks = data.get("risks") or []
    actions = data.get("next_3_actions") or []
    offer = data.get("offer_ladder") or []
    signals = [
        ("Target customer clarity", f"{_safe(segment.get('persona_name') or 'Recommended segment')} is the first target."),
        ("Offer strength", _safe((offer[0] or {}).get("name", "Starter offer")) if offer else "Starter offer ready."),
        ("Launch economics", f"Startup model: {_money(data, startup_total)}."),
        ("Risk level", _safe(data.get("launch_readiness_label", "Planning"))),
    ]
    kpis = [
        ("Business Type", _business_label(data), f"{_confidence(data)}% confidence"),
        ("Readiness", f"{data.get('readiness_score', 0)}/100", data.get("launch_readiness_label", "Planning")),
        ("Startup Cost", _money(data, startup_total), "Planning estimate"),
        ("Break-even", f"Month {data.get('breakeven_month')}", "Modelled scenario"),
    ]
    kpi_html = "".join(
        f"<div class='lf-kpi'><div class='lf-label'>{_safe(label)}</div><div class='lf-value'>{_safe(value)}</div><div class='lf-note'>{_safe(note)}</div></div>"
        for label, value, note in kpis
    )
    signal_html = "".join(
        f"<div class='lf-card'><div class='lf-label'>{_safe(label)}</div><div class='lf-note'>{note}</div></div>"
        for label, note in signals
    )
    evidence = "".join(f"<span class='lf-chip'>{_safe(item)}</span> " for item in classification.get("matched_signals", [])[:5])
    actions_html = "".join(
        f"<div class='lf-action-card'><span class='lf-mini-chip'>Action {idx}</span><div class='lf-module-title'>{_safe(action)}</div></div>"
        for idx, action in enumerate(actions[:3], start=1)
    )
    risks_html = "".join(f"<div class='lf-risk-card'><div class='lf-label'>Watchout</div><div class='lf-note'>{_safe(risk)}</div></div>" for risk in risks[:3])
    return f"""
    <div class="lf-kpi-grid">{kpi_html}</div>
    {_section("Business Potential Score", "Readiness, confidence, and route evidence")}
    <div class="lf-two-grid">
      <div class="lf-card">
        <div class="lf-gauge-wrap" style="justify-content:flex-start;">
          {_gauge(int(data.get("readiness_score", 0)))}
          <div>
            <div class="lf-label">{_safe(data.get("launch_readiness_label", "Planning"))}</div>
            <div class="lf-value">{_safe(_business_label(data))}</div>
            <div class="lf-note">{_safe(classification.get("reasoning", ""))}</div>
          </div>
        </div>
      </div>
      <div class="lf-card">
        <div class="lf-label">Classification Evidence</div>
        <div style="display:flex;flex-wrap:wrap;gap:7px;margin-top:8px;">{evidence or _status_chip("No evidence available")}</div>
      </div>
    </div>
    {_section("Key Signals")}
    <div class="lf-card-grid">{signal_html}</div>
    {_section("Target First")}
    <div class="lf-card">
      <div class="lf-persona-name">{_safe(segment.get("persona_name") or "Recommended segment")}</div>
      <div class="lf-note">{_safe(segment.get("segment") or "")}</div>
      <div style="display:flex;flex-wrap:wrap;gap:7px;margin-top:10px;">
        {_status_chip("Pain " + str(segment.get("pain_intensity", "-")) + "/5")}
        {_status_chip("Reach " + str(segment.get("reachability", "-")) + "/5")}
        {_status_chip("Urgency " + str(segment.get("urgency", "-")) + "/5")}
        {_status_chip("Pay " + str(segment.get("willingness_to_pay", "-")) + "/5")}
        {_status_chip("Control " + str(segment.get("buyer_control", "-")) + "/5")}
      </div>
      <div class="lf-note">{_safe(segment.get("rationale") or "LaunchForge recommends the first reachable segment with the best urgency and fit.")}</div>
    </div>
    {_section("Risks And Next Actions")}
    <div class="lf-two-grid"><div>{risks_html}</div><div>{actions_html}</div></div>
    """


def render_opportunity(pack: Any) -> str:
    data = _pack_dict(pack)
    if not data:
        return _placeholder()
    personas = data.get("personas") or []
    scores = data.get("segment_scores") or []
    offers = data.get("offer_ladder") or []
    offer_scores = {item.get("offer_name"): item for item in data.get("offer_fit_scores") or []}
    persona_cards = []
    for persona in personas:
        score = next((row for row in scores if row.get("persona_name") == persona.get("name")), {})
        chips = " ".join(
            [
                _status_chip(f"Pain {score.get('pain_intensity', '-')}/5"),
                _status_chip(f"Reach {score.get('reachability', '-')}/5"),
                _status_chip(f"Urgency {score.get('urgency', '-')}/5"),
                _status_chip(f"Pay {score.get('willingness_to_pay', '-')}/5"),
            ]
        )
        persona_cards.append(
            f"""
            <div class="lf-card">
              <div class="lf-persona-name">{_safe(persona.get('name'))}</div>
              <div class="lf-note"><strong>Segment:</strong> {_safe(persona.get('segment'))}</div>
              <div style="display:flex;flex-wrap:wrap;gap:7px;margin:10px 0;">{chips}</div>
              <div class="lf-note"><strong>Pain:</strong> {_safe('; '.join(persona.get('pains', [])[:2]))}</div>
              <div class="lf-note"><strong>Trigger:</strong> {_safe(persona.get('buying_trigger'))}</div>
              <div class="lf-note"><strong>Channels:</strong> {_safe(', '.join(persona.get('channels', [])))}</div>
            </div>
            """
        )
    offer_cards = []
    for idx, offer in enumerate(offers[:3], start=1):
        score = offer_scores.get(offer.get("name"), {})
        offer_cards.append(
            f"""
            <div class="lf-module">
              <div class="lf-stage">{idx}</div>
              <div class="lf-module-title">{_safe(offer.get('name'))}</div>
              <div class="lf-note">{_safe(offer.get('description'))}</div>
              {_list_html(offer.get('deliverables', []), 4)}
              <div style="margin-top:10px;">{_status_chip('Fit ' + str(score.get('overall_offer_score', '-')) + '/5')} {_status_chip(_safe(offer.get('success_metric', 'Success metric')))}</div>
            </div>
            """
        )
    return f"""
    {_section("Opportunity Matrix", "Who to target and what to sell first")}
    <div class="lf-two-grid">{''.join(persona_cards)}</div>
    {_section("Offer Ladder", "Entry to core to premium")}
    <div class="lf-three-grid">{''.join(offer_cards)}</div>
    """


def render_market(pack: Any) -> str:
    data = _pack_dict(pack)
    if not data:
        return _placeholder()
    funnel = data.get("funnel_model") or []
    marketing = data.get("marketing_messages") or {}
    capacity = data.get("capacity_model") or {}
    bottleneck = next((stage for stage in funnel if stage.get("bottleneck")), {})
    stages = []
    for stage in funnel[:5]:
        stages.append(
            f"""
            <div class="lf-funnel-stage {'bottleneck' if stage.get('bottleneck') else ''}">
              <div class="lf-label">{_safe(stage.get('stage_name'))}</div>
              <div class="lf-value" style="font-size:1.05rem;">{stage.get('output_volume', '-')}</div>
              <div class="lf-note">{int(float(stage.get('conversion_rate', 0))*100)}% conversion</div>
              <div class="lf-note">{_safe(stage.get('stage_objective'))}</div>
            </div>
            """
        )
    message_cards = []
    for key, values in marketing.items():
        message_cards.append(
            f"<div class='lf-card'><div class='lf-label'>{_safe(str(key).replace('_', ' ').title())}</div>{_list_html(values, 3)}</div>"
        )
    return f"""
    {_section("Conversion Funnel", "Volume, conversion, and bottleneck")}
    <div class="lf-funnel-row">{''.join(stages)}</div>
    <div class="lf-card" style="margin-top:12px;">
      <div class="lf-label">Bottleneck</div>
      <div class="lf-value">{_safe(bottleneck.get('stage_name', 'Not detected'))}</div>
      <div class="lf-note">{_safe(bottleneck.get('improvement_recommendation', 'Keep validating the weakest conversion step.'))}</div>
    </div>
    {_section("Marketing Message Pack")}
    <div class="lf-three-grid">{''.join(message_cards[:3])}</div>
    {_section("Capacity Model")}
    <div class="lf-card-grid">
      <div class="lf-kpi"><div class="lf-label">Founder Hours</div><div class="lf-value">{_safe(capacity.get('founder_hours_available_per_week', '-'))}/wk</div></div>
      <div class="lf-kpi"><div class="lf-label">Max Customers/Orders</div><div class="lf-value">{_safe(capacity.get('max_customers_or_orders_per_week', '-'))}</div></div>
      <div class="lf-kpi"><div class="lf-label">Bottleneck</div><div class="lf-note">{_safe(capacity.get('bottleneck', 'Not available'))}</div></div>
      <div class="lf-kpi"><div class="lf-label">Scaling Constraint</div><div class="lf-note">{_safe(capacity.get('scaling_constraint', 'Not available'))}</div></div>
    </div>
    """


def render_finance(pack: Any) -> str:
    data = _pack_dict(pack)
    if not data:
        return _placeholder()
    scenarios = (data.get("scenario_forecasts") or {}).get("scenarios", [])
    startup = data.get("startup_costs") or {}
    assumptions = data.get("cashflow_assumptions") or {}
    pricing = data.get("pricing_scenarios") or []
    total_startup = sum(startup.values())
    scenario_rows = "".join(
        f"<tr><td>{_safe(row.get('scenario'))}</td><td>{_safe(row.get('break_even_month'))}</td><td>{_money(data, row.get('month_3_revenue'))}</td><td>{_money(data, (row.get('cumulative_cashflow') or [0])[-1])}</td></tr>"
        for row in scenarios
    )
    pricing_cards = "".join(
        f"<div class='lf-card'><div class='lf-label'>{_safe(row.get('tier'))}</div><div class='lf-value'>{_safe(row.get('recommended_price'))}</div><div class='lf-note'>{_safe(row.get('rationale'))}</div></div>"
        for row in pricing[:3]
    )
    startup_rows = "".join(f"<tr><td>{_safe(name)}</td><td>{_money(data, value)}</td></tr>" for name, value in startup.items())
    return f"""
    <div class="lf-finance-section">
    {_section("Finance Command Deck", "Planning forecast, not financial advice")}
    <div class="lf-card-grid">
      <div class="lf-kpi"><div class="lf-label">Startup Cost</div><div class="lf-value">{_money(data, total_startup)}</div><div class="lf-note">Founder-input planning budget.</div></div>
      <div class="lf-kpi"><div class="lf-label">Modelled Break-even</div><div class="lf-value">Month {_safe(data.get('breakeven_month'))}</div><div class="lf-note">Deterministic scenarios, not probability.</div></div>
      <div class="lf-kpi"><div class="lf-label">Worst-case Gap</div><div class="lf-value">{_money(data, (data.get('scenario_forecasts') or {}).get('worst_case_gap'))}</div></div>
      <div class="lf-kpi"><div class="lf-label">Key Validation</div><div class="lf-note">{_safe((data.get('scenario_forecasts') or {}).get('key_assumption_to_validate', 'customer conversion rate'))}</div></div>
    </div>
    {_section("Pricing Scenarios")}
    <div class="lf-three-grid">{pricing_cards}</div>
    {_section("Scenario Table")}
    <div class="lf-card"><table class="lf-table"><thead><tr><th>Scenario</th><th>Break-even</th><th>M3 revenue</th><th>M3 cumulative</th></tr></thead><tbody>{scenario_rows}</tbody></table></div>
    <div class="lf-two-grid" style="margin-top:12px;">
      <div class="lf-card"><div class="lf-label">Startup Cost Breakdown</div><table class="lf-table"><tbody>{startup_rows}</tbody></table></div>
      <div class="lf-card"><div class="lf-label">Assumptions</div><div class="lf-note"><strong>Revenue:</strong></div>{_list_html(assumptions.get('revenue', []), 3)}<div class="lf-note"><strong>Costs:</strong></div>{_list_html(assumptions.get('costs', []), 3)}</div>
    </div>
    <div class="lf-risk-card" style="margin-top:12px;"><div class="lf-note">{_safe(data.get('forecast_disclaimer', 'Planning forecast only; not financial advice.'))}</div></div>
    </div>
    """


def forecast_plot(pack: Any) -> go.Figure:
    data = _pack_dict(pack)
    fig = go.Figure()
    if not data:
        fig.update_layout(template="plotly_dark", title="Generate a launch pack to activate forecast")
        return fig
    scenarios = (data.get("scenario_forecasts") or {}).get("scenarios", [])
    colors = {"conservative": "#f59e0b", "base": "#22d3ee", "aggressive": "#22c55e"}
    months = ["Month 1", "Month 2", "Month 3"]
    for row in scenarios:
        name = str(row.get("scenario", "scenario")).title()
        values = row.get("cumulative_cashflow") or []
        fig.add_trace(
            go.Scatter(
                x=months,
                y=values,
                mode="lines+markers",
                name=name,
                line=dict(width=4, color=colors.get(str(row.get("scenario")), "#8b5cf6")),
                marker=dict(size=9),
                fill="tozeroy" if str(row.get("scenario")) == "base" else None,
                fillcolor="rgba(34,211,238,0.12)" if str(row.get("scenario")) == "base" else None,
            )
        )
    fig.update_layout(
        template="plotly_dark",
        title=dict(text="Scenario Forecast - Cumulative Cashflow", font=dict(size=18, color="#eef5ff")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.035)",
        font=dict(color="#dbeafe"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=18, t=58, b=40),
        height=330,
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(34,211,238,0.35)")
    return fig


def render_action_plan(pack: Any) -> str:
    data = _pack_dict(pack)
    if not data:
        return _placeholder()
    roadmap = data.get("roadmap") or []
    priority = {item.get("day"): item for item in data.get("roadmap_priority_scores") or []}
    operations = data.get("operations_checklist") or []
    cards = []
    for task in roadmap:
        score = priority.get(task.get("day"), {})
        cards.append(
            f"""
            <div class="lf-card">
              <span class="lf-mini-chip">Day {_safe(task.get('day'))} / Week {_safe(task.get('week'))}</span>
              <div class="lf-module-title" style="margin-top:10px;">{_safe(task.get('title'))}</div>
              <div class="lf-note">{_safe(task.get('outcome'))}</div>
              <div style="display:flex;flex-wrap:wrap;gap:7px;margin-top:10px;">
                {_status_chip('Priority ' + str(score.get('priority_score', '-')))}
                {_status_chip(_safe(task.get('category', 'Launch')))}
                {_status_chip('Risk reduction ' + str(score.get('risk_reduction', '-')))}
              </div>
            </div>
            """
        )
    return f"""
    {_section("30-Day Launch Tracker", "Milestones with completion outcomes")}
    <div class="lf-three-grid">{''.join(cards)}</div>
    {_section("Operations Checklist")}
    <div class="lf-two-grid">
      <div class="lf-card">{_list_html(operations[: math.ceil(len(operations)/2)])}</div>
      <div class="lf-card">{_list_html(operations[math.ceil(len(operations)/2):])}</div>
    </div>
    """


def render_export(pack: Any) -> str:
    data = _pack_dict(pack)
    if not data:
        return _placeholder()
    preview = "\n".join(
        [
            "Launch Pack Ready",
            f"Business type: {_business_label(data)}",
            f"Readiness: {data.get('readiness_score')}/100 ({data.get('launch_readiness_label')})",
            f"Break-even: Month {data.get('breakeven_month')}",
            f"Next action: {(data.get('next_3_actions') or ['Not available'])[0]}",
        ]
    )
    included = [
        "classification evidence",
        "personas and segment scores",
        "offer ladder and pricing scenarios",
        "cashflow assumptions and forecast",
        "King's Trust-style business plan sections",
        "roadmap, risks, and next actions",
        "agent trace and technical artefacts",
    ]
    return f"""
    {_section("Launch Pack Deliverables", "Business Plan generated using the King's Trust-style section structure.")}
    <div class="lf-three-grid">
      <div class="lf-card"><div class="lf-label">Launch Pack Markdown</div><div class="lf-value">Readable Pack</div><div class="lf-note">Best for Kaggle writeup, review, or sharing.</div></div>
      <div class="lf-card"><div class="lf-label">Structured JSON</div><div class="lf-value">Audit Data</div><div class="lf-note">Best for debugging, downstream tooling, or technical review.</div></div>
      <div class="lf-card"><div class="lf-label">Business Plan DOCX</div><div class="lf-value">Template Style</div><div class="lf-note">Generated as DOCX when python-docx is installed.</div></div>
      <div class="lf-card"><div class="lf-label">Business Plan Markdown</div><div class="lf-value">Previewable</div><div class="lf-note">Always available as a complete structured plan.</div></div>
    </div>
    <div class="lf-two-grid" style="margin-top:12px;">
      <div class="lf-card"><div class="lf-label">Included</div>{_list_html(included)}</div>
      <div class="lf-card"><div class="lf-label">Preview</div><div class="lf-export-preview">{_safe(preview)}</div></div>
    </div>
    """


def render_business_plan_preview(pack: Any) -> str:
    data = _pack_dict(pack)
    if not data:
        return """
        <div class="lf-card">
          <div class="lf-label">Business Plan Markdown Preview</div>
          <div class="lf-note">Generate a launch pack to preview the King's Trust-style business plan export.</div>
        </div>
        """
    markdown = generate_business_plan_markdown(data)
    return f"""
    {_section("Business Plan Markdown Preview", "Structured plan preview generated from the current launch pack")}
    <div class="lf-card"><div class="lf-plan-preview">{_markdown_to_document_html(markdown)}</div></div>
    """


def empty_plot() -> go.Figure:
    return forecast_plot(None)


def generate_pack(
    idea: str,
    budget: float,
    location: str,
    resources: str,
    timeframe: str,
    stage: str,
    target_customer: str,
    privacy_mode: bool,
) -> Tuple[Any, str, str, str, str, str, go.Figure, str, str, str, List[Dict[str, str]], str]:
    if not str(idea or "").strip():
        message = "<div class='lf-risk-card'><div class='lf-value'>Founder brief needed</div><div class='lf-note'>Enter a business idea or load a demo preset first.</div></div>"
        return None, render_topbar(None), message, message, message, message, empty_plot(), message, message, render_business_plan_preview(None), [], render_copilot_meta(None)
    try:
        pack = run_launchforge_workflow(
            BusinessInput(
                idea=idea,
                budget=float(budget or 0),
                location=location or "Online",
                founder_resources=resources or "",
                timeframe=timeframe or "30 days",
                stage=stage or "Idea only",
                target_customer=target_customer or None,
                privacy_mode=bool(privacy_mode),
            )
        )
        data = model_to_dict(pack)
        welcome = [
            {
                "role": "assistant",
                "content": (
                    f"Launch pack generated for {_business_label(data)}. Ask me about the target segment, "
                    "readiness score, finance assumptions, funnel bottleneck, or next action."
                ),
            }
        ]
        return (
            data,
            render_topbar(data),
            render_overview(data),
            render_opportunity(data),
            render_market(data),
            render_finance(data),
            forecast_plot(data),
            render_action_plan(data),
            render_export(data),
            render_business_plan_preview(data),
            welcome,
            render_copilot_meta({"mode": data.get("runtime_status", {}).get("mode"), "provider": data.get("runtime_status", {}).get("provider"), "sources_used": ["launch_pack"], "fallback_reason": None}),
        )
    except Exception as exc:  # noqa: BLE001
        friendly = (
            "<div class='lf-risk-card'><div class='lf-value'>Generation paused</div>"
            f"<div class='lf-note'>LaunchForge could not generate the pack: {_safe(type(exc).__name__)}. "
            "Please check the founder brief and try again.</div></div>"
        )
        return None, render_topbar(None), friendly, friendly, friendly, friendly, empty_plot(), friendly, friendly, render_business_plan_preview(None), [], render_copilot_meta(None)


def load_preset(name: str) -> Tuple[str, int, str, str, str, str, str]:
    preset = DEMO_PRESETS[name]
    return (
        preset["idea"],
        int(preset["budget"]),
        preset["location"],
        preset["resources"],
        preset["timeframe"],
        preset["stage"],
        preset["target"],
    )


def render_copilot_meta(result: Dict[str, Any] | None) -> str:
    if not result:
        return """
        <div class="lf-meta-card">
          <strong>Copilot status:</strong> standby<br>
          Generate a launch pack, then ask about the dashboard, agents, or your launch plan.
        </div>
        """
    sources = ", ".join(result.get("sources_used") or []) or "not reported"
    fallback = _friendly_fallback_reason(result.get("fallback_reason") or result.get("error"))
    fallback_html = f"<br><strong>Fallback:</strong> {_safe(fallback)}" if fallback else ""
    return f"""
    <div class="lf-meta-card">
      <strong>Mode:</strong> {_safe(result.get('mode', 'deterministic-fallback'))}<br>
      <strong>Provider:</strong> {_safe(result.get('provider', 'fallback'))}<br>
      <strong>Model:</strong> {_safe(result.get('model', get_runtime_status().get('model', 'gemini-2.5-flash')))}<br>
      <strong>Sources:</strong> {_safe(sources)}
      {fallback_html}
    </div>
    """


def _friendly_fallback_reason(reason: Any) -> str:
    text = str(reason or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    if any(term in lowered for term in ["resource_exhausted", "quota", "429", "rate limit", "rate_limit"]):
        return "Gemini quota or rate limit was reached, so LaunchForge used the deterministic fallback."
    if any(term in lowered for term in ["api key", "google_api_key", "permission", "unauthorized", "403", "401"]):
        return "Gemini credentials were unavailable or rejected, so LaunchForge used the deterministic fallback."
    if "live web search is not configured" in lowered:
        return "Live web search was not configured, so Copilot answered without web grounding."
    if len(text) > 180:
        return text[:177].rstrip() + "..."
    return text


def gradio_ask_copilot(question: str, pack: Any, active_section: str | None) -> Dict[str, Any]:
    result = ask_launchforge_copilot(question, pack, active_section=active_section or "Overview")
    result["fallback_reason"] = _friendly_fallback_reason(result.get("fallback_reason") or result.get("error"))
    return result


def ask_copilot_ui(question: str, history: List[Dict[str, str]] | None, pack: Any, active_section: str | None) -> Tuple[str, List[Dict[str, str]], str]:
    history = list(history or [])
    question = str(question or "").strip()
    if not question:
        return "", history, render_copilot_meta(None)
    history.append({"role": "user", "content": question})
    if not pack:
        result = {
            "answer": "Generate a launch pack first, then I can explain the dashboard, agents, and launch plan.",
            "mode": "deterministic-fallback",
            "provider": "local-ui-guard",
            "sources_used": [],
            "fallback_reason": None,
        }
    else:
        try:
            result = gradio_ask_copilot(question, pack, active_section)
        except Exception as exc:  # noqa: BLE001
            result = {
                "answer": "Copilot hit a recoverable issue. Try a more specific launch-pack question or check Gemini quota/configuration.",
                "mode": "deterministic-fallback",
                "provider": "gradio-ui-guard",
                "sources_used": ["launch_pack"],
                "fallback_reason": _friendly_fallback_reason(str(exc)),
            }
    history.append({"role": "assistant", "content": str(result.get("answer", ""))})
    return "", history, render_copilot_meta(result)


def set_quick_prompt(prompt: str) -> str:
    return prompt


def write_export_file(pack: Any, format_name: str) -> str | None:
    data = _pack_dict(pack)
    if not data:
        return None
    suffix = ".md" if format_name == "markdown" else ".json"
    text = export_markdown(data) if format_name == "markdown" else export_json(data)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=suffix, prefix="launchforge_", delete=False) as handle:
        handle.write(text)
        return handle.name


def _export_status(title: str, note: str, good: bool = True) -> str:
    cls = "lf-card" if good else "lf-risk-card"
    return f"<div class='{cls}'><div class='lf-label'>{_safe(title)}</div><div class='lf-note'>{_safe(note)}</div></div>"


def export_markdown_file(pack: Any) -> Tuple[str | None, str]:
    path = write_export_file(pack, "markdown")
    if not path:
        return None, _export_status("Export unavailable", "Generate a launch pack first.", good=False)
    return path, _export_status("Launch Pack Markdown ready", "Readable launch pack export prepared.")


def export_json_file(pack: Any) -> Tuple[str | None, str]:
    path = write_export_file(pack, "json")
    if not path:
        return None, _export_status("Export unavailable", "Generate a launch pack first.", good=False)
    return path, _export_status("Structured JSON ready", "Machine-readable launch pack export prepared.")


def export_business_plan_markdown_file(pack: Any) -> Tuple[str | None, str]:
    data = _pack_dict(pack)
    if not data:
        return None, _export_status("Business plan unavailable", "Generate a launch pack first.", good=False)
    text = generate_business_plan_markdown(data)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", prefix="launchforge_business_plan_", delete=False) as handle:
        handle.write(text)
        return handle.name, _export_status("Business Plan Markdown ready", "Complete King's Trust-style business plan Markdown export prepared.")


def export_business_plan_docx_file(pack: Any) -> Tuple[str | None, str]:
    data = _pack_dict(pack)
    if not data:
        return None, _export_status("Business plan unavailable", "Generate a launch pack first.", good=False)
    try:
        path = generate_business_plan_docx(data)
        return path, _export_status("Business Plan DOCX ready", "DOCX export prepared from the current launch pack.")
    except RuntimeError as exc:
        text = generate_business_plan_markdown(data)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", prefix="launchforge_business_plan_fallback_", delete=False) as handle:
            handle.write(text)
            return handle.name, _export_status("DOCX needs python-docx", f"{exc} A Markdown business plan fallback has been prepared.", good=False)


def build_app() -> gr.Blocks:
    with gr.Blocks(title="LaunchForge Gradio", elem_id="lf-root") as demo:
        pack_state = gr.State(None)
        chat_state = gr.State([])
        active_section_state = gr.State("Overview")

        with gr.Row(equal_height=False, elem_classes=["lf-app-grid"]):
            with gr.Column(scale=2, min_width=260, elem_classes=["lf-left-rail"]):
                gr.HTML(
                    """
                    <div class="lf-brand">
                      <div class="lf-logo">LaunchForge</div>
                      <div class="lf-subtle">Holographic AI business command centre</div>
                      <div style="margin-top:10px;"><span class="lf-status-chip">Experimental Gradio Frontend</span></div>
                    </div>
                    <div class="lf-command-heading">Navigation</div>
                    """
                )
                nav_html = gr.HTML(render_sidebar_nav("Overview"))
                gr.HTML("<div class='lf-command-heading'>Demo Presets</div>")
                with gr.Row():
                    tutoring_btn = gr.Button("Tutoring", size="sm", elem_classes=["lf-demo-btn"])
                    shop_btn = gr.Button("Corner Shop", size="sm", elem_classes=["lf-demo-btn"])
                    shopify_btn = gr.Button("Shopify", size="sm", elem_classes=["lf-demo-btn"])

                gr.HTML("<div class='lf-command-heading'>Founder Brief</div>")
                idea = gr.Textbox(label="Business idea", lines=5, placeholder="Describe the business you want to launch...")
                budget = gr.Number(label="Budget", value=1000, precision=0)
                location = gr.Textbox(label="Location / online", value="Online")
                resources = gr.Textbox(label="Founder skills/resources", lines=3)
                timeframe = gr.Textbox(label="Target launch timeframe", value="30 days")
                stage = gr.Dropdown(["Idea only", "Testing", "Ready to launch"], value="Idea only", label="Business stage")
                target_customer = gr.Textbox(label="Optional target customer")
                privacy_mode = gr.Checkbox(label="Privacy mode: do not store my idea unless I export", value=True)
                generate_btn = gr.Button("Generate Launch Pack", variant="primary")
                gr.HTML(
                    "<div class='lf-subtle'>Financial outputs are planning assumptions, not financial advice. The Streamlit app remains the stable full technical dashboard.</div>"
                )

            with gr.Column(scale=6, min_width=0, elem_classes=["lf-main-canvas"]):
                topbar = gr.HTML(render_topbar(None))
                with gr.Tabs():
                    with gr.Tab("Overview") as overview_tab:
                        overview_html = gr.HTML(_placeholder())
                    with gr.Tab("Opportunity") as opportunity_tab:
                        opportunity_html = gr.HTML(_placeholder())
                    with gr.Tab("Market") as market_tab:
                        market_html = gr.HTML(_placeholder())
                    with gr.Tab("Finance") as finance_tab:
                        finance_html = gr.HTML(_placeholder())
                        finance_plot = gr.Plot(value=empty_plot(), label="Scenario forecast")
                    with gr.Tab("Action Plan") as action_tab:
                        action_html = gr.HTML(_placeholder())
                    with gr.Tab("Export") as export_tab:
                        export_html = gr.HTML(_placeholder())
                        business_plan_preview = gr.HTML(render_business_plan_preview(None))
                        with gr.Row(elem_classes=["lf-export-actions"]):
                            md_btn = gr.Button("Prepare Launch Pack Markdown", variant="primary")
                            json_btn = gr.Button("Prepare JSON")
                        with gr.Row(elem_classes=["lf-export-actions"]):
                            business_docx_btn = gr.Button("Prepare Business Plan DOCX", variant="primary")
                            business_md_btn = gr.Button("Prepare Business Plan Markdown")
                        export_status = gr.HTML("")
                        export_file = gr.File(label="Prepared export", elem_classes=["lf-export-file"])

            with gr.Column(scale=3, min_width=300, elem_classes=["lf-copilot-panel"]):
                gr.HTML(
                    """
                    <div class="lf-copilot-title">
                      <strong>LaunchForge Copilot</strong>
                      <span class="lf-status-chip">Context Router Online</span>
                    </div>
                    <div class="lf-subtle">Ask about this dashboard, the agents, your launch pack, or external/general context when Gemini is configured.</div>
                    """
                )
                runtime_status_html = gr.HTML(render_runtime_status_card())
                chatbot = gr.Chatbot(label="Command channel", height=470)
                copilot_meta = gr.HTML(render_copilot_meta(None))
                gr.HTML("<div class='lf-command-heading'>Quick Prompts</div>")
                with gr.Row(elem_classes=["lf-quick-row"]):
                    prompt_segment = gr.Button("Target?", size="sm", elem_classes=["lf-quick-btn"])
                    prompt_finance = gr.Button("Finance?", size="sm", elem_classes=["lf-quick-btn"])
                with gr.Row(elem_classes=["lf-quick-row"]):
                    prompt_next = gr.Button("Next?", size="sm", elem_classes=["lf-quick-btn"])
                    prompt_risk = gr.Button("Biggest risk?", size="sm", elem_classes=["lf-quick-btn"])
                with gr.Row(elem_classes=["lf-quick-row"]):
                    prompt_slogan = gr.Button("Write a slogan", size="sm", elem_classes=["lf-quick-btn"])
                    prompt_competitors = gr.Button("Find competitors", size="sm", elem_classes=["lf-quick-btn"])
                copilot_question = gr.Textbox(label="Ask Copilot", lines=2, placeholder="Ask LaunchForge Copilot...")
                ask_btn = gr.Button("Ask Copilot", variant="primary")

        preset_outputs = [idea, budget, location, resources, timeframe, stage, target_customer]
        tutoring_btn.click(lambda: load_preset("tutoring"), outputs=preset_outputs)
        shop_btn.click(lambda: load_preset("corner_shop"), outputs=preset_outputs)
        shopify_btn.click(lambda: load_preset("shopify"), outputs=preset_outputs)

        generate_outputs = [
            pack_state,
            topbar,
            overview_html,
            opportunity_html,
            market_html,
            finance_html,
            finance_plot,
            action_html,
            export_html,
            business_plan_preview,
            chatbot,
            copilot_meta,
        ]
        generate_btn.click(
            generate_pack,
            inputs=[idea, budget, location, resources, timeframe, stage, target_customer, privacy_mode],
            outputs=generate_outputs,
        )

        for tab, section in [
            (overview_tab, "Overview"),
            (opportunity_tab, "Opportunity"),
            (market_tab, "Market"),
            (finance_tab, "Finance"),
            (action_tab, "Action Plan"),
            (export_tab, "Export"),
        ]:
            tab.select(lambda section=section: set_active_section(section), outputs=[active_section_state, nav_html])

        ask_btn.click(
            ask_copilot_ui,
            inputs=[copilot_question, chatbot, pack_state, active_section_state],
            outputs=[copilot_question, chatbot, copilot_meta],
        ).then(lambda history: history, inputs=[chatbot], outputs=[chat_state])
        copilot_question.submit(
            ask_copilot_ui,
            inputs=[copilot_question, chatbot, pack_state, active_section_state],
            outputs=[copilot_question, chatbot, copilot_meta],
        ).then(lambda history: history, inputs=[chatbot], outputs=[chat_state])

        prompt_segment.click(
            lambda history, pack, active: ask_copilot_ui("Who should I target first and why?", history, pack, active),
            inputs=[chatbot, pack_state, active_section_state],
            outputs=[copilot_question, chatbot, copilot_meta],
        )
        prompt_finance.click(
            lambda history, pack, active: ask_copilot_ui("What does the Finance Agent assume?", history, pack, active),
            inputs=[chatbot, pack_state, active_section_state],
            outputs=[copilot_question, chatbot, copilot_meta],
        )
        prompt_next.click(
            lambda history, pack, active: ask_copilot_ui("What should I do first?", history, pack, active),
            inputs=[chatbot, pack_state, active_section_state],
            outputs=[copilot_question, chatbot, copilot_meta],
        )
        prompt_risk.click(
            lambda history, pack, active: ask_copilot_ui("What is the biggest risk I should validate?", history, pack, active),
            inputs=[chatbot, pack_state, active_section_state],
            outputs=[copilot_question, chatbot, copilot_meta],
        )
        prompt_slogan.click(
            lambda history, pack, active: ask_copilot_ui("Write a slogan for this launch.", history, pack, active),
            inputs=[chatbot, pack_state, active_section_state],
            outputs=[copilot_question, chatbot, copilot_meta],
        )
        prompt_competitors.click(
            lambda history, pack, active: ask_copilot_ui("Find competitors I should research.", history, pack, active),
            inputs=[chatbot, pack_state, active_section_state],
            outputs=[copilot_question, chatbot, copilot_meta],
        )

        md_btn.click(export_markdown_file, inputs=[pack_state], outputs=[export_file, export_status])
        json_btn.click(export_json_file, inputs=[pack_state], outputs=[export_file, export_status])
        business_docx_btn.click(export_business_plan_docx_file, inputs=[pack_state], outputs=[export_file, export_status])
        business_md_btn.click(export_business_plan_markdown_file, inputs=[pack_state], outputs=[export_file, export_status])

    return demo


if __name__ == "__main__":
    build_app().launch(css=CSS)
