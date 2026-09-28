import pytest

from trolley.cli import _samples, build_parser


def test_budget_is_accepted_after_the_subcommand():
    # "trolley run --budget 4.5" is the form the plan documents and the form
    # anyone would type; a top-level-only flag rejects it.
    args = build_parser().parse_args(["run", "--budget", "4.5"])
    assert args.budget == 4.5
    assert args.samples is None


def test_each_subcommand_takes_the_shared_flags():
    for cmd in ("preflight", "run", "analyze"):
        args = build_parser().parse_args([cmd, "--budget", "1.0", "--samples", "2"])
        assert args.budget == 1.0
        assert args.samples == 2


def test_budget_defaults_to_five():
    assert build_parser().parse_args(["run"]).budget == 5.0


def test_samples_override_applies_to_every_model():
    assert _samples("opus5", None) == 4
    assert _samples("jev", None) == 2
    assert _samples("opus5", 6) == 6
    assert _samples("jev", 6) == 6


def test_subcommand_is_required():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])
