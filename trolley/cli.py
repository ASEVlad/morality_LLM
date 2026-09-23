"""Entry points: preflight, run, analyze."""
import argparse
import json
import os
from pathlib import Path

from trolley.analyze import load, metrics
from trolley.grid import cells_for_model, samples_for
from trolley.models import ALL_MODELS
from trolley.preflight import discover_reasoning_off, project_cost
from trolley.runner import run_cells

RESULTS = Path("results")
CONFIG = RESULTS / "reasoning_off.json"
DATA = RESULTS / "calls.jsonl"


def _load_env(path: str = ".env") -> None:
    if not Path(path).exists():
        return
    for line in Path(path).read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, _, value = line.partition("=")
            if value.strip():
                os.environ.setdefault(key.strip(), value.strip())


def _samples(model_key: str, override: int | None) -> int:
    return samples_for(model_key) if override is None else override


def cmd_preflight(args: argparse.Namespace) -> None:
    RESULTS.mkdir(exist_ok=True)
    chosen, total = {}, 0.0
    for spec in ALL_MODELS:
        params, probe = discover_reasoning_off(spec)
        calls = 10 * 5 * _samples(spec.key, args.samples)
        if params is None:
            print(f"  {spec.key:9s} FAILED  every candidate errored: {probe.error}")
            continue
        projected = project_cost(spec, probe.input_tokens, probe.output_tokens, calls)
        total += projected
        forced = " (REASONING FORCED - separate comparison class)" if (
            params == {} and spec.provider != "typesafe"
        ) else ""
        print(
            f"  {spec.key:9s} ok  {json.dumps(params)}  "
            f"{probe.input_tokens} in / {probe.output_tokens} out  "
            f"-> ${projected:.4f} for {calls} calls{forced}"
        )
        chosen[spec.key] = params
    CONFIG.write_text(json.dumps(chosen, indent=2) + "\n")
    print(f"\nProjected total: ${total:.2f} (budget ${args.budget:.2f})")
    print(f"Wrote {CONFIG}")


def cmd_run(args: argparse.Namespace) -> None:
    reasoning_off = json.loads(CONFIG.read_text())
    keys = args.models or list(reasoning_off)
    cells = [
        c for k in keys
        for c in cells_for_model(k, samples=_samples(k, args.samples))
    ]
    print(f"{len(cells)} cells across {len(keys)} models")
    spent = run_cells(cells, DATA, reasoning_off, budget_usd=args.budget)
    print(f"Done. Spent ${spent:.4f}. Wrote {DATA}")


def cmd_analyze(args: argparse.Namespace) -> None:
    print(json.dumps(metrics(load(DATA)), indent=2))


def main() -> None:
    _load_env()
    parser = argparse.ArgumentParser(prog="trolley")
    parser.add_argument("--budget", type=float, default=5.0)
    # Default None means "use the per-model count from grid.SAMPLES_BY_MODEL":
    # 4 for the panel, 2 for the deterministic Jev arm.
    parser.add_argument("--samples", type=int, default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("preflight").set_defaults(func=cmd_preflight)
    run = sub.add_parser("run")
    run.add_argument("--models", nargs="*")
    run.set_defaults(func=cmd_run)
    sub.add_parser("analyze").set_defaults(func=cmd_analyze)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
