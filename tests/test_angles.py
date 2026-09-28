from trolley.angles import ANGLES


def test_five_angles_with_unique_keys():
    assert len(ANGLES) == 5
    assert {a.key for a in ANGLES} == {
        "observer", "actor", "user_victim", "user_saved", "code",
    }


def test_every_angle_has_a_preamble_and_a_question():
    for a in ANGLES:
        assert len(a.preamble) > 20
        assert a.question.endswith("?")


def test_only_the_user_angles_mention_the_user():
    for a in ANGLES:
        mentions = "user you are assisting" in a.preamble
        assert mentions == a.key.startswith("user_"), a.key
