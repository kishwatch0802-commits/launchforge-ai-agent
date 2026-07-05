# Security and Privacy

LaunchForge is designed as a lightweight capstone MVP with sensible defaults.

## API Keys

The app runs without API keys. `GOOGLE_API_KEY` is optional and read only from the environment. No key is hard-coded, printed, logged, displayed, or stored in exports. Runtime status shows only whether a key is available.

## Input Handling

User input is sanitized in `config.py` and capped to avoid accidental huge submissions. Null bytes are removed and whitespace is normalized.

Copilot input is additionally checked in `security.py`:

- prompt-injection phrases such as "ignore previous instructions" are blocked;
- email addresses are redacted;
- phone numbers are redacted;
- API-key-like strings are redacted.

If Gemini is configured, Copilot sends only the sanitized question, retrieved platform context, and compact launch-pack summary. If the Gemini call fails, the answer is labeled as fallback after AI error and deterministic fallback is used.

## Data Storage

The Streamlit app keeps inputs in session memory. It does not write user ideas to disk. The only way to persist a launch pack is for the user to click a download button for Markdown or JSON export.

## Privacy Mode

The sidebar includes "Do not store my business idea" and defaults it to enabled. In the MVP this is a visible product commitment and implementation constraint: no automatic persistence.

## Secrets and Git

`.gitignore` excludes `.env`, Streamlit secrets, cache folders, bytecode, and generated exports.

## Financial Disclaimer

Forecasts are illustrative planning assumptions. They are not financial, legal, tax, accounting, or investment advice. Real founders should validate numbers and seek professional advice where needed.

## Limitations

This MVP does not include authentication, encrypted storage, audit logs, or rate limiting because it does not persist user accounts or serve as a production multi-tenant system. Those controls should be added before production use. Gemini/ADK mode is optional and must be configured through environment variables only.
