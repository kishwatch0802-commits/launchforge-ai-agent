# Deployment

## Local

```bash
cd launchforge
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Windows PowerShell

```powershell
cd launchforge
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud

1. Push the repository to GitHub.
2. Create a new Streamlit app.
3. Set the entry point to `app.py`.
4. Leave secrets empty for deterministic mode.
5. Optionally add `GOOGLE_API_KEY` later for Gemini-backed extensions.

## Docker

```bash
docker build -t launchforge .
docker run -p 8501:8501 launchforge
```

Then open `http://localhost:8501`.

## Production Notes

- Put secrets in the hosting platform's secret manager.
- Keep privacy mode visible and defaulted on.
- Add proper auth and encrypted persistence before storing user launch packs.
