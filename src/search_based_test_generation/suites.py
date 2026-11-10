"""Deterministic archive-only set cover and separately counted regression replay."""

from .fixtures import execute
from .probe import outcomes


def greedy(archive: list[dict]) -> list[dict]:
    remaining = set().union(*(outcomes(c["trace"]) for c in archive))
    selected = []
    while remaining:
        best = min(
            archive,
            key=lambda c: (
                -len(outcomes(c["trace"]) & remaining),
                c["evaluation"],
                c["fixture"],
                tuple(c["inputs"]),
            ),
        )
        selected.append(best)
        remaining -= outcomes(best["trace"])
    return selected


def replay(cases: list[dict]) -> dict:
    covered = set()
    for case in cases:
        value, trace = execute(case["fixture"], tuple(case["inputs"]))
        if value != case["output"] or trace != case["trace"]:
            raise ValueError(f"Snapshot mismatch at evaluation {case['evaluation']}")
        covered |= outcomes(trace)
    return {"fixture_calls": len(cases), "covered": sorted(covered)}


def export_pytest(path, suite_file: str) -> None:
    """Emit portable pytest cases backed by the adjacent transparent JSON suite."""
    path.write_text(
        '''"""Generated regression snapshots; not an independent correctness oracle."""
import json
from pathlib import Path
import pytest
from search_based_test_generation.suites import replay
CASES = json.loads((Path(__file__).parent / SUITE_FILE).read_text())
@pytest.mark.parametrize("case", CASES)
def test_snapshot(case):
    assert replay([case])["fixture_calls"] == 1
'''.replace("SUITE_FILE", repr(suite_file))
    )
