# Frozen primary protocol

This document implements the unchanged fixture table in [PROJECT_SPEC.md](PROJECT_SPEC.md).
Six fixtures, three atomic nested decisions each, T then F, give 36 targets in table order.
All nested ancestors require true. A false ancestor exits; descendants are never probed.
Return codes are 0 (D1 false), 1 (D2 false), 2 (D3 false), 3 (D3 true).
The offline exhaustive audit and independent hand-written examples validate feasibility and outputs.
Its witness file is never read by the optimizer or suite generator.

For each method ga/random and base seed 0..19, run every target for exactly 60 actual
fixture calls. Explicit population 12, fresh optimizer per target, seed base*1000+index.
Installed Project 1 commit: `6b4ef0fa3d72f608146f3dd7eabb84bf39fa896e`.
GA settings are crossover 0.9, mutation None (effective 1/dimension), scale 0.1,
tournament 3, continuous domain; RandomSearch uses explicit continuous domain.
Both use Problem.continuous with [-20.5,20.5] bounds, decoding floor(v+0.5)
then clamping to [-20,20]. Endpoint cells have equal measure for uniform sampling;
GA quantization plateaus and clipping can create duplicates. All calls count.
No target skipping, caching, result reevaluation, early stopping, or budget reallocation.
Planned total 86,400 = 2 methods * 20 seeds * 36 targets * 60 calls.

Each objective records integer tuple, fixture, target/index, derived seed, output,
executed comparator operands/outcomes/distances, fitness, run-global evaluation number,
and duplicate flag. Coverage is only the union of observed outcomes divided by 36.
Fitness is zero on an observed target; otherwise A+d/(1+d), using the first path
divergence and remaining downstream depth A. Comparison distances follow the spec
including strict integer +1 boundaries. Composite-expression distances are heuristics.

Metrics: per-evaluation coverage (including initial zero), first discovery per outcome,
per-fixture final counts, final coverage, elapsed search wall time, unique (fixture,tuple)
count, duplicate fraction, and greedy suite size. Normalized right-step AUC is
sum(C_t, t=1..2160)/(36*2160), in [0,1]. Describe mean, median, sample SD,
min and max across all 20 seeds and seed-wise coverage differences. No significance
claim or assumed GA advantage. No ablation, hence no causal attribution to guidance.
Runtime includes tracing/archive but excludes greedy extraction, JSON I/O and replay.

Greedy set cover only reads the archive: maximal new outcomes; ties by earliest
evaluation, fixture ID, tuple. Export snapshots backed by JSON and executable pytest.
Separately count replay calls and offline exhaustive executions; neither augments search.
Snapshots establish regression behavior, not independent correct specifications.
The benchmark is deliberate white-box search on public toy fixtures, with no ML holdout
or industry-scale or cross-program effectiveness claim.

Before full execution, commit source, tests, scripts, CI, settings and a machine-readable
manifest hashing these files and the installed dependency. The study refuses changed
hashes and records the protocol commit. Results are a later commit. Raw gzip JSON retains
all candidates; summaries retain full 2161-point curves. CI audits saved results if present,
otherwise reports the pre-results phase. Full batch is explicit, never a CI test.
