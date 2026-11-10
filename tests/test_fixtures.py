"""Hand-authored output/path expectations, independent of generated snapshots."""

import ast
import inspect
import itertools

import pytest

from search_based_test_generation.fixtures import ARITIES, FIXTURES, TARGETS, execute
from search_based_test_generation.probe import outcomes

# Each row explicitly specifies all four terminal paths, including nested boundaries.
REFERENCES = {
    "threshold_gate": [((7, -3), 0), ((8, -2), 1), ((8, -3), 2), ((12, -3), 3)],
    "sign_balance": [((0, 0), 0), ((-1, -1), 1), ((-2, 1), 2), ((-1, 1), 3)],
    "modulo_guard": [((1, 1), 0), ((-5, -3), 1), ((0, 1), 2), ((0, 2), 3)],
    "distance_gate": [((5, -5), 0), ((20, 0), 1), ((-20, 0), 2), ((0, -20), 3)],
    "product_guard": [((-1, 1), 0), ((0, 0), 1), ((0, 1), 2), ((11, 13), 3)],
    "triple_gate": [((2, 3, 0), 0), ((2, 4, 4), 1), ((1, 5, 4), 2), ((3, 3, 6), 3)],
}


@pytest.mark.parametrize(
    "fixture,inputs,expected",
    [(f, inputs, expected) for f, rows in REFERENCES.items() for inputs, expected in rows],
)
def test_handwritten(fixture, inputs, expected):
    value, trace = execute(fixture, inputs)
    assert value == FIXTURES[fixture](*inputs) == expected
    expected_truths = {0: [False], 1: [True, False], 2: [True, True, False], 3: [True] * 3}
    assert [o["outcome"] for o in trace] == expected_truths[expected]
    assert [o["decision"] for o in trace] == [f"{fixture}:d{i}" for i in range(1, len(trace) + 1)]


def test_static_inventory():
    assert len(TARGETS) == len(set(TARGETS)) == 36
    assert list(ARITIES.values()) == [2, 2, 2, 2, 2, 3]
    for function in FIXTURES.values():
        tree = ast.parse(inspect.getsource(function))
        assert sum(isinstance(n, ast.If) for n in ast.walk(tree)) == 3
        assert not any(isinstance(n, (ast.For, ast.While, ast.BoolOp)) for n in ast.walk(tree))


def reference_predicates(name, args):
    """Independent plain comparisons, used only for validation, never for search."""
    a, b = args[:2]
    if name == "threshold_gate":
        return a > 7, b <= -3, a + b == 9
    if name == "sign_balance":
        return a < 0, b >= 0, a + b == 0
    if name == "modulo_guard":
        return a % 5 == 0, b % 3 != 0, a - b <= -2
    if name == "distance_gate":
        return abs(a - b) > 10, a + b < 0, a - b >= 4
    if name == "product_guard":
        return a >= 0, b > 0, a * b == 143
    c = args[2]
    return a + b >= 6, c - a == 3, b < c


def test_exhaustive_independent_reference():
    """All 77,326 executions are validation cost, outside all optimization budgets."""
    covered = set()
    calls = 0
    for name, arity in ARITIES.items():
        for args in itertools.product(range(-20, 21), repeat=arity):
            predicates = reference_predicates(name, args)
            expected = next((i for i, truth in enumerate(predicates) if not truth), 3)
            value, trace = execute(name, args)
            assert value == expected
            assert [o["outcome"] for o in trace] == list(predicates[: min(expected + 1, 3)])
            covered |= outcomes(trace)
            calls += 1
    assert calls == 77326
    assert covered == set(TARGETS)


@pytest.mark.parametrize(
    "name,args",
    [
        ("unknown", (0, 0)),
        ("threshold_gate", (0,)),
        ("threshold_gate", (21, 0)),
        ("threshold_gate", (True, 0)),
    ],
)
def test_invalid_domain(name, args):
    with pytest.raises(ValueError):
        execute(name, args)


def test_no_false_coverage_or_global_leak():
    _, trace = execute("product_guard", (-1, 13))
    assert outcomes(trace) == {"product_guard:d1:F"}
    assert "product_guard:d3:T" not in outcomes(trace)
    _, later = execute("product_guard", (11, 13))
    assert len(later) == 3
    assert len(trace) == 1
