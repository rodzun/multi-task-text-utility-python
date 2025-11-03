import os
import time
import json
import argparse
from typing import Dict, Any

from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    # We'll let the script run but raise a clear error when making API calls.
    pass

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENAI_API_KEY,
)

# Estimated pricing per 1k tokens (USD). These are approximate and for monitoring only.
MODEL_COST_PER_1K = {
    "gpt-3.5-turbo": 0.002,  # low-cost baseline (approx)
    "gpt-4-turbo": 0.03,     # higher-quality, higher-cost (approx)
}

PROMPT_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "main_prompt.txt")
PROMPT_TEMPLATE_PATH = os.path.normpath(PROMPT_TEMPLATE_PATH)
METRICS_DIR = os.path.join(os.path.dirname(__file__), "..", "metrics")
METRICS_PATH = os.path.join(METRICS_DIR, "metrics.json")
ALL_RESPONSES_PATH = os.path.join(METRICS_DIR, "all_responses.json")



def load_prompt_template() -> str:
    try:
        with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # fallback minimal template
        return (
            "You are a helpful assistant. Return a JSON object with fields answer, confidence, actions, reasoning_summary."
        )


PROMPT_TEMPLATE = load_prompt_template()


def estimate_cost(total_tokens: int, model: str) -> float:
    # cost per 1000 tokens * total_tokens / 1000
    per_k = MODEL_COST_PER_1K.get(model, MODEL_COST_PER_1K["gpt-3.5-turbo"])
    return round(per_k * (total_tokens / 1000.0), 6)


def call_model(question: str, model: str = "openai/gpt-3.5-turbo") -> Dict[str, Any]:
    # Build the instruction prompt using chain-of-thought trimming technique.
    prompt = PROMPT_TEMPLATE + "\n\nInput: \"" + question.replace('"', '\\"') + "\"\nOutput JSON:" 

    start = time.perf_counter()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a concise JSON-output assistant for support agents."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=512,
    )
    end = time.perf_counter()

    latency_ms = int((end - start) * 1000)

    usage = getattr(resp, "usage", None)
    tokens_prompt = getattr(usage, "prompt_tokens", None)
    tokens_completion = getattr(usage, "completion_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)

    estimated_cost = estimate_cost(total_tokens or 0, model)

    text = resp.choices[0].message.content.strip()

    # Try to parse the content as JSON. If it's not valid, attempt to find the first JSON block.
    parsed = None
    try:
        parsed = json.loads(text)
    except Exception:
        # attempt to extract JSON substring
        import re

        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                parsed = json.loads(m.group(0))
            except Exception:
                parsed = {"raw_output": text}
        else:
            parsed = {"raw_output": text}

    # Build final payload
    result = {
        "answer": parsed.get("answer") if isinstance(parsed, dict) else None,
        "confidence": parsed.get("confidence") if isinstance(parsed, dict) else None,
        "actions": parsed.get("actions") if isinstance(parsed, dict) else None,
        "reasoning_summary": parsed.get("reasoning_summary") if isinstance(parsed, dict) else None,
        "raw_model_output": text,
        "_meta": {
            "model": model,
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
            "total_tokens": total_tokens,
            "latency_ms": latency_ms,
            "estimated_cost_usd": estimated_cost,
        },
    }

    return result


def append_metrics(metrics: Dict[str, Any]):
    # Ensure metrics dir exists
    os.makedirs(os.path.dirname(METRICS_PATH), exist_ok=True)
    entry = metrics.copy()
    entry["timestamp"] = int(time.time())
    try:
        if os.path.exists(METRICS_PATH):
            with open(METRICS_PATH, "r+", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = []
                data.append(entry)
                f.seek(0)
                json.dump(data, f, indent=2)
        else:
            with open(METRICS_PATH, "w", encoding="utf-8") as f:
                json.dump([entry], f, indent=2)
    except Exception as e:
        print("Warning: failed to write metrics:", e)


def save_all_responses(response: Dict[str, Any]):
    """Append the full JSON response to metrics/all_responses.json for reproducibility."""
    try:
        os.makedirs(os.path.dirname(ALL_RESPONSES_PATH), exist_ok=True)
        data = []
        if os.path.exists(ALL_RESPONSES_PATH):
            try:
                with open(ALL_RESPONSES_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = []

        response["timestamp"] = time.strftime('%Y-%m-%d %H:%M:%S')
        data.append(response)

        with open(ALL_RESPONSES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    except Exception as e:
        print("Warning: failed to save response:", e)


def ask(question: str, model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set. Copy .env.example to .env and set the key.")
    resp = call_model(question, model)
    # store metrics
    metrics = {
        "question": question,
        "model": resp["_meta"]["model"],
        "tokens_prompt": resp["_meta"]["tokens_prompt"],
        "tokens_completion": resp["_meta"]["tokens_completion"],
        "total_tokens": resp["_meta"]["total_tokens"],
        "latency_ms": resp["_meta"]["latency_ms"],
        "estimated_cost_usd": resp["_meta"]["estimated_cost_usd"],
    }
    append_metrics(metrics)
    save_all_responses(resp)
    return resp


def main():
    parser = argparse.ArgumentParser(description="Run Multi-Task Text Utility CLI")
    parser.add_argument("question", type=str, help="Question to ask the assistant")
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo", help="Model to use")
    args = parser.parse_args()

    try:
        result = ask(args.question, model=args.model)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    main()
