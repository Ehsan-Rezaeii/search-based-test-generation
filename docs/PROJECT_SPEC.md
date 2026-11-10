# Project 5 — Search-Based Automated Test Generation: Research and Engineering Specification

**Status: Approved kickoff design. No code, test pass, search result, coverage advantage, benchmark number or publication is claimed here.** This specification implements P5 of `PROJECT_BLUEPRINT.md`; changes to the six fixtures, branch inventory, budget or evaluation protocol require explicit documentation **before full experimental results are inspected**.

## 1. Research question and intended contribution

**RQ1 — Coverage:** Does a Genetic Algorithm guided by branch-distance/approach-level fitness achieve higher **true/false decision-outcome coverage** than independent random testing at equal counts of actual function executions?

**RQ2 — Cost and variability:** How do discovery curves, time, duplicate input rates, final suite size and seed-to-seed variation compare?

**RQ3 — Fitness mechanism:** What do branch-distance and control-dependence guidance contribute, especially for nested equality guards? Do not attribute differences to guidance without a controlled ablation; an optional ablation must be predeclared and separated from the two-method primary study.

This demonstrates search-based software engineering (SBSE), distinctly different from Projects 2–4's feature selection. The purpose is a transparent educational research study on small deterministic functions; it does not claim industrial-scale test generation or fault detection.

## 2. Pinned dependency and integer adapter

The optimizer dependency is **`metaheuristics-lab` at commit `6b4ef0fa3d72f608146f3dd7eabb84bf39fa896e`** from `https://github.com/Ehsan-Rezaeii/metaheuristics-lab`. Install it as a proper pinned VCS dependency, not a source copy or Python path hack. Check `direct_url.json` / PEP 610 metadata or equivalent evidence.

At that commit, the actual public interface is:

```python
from metaheuristics_lab import GA, RandomSearch, Problem

optimizer = GA(population_size=12)  # reference continuous GA
baseline = RandomSearch(population_size=12, domain="continuous")
problem = Problem.continuous(objective, dimension=arity, lower=-20.5, upper=20.5)
result = optimizer.optimize(problem, max_evaluations=60, seed=seed)
```

The `Problem.continuous` objective receives a floating-point vector; the **application adapter** maps each component to one integer in `[-20,20]` via `int(floor(value + 0.5))` and clamps the result to the permitted integer interval. The continuous search box `[-20.5, 20.5]` ensures equal-width integer cells for independent uniform Random Search; the GA's genetic operators still operate in continuous space. Document quantization plateaus, duplicate integer inputs, clipping, endpoint behavior and the fact that this is **not a native integer GA**. Unit-test the mapping at boundaries and representative half-step values. Apply the exact same adapter for both algorithms; do not use a different sampling representation for the baseline.

Both optimizers must explicitly receive `population_size=12` and `max_evaluations=60`. Run `20` independent paired base seeds, `0..19`, and use an unambiguous deterministic mapping `optimizer_seed = base_seed * 1000 + target_index` for each fixed target index (target indices `0..35`). Both methods use the same target index/seed schedule. No carryover of optimizer state between branches; no implicit parameter defaults. Do not assume that paired RNG seeds make methods' outputs statistically paired at the candidate level; they only structure runs reproducibly.

## 3. Six static target functions and branch inventory

Create six **real Python functions** under `src/search_based_test_generation/fixtures.py` with deliberately simple but distinct nested `if` statements. Keep all predicates **atomic**; avoid short-circuit `and`/`or`, exception paths, nondeterminism, external I/O, loops, or recursion in target functions. Five take two integers (`a,b`); one takes three (`a,b,c`). The inclusive domain for every argument is `[-20,20]`. Each function has three ordered decisions, exactly **18 decisions / 36 target outcomes**, including the true and false outcome of every decision.

The following expressions and ancestor conditions are the predeclared fixture contract. Each target function should return a small deterministic result (e.g. distinct integers for the encountered nested return paths), and all six must have hand-written reference-input/output tests. Use the same expression for its executable `if` and distance probe; do not implement a parallel approximation of the SUT.

