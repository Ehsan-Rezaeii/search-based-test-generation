from unittest.mock import patch

import pytest

from search_based_test_generation import runner
from search_based_test_generation.evidence import validate_archive
from search_based_test_generation.fixtures import TARGETS


@pytest.mark.parametrize("method", ["ga", "random"])
def test_run_accounting_and_determinism(method):
    with patch.object(runner, "execute", wraps=runner.execute) as sut:
        first = runner.run(method, 2, budget=3)
    assert sut.call_count == 108  # Replay is in a separate module/stage.
    second = runner.run(method, 2, budget=3)
    assert first["archive"] == second["archive"]
    summary = first["summary"]
    assert summary["evaluations"] == 108
    assert len(summary["curve"]) == 109 and summary["curve"][0] == 0
    assert summary["curve"] == sorted(summary["curve"])
    assert summary["curve"][-1] == len(summary["covered"])
    assert 0 <= summary["auc"] <= 1
    assert sum(summary["per_fixture"].values()) == len(summary["covered"])
    assert validate_archive(first, method, 2, budget=3)["search_calls"] == 108
    assert [r["target"] for r in first["optimizer_runs"]] == list(TARGETS)


def test_duplicate_calls_not_discounted_or_cached():
    def repeated(method, objective, arity, budget, seed):
        from types import SimpleNamespace

        for _ in range(budget):
            objective([0.0] * arity)
        return SimpleNamespace(n_evaluations=budget, runtime_seconds=0, best_fitness=0)

    with (
        patch.object(runner, "optimize", repeated),
        patch.object(runner, "execute", wraps=runner.execute) as sut,
    ):
        result = runner.run("ga", 0, budget=4, targets=TARGETS[:2])
    assert sut.call_count == len(result["archive"]) == 8
    assert result["summary"]["unique_inputs"] == 1
    assert sum(c["duplicate"] for c in result["archive"]) == 7


def test_empty_summary():
    assert runner.summarize([])["curve"] == [0]
