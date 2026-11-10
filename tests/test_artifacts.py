from copy import deepcopy
from pathlib import Path

import pytest

from search_based_test_generation.evidence import audit, validate_archive
from search_based_test_generation.runner import run


@pytest.mark.parametrize(
    "mutation",
    ["duplicate", "fitness", "seed", "descendant", "summary", "output", "config", "suite"],
)
def test_audit_rejects_mutations(mutation):
    result = deepcopy(run("ga", 0, budget=1))
    case = result["archive"][0]
    if mutation == "duplicate":
        case["duplicate"] = not case["duplicate"]
    elif mutation == "fitness":
        case["fitness"] += 1
    elif mutation == "seed":
        case["optimizer_seed"] = 99
    elif mutation == "descendant":
        case["trace"] = [dict(case["trace"][0], outcome=False)] + case["trace"]
    elif mutation == "summary":
        result["summary"]["curve"][-1] = -1
    elif mutation == "output":
        case["output"] = 999
    elif mutation == "config":
        result["configuration"]["settings"]["population_size"] = 30
    else:
        result["suite"] = []
    with pytest.raises(ValueError):
        validate_archive(result, "ga", 0, budget=1)


def test_saved_artifacts_when_present():
    root = Path(__file__).resolve().parents[1]
    output = root / "results/study"
    if not output.exists():
        pytest.skip("Pre-results phase: full experiment has not been executed")
    counts = audit(root, output)
    assert counts["search_calls"] == 86400
    assert counts["runs"] == 40
