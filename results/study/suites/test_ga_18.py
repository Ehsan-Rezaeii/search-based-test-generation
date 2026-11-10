"""Generated regression snapshots; not an independent correctness oracle."""
import json
from pathlib import Path
import pytest
from search_based_test_generation.suites import replay
CASES = json.loads((Path(__file__).parent / 'ga-18.json').read_text())
@pytest.mark.parametrize("case", CASES)
def test_snapshot(case):
    assert replay([case])["fixture_calls"] == 1
