# Owner handoff

The complete study is implemented and locally verified, with the original fixture,
distance and experimental contract preserved. The feature branch is
`feat/project5-complete-study`; its PR remains unmerged for independent review.

Read README for commands and measured overview, RESULTS for every seed and figures,
IMPLEMENTATION_WALKTHROUGH for beginner explanations, and VERIFICATION for real logs.
PROJECT_SPEC and EXPERIMENT_PROTOCOL define the research contract.

The frozen pre-run commit is `46d2b6e74fde166406e0154600ed69b453041e29`.
Manifest SHA-256: `73a5ea883ad880f20e35884041cada99d79f3b58ab448c3e2ff9e0137cd27ad2`.
Settings SHA-256: `567fac3f45a10fce64ea766d0cf9e01d4c3c99693b3bad0d40d5872ae167d836`.
Source hashes are listed individually in `experiments/prerun_manifest.json`.
Installed Project 1 dependency commit: `6b4ef0fa3d72f608146f3dd7eabb84bf39fa896e`.

Fixture IDs are threshold_gate, sign_balance, modulo_guard, distance_gate, product_guard
and triple_gate. The first five take two integers; triple_gate takes three. Every fixture
has exactly three nested atomic decisions, totaling 18 decisions / 36 reachable outcomes.

Measured budget is 43,200 calls per method, 86,400 total, all seeds 0..19 retained.
Each method/seed has exactly 36*60=2160 fixture calls with population 12 and the fixed
seed schedule. GA final coverage mean is 98.4722% (35.45 outcomes), sample SD 1.4178
percentage points, range 35–36; random mean is 95.8333% (34.5 outcomes), SD 2.7778
points, range 32–36. GA wins/ties/losses are 12/7/1; seed 19 is a real GA loss.
Mean search runtimes are GA 0.153612 seconds and random 0.113842 seconds in this environment.
Mean distinct candidates are 1748.1 and 1981.05 per run; mean suite sizes 23.45 and 22.6.
The 40 suites contain 921 cases, each selected from the actual archive.
Replay verified exact archive coverage and outputs, separately from search calls.

`src/search_based_test_generation/` contains static fixtures, tracing, distances, adapter,
runner, suites, evidence and CLI. `tests/` includes independent reference and failure tests.
`experiments/` contains frozen settings/manifest, full-run, audit, plot and smoke entry points.
`results/study/*.json.gz` retain all 86,400 candidates and their true paths, outputs and fitness;
`summaries.json` contains curves/discovery times; `suites/` contains JSON and executable pytest;
`hashes.json` protects batch artifacts. `results/figures/` and `statistics.json` report measured
comparisons. `results/reachability.json` holds offline witnesses for validation only.
`results/verification/` contains execution/build/test/audit/CI evidence.

Local verification: 370 tests passed; package statement coverage 94%; all 921 generated
snapshot cases passed; Ruff, format, source/wheel builds and external clean wheel import passed.
GitHub CI evidence is separate and must be read from the observed workflow status.

Limitations: tiny public teaching fixtures, a short continuous GA allocation over integer
plateaus, repeated/clipped candidates, heuristic composite-expression distances, fixed-order
AUC, noisy subsecond timings, no guidance ablation, no independent generated correctness
oracle, and no industrial or cross-program claim. No statistical significance is asserted.
The exhaustive audit costs 77,326 calls separately; every test/audit rerun adds validation
calls. Generated snapshots reproduce regression behavior. No ML holdout exists.

To independently review, begin with the fixture table and handwritten tests, then inspect
one compressed run's trace and recompute the coverage union with the audit command.
To reproduce optimization use a fresh output directory and the committed frozen sources.
Runtime and wall-clock timestamps may differ; seeded candidate archives should match.

Review PR: https://github.com/Ehsan-Rezaeii/search-based-test-generation/pull/1 (open and unmerged). The full Python 3.10/3.12/3.13 CI matrix passed in run 42910547346; its observed commit and job/step evidence are retained in results/verification/ci.json. Total measured search wall time summed across runs was 3.072235 seconds for GA and 2.276845 seconds for Random Search. Runtime excludes suite selection, exports and replay.
