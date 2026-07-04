# 5-Minute Video Script

## 0:00 Problem

"Many small-business founders start with a rough idea, but generic AI advice does not tell them what to do this week. A tutoring business, a corner shop, and a Shopify store need completely different launch plans."

## 0:30 Solution

"LaunchForge is an adaptive multi-agent small business launch studio. I enter an idea, budget, location, stage, resources, and timeframe. It classifies the business type and generates a visual launch pack."

## 1:00 Architecture

"The app uses an ADK-style sequential agent runtime. Each agent has a role: classifier, market, offer, pricing, marketing, operations, finance, roadmap, critic, and visual pack. The agents share a context and validate the final output with Pydantic."

Show `docs/architecture.md`, `workflow.py`, and `AGENTS.md`.

## 1:45 Demo Local Service Business

Click "Load Tutoring Demo" and generate. Show the classification, personas, offer ladder, pricing, WhatsApp copy, referral loops, booking operations, and next 3 actions.

## 2:30 Demo Physical Retail Business

Click "Load Corner Shop Demo" and generate. Show footfall-focused funnel, stock/supplier checklist, commuter bundle, daily cash-up, and retail-specific risks.

## 3:15 Demo Ecommerce Business

Click "Load Shopify Demo" and generate. Show hero product validation, bundle pricing, product-page funnel, content hooks, fulfilment checklist, and cashflow chart.

## 4:00 Technical Build

"This project demonstrates ADK-style agents, MCP tools, agent skills, security, and deployability. The MCP layer exposes classification, pricing, cashflow, funnel, launch tasks, and export. Skills wrap cashflow, funnel, export, and pack assembly. Security features include no hard-coded keys, input sanitization, privacy mode, no disk writes for user ideas, and export-only downloads."

Show `mcp_server/tools.py`, `skills/`, `docs/security.md`, `Dockerfile`, and tests.

## 4:45 Conclusion

"LaunchForge is capstone-ready because it is a complete working app, not just a prototype prompt. It adapts outputs by business type and gives founders a practical launch pack they can act on immediately."
