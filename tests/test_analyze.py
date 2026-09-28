import json

from trolley.analyze import ATTENTION_CHECK_RUNG, metrics, load


def write(tmp_path, records):
    p = tmp_path / "r.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return p


def rec(model="m", rung="switch_1v5", idx=1, angle="actor", norm="act", **kw):
    base = {
        "model": model, "rung": rung, "rung_index": idx, "angle": angle,
        "choice_normalized": norm, "parse_ok": norm is not None,
        "refused": norm is None, "confidence": 80, "error": None,
        "cost_usd": 0.001, "p_act": None, "option_a_is_act": True,
    }
    base.update(kw)
    return base


def test_act_rate_ignores_refusals(tmp_path):
    p = write(tmp_path, [rec(norm="act"), rec(norm="refrain"), rec(norm=None)])
    m = metrics(load(p))
    assert m["m"]["act_rate_overall"] == 0.5
    assert m["m"]["refusal_rate"] == 1 / 3


def test_means_gap_is_rung_one_minus_rung_six(tmp_path):
    rows = (
        [rec(rung="switch_1v5", idx=1, norm="act") for _ in range(4)]
        + [rec(rung="footbridge", idx=6, norm="refrain") for _ in range(4)]
    )
    m = metrics(load(write(tmp_path, rows)))
    assert m["m"]["means_gap"] == 1.0


def test_attention_check_reported_and_excluded_from_pools(tmp_path):
    rows = (
        [rec(rung="switch_1v5", idx=1, norm="refrain") for _ in range(4)]
        + [rec(rung=ATTENTION_CHECK_RUNG, idx=3, norm="act") for _ in range(4)]
    )
    m = metrics(load(write(tmp_path, rows)))
    assert m["m"]["attention_check_act_rate"] == 1.0
    assert m["m"]["attention_check_failed"] is True
    # The four "act" attention-check rows must not lift the pooled act rate.
    assert m["m"]["act_rate_overall"] == 0.0


def test_self_interest_delta_is_user_victim_minus_user_saved(tmp_path):
    rows = (
        [rec(angle="user_victim", norm="refrain") for _ in range(4)]
        + [rec(angle="user_saved", norm="act") for _ in range(4)]
    )
    m = metrics(load(write(tmp_path, rows)))
    assert m["m"]["self_interest_delta"] == -1.0


def test_angle_sensitivity_is_zero_when_all_angles_agree(tmp_path):
    rows = [rec(angle=a, norm="act") for a in
            ("observer", "actor", "user_victim", "user_saved", "code")]
    m = metrics(load(write(tmp_path, rows)))
    assert m["m"]["angle_sensitivity"] == 0.0


def test_jev_gets_a_probability_curve_and_the_panel_does_not(tmp_path):
    rows = [
        rec(model="jev", rung="switch_1v5", idx=1, p_act=0.9),
        rec(model="jev", rung="footbridge", idx=6, p_act=0.2),
        rec(model="opus5", rung="switch_1v5", idx=1),
    ]
    m = metrics(load(write(tmp_path, rows)))
    assert m["jev"]["is_reference_arm"] is True
    assert m["jev"]["p_act_by_rung"] == {"switch_1v5": 0.9, "footbridge": 0.2}
    assert m["opus5"]["is_reference_arm"] is False
    assert m["opus5"]["p_act_by_rung"] is None


def test_order_stability_is_the_gap_between_the_two_option_orders(tmp_path):
    rows = [
        rec(model="jev", p_act=0.60, option_a_is_act=True),
        rec(model="jev", p_act=0.50, option_a_is_act=False),
    ]
    m = metrics(load(write(tmp_path, rows)))
    assert abs(m["jev"]["order_stability"] - 0.10) < 1e-9
