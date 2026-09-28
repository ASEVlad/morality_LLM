import json

from trolley.clients import (
    anthropic_kwargs, jev_payload, openai_kwargs, parse_jev_text, parse_response,
)
from trolley.models import by_key
from trolley.prompts import build
from trolley.angles import ANGLES
from trolley.scenarios import RUNGS

PROMPT = build(RUNGS[0], ANGLES[1], option_a_is_act=True)


def test_anthropic_kwargs_never_send_temperature():
    kw = anthropic_kwargs(by_key("opus5"), PROMPT, {"thinking": {"type": "disabled"}}, 256)
    assert "temperature" not in kw
    assert kw["thinking"] == {"type": "disabled"}
    assert kw["model"] == "claude-opus-5"
    assert kw["output_config"]["format"]["type"] == "json_schema"


def test_openai_kwargs_set_temperature_one():
    kw = openai_kwargs(by_key("sol6"), PROMPT, {"reasoning_effort": "none"}, 256)
    assert kw["temperature"] == 1.0
    assert kw["reasoning_effort"] == "none"
    assert kw["response_format"]["json_schema"]["strict"] is True


def test_openai_kwargs_put_system_in_the_message_list():
    kw = openai_kwargs(by_key("sol6"), PROMPT, {}, 256)
    assert kw["messages"][0] == {"role": "system", "content": PROMPT.system}
    assert kw["messages"][1]["role"] == "user"


def test_parse_response_extracts_the_three_fields():
    raw = json.dumps({"choice": "B", "confidence": 70, "reason": "x"})
    parsed = parse_response(raw)
    assert parsed == {"choice": "B", "confidence": 70, "reason": "x"}


def test_parse_response_returns_none_on_non_json():
    assert parse_response("I cannot answer that.") is None


def test_parse_response_returns_none_on_wrong_choice_value():
    assert parse_response(json.dumps({"choice": "C", "confidence": 1, "reason": "x"})) is None


def test_jev_payload_sends_state_and_a_criteria_map_and_no_system_prompt():
    body = jev_payload(by_key("jev"), PROMPT)
    assert body["model"] == "jev-latest"
    assert body["state"] == PROMPT.state
    assert "system" not in body
    question = body["questions"]["decision"]
    assert question["type"] == "choice"
    assert question["instructions"] == PROMPT.question
    assert question["criteria"] == {"A": PROMPT.option_a, "B": PROMPT.option_b}


def test_parse_jev_rescales_confidence_and_extracts_probability():
    raw = json.dumps({"answers": {"decision": {
        "choice": "A", "confidence": 0.82, "probabilities": {"A": 0.82, "B": 0.18},
    }}})
    parsed = parse_jev_text(raw)
    assert parsed["choice"] == "A"
    assert parsed["confidence"] == 82   # Jev reports 0..1, the panel 0..100
    assert parsed["p_a"] == 0.82
    assert parsed["reason"] is None     # Jev emits no prose


def test_parse_jev_returns_none_on_a_malformed_envelope():
    assert parse_jev_text(json.dumps({"answers": {}})) is None
    assert parse_jev_text("not json") is None

def test_out_of_range_confidence_is_clamped_not_rejected():
    # The choice is the primary metric and must survive a bad confidence.
    high = parse_response(json.dumps({"choice": "A", "confidence": 150, "reason": "x"}))
    low = parse_response(json.dumps({"choice": "B", "confidence": -20, "reason": "x"}))
    assert high == {"choice": "A", "confidence": 100, "reason": "x"}
    assert low == {"choice": "B", "confidence": 0, "reason": "x"}


def test_xai_non_reasoning_model_takes_no_reasoning_parameter():
    # grok-4.20-0309-non-reasoning rejects reasoning_effort outright, so the
    # empty candidate must produce a clean request.
    kw = openai_kwargs(by_key("grok420"), PROMPT, {}, 256)
    assert "reasoning_effort" not in kw
    assert kw["model"] == "grok-4.20-0309-non-reasoning"
