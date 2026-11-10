import itertools

import pytest

from search_based_test_generation.distance import fitness
from search_based_test_generation.fixtures import execute
from search_based_test_generation.probe import COMPARATORS, distances


@pytest.mark.parametrize(
    "op,lhs,rhs", list(itertools.product(COMPARATORS, range(-3, 4), range(-3, 4)))
)
def test_every_direction_and_minimum_adjustment(op, lhs, rhs):
    dt, df = distances(lhs, op, rhs)
    assert (dt == 0) == COMPARATORS[op](lhs, rhs)
    assert (df == 0) != COMPARATORS[op](lhs, rhs)
    # Distance is the smallest absolute lhs adjustment satisfying each truth direction.
    for wanted, distance in ((True, dt), (False, df)):
        minimum = min(abs(x - lhs) for x in range(-15, 16) if COMPARATORS[op](x, rhs) == wanted)
        assert distance == minimum


@pytest.mark.parametrize("args,low,high", [((-1, 13), 2, 3), ((11, 0), 1, 2), ((11, 12), 0, 1)])
def test_nested_approach(args, low, high):
    _, trace = execute("product_guard", args)
    assert low < fitness("product_guard:d3:T", trace) < high


def test_zero_and_opposite_directions():
    _, trace = execute("product_guard", (11, 13))
    assert fitness("product_guard:d3:T", trace) == 0
    assert fitness("product_guard:d3:F", trace) == 0.5
    _, trace = execute("threshold_gate", (7, -3))
    assert fitness("threshold_gate:d1:T", trace) == 0.5
    assert fitness("threshold_gate:d1:F", trace) == 0
    assert fitness("threshold_gate:d2:T", trace) == 1.5


def test_invalid_target_and_trace():
    with pytest.raises(ValueError, match="Unknown"):
        fitness("fake", [])
    with pytest.raises(ValueError, match="Missing"):
        fitness("threshold_gate:d3:T", [])
    with pytest.raises(ValueError):
        distances(0, "invalid", 0)
    _, trace = execute("threshold_gate", (7, 0))
    trace[0]["distance_true"] = 0
    with pytest.raises(ValueError, match="positive"):
        fitness("threshold_gate:d3:T", trace)
