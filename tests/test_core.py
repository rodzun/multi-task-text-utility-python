import json
import re
from src import run_query


def test_prompt_has_instructions():
    pt = run_query.load_prompt_template()
    assert "answer" in pt
    assert "confidence" in pt
    assert "actions" in pt
    assert "reasoning_summary" in pt


def test_json_schema_example_parses():
    s = '{"answer": "ok", "confidence": 0.9, "actions": ["a"], "reasoning_summary": "r"}'
    parsed = json.loads(s)
    assert isinstance(parsed.get("answer"), str)
    assert 0.0 <= float(parsed.get("confidence")) <= 1.0
    assert isinstance(parsed.get("actions"), list)
    assert isinstance(parsed.get("reasoning_summary"), str)


def test_ask_returns_structure(monkeypatch):
    def fake_create(*args, **kwargs):
        class FakeUsage:
            prompt_tokens = 10
            completion_tokens = 20
            total_tokens = 30

        class FakeChoice:
            class Msg:
                content = '{"answer":"ok","confidence":0.9,"actions":["a"],"reasoning_summary":"r"}'
            message = Msg()

        class FakeCompletion:
            usage = FakeUsage()
            choices = [FakeChoice()]

        return FakeCompletion()

    monkeypatch.setattr(run_query.client.chat.completions, "create", fake_create)
    res = run_query.ask("How do I reset?", model="gpt-3.5-turbo")
    assert "answer" in res
    assert "confidence" in res
    assert "actions" in res
    assert "reasoning_summary" in res
    assert "_meta" in res