"""Walk the grid, append JSONL per call, resume, and stop at the budget."""
import json
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from trolley.clients import CallResult, call, parse_jev_text, parse_response
from trolley.grid import Cell
from trolley.models import by_key, cost_usd
from trolley.prompts import build

MAX_TOKENS = 256
# Worst case for the pre-call budget check: full prompt in, cap out.
WORST_CASE_INPUT = 800


class BudgetExceeded(RuntimeError):
    pass


def cell_id(cell: Cell) -> tuple[str, str, str, int]:
    return (cell.model_key, cell.rung.key, cell.angle.key, cell.sample_idx)


def completed_ids(path: Path) -> set[tuple[str, str, str, int]]:
    path = Path(path)
    if not path.exists():
        return set()
    done = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        done.add((r["model"], r["rung"], r["angle"], r["sample_idx"]))
    return done


def record_for(cell: Cell, result: CallResult, run_id: str) -> dict[str, Any]:
    spec = by_key(cell.model_key)
    prompt = build(cell.rung, cell.angle, cell.option_a_is_act)

    if result.error is not None:
        parsed = None
    elif spec.provider == "typesafe":
        parsed = parse_jev_text(result.raw_text)
    else:
        parsed = parse_response(result.raw_text)

    normalized = None
    if parsed is not None:
        chose_a = parsed["choice"] == "A"
        normalized = "act" if chose_a == cell.option_a_is_act else "refrain"

    # Jev alone returns a distribution. Normalise it onto the act option so it
    # is comparable across both option orders.
    p_a = parsed.get("p_a") if parsed else None
    p_act = None if p_a is None else (p_a if cell.option_a_is_act else 1.0 - p_a)

    return {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": cell.model_key,
        "rung": cell.rung.key,
        "rung_index": cell.rung.index,
        "angle": cell.angle.key,
        "sample_idx": cell.sample_idx,
        "option_a_is_act": cell.option_a_is_act,
        "prompt_sha256": prompt.sha256,
        "raw_response": result.raw_text,
        "choice": parsed["choice"] if parsed else None,
        "choice_normalized": normalized,
        "confidence": parsed["confidence"] if parsed else None,
        "reason": parsed["reason"] if parsed else None,
        "p_act": p_act,
        "parse_ok": parsed is not None,
        "refused": parsed is None and result.error is None,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "cost_usd": cost_usd(spec, result.input_tokens, result.output_tokens),
        "latency_ms": result.latency_ms,
        "error": result.error,
    }


def run_cells(
    cells: Iterable[Cell],
    out_path: Path,
    reasoning_off: dict[str, dict[str, Any]],
    budget_usd: float,
    call_fn: Callable[..., CallResult] = call,
    run_id: str | None = None,
) -> float:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    done = completed_ids(out_path)
    spent = sum(
        json.loads(ln)["cost_usd"]
        for ln in out_path.read_text().splitlines()
        if ln.strip()
    ) if out_path.exists() else 0.0

    with out_path.open("a") as fh:
        for cell in cells:
            if cell_id(cell) in done:
                continue
            spec = by_key(cell.model_key)
            headroom = cost_usd(spec, WORST_CASE_INPUT, MAX_TOKENS)
            if spent + headroom > budget_usd:
                raise BudgetExceeded(
                    f"spent ${spent:.4f}; next call could reach "
                    f"${spent + headroom:.4f}, over the ${budget_usd:.2f} ceiling"
                )
            prompt = build(cell.rung, cell.angle, cell.option_a_is_act)
            result = call_fn(
                spec, prompt, reasoning_off[cell.model_key], MAX_TOKENS
            )
            record = record_for(cell, result, run_id)
            fh.write(json.dumps(record) + "\n")
            fh.flush()
            spent += record["cost_usd"]
    return spent
