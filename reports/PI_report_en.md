# Report — Multi-Task Text Utility

## Architecture

Small CLI Python app that sends an instruction prompt to the LLM (via OpenRouter/OpenAI client) and expects a JSON object. `src/run_query.py` is the program entrypoint. Metrics (prompt/completion/total tokens, latency_ms, estimated_cost_usd) are appended to `metrics/metrics.json` per run.

## Prompt technique: Chain-of-Thought Trimming

We use chain-of-thought trimming: instead of a verbose internal chain-of-thought, the prompt requires a short `reasoning_summary` (1–2 sentences). This keeps explanations useful while avoiding long, brittle internal reasoning.

## Metrics and sample run

A recorded run will produce `_meta` with tokens and latency. Estimated cost uses a conservative per-1k-token cost table; these are estimates only and intended for monitoring.

## Trade-offs
- Quality vs. cost: `gpt-3.5-turbo` by default is cost-effective. Use higher-tier models for better quality at higher cost.
- JSON enforcement: we rely on prompt constraints and a fallback parser that extracts JSON from model output.