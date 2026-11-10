# Verification evidence

Commands below ran from the repository root in the managed Linux environment on
2026-11-11 (Asia/Tehran; raw timestamps are UTC). Python was 3.12.14.
Complete stdout is retained under `results/verification/`; values here are measured.

Before the primary batch:

```console
$ .venv/bin/pytest --cov=search_based_test_generation --cov-report=term-missing
369 passed, 1 skipped in 8.95s
TOTAL 428 statements, 27 missed, 94%
```

The single skip was the intentional pre-results artifact gate. All comparators and truth
directions are tested across 294 operand combinations, including strict boundaries.
Tests cover nested fitness, 24 hand-authored output/path cases, independent full-domain
expression comparison, no false nested coverage, actual optimizer constructor kwargs and
instances, 1/13/60-call budgets, deterministic seeds, duplicates, trajectories, set cover,
executable snapshot export, replay mismatch, manifest pipeline and corrupted evidence.
The independent exhaustive test uses 77,326 validation executions per invocation.

```console
$ .venv/bin/python -m search_based_test_generation.cli reachability
"fixture_calls": 77326
# All 36 predeclared outcomes observed; results/reachability.json stores per-fixture costs.
$ .venv/bin/python experiments/smoke_test.py
ga 0.8055555555555556
random 0.8055555555555556
```

Smoke uses 3 calls per target (108 per method), outside the primary budget.
The reference audit enumerates 5*41^2 + 41^3 = 77,326 inputs. Witnesses never enter search.
Repeated validation/test invocations incur additional validation cost, not search calls.

The full study was executed only after protocol commit
`46d2b6e74fde166406e0154600ed69b453041e29`:

```console
$ .venv/bin/python experiments/run_study.py
# 40 logged runs, each reporting 2160 actual calls; see full-study.txt.
$ .venv/bin/python experiments/audit_results.py
{
  "search_calls": 86400,
  "audit_suite_replay_calls": 921,
  "runs": 40
}
```

The batch itself replayed 921 selected tests after search; this audit replayed another 921.
Each subsequent artifact audit independently repeats that replay. The raw search count
stays 86,400. The exported generated-suite pytest invocation below is another 921 replays.
The first audit command was attempted before the batch finished and correctly failed
because the final hash file did not yet exist; the completed-batch audit above passed.
No candidates were regenerated or primary runs discarded.

```console
$ .venv/bin/pytest --cov=search_based_test_generation --cov-report=term-missing --cov-report=xml
370 passed in 20.15s
TOTAL 428 statements, 27 missed, 94%
$ .venv/bin/pytest -q results/study/suites
921 passed in 0.88s
$ .venv/bin/ruff check .
All checks passed!
$ .venv/bin/ruff format --check .
25 files already formatted
$ .venv/bin/python -m build
# Source distribution and wheel built successfully; see build.txt.
```

The 94% is package statement coverage, distinct from the 36-outcome research metric.
Uncovered lines are mostly defensive failure paths. Generated suite files are excluded
from Ruff because they are deterministic output templates; package/tests/scripts are checked.
Plots were generated with `python experiments/plot_results.py` and visually inspected.
Matplotlib used a writable temporary cache after the default home cache was read-only;
this did not affect figure generation. Set `MPLCONFIGDIR=/tmp/p5-mpl` to avoid that message.

Clean wheel verification uses an independent venv and imports from `/tmp`, outside the checkout:

```bash
python -m venv /tmp/p5-wheel-venv
/tmp/p5-wheel-venv/bin/pip install dist/*.whl
cd /tmp
/tmp/p5-wheel-venv/bin/python -c 'import search_based_test_generation as p; from search_based_test_generation.fixtures import threshold_gate; from search_based_test_generation.evidence import dependency; assert threshold_gate(12,-3)==3; print(p.__file__); print(dependency())'
```

See `wheel-import.txt` for the actual site-packages path and pinned dependency commit.
PEP 610 metadata and installed dependency source hashes are also in the frozen manifest.
Local Python 3.10/3.13 execution is not claimed; those versions are checked by GitHub Actions.
The CI matrix runs Ruff, all tests/artifact audit, tiny smoke, builds and a fresh external
wheel install/import. CI evidence and URLs are recorded in `results/verification/ci.json`
after observing the completed checks.

Observed GitHub Actions run [42910547346](https://github.com/Ehsan-Rezaeii/search-based-test-generation/actions/runs/42910547346) completed successfully for Python 3.10, 3.12 and 3.13 at commit `ae6e121350bde07dc468c3314415b968da0288db`. Every matrix job passed installation, lint/format, tests/artifact audit, tiny smoke, build, clean wheel install/import and artifact upload. The exact job IDs and step conclusions are saved in `results/verification/ci.json`.
