from trolley.models import ALL_MODELS, PANEL, REFERENCE, ModelSpec, cost_usd, by_key


def test_panel_is_six_models_across_three_providers():
    assert len(PANEL) == 6
    assert {m.provider for m in PANEL} == {"anthropic", "openai", "xai"}
    assert len({m.key for m in PANEL}) == 6


def test_reference_arm_is_jev_and_is_kept_out_of_the_panel():
    assert [m.key for m in REFERENCE] == ["jev"]
    assert "jev" not in {m.key for m in PANEL}
    assert len(ALL_MODELS) == 7
    assert len({m.key for m in ALL_MODELS}) == 7


def test_jev_charges_for_input_only():
    jev = by_key("jev")
    assert jev.usd_per_m_output == 0.0
    # 1M input at $0.042/M plus 5M free output.
    assert cost_usd(jev, 1_000_000, 5_000_000) == 0.042


def test_cost_usd_uses_per_million_rates():
    spec = ModelSpec(
        key="t", api_id="t", provider="openai",
        usd_per_m_input=2.0, usd_per_m_output=10.0,
    )
    # 500_000 input tokens at $2/M = $1.00; 100_000 output at $10/M = $1.00
    assert cost_usd(spec, 500_000, 100_000) == 2.0


def test_cost_usd_is_zero_for_no_tokens():
    assert cost_usd(by_key("opus5"), 0, 0) == 0.0


def test_by_key_raises_on_unknown_model():
    import pytest
    with pytest.raises(KeyError):
        by_key("not-a-model")
