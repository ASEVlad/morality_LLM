"""One uniform call() over four providers."""
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from trolley.models import ModelSpec
from trolley.prompts import RESPONSE_SCHEMA, Prompt

XAI_BASE_URL = "https://api.x.ai/v1"
JEV_URL = "https://tokenra.io/v1/decisions"


@dataclass
class CallResult:
    raw_text: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    error: str | None = None


def anthropic_kwargs(
    spec: ModelSpec, prompt: Prompt, reasoning_off: dict[str, Any], max_tokens: int
) -> dict[str, Any]:
    # No temperature: Claude Opus 5 / Sonnet 5 return 400 on sampling params.
    return {
        "model": spec.api_id,
        "max_tokens": max_tokens,
        "system": prompt.system,
        "messages": [{"role": "user", "content": prompt.user}],
        "output_config": {
            "format": {"type": "json_schema", "schema": RESPONSE_SCHEMA}
        },
        **reasoning_off,
    }


def openai_kwargs(
    spec: ModelSpec, prompt: Prompt, reasoning_off: dict[str, Any], max_tokens: int
) -> dict[str, Any]:
    return {
        "model": spec.api_id,
        "max_completion_tokens": max_tokens,
        "temperature": 1.0,
        "messages": [
            {"role": "system", "content": prompt.system},
            {"role": "user", "content": prompt.user},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "trolley_choice",
                "strict": True,
                "schema": RESPONSE_SCHEMA,
            },
        },
        **reasoning_off,
    }


def jev_payload(spec: ModelSpec, prompt: Prompt) -> dict[str, Any]:
    """Jev takes free-text state plus a map of typed questions. There is no
    system prompt and no inline option text; the options are the criteria."""
    return {
        "model": spec.api_id,
        "state": prompt.state,
        "questions": {
            "decision": {
                "type": "choice",
                "instructions": prompt.question,
                "criteria": {"A": prompt.option_a, "B": prompt.option_b},
            }
        },
    }


def parse_jev_text(raw: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None
    answer = (payload.get("answers") or {}).get("decision")
    if not isinstance(answer, dict) or answer.get("choice") not in ("A", "B"):
        return None
    confidence = answer.get("confidence")
    p_a = (answer.get("probabilities") or {}).get("A")
    return {
        "choice": answer["choice"],
        # Jev reports confidence on 0..1; the rest of the panel uses 0..100.
        "confidence": (
            round(float(confidence) * 100)
            if isinstance(confidence, (int, float))
            else None
        ),
        "reason": None,  # Jev emits no prose
        "p_a": float(p_a) if isinstance(p_a, (int, float)) else None,
    }


def parse_response(raw: str) -> dict[str, Any] | None:
    """Return the validated payload, or None if the model did not comply."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    if data.get("choice") not in ("A", "B"):
        return None
    if not isinstance(data.get("confidence"), int):
        return None
    if not isinstance(data.get("reason"), str):
        return None
    return {k: data[k] for k in ("choice", "confidence", "reason")}


_clients: dict[str, Any] = {}


def _client(provider: str):
    if provider not in _clients:
        if provider == "anthropic":
            import anthropic

            _clients[provider] = anthropic.Anthropic(
                api_key=os.environ["ANTHROPIC_API_KEY"]
            )
        elif provider == "openai":
            import openai

            _clients[provider] = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        elif provider == "xai":
            import openai

            _clients[provider] = openai.OpenAI(
                api_key=os.environ["XAI_API_KEY"], base_url=XAI_BASE_URL
            )
        else:
            raise ValueError(f"unknown provider {provider}")
    return _clients[provider]


def _call_jev(prompt: Prompt, spec: ModelSpec) -> tuple[str, int, int]:
    body = json.dumps(jev_payload(spec, prompt)).encode()
    request = urllib.request.Request(
        JEV_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {os.environ['JEV_API_KEY']}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read().decode()
    usage = json.loads(raw).get("usage") or {}
    # Usage field names are unconfirmed; fall back to a 4-chars-per-token
    # estimate. Output is free and input is $0.042/M, so an error here is
    # worth fractions of a cent. Verify the field names at preflight.
    input_tokens = usage.get("input_tokens") or len(body) // 4
    return raw, int(input_tokens), 0


def call(
    spec: ModelSpec,
    prompt: Prompt,
    reasoning_off: dict[str, Any],
    max_tokens: int = 256,
) -> CallResult:
    started = time.monotonic()
    try:
        if spec.provider == "typesafe":
            text, usage_in, usage_out = _call_jev(prompt, spec)
            return CallResult(
                text, usage_in, usage_out, int((time.monotonic() - started) * 1000)
            )
        client = _client(spec.provider)
        if spec.provider == "anthropic":
            resp = client.messages.create(
                **anthropic_kwargs(spec, prompt, reasoning_off, max_tokens)
            )
            text = next(b.text for b in resp.content if b.type == "text")
            usage_in = resp.usage.input_tokens
            usage_out = resp.usage.output_tokens
        else:
            resp = client.chat.completions.create(
                **openai_kwargs(spec, prompt, reasoning_off, max_tokens)
            )
            text = resp.choices[0].message.content or ""
            usage_in = resp.usage.prompt_tokens
            usage_out = resp.usage.completion_tokens
    except Exception as exc:  # recorded, never raised into the grid loop
        return CallResult("", 0, 0, int((time.monotonic() - started) * 1000), repr(exc))
    return CallResult(
        text, usage_in, usage_out, int((time.monotonic() - started) * 1000)
    )
