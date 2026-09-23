"""One probe call per model: confirm reasoning can be disabled, and measure
real token usage so the full-run cost can be projected before spending."""
from typing import Any, Callable

from trolley.angles import ANGLES
from trolley.clients import CallResult, call, parse_jev_text, parse_response
from trolley.models import ModelSpec, cost_usd
from trolley.prompts import build
from trolley.scenarios import RUNGS

# Ordered most- to least-preferred. The trailing {} means "send nothing extra",
# which always connects but leaves the model at its default reasoning setting.
CANDIDATES: dict[str, list[dict[str, Any]]] = {
    "anthropic": [{"thinking": {"type": "disabled"}}, {}],
    "openai": [
        {"reasoning_effort": "none"},
        {"reasoning_effort": "minimal"},
        {"reasoning_effort": "low"},
        {},
    ],
    # No "low" fallback: it is not reasoning-off, and accepting it silently
    # passed Grok 4.7 as compliant when it was still emitting 210 thinking
    # tokens per call. Candidates are verified by reasoning_tokens below.
    "xai": [
        {"reasoning_effort": "none"},
        {},
    ],
    # Jev has no reasoning to disable; it is a decision head, not a sampler.
    "typesafe": [{}],
}

PROBE = build(RUNGS[0], ANGLES[0], option_a_is_act=True)


def discover_reasoning_off(
    spec: ModelSpec, call_fn: Callable[..., CallResult] = call
) -> tuple[dict[str, Any] | None, CallResult]:
    """Try each candidate; return the first that returns a parseable answer."""
    parse = parse_jev_text if spec.provider == "typesafe" else parse_response
    last = CallResult("", 0, 0, 0, "no candidates tried")
    for candidate in CANDIDATES[spec.provider]:
        last = call_fn(spec, PROBE, candidate, 256)
        if (
            last.error is None
            and parse(last.raw_text) is not None
            and last.reasoning_tokens == 0
        ):
            return candidate, last
    return None, last


def project_cost(
    spec: ModelSpec, input_tokens: int, output_tokens: int, calls: int
) -> float:
    return round(cost_usd(spec, input_tokens * calls, output_tokens * calls), 6)
