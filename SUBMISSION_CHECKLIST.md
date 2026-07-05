# LaunchForge Submission Checklist

## Readiness

- Kaggle writeup ready: yes (`docs/kaggle_writeup.md`)
- Video script ready: yes (`docs/video_script.md`)
- Antigravity notes ready: yes (`docs/antigravity_notes.md`)
- Security notes ready: yes (`docs/security.md`)
- Deployment docs included: yes (`docs/deployment.md`, `Dockerfile`, README)
- Tests passing locally: yes, confirm with `pytest`

## Media Gallery Assets Needed

- App overview screenshot after generating the Tutoring demo.
- Agent trace screenshot showing the specialist agents completed.
- Customers & Offer screenshot showing persona cards and offer ladder.
- Pricing & Finance screenshot showing pricing table and cashflow chart.
- Marketing & Operations screenshot showing funnel and tailored copy.
- Roadmap screenshot showing 30-day task cards.
- Optional short GIF or clip cycling through the three demo buttons.

Suggested filenames:

- `assets/screenshot_overview.png`
- `assets/screenshot_customers_offer.png`
- `assets/screenshot_finance.png`
- `assets/screenshot_marketing_ops.png`
- `assets/screenshot_roadmap.png`

## Public Project Link Steps

1. Create a clean GitHub repository.
2. Commit the `launchforge/` project files.
3. Confirm `.env`, caches, logs, and generated exports are not committed.
4. Add screenshots to the README or Kaggle media gallery.
5. Paste `docs/kaggle_writeup.md` into the Kaggle writeup.
6. Add the GitHub URL and optional Streamlit Cloud URL to the Kaggle submission.

## Deployment Steps

Local:

```bash
cd launchforge
pip install -r requirements.txt
streamlit run app.py
```

Streamlit Community Cloud:

1. Push the repository to GitHub.
2. Create a new Streamlit app.
3. Set the entry point to `app.py`.
4. Leave secrets empty for deterministic demo mode.

Docker:

```bash
cd launchforge
docker build -t launchforge .
docker run -p 8501:8501 launchforge
```

## Final Manual Checks

- Run `pytest`.
- Run `streamlit run app.py` from the repo root.
- Click each demo button and generate a launch pack.
- Confirm Tutoring classifies as `local_service`.
- Confirm Corner Shop classifies as `physical_retail`.
- Confirm Shopify classifies as `ecommerce`.
- Confirm exports download as Markdown and JSON.
- Confirm no real API keys or secrets appear in files.
- Confirm financial disclaimer is visible in the UI and exports.
- Confirm deployment wording says deployable/documented, not already deployed.
