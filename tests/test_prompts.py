from trolley.angles import ANGLES
from trolley.prompts import RESPONSE_SCHEMA, SYSTEM, build
from trolley.scenarios import RUNGS

RUNG = RUNGS[0]
ANGLE = ANGLES[1]  # actor


def test_option_order_places_act_where_requested():
    a_is_act = build(RUNG, ANGLE, option_a_is_act=True)
    b_is_act = build(RUNG, ANGLE, option_a_is_act=False)
    assert f"Option A: {RUNG.act_label}" in a_is_act.user
    assert f"Option B: {RUNG.refrain_label}" in a_is_act.user
    assert f"Option A: {RUNG.refrain_label}" in b_is_act.user
    assert f"Option B: {RUNG.act_label}" in b_is_act.user


def test_both_options_always_appear_exactly_once():
    for flag in (True, False):
        p = build(RUNG, ANGLE, option_a_is_act=flag)
        assert p.user.count(RUNG.act_label) == 1
        assert p.user.count(RUNG.refrain_label) == 1


def test_prompt_contains_preamble_body_and_question():
    p = build(RUNG, ANGLE, option_a_is_act=True)
    assert ANGLE.preamble in p.user
    assert RUNG.body in p.user
    assert ANGLE.question in p.user


def test_hash_is_deterministic_and_order_sensitive():
    first = build(RUNG, ANGLE, option_a_is_act=True)
    again = build(RUNG, ANGLE, option_a_is_act=True)
    flipped = build(RUNG, ANGLE, option_a_is_act=False)
    assert first.sha256 == again.sha256
    assert first.sha256 != flipped.sha256
    assert len(first.sha256) == 64


def test_system_prompt_guards_against_xml_tag_leakage():
    # Claude Opus 5 with thinking disabled can emit internal tags; the system
    # prompt must suppress that. See spec section 6.
    assert "XML" in SYSTEM


def test_parts_are_exposed_for_the_typed_jev_interface():
    p = build(RUNG, ANGLE, option_a_is_act=True)
    assert p.state == f"{ANGLE.preamble}\n\n{RUNG.body}"
    assert p.question == ANGLE.question
    assert p.option_a == RUNG.act_label
    assert p.option_b == RUNG.refrain_label
    # The chat rendering must be built from the same parts.
    assert p.state in p.user


def test_schema_is_closed_and_fully_required():
    props = set(RESPONSE_SCHEMA["properties"])
    assert props == {"choice", "confidence", "reason"}
    assert set(RESPONSE_SCHEMA["required"]) == props
    assert RESPONSE_SCHEMA["additionalProperties"] is False
    assert RESPONSE_SCHEMA["properties"]["choice"]["enum"] == ["A", "B"]
