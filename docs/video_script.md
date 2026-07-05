# 5-Minute Video Script

## 0:00 Problem

"Many small-business founders start with a rough idea, but generic AI advice does not tell them what to do this week. A tutoring business, a corner shop, and a Shopify store need completely different launch plans."

## 0:30 Solution

"LaunchForge is an adaptive multi-agent small business launch studio. I enter an idea, budget, location, stage, resources, and timeframe. It classifies the business type and generates a visual launch pack."

## 1:00 Architecture

"The app uses a three-layer architecture. The top layer is a set of ADK/LlmAgent-style agent definitions: orchestrator, classifier, market, offer, pricing, marketing, operations, finance, roadmap, critic, visual packaging, and Copilot. Under that, deterministic MCP-style tools do the reliable calculations. The dashboard shows both layers separately in the Agent Control Room."

Show `docs/architecture.md`, `agent_registry.py`, `adk_runtime.py`, `workflow.py`, and `AGENTS.md`.

## 1:45 Demo Local Service Business

Click "Load Tutoring Demo" and generate. Show the classification, personas, offer ladder, pricing, WhatsApp copy, referral loops, booking operations, and next 3 actions.

## 2:30 Demo Physical Retail Business

Click "Load Corner Shop Demo" and generate. Show footfall-focused funnel, stock/supplier checklist, commuter bundle, daily cash-up, and retail-specific risks.

## 3:15 Demo Ecommerce Business

Click "Load Shopify Demo" and generate. Show hero product validation, bundle pricing, product-page funnel, content hooks, fulfilment checklist, and cashflow chart.

## 4:00 Technical Build

"This project demonstrates ADK/LlmAgent-style agent definitions, a real Gemini Copilot path through google-genai when a key is configured, deterministic MCP tools, agent skills, security, and deployability. LaunchForge uses deterministic tools for reliable calculations and Gemini/ADK-style agents for AI-assisted reasoning and synthesis when configured. The Agent Control Room shows runtime status, provider, model, agent definitions, tool mapping, and execution trace."

Show `agent_registry.py`, `adk_runtime.py`, `mcp_server/tools.py`, `.agents/skills/`, `docs/security.md`, `Dockerfile`, and tests. Ask Copilot: "Why is my readiness score?" Show the Finance Simulation scenario forecasts, Growth Marketing funnel bottleneck, Risk Critic findings, prompt-injection guardrail, and Export tab.

## 4:45 Conclusion

"LaunchForge is capstone-ready because it is a complete working app, not just a prototype prompt. It adapts outputs by business type and gives founders a practical launch pack they can act on immediately."
