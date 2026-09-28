# Where Models Stop Counting

A small experiment: seven AI models, thirteen versions of the trolley problem,
five ways of asking each one. 2,890 questions, about five dollars.

**Read the report:** [docs/report.html](docs/report.html) is a single
self-contained page with the findings, the charts and every number. Open it in
a browser, or clone the repo and double-click it.

## What we found

- **Two models never read the question.** A reversed version, where pulling the
  lever kills five to save one, caught both Grok models pulling anyway. Grok 4.3
  did it 27 times out of 40. The other four models got it right every time.
- **The lever-to-push drop is real, and bigger than in people.** People fall
  from about 90% to about 30% willingness. The four trusted models fall from
  0.90 to 0.07.
- **The drop comes earlier than the philosophy predicts.** The big step is not
  between using a lever and using your hands. It is between a man who is already
  on the track and a man you drop onto it.
- **After the drop, counting stops.** Once the action is pushing, the models give
  almost the same answer whether the trade saves four lives or none. A
  probability-only decision model with no chat training, included as a reference
  arm, keeps weighing the trade.
- **Claude Sonnet 5 reacts to the word "user".** It acts less as soon as the
  user is mentioned, whether the user would die or be saved.

The report also has a section on what these numbers cannot tell you. Please read
it before quoting any of them. This was built in a day, with eight answers per
question, and it is not a study.

## Repository layout

| Path | What it is |
|---|---|
| `trolley/scenarios.py` | The thirteen scenario texts |
| `trolley/angles.py` | The five framings wrapped around each scenario |
| `trolley/prompts.py`, `trolley/grid.py` | Prompt assembly, SHA-256 hashing, and the balanced call grid |
| `trolley/models.py`, `trolley/clients.py` | The model panel with pricing, and one adapter per provider |
| `trolley/preflight.py` | Finds the per-model settings that switch reasoning off and verifies it |
| `trolley/runner.py` | Resumable runner with a hard budget ceiling |
| `trolley/analyze.py` | The metrics behind the report |
| `docs/make_report.py`, `docs/render_report.py` | Build `docs/report.html` from the run data |
| `results/metrics.json` | The aggregate numbers the report is built from |
| `docs/superpowers/` | The original design spec and implementation plan |
| `tests/` | 69 tests, no network needed |

Raw per-call data (`results/calls.jsonl`) is not in the repo. `metrics.json` is.

## Run it yourself

Python 3.12. You need API keys for the providers you want to test.

```sh
pip install -r requirements.txt
cp .env.example .env      # then fill in the keys
```

`.env` is read at startup and never committed:

```
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
XAI_API_KEY=...
JEV_API_KEY=...
```

Then three commands:

```sh
python3 -m trolley.cli preflight   # one probe call per model; verifies reasoning is off; projects cost
python3 -m trolley.cli run         # the full grid; resumable; stops at the budget ceiling
python3 -m trolley.cli analyze     # prints every metric as JSON
```

Useful flags: `--budget 5.0` (USD ceiling, default 5), `--samples N` (answers per
question), and `run --models opus5 sonnet5` to restrict the panel.

To rebuild the report page after a run:

```sh
python3 docs/make_report.py && python3 docs/render_report.py
```

Every prompt is stored with a SHA-256 hash of its exact text, and the runner
writes each answer as it arrives, so an interrupted run resumes without paying
twice.

## Tests

```sh
python3 -m pytest -q
```

## Limits, briefly

Eight answers per question is not many, and one cell in the table is a rough
direction rather than a number. Claude models do not accept a temperature
setting, so settings are not identical across providers. Every model has seen
the trolley problem thousands of times in training. Nobody refused, but the
fixed answer format forced a choice. The report's limits section says all of
this at proper length.
