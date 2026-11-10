"""Atomic comparisons: the recorded Boolean is the one used by Python's if."""

import operator
from dataclasses import asdict, dataclass, field

COMPARATORS = {
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "==": operator.eq,
    "!=": operator.ne,
}


def distances(lhs: int, op: str, rhs: int) -> tuple[int, int]:
    """Comparison-operand distances (true, false), including integer strictness."""
    if op == "<":
        return max(0, lhs - rhs + 1), max(0, rhs - lhs)
    if op == "<=":
        return max(0, lhs - rhs), max(0, rhs - lhs + 1)
    if op == ">":
        return max(0, rhs - lhs + 1), max(0, lhs - rhs)
    if op == ">=":
        return max(0, rhs - lhs), max(0, lhs - rhs + 1)
    if op == "==":
        return abs(lhs - rhs), int(lhs == rhs)
    if op == "!=":
        return int(lhs == rhs), abs(lhs - rhs)
    raise ValueError(f"Unknown comparator: {op}")


@dataclass
class Probe:
    observations: list[dict] = field(default_factory=list)

    def check(self, decision: str, lhs: int, op: str, rhs: int) -> bool:
        outcome = bool(COMPARATORS[op](lhs, rhs))
        dt, df = distances(lhs, op, rhs)
        self.observations.append(asdict(Observation(decision, lhs, op, rhs, outcome, dt, df)))
        return outcome


@dataclass(frozen=True)
class Observation:
    decision: str
    lhs: int
    op: str
    rhs: int
    outcome: bool
    distance_true: int
    distance_false: int


def outcomes(trace: list[dict]) -> set[str]:
    return {f"{o['decision']}:{'T' if o['outcome'] else 'F'}" for o in trace}
