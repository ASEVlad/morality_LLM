from trolley.scenarios import RUNGS, Rung


def test_ladder_has_ten_rungs_in_order():
    assert len(RUNGS) == 10
    assert [r.index for r in RUNGS] == list(range(1, 11))
    assert len({r.key for r in RUNGS}) == 10


def test_exactly_rung_three_is_the_attention_check():
    checks = [r for r in RUNGS if r.is_attention_check]
    assert len(checks) == 1
    assert checks[0].index == 3


def test_every_rung_has_substantive_text_and_distinct_options():
    for r in RUNGS:
        assert len(r.body) > 150, f"{r.key} body too short"
        assert r.act_label != r.refrain_label
        assert r.act_label.endswith(".") and r.refrain_label.endswith(".")


def test_bodies_are_angle_neutral():
    # The body must read identically under every angle, so it never says "you".
    for r in RUNGS:
        lowered = f" {r.body.lower()} "
        assert " you " not in lowered, f"{r.key} body addresses the reader"
        assert " your " not in lowered, f"{r.key} body addresses the reader"
        assert "the operator" in r.body.lower(), f"{r.key} lacks the operator"
