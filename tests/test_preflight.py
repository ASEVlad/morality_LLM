from trolley.clients import CallResult
from trolley.preflight import CANDIDATES, discover_reasoning_off, project_cost
from trolley.models import by_key


def test_anthropic_candidates_start_with_thinking_disabled():
    assert CANDIDATES["anthropic"][0] == {"thinking": {"type": "disabled"}}


def test_jev_has_exactly_one_no_op_candidate():
    assert CANDIDATES["typesafe"] == [{}]


def test_every_provider_ends_with_an_empty_fallback():
    for provider, options in CANDIDATES.items():
        assert options[-1] == {}, f"{provider} lacks a no-op fallback"


def test_discover_returns_first_candidate_that_succeeds():
    attempts = []

    def fake_call(spec, prompt, reasoning_off, max_tokens):
        attempts.append(reasoning_off)
        ok = reasoning_off == CANDIDATES["openai"][1]
        return CallResult('{"choice":"A","confidence":1,"reason":"x"}' if ok else "",
                          10, 5, 1, None if ok else "400 bad param")

    chosen, result = discover_reasoning_off(by_key("sol6"), call_fn=fake_call)
    assert chosen == CANDIDATES["openai"][1]
    assert attempts[:2] == CANDIDATES["openai"][:2]
    assert result.error is None


def test_discover_returns_none_when_every_candidate_fails():
    def always_fail(spec, prompt, reasoning_off, max_tokens):
        return CallResult("", 0, 0, 1, "400 bad param")

    chosen, result = discover_reasoning_off(by_key("sol6"), call_fn=always_fail)
    assert chosen is None


def test_project_cost_scales_the_probe_to_the_full_grid():
    # 500 in / 100 out probe on sol6 ($2/$10) over 200 calls:
    # 200*500/1e6*2 + 200*100/1e6*10 = 0.2 + 0.2 = 0.4
    assert project_cost(by_key("sol6"), 500, 100, calls=200) == 0.4

def test_candidate_that_still_reasons_is_rejected():
    # Grok 4.7 parsed fine under reasoning_effort="low" while emitting 210
    # thinking tokens. A parseable answer is not proof that reasoning is off.
    def reasons_anyway(spec, prompt, reasoning_off, max_tokens):
        return CallResult(
            '{"choice":"A","confidence":1,"reason":"x"}', 10, 5, 1, None,
            reasoning_tokens=210,
        )

    chosen, result = discover_reasoning_off(by_key("grok43"), call_fn=reasons_anyway)
    assert chosen is None
    assert result.reasoning_tokens == 210


def test_xai_candidates_no_longer_offer_low():
    assert {"reasoning_effort": "low"} not in CANDIDATES["xai"]
