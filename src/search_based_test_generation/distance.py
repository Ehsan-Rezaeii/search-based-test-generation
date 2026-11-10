"""Control dependence for the predeclared three-decision true-guard chain."""

from .fixtures import TARGETS
from .probe import outcomes


def fitness(target: str, trace: list[dict]) -> float:
    if target not in TARGETS:
        raise ValueError(f"Unknown target: {target}")
    if target in outcomes(trace):
        return 0.0
    fixture, decision, truth = target.split(":")
    depth = int(decision[1:])
    by_id = {o["decision"]: o for o in trace}
    for level in range(1, depth + 1):
        required = level < depth or truth == "T"
        observation = by_id.get(f"{fixture}:d{level}")
        if observation is None:
            raise ValueError("Missing executed ancestor or target in trace")
        if observation["outcome"] != required:
            d = observation["distance_true" if required else "distance_false"]
            if d <= 0:
                raise ValueError("Divergence must have positive distance")
            return depth - level + d / (1 + d)
    raise ValueError("Trace inconsistent with target")
