# Search-Based Test Generation

Project 5 studies automated integer test generation on six deterministic Python fixtures.
It compares the installed Project 1 continuous GA against independent Random Search,
using real execution traces, nested approach levels and branch distance under equal budgets.
This is a white-box software-engineering experiment, distinct from feature selection.

Implementation and pre-run checks are complete. The full primary study has not yet run
in this protocol commit; results will be committed separately.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev,plots]'
pytest --cov=search_based_test_generation
ruff check .
ruff format --check .
python experiments/smoke_test.py
sbst reachability
sbst study --output /tmp/p5-reproduction
sbst audit --output /tmp/p5-reproduction
python -m build
```

The frozen manifest records source/dependency SHA-256 hashes and environment packages.
The study refuses changed source or existing output. Run from the committed repository root.
The primary study plans 86,400 actual fixture calls: 2 methods × 20 seeds × 36 targets × 60.
Replay and exhaustive validation have separate costs. See [the protocol](docs/EXPERIMENT_PROTOCOL.md)
and [the specification](docs/PROJECT_SPEC.md). Generated output snapshots establish regression
consistency, not independent correctness. There is no ML holdout or claim about real-world scale.

The optimizer is an installable VCS dependency pinned to
[Project 1 commit 6b4ef0f](https://github.com/Ehsan-Rezaeii/metaheuristics-lab/tree/6b4ef0fa3d72f608146f3dd7eabb84bf39fa896e).
No GA is copied or reimplemented. Background: [Harman et al., SBSE tutorial](https://coinse.github.io/publications/pdfs/Harman2012lr.pdf),
[basic block coverage for search-based testing](https://link.springer.com/article/10.1007/s10664-022-10155-0),
and [Coverage.py branch documentation](https://coverage.readthedocs.io/en/latest/branch.html).