| Function ID (suggested name) | Decision 1 | Decision 2 (nested under D1 True) | Decision 3 (nested under D2 True) |
|---|---|---|---|
| `threshold_gate(a,b)` | `a > 7` | `b <= -3` | `a + b == 9` |
| `sign_balance(a,b)` | `a < 0` | `b >= 0` | `a + b == 0` |
| `modulo_guard(a,b)` | `a % 5 == 0` | `b % 3 != 0` | `a - b <= -2` |
| `distance_gate(a,b)` | `abs(a - b) > 10` | `a + b < 0` | `a - b >= 4` |
| `product_guard(a,b)` | `a >= 0` | `b > 0` | `a * b == 143` |
| `triple_gate(a,b,c)` | `a + b >= 6` | `c - a == 3` | `b < c` |

**Control flow:** If D1 False, return a deterministic value without executing D2/D3; if D1 True and D2 False, return another; if D1 and D2 True, execute D3 and return according to its result. Thus every D2 outcome requires D1 True, and every D3 outcome requires both D1 and D2 True. All D1, D2, D3 true and false outcomes must be feasible for some bounded integer tuple; verify by independent exhaustive enumeration as a reference audit **outside** the optimizer experiment. A function may not silently eliminate any target branch or add unintended conditional decisions.

Inventory decision outcomes as canonical stable IDs, e.g. `threshold_gate:d1:T`, `threshold_gate:d1:F`, ..., `triple_gate:d3:F` in the table's function/decision/order. The denominator is **36 feasible target decision outcomes**, not statement count, full Python arc count or a moving denominator. If exhaustive audit finds a target outcome unreachable, treat it as an implementation/specification blocker and fix the fixture **before** running the main study, not by dropping that target afterward. Do not use exhaustive witness solutions as optimizer seeds, fixtures or priority hints.

### Instrumentation

Use a tiny explicit comparison probe in the **executed target path**. An illustrative interface is `probe.check(decision_id, lhs, op, rhs) -> bool`; it records only that *actual* predicate evaluation, its observed truth outcome and its distances to requested true/false outcomes. The target's actual `if` statement must branch on the returned bool. A call of `probe.check` must not evaluate predicates on paths Python would never execute. Each target function invocation returns its regular output plus trace of probe observations via a controlled wrapper (or another equally transparent mechanism). Instrumentation must be sufficiently separate from benchmark code to keep branch IDs and target semantics auditable, but no duplicate sidecar execution may be used to claim covered branches.

For independent verification, optionally use `coverage.py --branch` on generated suites and manually map relevant fixture source arcs to explicit IDs. Coverage.py automatically includes non-target internal arcs; do not substitute its unfiltered total for the 36-outcome denominator. Branch instrumentation and the function's actual behavior must agree on reference cases.

## 4. Branch distance and approach level

For an integer comparison of expressions `lhs` and `rhs`, define distances to **both** desired truth outcomes. The distance for the observed outcome is always zero. For the non-observed desired direction use the minimum positive integer adjustment to satisfy it under the integer relation (not necessarily the true minimum change to the original inputs for composite expressions). Define the following `distance_true` and `distance_false`:

| Comparison | distance_true | distance_false |
|---|---|---|
| `lhs < rhs` | `max(0,lhs-rhs+1)` | `max(0,rhs-lhs)` |
| `lhs <= rhs` | `max(0,lhs-rhs)` | `max(0,rhs-lhs+1)` |
| `lhs > rhs` | `max(0,rhs-lhs+1)` | `max(0,lhs-rhs)` |
| `lhs >= rhs` | `max(0,rhs-lhs)` | `max(0,lhs-rhs+1)` |
| `lhs == rhs` | `abs(lhs-rhs)` | `0 if lhs != rhs else 1` |
| `lhs != rhs` | `0 if lhs != rhs else 1` | `abs(lhs-rhs)` |

These are comparison-level heuristics; for composite operands such as `a*b`, distance need not equal the number of changes to integer inputs. Use unit tests for equality, strict and non-strict edge cases, negative values, exact boundaries and opposite directions. Never use a fake branch as covered just because its distance is zero in a hypothetical, unexecuted expression.

For each *target outcome*, define its ancestor/guard outcome sequence from the fixture's control-dependence tree. Evaluate candidate test inputs by **executing the target function once** and inspecting the encountered probe outcomes:

