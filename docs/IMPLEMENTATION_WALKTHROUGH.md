# Implementation walkthrough

Start with `fixtures.py`. Its six functions follow exactly the table in PROJECT_SPEC.
An input exits at the first false guard. The four outputs 0/1/2/3 identify D1 false,
D2 false, D3 false and D3 true. The optional invocation-local probe preserves outputs.
`execute` validates arity and bounds, allocates a fresh probe and calls one function once.
There is no observation state shared between calls.

`Probe.check` computes an atomic comparison on the supplied integer operands, records
that Boolean and both directional distances, and returns the same Boolean to `if`.
The next nested probe is called only if Python enters its guard. For example,
`product_guard(-1,13)` records only `product_guard:d1:F`; it says nothing about D2 or D3.
Neither the coverage numerator nor the archive invents those descendants.

Distances in `probe.py` measure comparison operands. For `a > 7`, an observed a=7
has distance 1 to true, because integers require reaching 8. For equality at 143,
true distance is abs(lhs-143) and false distance at equality is 1. Opposite observed
directions have distance zero. With product and modulo expressions these distances
are guidance, not the minimum number of input edits. Tests independently search small
operand intervals to check every comparator direction and integer boundary.

`distance.fitness` looks up the requested target's depth and reads only the observed
path. A target hit scores zero. On a miss it finds the first disagreement with required
ancestors/target. The approach level is target depth minus divergence depth. D3 misses
at D1 thus score 2+d/(1+d), at D2 score 1+d/(1+d), at D3 score d/(1+d).
Any reached deeper guard beats every earlier divergence. Only distance is normalized.
A small fitness never grants branch coverage.

`adapters.py` imports the installed Project 1 GA, RandomSearch and Problem; it contains
no evolutionary implementation. Both optimizers explicitly use population 12 and a
continuous box [-20.5,20.5]. The decoder floors value+0.5 and clamps to [-20,20].
Every uniform integer cell has width one (endpoints have zero probability mass under
ideal continuous uniform sampling). This is a continuous GA on a quantized objective,
not a native integer GA. Arithmetic crossover can sit on plateaus; Gaussian mutation,
clipping and reproduction create duplicates, which still cost executions.

`runner.run` visits the fixed 36-target schedule even when a target was already covered.
A fresh optimizer receives seed base_seed*1000+target_index and exactly 60 calls.
The objective decodes, executes once, computes fitness from that trace and appends the
candidate. It never reexecutes returned best points, caches inputs or discounts duplicates.
The actual optimizer count and archive length must agree. Run-global indices restart at
one for each method/base seed; fixture IDs distinguish equal tuples across functions.

`summarize` recomputes the union, first-hit indices, all 2161 curve values, unique inputs
and normalized right-step AUC. Curves are strongly affected by the fixed fixture schedule:
new fixture allocations create steps. AUC compares this schedule, not arbitrary orderings.
Timing includes optimization/tracing/archive construction and excludes export/set cover/replay.
Both methods use the same population size but have different computational costs.

`suites.greedy` reads only archived rows. It repeatedly picks maximal uncovered gain,
then earliest evaluation, fixture and tuple. No candidate is created or evaluated during
selection. Each selected output and trace becomes a regression snapshot. JSON cases and
adjacent generated pytest files are transparent and executable. `replay` separately counts
fixture calls, checks every output and trace, and must reproduce the exact archive union.
These assertions capture current behavior; the hand-written reference tests remain independent.

`evidence.freeze` captures settings, source/config/test hashes, Python/package details,
actual optimizer instances' settings and PEP 610 dependency provenance. `study` refuses
changed sources and existing output, records the frozen protocol commit, and writes
compressed raw logs, suites, summaries and file hashes. Reference witnesses are only
written by `reachability`; the search and suite code never reads that file.

`evidence.audit` invokes no optimizer. It checks hashes, allocation/seed order, integer
inputs, independently recomputed operand expressions, actual trace structure, comparison
distances, output/path consistency, fitness, exact counts, duplicate flags, curve and summary
values, target discovery summaries and canonical greedy selection. Its suite replay cost
is explicit. Tests corrupt evidence to check rejection, rather than merely accepting a
matching report. Fast CI runs a separate tiny budget and audits saved primary artifacts;
it does not rerun the primary experiment.

The model is deliberately limited to a known chain of three atomic decisions. It does not
parse arbitrary Python branches, handle loops/exceptions, synthesize correct specifications
or establish bug-finding ability. For study context and attribution, see the literature in
README and PROJECT_SPEC and the pinned Project 1 implementation.
