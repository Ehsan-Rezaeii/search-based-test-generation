import json
import subprocess
import sys

import pytest

from search_based_test_generation.runner import run
from search_based_test_generation.suites import export_pytest, greedy, replay


def test_greedy_and_export(tmp_path):
    result = run("random", 0, budget=2)
    archive, selected = result["archive"], result["suite"]
    assert len(selected) < len(archive)
    assert all(c in archive for c in selected)
    assert replay(selected)["covered"] == result["summary"]["covered"]
    assert greedy(archive) == selected
    (tmp_path / "cases.json").write_text(json.dumps(selected))
    export_pytest(tmp_path / "test_generated.py", "cases.json")
    process = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(tmp_path / "test_generated.py")],
        capture_output=True,
        text=True,
    )
    assert process.returncode == 0, process.stdout + process.stderr


def test_empty_and_earliest_tie():
    assert greedy([]) == [] and replay([]) == {"fixture_calls": 0, "covered": []}
    c = run("ga", 0, budget=1)["archive"][0]
    later = dict(c, evaluation=2)
    assert greedy([later, c]) == [c]
    broken = dict(c, output=999)
    with pytest.raises(ValueError, match="Snapshot"):
        replay([broken])