- If the target outcome itself was observed, **fitness = 0**.
- Otherwise identify the *first observed divergence* from the requisite path leading to the target outcome (it may be at the target decision itself). Let `d > 0` be the directional distance from that observed predicate to the required outcome. Let `A` be the number of **still-unreached downstream guarded decisions** along the path to the target; this is a predeclared nonnegative integer derived from the control-dependence structure, not from guessed predicate outcomes.
- Minimize `fitness = A + d/(1+d)`; if the target is reached but its direction is wrong, `A=0`; if the path diverges earlier, `A>=1`. This ensures a candidate that reaches a deeper guard is rewarded regardless of how small the earlier guard's distance was.

For a D3 target, diverging at D1 has `A=2`, diverging at D2 has `A=1`, diverging at D3 has `A=0`. For a D2 target, divergence at D1 has `A=1`, at D2 has `A=0`. For a D1 target, divergence at D1 has `A=0`. When the candidate hits the desired target outcome, return zero. All fitness values must be finite, deterministic, nonnegative real numbers. Do not add a coverage-count reward that changes this predeclared objective without a separate approved study.

### Distinguish three measurements

- **Fitness** is a scalar *guiding one target search*; it can improve before a new branch is covered.
- **Observed branch coverage** is the union of branch outcomes actually traversed by executed inputs; it never increases based on fitness alone.
- **Suite coverage** is the same union after deterministic archiving/greedy minimization; suite generation itself is not another optimizer.

## 5. Fair study protocol

1. Commit fixture code, canonical branch inventory, decoder, full settings, metrics, exact target order and experimental scripts **before full-batch execution**. Save source/dependency hashes and environment details in a protocol manifest. An external held-out dataset is neither necessary nor meaningful for this *white-box* branch coverage study; do not advertise a untouched test set.
2. For each method (`ga`, `random`) and each base seed `0..19`, visit **all 36 targets in the same fixed order**. Perform a separate optimizer call for each target; each call consumes exactly **60** `Problem.continuous` objective evaluations (population `12`, deterministic derived seed), and each objective call invokes its target function **once**. The target outcome itself may already be covered in the archive, but do not skip its predeclared allocation. Do not early-stop or silently reallocate budgets based on observed coverage.
3. Archive the exact decoded integer test input, target ID, observed target-function output, actual predicate/outcome trace, fitness, global evaluation number and seed after every call. Preserve duplicates; measure distinct test tuples separately. No fitness or test-function-call cache is allowed. Build cumulative union coverage progress indexed by **actual objective evaluation count** (0..2160 per run). Cross-function archiving is allowed as a suite union only if every archived input is associated with its actual function/arity; never count a test for an unexecuted function.
4. Record final raw outcome counts, `covered/36`, per-function coverage, first-hit evaluation for each branch, time, evaluations, distinct input count, duplicate rate and optional coverage area-under-curve. The AUC is a descriptive curve summary; define normalization and scale in advance. Report median, mean, sample SD, min and max across 20 seeds for both methods; include per-seed paired coverage differences and individual curves. No invented p-values or guaranteed GA superiority.
5. After the run, greedily minimize the archived test set **without evaluating new candidates**: repeatedly select an archived test that covers the most as-yet-uncovered outcomes, breaking ties deterministically (first lower global evaluation index, then function ID and integer tuple). Store selected tests and their output snapshots. Validate by replay in a **separately logged verification phase** that the smaller suite covers exactly the same outcomes and yields identical outputs. Never count verification replays as additional optimizer evaluations.
6. The search executes a fixture once per objective call, no additional `coverage.py` run per evaluation. Full-domain exhaustive feasibility checks run once in a separate verification stage; record their cost independently. Avoid leaking oracle witnesses to the optimization stage.
7. The two methods' same budgets do **not** imply identical CPU cost, population dynamics, or solution distributions. Measure actual wall time. No cross-program or industrial generalization claim; these six toy functions are intentionally hand-designed and favorable to distance-based guidance.

**Primary predeclared budget:** 36 outcomes × 60 calls = **2,160 function executions per method × seed**; 20 seeds × two methods = **86,400 search evaluations**, before separate reference/suite-verification work. This number is a *planned target*, not a reported execution result.

## 6. Test generation and limitations

Export one Python `pytest`-style regression suite per seed/method or a compact machine-readable JSON suite plus a deterministic pytest generator. Every emitted case must originate from actually evaluated inputs, with recorded expected function outputs; generated assertions test **regression consistency** with the current fixture implementation. Do **not** call them independent correctness tests. Hand-written reference assertions for fixture logic must be maintained separately from generated suites, and tests should detect deliberately mutated fixture outputs on representative cases.

