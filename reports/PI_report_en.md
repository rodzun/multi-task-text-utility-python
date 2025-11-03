# Multi-Task Text Utility — Final Report

## 1. Architecture Overview
The **Multi-Task Text Utility** is a Python CLI application designed to interact with LLMs through the OpenRouter API (OpenAI-compatible). Its architecture is intentionally modular for clarity and reproducibility:

- **run_query.py**: Main CLI script handling argument parsing, API calls, and structured output.
- **prompt templates (/prompts)**: Defines the JSON-output instruction and reasoning constraints.
- **metrics (/metrics)**: Stores per-run metrics (tokens, latency, estimated cost) and accumulated responses in `all_responses.json`.
- **tests/**: Contains basic validation tests to ensure schema compliance.

The data flow follows this sequence:
1. User question → formatted prompt → API call
2. Response → JSON parsed → metrics logged
3. Results printed to console and stored in `metrics/all_responses.json`.

This design ensures a stable, reproducible contract for downstream systems.

---

## 2. Prompt Technique(s) Used and Rationale
The project applies the **Chain-of-Thought Trimming** technique. The prompt encourages the model to reason internally but only return structured JSON fields — avoiding verbose explanations. This ensures:
- Deterministic and parseable outputs.
- Reduced token usage (lower cost, faster latency).
- Cleaner responses for system integration.

Example template (simplified):
```
You are a helpful assistant. Return only valid JSON with fields: answer, confidence, actions, reasoning_summary.
Input: "{{question}}"
Output JSON:
```

This structure guides reasoning implicitly but trims any internal chain before the final response.

---

## 3. Metrics Summary with Sample Results
Each model interaction records key metrics for monitoring usage and efficiency:

| Metric | Description | Example Value |
|---------|--------------|----------------|
| tokens_prompt | Tokens in input prompt | 110 |
| tokens_completion | Tokens in model output | 80 |
| total_tokens | Sum of prompt + completion | 190 |
| latency_ms | API response latency | 1243 |
| estimated_cost_usd | Cost per run (approx.) | 0.0007 |
| timestamp | Unix epoch for traceability | 1730654123 |

**Sample recorded JSON response:**
```json
{
  "answer": "Photosynthesis converts sunlight into chemical energy in plants.",
  "confidence": 0.93,
  "actions": ["Summarize key stages"],
  "reasoning_summary": "The model identified the main process steps and confidence.",
  "_meta": {
    "model": "gpt-3.5-turbo",
    "latency_ms": 1243,
    "estimated_cost_usd": 0.0007
  }
}
```

---

## 4. Challenges Faced
- **Parsing reliability**: Some completions included extra text outside the JSON. This was solved by extracting the first valid JSON block using regex and fallbacks.
- **Metric persistence**: Ensuring that both metrics and responses were appended rather than overwritten required careful file handling.
- **Cost tracking**: Estimations had to balance precision with simplicity since OpenRouter pricing may vary slightly.
- **Compatibility with OpenRouter**: The API client syntax differs slightly from OpenAI’s original library, so calls were updated accordingly.

---

## 5. Improvements & Future Work
- Add **safety/adversarial prompt handling** to sanitize or reject malicious inputs.
- Integrate **unit tests** for latency and cost computation consistency.
- Implement **optional web endpoint** to expose the same contract for REST clients.
- Use **streaming responses** for faster perceived latency.

---

## 6. Summary
This project demonstrates a reliable, low-cost implementation for structured LLM responses with reproducible metrics. The combination of **prompt engineering**, **JSON schema validation**, and **automatic run logging** ensures both developer transparency and operational traceability — fulfilling all required deliverables.