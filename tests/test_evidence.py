"""Exercise the artifact pipeline with a separate tiny budget and isolated files."""

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from search_based_test_generation import cli, evidence


def test_manifest_study_audit_and_tampering(tmp_path):
    root = Path(__file__).resolve().parents[1]
    for path in evidence.source_paths(root):
        destination = tmp_path / path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
    settings = tmp_path / "experiments/settings.json"
    settings.write_text(
        json.dumps({"methods": ["ga", "random"], "base_seeds": [0], "evaluations_per_target": 1})
    )
    manifest = tmp_path / "experiments/prerun_manifest.json"
    with patch.object(evidence.subprocess, "check_output", return_value="test-only-commit\n"):
        evidence.freeze(tmp_path, manifest)
        with pytest.raises(ValueError, match="overwrite"):
            evidence.freeze(tmp_path, manifest)
        with patch.object(evidence.subprocess, "run"):
            evidence.study(tmp_path, tmp_path / "output")
            with pytest.raises(ValueError, match="overwrite"):
                evidence.study(tmp_path, tmp_path / "output")
    result = evidence.audit(tmp_path, tmp_path / "output")
    assert result["search_calls"] == 72 and result["runs"] == 2
    original = settings.read_text()
    settings.write_text("{}")
    with pytest.raises(ValueError, match="Source hash"):
        evidence.audit(tmp_path, tmp_path / "output")
    settings.write_text(original)
    summaries = tmp_path / "output/summaries.json"
    summaries.write_text("[]")
    with pytest.raises(ValueError, match="Artifact hash"):
        evidence.audit(tmp_path, tmp_path / "output")


def test_reachability_explicit_cost():
    result = evidence.reachability()
    assert result["fixture_calls"] == 77326
    assert len(result["covered"]) == 36


@pytest.mark.parametrize(
    "command,called",
    [
        ("freeze", "freeze"),
        ("study", "study"),
        ("audit", "audit"),
        ("reachability", "reachability"),
    ],
)
def test_cli_routes(command, called, tmp_path):
    with (
        patch("sys.argv", ["sbst", command, "--root", str(tmp_path)]),
        patch.object(cli, called, return_value={"covered": []}) as function,
    ):
        cli.main()
        assert function.call_count == 1


def test_cli_smoke(capsys):
    with patch("sys.argv", ["sbst", "smoke"]):
        cli.main()
    assert '"evaluations": 108' in capsys.readouterr().out
