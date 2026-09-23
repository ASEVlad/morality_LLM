import json

from trolley.clients import CallResult
from trolley.grid import cells_for_model
from trolley.runner import BudgetExceeded, completed_ids, record_for, run_cells

OK = '{"choice":"A","confidence":80,"reason":"because"}'
JEV_OK = json.dumps({"answers": {"decision": {
    "choice": "B", "confidence": 0.7, "probabilities": {"A": 0.3, "B": 0.7},
}}})


def ok_call(spec, prompt, reasoning_off, max_tokens):
    return CallResult(OK, 500, 100, 42, None)


def test_record_normalises_choice_to_act_when_a_is_act():
    cell = next(cells_for_model("sol6", samples=4))
    assert cell.option_a_is_act is True
    rec = record_for(cell, ok_call(None, None, None, 0), run_id="r")
    assert rec["choice"] == "A"
    assert rec["choice_normalized"] == "act"
    assert rec["parse_ok"] is True
    assert rec["refused"] is False
    assert rec["cost_usd"] > 0


def test_record_normalises_choice_to_refrain_when_b_is_act():
    cells = list(cells_for_model("sol6", samples=4))
    cell = cells[1]  # sample_idx 1 -> option_a_is_act False
    assert cell.option_a_is_act is False
    rec = record_for(cell, ok_call(None, None, None, 0), run_id="r")
    assert rec["choice"] == "A"
    assert rec["choice_normalized"] == "refrain"


def test_panel_records_have_no_probability():
    cell = next(cells_for_model("sol6", samples=4))
    assert record_for(cell, ok_call(None, None, None, 0), run_id="r")["p_act"] is None


def test_jev_probability_is_normalised_for_option_order():
    a_is_act, b_is_act = list(cells_for_model("jev", samples=2))[:2]
    assert a_is_act.option_a_is_act is True
    assert b_is_act.option_a_is_act is False
    result = CallResult(JEV_OK, 400, 0, 9, None)
    # P(A)=0.3. Where A is the act option, P(act)=0.3; flipped, P(act)=0.7.
    assert record_for(a_is_act, result, run_id="r")["p_act"] == 0.3
    assert record_for(b_is_act, result, run_id="r")["p_act"] == 0.7
    rec = record_for(a_is_act, result, run_id="r")
    assert rec["confidence"] == 70   # rescaled from Jev's 0..1
    assert rec["reason"] is None     # Jev emits no prose
    assert rec["parse_ok"] is True


def test_unparseable_response_is_recorded_as_refusal():
    cell = next(cells_for_model("sol6", samples=4))
    rec = record_for(cell, CallResult("I won't answer.", 500, 20, 5, None), run_id="r")
    assert rec["parse_ok"] is False
    assert rec["refused"] is True
    assert rec["choice_normalized"] is None


def test_run_appends_one_jsonl_line_per_cell(tmp_path):
    out = tmp_path / "r.jsonl"
    cells = list(cells_for_model("sol6", samples=4))[:6]
    run_cells(cells, out, {"sol6": {}}, budget_usd=5.0, call_fn=ok_call, run_id="r")
    lines = out.read_text().strip().split("\n")
    assert len(lines) == 6
    assert all(json.loads(ln)["model"] == "sol6" for ln in lines)


def test_resume_skips_cells_already_recorded(tmp_path):
    out = tmp_path / "r.jsonl"
    cells = list(cells_for_model("sol6", samples=4))[:6]
    run_cells(cells, out, {"sol6": {}}, budget_usd=5.0, call_fn=ok_call, run_id="r")
    done = completed_ids(out)
    assert len(done) == 6
    run_cells(cells, out, {"sol6": {}}, budget_usd=5.0, call_fn=ok_call, run_id="r")
    assert len(out.read_text().strip().split("\n")) == 6


def test_run_aborts_before_exceeding_the_budget(tmp_path):
    import pytest
    out = tmp_path / "r.jsonl"
    cells = list(cells_for_model("sol6", samples=4))
    # Each ok_call costs $0.002; the pre-call headroom check reserves $0.00416.
    # A $0.01 ceiling therefore admits three calls and refuses the fourth.
    with pytest.raises(BudgetExceeded):
        run_cells(cells, out, {"sol6": {}}, budget_usd=0.01, call_fn=ok_call, run_id="r")
    # Whatever completed before the abort is still on disk.
    assert len(out.read_text().strip().split("\n")) == 3
