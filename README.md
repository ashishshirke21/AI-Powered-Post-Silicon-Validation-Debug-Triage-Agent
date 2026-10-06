# AI-Powered Post-Silicon Validation & Debug Triage Agent

An **assisted** triage workflow for post-silicon validation logs. The AI never
invents a root cause — every hypothesis must cite the exact log lines that
produced it, and a guardrail drops any claim whose evidence can't be verified.

```
Validation logs → Parse → Detect failures → Correlate evidence → AI triage
→ Root-cause hypotheses → Experiment summary → Recommended next steps → Traceable report
```

## Architecture

Deterministic LangGraph pipeline:

`parse → detect → correlate → triage(LLM) → summarize`

- **parse** — raw log → structured lines; the line number is the stable evidence ID.
- **detect** — a regex/rule signature catalog (`data/signatures.yaml`) finds failures. No LLM.
- **correlate** — groups each failure with surrounding context into an evidence bundle.
- **triage** — the LLM proposes hypotheses that may only cite lines in the bundle.
- **guardrail** (`app/triage/guardrails.py`) — rejects/flags any uncited or fabricated citation.

Failure detection is fully deterministic; the LLM only reasons over already-detected,
evidence-bounded failures.

## Stack

Python 3.12 · FastAPI · Pydantic v2 · LangGraph · SQLAlchemy (SQLite) ·
OpenAI/Azure OpenAI (pluggable, with offline `mock` provider) · pytest.

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
copy .env.example .env   # set LLM_PROVIDER=openai and OPENAI_API_KEY to use a real model
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The default `LLM_PROVIDER=mock` runs the entire pipeline offline (no API key needed).

## Web UI (React + TypeScript)

With the backend running on port 8000:

```powershell
cd ui
npm install
npm run dev      # http://localhost:5173 (proxies /api to the backend)
```

Generate or upload a log, run triage, then click any evidence reference (e.g.
`L12`) to trace a hypothesis back to the exact log lines that produced it.

## API

| Method | Path | Purpose |
| ------ | ---- | ------- |
| POST | `/api/logs/generate` | Generate a synthetic log (optional `scenarios`, `seed`) |
| POST | `/api/runs` | Upload a log file |
| POST | `/api/runs/{id}/analyze` | Run the triage pipeline |
| GET | `/api/runs/{id}/report` | Structured JSON report |
| GET | `/api/runs/{id}/report.md` | Traceable Markdown report |
| GET | `/api/signatures` | Failure signature catalog |

## Testing

```powershell
.venv\Scripts\python.exe -m pytest        # 18 tests, ~92% coverage
.venv\Scripts\python.exe -m ruff check app tests
```

Key tests: detection precision vs synthetic ground truth, the evidence guardrail
(fabricated citations are dropped), and an end-to-end run proving the report
contains only evidence-backed hypotheses.

## Docker

```powershell
docker compose up --build   # serves the API on http://localhost:8000
```

## Roadmap

- Blend LLM confidence with signature severity weighting.
- PDF report export.
- Validate triage quality against a live OpenAI/Azure model.