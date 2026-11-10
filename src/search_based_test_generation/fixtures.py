"""The six static fixtures. Return codes: D1 false=0, D2 false=1, D3 false=2, true=3.

The optional local probe changes no return values and introduces no shared state.
Only the three explicit nested if statements are benchmark decisions.
"""

from .probe import Probe


def threshold_gate(a: int, b: int, *, probe: Probe | None = None) -> int:
    p = probe if probe is not None else Probe()
    if p.check("threshold_gate:d1", a, ">", 7):
        if p.check("threshold_gate:d2", b, "<=", -3):
            if p.check("threshold_gate:d3", a + b, "==", 9):
                return 3
            return 2
        return 1
    return 0


def sign_balance(a: int, b: int, *, probe: Probe | None = None) -> int:
    p = probe if probe is not None else Probe()
    if p.check("sign_balance:d1", a, "<", 0):
        if p.check("sign_balance:d2", b, ">=", 0):
            if p.check("sign_balance:d3", a + b, "==", 0):
                return 3
            return 2
        return 1
    return 0


def modulo_guard(a: int, b: int, *, probe: Probe | None = None) -> int:
    p = probe if probe is not None else Probe()
    if p.check("modulo_guard:d1", a % 5, "==", 0):
        if p.check("modulo_guard:d2", b % 3, "!=", 0):
            if p.check("modulo_guard:d3", a - b, "<=", -2):
                return 3
            return 2
        return 1
    return 0


def distance_gate(a: int, b: int, *, probe: Probe | None = None) -> int:
    p = probe if probe is not None else Probe()
    if p.check("distance_gate:d1", abs(a - b), ">", 10):
        if p.check("distance_gate:d2", a + b, "<", 0):
            if p.check("distance_gate:d3", a - b, ">=", 4):
                return 3
            return 2
        return 1
    return 0


def product_guard(a: int, b: int, *, probe: Probe | None = None) -> int:
    p = probe if probe is not None else Probe()
    if p.check("product_guard:d1", a, ">=", 0):
        if p.check("product_guard:d2", b, ">", 0):
            if p.check("product_guard:d3", a * b, "==", 143):
                return 3
            return 2
        return 1
    return 0


def triple_gate(a: int, b: int, c: int, *, probe: Probe | None = None) -> int:
    p = probe if probe is not None else Probe()
    if p.check("triple_gate:d1", a + b, ">=", 6):
        if p.check("triple_gate:d2", c - a, "==", 3):
            if p.check("triple_gate:d3", b, "<", c):
                return 3
            return 2
        return 1
    return 0


FIXTURES = {
    f.__name__: f
    for f in (threshold_gate, sign_balance, modulo_guard, distance_gate, product_guard, triple_gate)
}
ARITIES = {name: 3 if name == "triple_gate" else 2 for name in FIXTURES}
TARGETS = tuple(
    f"{name}:d{d}:{truth}" for name in FIXTURES for d in (1, 2, 3) for truth in ("T", "F")
)


def execute(fixture: str, inputs: tuple[int, ...]) -> tuple[int, list[dict]]:
    if fixture not in FIXTURES:
        raise ValueError(f"Unknown fixture: {fixture}")
    if len(inputs) != ARITIES[fixture] or any(
        type(x) is not int or not -20 <= x <= 20 for x in inputs
    ):
        raise ValueError("Expected bounded integer inputs with the fixture arity")
    probe = Probe()
    output = FIXTURES[fixture](*inputs, probe=probe)
    return output, probe.observations
