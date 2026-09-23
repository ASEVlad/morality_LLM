"""The six-model panel, the Jev reference arm, and their pricing. Rates are
USD per million tokens, verified 2026-09-23 against provider pricing pages.

PANEL and REFERENCE are deliberately separate: Jev is a decision model, not a
conversational one, and must never be pooled into the panel's act-rate table.
See spec section 2.1."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSpec:
    key: str
    api_id: str
    provider: str  # "anthropic" | "openai" | "xai" | "typesafe"
    usd_per_m_input: float
    usd_per_m_output: float


PANEL: tuple[ModelSpec, ...] = (
    ModelSpec("opus5",   "claude-opus-5",   "anthropic", 5.00, 25.00),
    ModelSpec("sonnet5", "claude-sonnet-5", "anthropic", 2.00, 10.00),
    ModelSpec("sol6",    "gpt-6-sol",       "openai",    2.00, 10.00),
    ModelSpec("terra56", "gpt-5.6-terra",   "openai",    2.00, 12.00),
    ModelSpec("grok420", "grok-4.20-0309-non-reasoning", "xai", 1.25, 2.50),
    ModelSpec("grok43",  "grok-4.3",        "xai",       1.25,  2.50),
)

# Reported separately from PANEL. Output tokens are free on Jev.
REFERENCE: tuple[ModelSpec, ...] = (
    ModelSpec("jev", "jev-latest", "typesafe", 0.042, 0.00),
)

ALL_MODELS: tuple[ModelSpec, ...] = PANEL + REFERENCE

_BY_KEY = {m.key: m for m in ALL_MODELS}


def by_key(key: str) -> ModelSpec:
    return _BY_KEY[key]


def cost_usd(spec: ModelSpec, input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens / 1_000_000 * spec.usd_per_m_input
        + output_tokens / 1_000_000 * spec.usd_per_m_output
    )
