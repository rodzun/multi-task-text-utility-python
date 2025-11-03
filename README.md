# Multi-Task Text Utility (Python CLI)

Minimal runnable Python CLI that queries an LLM (via OpenRouter/OpenAI client) to return a constrained JSON response for customer-support agents. Tracks per-run metrics (tokens, latency, estimated cost) and includes a prompt-engineering technique (chain-of-thought trimming).

## Quick start

1. Copy `.env.example` to `.env` and set your `OPENAI_API_KEY` (or OpenRouter key if you're using OpenRouter).

2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Run from CLI:

```bash
python src/run_query.py "How do I reset my password?"
```

4. Run tests:

```bash
pytest -q
```

## Notes
- Default model: `gpt-3.5-turbo` for cost-efficiency. Change via `--model` flag.

## Deliverables
- `src/run_query.py` — CLI and core logic.
- `prompts/main_prompt.txt` — prompt template.
- `tests/test_core.py` — unit + integration tests (integration patched to avoid external calls by default).
- `reports/PI_report_en.md` — 1–2 page report.
- `.env.example` and `requirements.txt`.