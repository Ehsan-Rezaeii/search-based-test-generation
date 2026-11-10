"""One real fixture invocation per objective; all candidates, including duplicates, survive."""

from time import perf_counter

from .adapters import configuration, decode, optimize
from .distance import fitness
from .fixtures import ARITIES, TARGETS, execute
from .probe import outcomes
from .suites import greedy, replay


def summarize(archive: list[dict]) -> dict:
    covered, seen, first = set(), set(), {}
    curve = [0]
    for index, c in enumerate(archive, 1):
        key = (c["fixture"], tuple(c["inputs"]))
        if c["evaluation"] != index or c["duplicate"] != (key in seen):
            raise ValueError("Archive evaluation/duplicate accounting mismatch")
        seen.add(key)
        for branch in outcomes(c["trace"]):
            first.setdefault(branch, index)
            covered.add(branch)
        curve.append(len(covered))
    return {
        "evaluations": len(archive),
        "covered": sorted(covered),
        "coverage": len(covered) / 36,
        "curve": curve,
        "first_hit": dict(sorted(first.items())),
        "unique_inputs": len(seen),
        "duplicate_rate": 1 - len(seen) / len(archive) if archive else 0,
        "per_fixture": {f: sum(b.startswith(f + ":") for b in covered) for f in ARITIES},
        "auc": sum(curve[1:]) / (36 * len(archive)) if archive else 0,
    }


def run(method: str, base_seed: int, budget: int = 60, targets=TARGETS) -> dict:
    archive, seen = [], set()
    started = perf_counter()
    optimizer_runs = []
    for target in targets:
        target_index = TARGETS.index(target)
        fixture = target.split(":")[0]
        seed = base_seed * 1000 + target_index
        start = len(archive)

        def objective(vector, fixture=fixture, target=target, target_index=target_index, seed=seed):
            inputs = decode(vector)
            output, trace = execute(fixture, inputs)  # The sole objective SUT invocation.
            value = fitness(target, trace)
            key = (fixture, inputs)
            archive.append(
                {
                    "fixture": fixture,
                    "inputs": list(inputs),
                    "target": target,
                    "target_index": target_index,
                    "optimizer_seed": seed,
                    "trace": trace,
                    "output": output,
                    "fitness": value,
                    "evaluation": len(archive) + 1,
                    "duplicate": key in seen,
                }
            )
            seen.add(key)
            return value

        result = optimize(method, objective, ARITIES[fixture], budget, seed)
        if len(archive) - start != budget or result.n_evaluations != budget:
            raise RuntimeError("Optimizer did not consume the exact budget")
        # Never reevaluate best_solution or any returned optimizer point.
        optimizer_runs.append(
            {
                "target": target,
                "seed": seed,
                "evaluations": result.n_evaluations,
                "runtime_seconds": result.runtime_seconds,
                "best_fitness": result.best_fitness,
                "target_hits_in_allocation": sum(
                    target in outcomes(c["trace"]) for c in archive[start:]
                ),
                "first_target_hit_in_allocation": next(
                    (c["evaluation"] for c in archive[start:] if target in outcomes(c["trace"])),
                    None,
                ),
            }
        )
    elapsed = perf_counter() - started
    summary = summarize(archive)
    selected = greedy(archive)
    replay_started = perf_counter()
    verification = replay(selected)
    verification["runtime_seconds"] = perf_counter() - replay_started
    if verification["covered"] != summary["covered"]:
        raise RuntimeError("Greedy replay changed coverage")
    summary.update(
        {
            "method": method,
            "base_seed": base_seed,
            "runtime_seconds": elapsed,
            "suite_size": len(selected),
            "replay": verification,
        }
    )
    return {
        "archive": archive,
        "summary": summary,
        "suite": selected,
        "configuration": configuration(method),
        "optimizer_runs": optimizer_runs,
    }