The approach-level instrumented helper is a limited teaching implementation, not a general Python branch analyzer. Do not claim generated tests for arbitrary repositories, loops, exceptions, dynamic classes, or real production applications. Avoid deploying, executing, or fetching untrusted code.

## 7. Repository architecture and verification

Suggested minimal structure (adapt naming modestly if justified):

```
README.md
AGENTS.md
pyproject.toml
src/search_based_test_generation/
    __init__.py
    fixtures.py             # static pure target functions; branch inventory
    probe.py                # real execution outcome tracing
    distance.py             # 6 comparator formulas and target path fitness
    adapters.py             # Project 1 integration and continuous->integer decode
    runner.py               # seeds, target schedule, archives, coverage curves
    suites.py               # deterministic greedy suite extraction/replay
    cli.py                  # quick smoke, full experiment, audit
experiments/
    run_study.py
    audit_results.py
    plot_results.py
    smoke_test.py
src/... (no GA implementation)
tests/
    test_fixtures.py
    test_distance.py
    test_adapters.py
    test_runner.py
    test_suites.py
    test_artifacts.py
.github/workflows/ci.yml
docs/EXPERIMENT_PROTOCOL.md
docs/RESULTS.md
docs/IMPLEMENTATION_WALKTHROUGH.md
docs/VERIFICATION.md
docs/HANDOFF.md
results/                 # actual raw evidence and plots after execution
```

Required tested properties:

- All **36 IDs** unique, each reaches an observed true/false branch in exhaustive reference audit; every decision has a feasible true/false outcome; `[-20,20]` domain enforced.
- Each fixture's trace matches its actual branch path; no trace entries from branches not executed; hand-written outputs at boundary and nested cases; no global mutable observation leak between calls.
- Correct normalized distance to true/false for all six comparison operators, with minimum positive adjustment on the wrong side; tested approach levels for diverging at D1/D2/D3 and exact zero on a hit.
- Integer decoder is deterministic and valid for [-20.5,20.5] with exact boundary unit tests; no accidentally biased different baseline representation.
- Real installed Project 1 `GA`, `RandomSearch` and `Problem` used, actual constructor kwargs verified, population `12`, budget `60`, exact calls even for duplicate integer vectors, seeded determinism on fixed fixtures.
- Every archived candidate corresponds to exactly one actual fixture execution. Coverage union/trajectory is monotone, its values are in [0,36], and `covered/36` matches reported final coverage.
- Empty and full archived suites, deterministic tie resolution, greedy set-cover preservation and independent replay tested; correctness oracle caveat documented.
- Smoke study on a **tiny separate budget** completes within CI; full study is run explicitly once as a measured experiment. Artifact audit recomputes per-run outcomes/curves/summary/coverage and checks hashes, seeds, configuration and timestamps without running optimizers. If saved artifacts are not yet present, CI should not spuriously fail on the pre-run branch.
- `ruff check`, `ruff format --check`, `pytest` (+ statement coverage), source/wheel build, clean wheel install/import away from the checkout, CI matrix Python 3.10/3.12/3.13 all pass if feasible. Do not claim success without logs.

All scientific results must be computed from actual saved raw evaluation traces and documented with genuine figures. A negative or tied GA outcome is a successful study result if the experiment is correct.

## 8. References and attribution

- Project 1 pinned library: https://github.com/Ehsan-Rezaeii/metaheuristics-lab/tree/6b4ef0fa3d72f608146f3dd7eabb84bf39fa896e
- Harman et al., *Search Based Software Engineering: Techniques, Taxonomy, Tutorial*: https://coinse.github.io/publications/pdfs/Harman2012lr.pdf
- *Basic block coverage for search-based unit testing and crash reproduction*: https://link.springer.com/article/10.1007/s10664-022-10155-0
- Coverage.py branch-coverage documentation: https://coverage.readthedocs.io/en/latest/branch.html
- Pynguin documentation, background context only, **not** an optimization backend: https://pynguin.readthedocs.io/latest/

Properly credit references but do not copy another codebase's optimizer or present existing heuristics as a novel algorithm.
