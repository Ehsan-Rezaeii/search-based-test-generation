import math
from unittest.mock import patch

import numpy as np
import pytest
from metaheuristics_lab import GA, RandomSearch

from search_based_test_generation import adapters
from search_based_test_generation.evidence import dependency


@pytest.mark.parametrize(
    "value,expected",
    [
        (-100, -20),
        (-20.5, -20),
        (-20, -20),
        (-1.5, -1),
        (-0.5, 0),
        (0.49999, 0),
        (0.5, 1),
        (19.5, 20),
        (20.5, 20),
        (100, 20),
    ],
)
def test_decoder_boundaries(value, expected):
    assert adapters.decode([value]) == (expected,)


def test_equal_width_cells():
    values = np.arange(-20.5, 20.5, 0.01) + 0.005
    unique, counts = np.unique([adapters.decode([v])[0] for v in values], return_counts=True)
    assert list(unique) == list(range(-20, 21))
    assert set(counts) == {100}
    with pytest.raises((ValueError, OverflowError)):
        adapters.decode([math.inf])


def test_actual_constructors():
    for method, cls in (("ga", GA), ("random", RandomSearch)):
        with patch.object(adapters, cls.__name__, wraps=cls) as constructor:
            optimizer = adapters.make_optimizer(method)
            assert isinstance(optimizer, cls)
            assert constructor.call_args.kwargs["population_size"] == 12
            if method == "random":
                assert constructor.call_args.kwargs["domain"] == "continuous"
            assert optimizer.population_size == 12 and optimizer.domain == "continuous"
    assert adapters.configuration("ga")["settings"]["mutation_rate"] is None
    with pytest.raises(ValueError):
        adapters.make_optimizer("fake")
    assert dependency()["direct_url"]["vcs_info"]["commit_id"] == adapters.DEPENDENCY_COMMIT


@pytest.mark.parametrize("method", ["ga", "random"])
@pytest.mark.parametrize("budget", [1, 13, 60])
def test_real_optimizer_exact_budget_and_problem(method, budget):
    calls = []

    def objective(vector):
        calls.append(vector.copy())
        return 0.0  # Already covered does not permit early stopping.

    with patch.object(adapters.Problem, "continuous", wraps=adapters.Problem.continuous) as create:
        result = adapters.optimize(method, objective, 2, budget, 7)
    assert len(calls) == result.n_evaluations == budget
    assert create.call_args.kwargs == {"dimension": 2, "lower": -20.5, "upper": 20.5}
    assert len(result.history) == budget
