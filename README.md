# Search-Based Test Generation

[![CI](https://github.com/Ehsan-Rezaeii/search-based-test-generation/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Ehsan-Rezaeii/search-based-test-generation/actions/workflows/ci.yml)

**Reproducible white-box test generation using Genetic Algorithms, branch distance, and real
execution traces.** This project adapts an installed, reusable optimization library to generate
bounded integer inputs for six Python test fixtures and compares its results against uniform Random
Search under identical execution budgets.

**Research question:** Under a fixed budget of actual program executions, does branch-distance-guided
Genetic Algorithm (GA) search discover more branch outcomes than Random Search?

**Main finding:** Across **20 paired seeds**, GA covered **35.45 of 36 outcomes on average
(98.47%)**, compared with **34.50 (95.83%)** for Random Search. GA won **12** seed comparisons, tied
**7**, and lost **1**. It also produced more duplicate inputs and took longer on average. These are
**descriptive results on six small, hand-designed fixtures**, not evidence of statistical or
industrial superiority.

## Results at a glance

The completed experiment comprises **40 runs** (two methods × 20 seeds). Each run targets **36
predefined true/false decision outcomes** and uses exactly **2,160 actual fixture executions**, for
**43,200 calls per method** and **86,400 total search calls**.

| Measured metric (20 seeds) | Genetic Algorithm | Random Search |
|---|---:|---:|
| **Mean observed branch-outcome coverage** | **98.47%** | 95.83% |
| Mean covered outcomes / 36 | **35.45** | 34.50 |
| Coverage sample SD (percentage points) | **1.42** | 2.78 |
| Final covered-outcome range | 35–36 | 32–36 |
| Mean normalized coverage-curve AUC | **0.56870** | 0.56274 |
| Mean distinct test inputs per run | 1,748.10 | **1,981.05** |
| Mean duplicate-input rate | 19.07% | **8.28%** |
| Mean search time per run (seconds) | 0.15361 | **0.11384** |
| Mean greedy regression-suite size | 23.45 | **22.60** |
| Objective / fixture calls across all seeds | 43,200 | 43,200 |

![Measured branch-outcome coverage curves](results/figures/coverage_curves.png)

**Interpretation:** GA's mean advantage was **2.64 percentage points** on this exact benchmark, not
on arbitrary Python branches or real-world projects. The methods shared a common input
representation, schedule, and evaluation budget, but searched differently after initialization.
Random Search was faster and generated fewer duplicate tests; it achieved full coverage in one seed
where GA did not. No significance test or guidance-ablation study establishes why the observed
difference arose.

[Complete per-seed results and negative findings](docs/RESULTS.md) · [Final coverage by seed](results/figures/final_by_seed.png) · [Results by fixture](results/figures/per_fixture.png)

## How the test generation works

The system targets **18 nested atomic decisions**, each with a true and false outcome. These yield
**36 reachable, predeclared outcomes** across six deterministic fixtures:

| Fixture | Inputs | What it exercises |
|---|---|---|
| `threshold_gate` | Two integers | Thresholds and a nested equality |
| `sign_balance` | Two integers | Signed comparisons and balance |
| `modulo_guard` | Two integers | Modulo and difference conditions |
| `distance_gate` | Two integers | Absolute-distance and ordering guards |
| `product_guard` | Two integers | Product equality after nested guards |
| `triple_gate` | Three integers | Nested conditions involving three inputs |

1. **Generate an input.** Both methods search a continuous box `[-20.5, 20.5]` and decode every
   coordinate to an integer in `[-20, 20]` with `clamp(floor(v + 0.5), -20, 20)`.
2. **Execute the real fixture.** Each objective call executes the selected Python function exactly
   once and records its observed decision path, comparisons, and output. Coverage is awarded **only
   for outcomes actually executed**.
3. **Compute guidance.** GA minimizes fitness based on the remaining *approach level* in the nested
   path and normalized *branch distance*, `d / (1 + d)`. Reaching the targeted outcome gives fitness
   `0`. Random Search samples without using this feedback to guide later candidates.
4. **Preserve the evidence.** Every candidate, including repeated inputs and evaluations after a
   target is found, remains in the execution archive. No fitness caching or extra best-point
   reevaluation changes the search budget.
5. **Export regression tests.** A deterministic greedy set-cover procedure selects actual archived
   inputs that preserve the observed coverage. Generated JSON suites and executable pytest snapshots
   are replayed separately from search.

This is **execution-based branch-outcome instrumentation**, not a claim that a generic coverage tool
measured all possible branches of an arbitrary codebase. The [beginner-friendly implementation walkthrough](docs/IMPLEMENTATION_WALKTHROUGH.md) explains the trace
format, control dependence, distance calculations, and set-cover procedure.

### Equal-budget comparison

The GA and Random Search implementations are **imported, not copied**, from [`metaheuristics-lab` at commit `6b4ef0f`](https://github.com/Ehsan-Rezaeii/metaheuristics-lab/tree/6b4ef0fa3d72f608146f3dd7eabb84bf39fa896e). Both use
population size **12**, the same integer decoder, and a fixed schedule:

- **36 targets × 60 objective evaluations × 20 seeds = 43,200 calls per method.** Each method/seed
  run therefore consumes exactly 2,160 calls.
- Base seeds are `0–19`; the per-target seed is `base_seed * 1000 + target_index`.
- The final score is the union of actually covered outcomes across the run, including outcomes
  discovered while searching for other targets.
- The coverage-curve AUC follows the **fixed target order**. It is not a schedule-independent measure
  of general search efficiency.

An independent exhaustive reachability check covered the entire permitted integer domain, using
**77,326 additional validation executions** to confirm that all 36 outcomes are feasible. Those
checks and the regression-suite replays are **not included** in the equal search budgets.

## Install and verify

**Requirements:** Python 3.10+ and Git. Initial installation requires network access to retrieve the
commit-pinned optimizer dependency. CI checks Python **3.10, 3.12, and 3.13**.

```bash
git clone https://github.com/Ehsan-Rezaeii/search-based-test-generation.git
cd search-based-test-generation
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,plots]'
```

Run the tests and inspect the committed study **without repeating the complete search experiment**:

```bash
ruff check .
ruff format --check .
python -m pytest --cov=search_based_test_generation --cov-report=term-missing
python -m pytest -q results/study/suites
python experiments/smoke_test.py
python experiments/audit_results.py
python -m build
```

**Recorded verification:** **370 passing package tests** with **94% statement coverage**; all **921
exported regression snapshot cases** passed separately. Ruff checks, synthetic smoke, artifact audit,
sdist/wheel builds, and a clean wheel import outside the repository also passed. The [GitHub Actions workflow](https://github.com/Ehsan-Rezaeii/search-based-test-generation/actions/workflows/ci.yml)
checks the three Python versions and does **not** rerun all 86,400 experiment calls. See the
[verification evidence](docs/VERIFICATION.md) for executed commands, environments, and limitations of the checks.

## Reproduce the study

The original frozen protocol and results remain committed. Use a **new output directory** rather than
overwriting `results/study/`:

```bash
sbst study --output /tmp/p5-reproduction
sbst audit --output /tmp/p5-reproduction
sbst reachability --output /tmp/p5-reachability.json
MPLCONFIGDIR=/tmp/p5-mpl python experiments/plot_results.py
```

`study` checks the frozen source and installed dependency and refuses to overwrite existing
output. `audit` reconstructs paths, fitness, coverage, duplicate counts, curves, and greedy
suites from saved execution evidence; it then replays the selected tests with separate accounting.
Plot generation reads the **committed primary** study results, not the `/tmp` reproduction
directory. Random seeds support reproducible candidate traces; timings and timestamps can vary by
environment.

The [frozen pre-run manifest](experiments/prerun_manifest.json) records the Python environment, optimizer configuration, source hashes, and
Project 1 commit. The [protocol](docs/EXPERIMENT_PROTOCOL.md) was committed before the primary experiment. Raw traces for all
40 runs are retained under [`results/study/`](results/study/) in compressed JSON files.

## Evidence and repository guide

| Resource | What it contains |
|---|---|
| [Measured results](docs/RESULTS.md) | Per-seed coverage, variance, runtime, AUC, duplicate rates, difficult outcomes, and plots |
| [Study statistics](results/statistics.json) | Machine-readable aggregate results and the 12/7/1 paired comparison |
| [Execution summaries](results/study/summaries.json) | Coverage curves, discovery times, and run-level results |
| [Archived search runs](results/study/) | Every generated input, actual execution path, fitness value, and objective call |
| [Exported test suites](results/study/suites/) | 40 JSON suites and 40 generated pytest files based on observed inputs |
| [Reachability evidence](results/reachability.json) | Exhaustive feasibility checks, separate from optimizer search |
| [Protocol](docs/EXPERIMENT_PROTOCOL.md) | Predefined fixture targets, fitness, equal budgets, seeds, and evaluation rules |
| [Source walkthrough](docs/IMPLEMENTATION_WALKTHROUGH.md) | Python architecture and the reasoning behind the implementation |
| [Verification](docs/VERIFICATION.md) | Actual tests, package builds, CI, artifact auditing, and known limitations |

## Limitations

- **Small teaching fixtures:** All six functions are deliberately hand-designed. Results do not
  demonstrate improvement on real repositories, arbitrary Python programs, or fault detection.
- **Search representation:** A continuous GA mapped onto integers creates plateaus and duplicate
  inputs. Some product/modulo branch distances are heuristics rather than input-edit distances.
- **Fixed budget and schedule:** Only 60 evaluations are allotted per target. The target order shapes
  the coverage curves and AUC; different budgets, schedules, and search operators may change the
  comparison.
- **No isolated causal explanation:** The study compares guided GA with uniform Random Search, not an
  ablation that separates branch-distance guidance from evolutionary selection. The 20 seed results
  are descriptive and do not establish statistical significance.
- **Regression is not correctness:** Generated snapshot tests verify consistent recorded behavior;
  they are not independent test oracles. The deterministic greedy suite is not guaranteed to be
  minimum-sized. Handwritten reference checks provide separate, limited validation.
- **Timing and scope:** Subsecond runtimes include instrumentation and are machine-dependent. This is
  white-box, search-based testing with **no ML holdout**, no production deployment, and no claim of a
  novel optimizer.

## Attribution and portfolio connection

This repository is the **search-based software testing** application in a five-project research
portfolio. It reuses the installed [metaheuristics-lab](https://github.com/Ehsan-Rezaeii/metaheuristics-lab) dependency, while the other application studies
address [breast cancer feature selection](https://github.com/Ehsan-Rezaeii/breast-cancer-feature-selection), [cross-version software defect prediction](https://github.com/Ehsan-Rezaeii/software-defect-prediction), and [SQL injection detection](https://github.com/Ehsan-Rezaeii/sqli-detection-lab). Their tasks, datasets, and evaluation
metrics differ; numerical outcomes are not directly comparable.

The approach-level and branch-distance ideas follow established search-based software testing
research. Background reading:

- Harman et al., [*Search Based Software Engineering: Techniques, Taxonomy, Tutorial*](https://coinse.github.io/publications/pdfs/Harman2012lr.pdf).
- [*Basic block coverage for search-based unit testing and crash reproduction*](https://link.springer.com/article/10.1007/s10664-022-10155-0).
- [Coverage.py branch measurement](https://coverage.readthedocs.io/en/latest/branch.html) (related background; not this study's coverage oracle).
- [Pynguin](https://pynguin.readthedocs.io/latest/) (related tool; not used as the optimizer backend).

**Code license:** [MIT](LICENSE). Source code and benchmark evidence have separate attribution from
the research literature.
