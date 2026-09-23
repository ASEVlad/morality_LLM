from trolley.scenarios import RUNGS, Rung


def test_twelve_rungs_declared_in_index_order():
    assert len(RUNGS) == 12
    assert [r.index for r in RUNGS] == list(range(1, 13))
    assert len({r.key for r in RUNGS}) == 12


def test_the_ladder_itself_is_the_nine_escalating_rungs():
    ladder = [r for r in RUNGS if r.in_ladder]
    assert len(ladder) == 9
    # The reading tests and the age pair sit off the escalation axis and must
    # never be pooled into the per-rung figures.
    assert {r.key for r in RUNGS if not r.in_ladder} == {
        "switch_5v1_rev", "switch_5v3_rev", "switch_5old_v3child",
    }


def test_both_reversed_cases_are_attention_checks():
    checks = {r.key for r in RUNGS if r.is_attention_check}
    assert checks == {"switch_5v1_rev", "switch_5v3_rev"}
    # The age pair is NOT a reading test: pulling is defensible there if you
    # weigh children over the elderly, which is the whole point of the pair.
    age = next(r for r in RUNGS if r.key == "switch_5old_v3child")
    assert age.is_attention_check is False


def test_the_age_pair_differs_only_in_who_is_standing_where():
    rev = next(r for r in RUNGS if r.key == "switch_5v3_rev")
    age = next(r for r in RUNGS if r.key == "switch_5old_v3child")
    assert rev.act_label == age.act_label
    assert "three children" in age.body and "five elderly" in age.body
    assert "children" not in rev.body and "elderly" not in rev.body


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
