# Search-Based Test Generation

**Status: research design and kickoff only.** No implementation, experiments, tests, metrics or coverage improvements are claimed in this initial README.

This is Project 5 of a five-project research portfolio. It studies whether a **genetic algorithm (GA)** can generate integer-valued Python unit-test inputs that exercise more decision/branch outcomes than **Random Search** under the same number of target-function executions.

## Research question

> Under identical evaluation budgets, does a branch-distance-guided GA discover more branches than independent random testing on six deterministic, bounded integer-input Python functions?

The project imports `GA`, `RandomSearch`, and `Problem` from the **real installed** [Project 1 optimizer library](https://github.com/Ehsan-Rezaeii/metaheuristics-lab/tree/6b4ef0fa3d72f608146f3dd7eabb84bf39fa896e). The GA is not copied or reimplemented. Continuous candidate vectors are decoded deterministically to integer tuples.

## Planned, predeclared scope

- Six small local Python functions, 18 atomic decisions, 36 feasible true/false branch outcomes.
- Integer inputs in `[-20,20]`; five two-argument functions and one three-argument function.
- Actual execution-based outcome traces; approach-level and normalized branch-distance fitness.
- GA vs Random Search; population size 12 and **60 function executions per target**, 36 targets per run.
- **20 independent paired seeds** per method; track per-evaluation coverage curves, branch hit sets, duplicates, runtime, seed variability, and retained suites.
- A separate bounded-domain reachability/reference audit; generated regression tests with explicitly qualified oracle limitations.
- Real CLI, reproducible experiment artifacts, tests, CI, clean wheel installation and documented limitations.

**The project measures coverage, not software correctness.** A generated test that reproduces the current fixture output does not prove that output is correct. Synthetic target functions are deliberately small and do not establish effectiveness on real-world systems.

## Implementation instructions

See [`AGENTS.md`](AGENTS.md) and [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md) for the complete technical and experimental contract. Setup, real measured results, commands and figures will be added **only after they are actually executed**.

## Background

- [Project 1 — metaheuristics-lab](https://github.com/Ehsan-Rezaeii/metaheuristics-lab)
- [Coverage.py branch measurement](https://coverage.readthedocs.io/en/latest/branch.html)
- [Basic block coverage for search-based unit testing and crash reproduction](https://link.springer.com/article/10.1007/s10664-022-10155-0)
- [Search Based Software Engineering: Techniques, Taxonomy, Tutorial](https://coinse.github.io/publications/pdfs/Harman2012lr.pdf)

Copyright and citation for upstream code/papers must remain separate from the license of this repository.
