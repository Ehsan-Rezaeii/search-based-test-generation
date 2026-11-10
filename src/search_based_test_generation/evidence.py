"""Frozen protocol, compressed evidence, exhaustive reachability, and independent audits."""

import gzip
import hashlib
import importlib.metadata as metadata
import itertools
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .adapters import DEPENDENCY_COMMIT, configuration
from .distance import fitness
from .fixtures import ARITIES, TARGETS, execute
from .probe import COMPARATORS, distances, outcomes
from .runner import run, summarize
from .suites import export_pytest, greedy, replay


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dependency() -> dict:
    dist = metadata.distribution("metaheuristics-lab")
    direct = json.loads(dist.read_text("direct_url.json") or "{}")
    if direct.get("vcs_info", {}).get("commit_id") != DEPENDENCY_COMMIT:
        raise ValueError("Installed dependency is not the pinned Git commit")
    return {
        "version": dist.version,
        "direct_url": direct,
        "source_hashes": {
            str(p): sha(Path(dist.locate_file(p)))
            for p in dist.files
            if str(p).startswith("metaheuristics_lab/") and str(p).endswith(".py")
        },
    }


def source_paths(root: Path) -> list[Path]:
    paths = [
        root / "pyproject.toml",
        root / "docs/PROJECT_SPEC.md",
        root / "docs/EXPERIMENT_PROTOCOL.md",
        root / "experiments/settings.json",
        root / ".github/workflows/ci.yml",
    ]
    for directory in ("src", "tests", "experiments"):
        paths.extend((root / directory).rglob("*.py"))
    return sorted(set(paths))


def freeze(root: Path, destination: Path) -> dict:
    if destination.exists():
        raise ValueError("Refusing to overwrite a frozen manifest")
    manifest = {
        "phase": "preregistered",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "parent_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "settings": json.loads((root / "experiments/settings.json").read_text()),
        "targets": TARGETS,
        "dependency": dependency(),
        "configurations": {m: configuration(m) for m in ("ga", "random")},
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {d.metadata["Name"]: d.version for d in metadata.distributions()},
        "source_sha256": {str(p.relative_to(root)): sha(p) for p in source_paths(root)},
    }
    write_json(destination, manifest)
    return manifest


def reachability() -> dict:
    """Reference-only domain enumeration. Witnesses never enter the search API."""
    covered, counts, witnesses = set(), {}, {}
    for fixture, arity in ARITIES.items():
        calls = 0
        for inputs in itertools.product(range(-20, 21), repeat=arity):
            _, trace = execute(fixture, inputs)
            calls += 1
            for branch in outcomes(trace):
                covered.add(branch)
                witnesses.setdefault(branch, list(inputs))
        counts[fixture] = calls
    if covered != set(TARGETS):
        raise ValueError("Infeasible predeclared branch outcomes")
    return {
        "stage": "offline exhaustive feasibility; excluded from search",
        "fixture_calls": sum(counts.values()),
        "per_fixture_calls": counts,
        "covered": sorted(covered),
        "witnesses_validation_only": witnesses,
    }


def study(root: Path, output: Path) -> None:
    manifest_path = root / "experiments/prerun_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for name, digest in manifest["source_sha256"].items():
        if sha(root / name) != digest:
            raise ValueError(f"Frozen source changed: {name}")
    if dependency() != manifest["dependency"]:
        raise ValueError("Dependency changed since freeze")
    # Verify manifest and source were actually committed, and record that commit.
    subprocess.run(
        [
            "git",
            "diff",
            "--exit-code",
            "HEAD",
            "--",
            "src",
            "tests",
            "experiments",
            "pyproject.toml",
            "docs/EXPERIMENT_PROTOCOL.md",
        ],
        cwd=root,
        check=True,
    )
    if (
        subprocess.check_output(
            ["git", "ls-files", "experiments/prerun_manifest.json"], cwd=root, text=True
        ).strip()
        == ""
    ):
        raise ValueError("Manifest must be committed before execution")
    if output.exists():
        raise ValueError("Refusing to overwrite study output")
    output.mkdir(parents=True)
    settings = manifest["settings"]
    provenance = {
        "protocol_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "manifest_sha256": sha(manifest_path),
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "dependency_commit": DEPENDENCY_COMMIT,
        "settings": settings,
    }
    write_json(output / "provenance.json", provenance)
    summaries = []
    for method in settings["methods"]:
        for seed in settings["base_seeds"]:
            result = run(method, seed, budget=settings["evaluations_per_target"])
            stem = f"{method}-{seed:02}"
            with (output / f"{stem}.json.gz").open("wb") as raw:
                with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as zipped:
                    zipped.write(json.dumps(result, separators=(",", ":"), sort_keys=True).encode())
            cases = output / "suites" / f"{stem}.json"
            write_json(cases, result["suite"])
            export_pytest(cases.with_name(f"test_{method}_{seed:02}.py"), cases.name)
            summaries.append(result["summary"])
            print(method, seed, len(result["archive"]), result["summary"]["coverage"], flush=True)
    write_json(output / "summaries.json", summaries)
    write_json(
        output / "hashes.json",
        {str(p.relative_to(output)): sha(p) for p in sorted(output.rglob("*")) if p.is_file()},
    )


def reference_operands(fixture: str, inputs: list[int]) -> tuple:
    """Offline audit expressions; never award coverage or guide optimizer calls."""
    a, b = inputs[:2]
    if fixture == "threshold_gate":
        return ((a, ">", 7), (b, "<=", -3), (a + b, "==", 9))
    if fixture == "sign_balance":
        return ((a, "<", 0), (b, ">=", 0), (a + b, "==", 0))
    if fixture == "modulo_guard":
        return ((a % 5, "==", 0), (b % 3, "!=", 0), (a - b, "<=", -2))
    if fixture == "distance_gate":
        return ((abs(a - b), ">", 10), (a + b, "<", 0), (a - b, ">=", 4))
    if fixture == "product_guard":
        return ((a, ">=", 0), (b, ">", 0), (a * b, "==", 143))
    c = inputs[2]
    return ((a + b, ">=", 6), (c - a, "==", 3), (b, "<", c))


def validate_archive(result: dict, method: str, seed: int, budget: int = 60) -> dict:
    archive = result["archive"]
    if len(archive) != len(TARGETS) * budget:
        raise ValueError("Incorrect archive length")
    if result["configuration"] != configuration(method):
        raise ValueError("Optimizer configuration mismatch")
    for i, c in enumerate(archive):
        target_index = i // budget
        target = TARGETS[target_index]
        fixture = target.split(":")[0]
        if (c["target"], c["target_index"], c["optimizer_seed"], c["fixture"]) != (
            target,
            target_index,
            seed * 1000 + target_index,
            fixture,
        ):
            raise ValueError("Target/seed schedule mismatch")
        inputs = c["inputs"]
        if len(inputs) != ARITIES[fixture] or any(
            type(x) is not int or not -20 <= x <= 20 for x in inputs
        ):
            raise ValueError("Invalid candidate domain")
        trace = c["trace"]
        if not 1 <= len(trace) <= 3:
            raise ValueError("Invalid trace length")
        for level, observation in enumerate(trace, 1):
            if observation["decision"] != f"{fixture}:d{level}":
                raise ValueError("Trace decision order mismatch")
            lhs, op, rhs = observation["lhs"], observation["op"], observation["rhs"]
            if (lhs, op, rhs) != reference_operands(fixture, inputs)[level - 1]:
                raise ValueError("Operand evidence does not match actual integer input")
            dt, df = distances(lhs, op, rhs)
            actual = bool(COMPARATORS[op](lhs, rhs))
            if (
                observation["outcome"],
                observation["distance_true"],
                observation["distance_false"],
            ) != (actual, dt, df):
                raise ValueError("Invalid comparison evidence")
            if level < len(trace) and not actual:
                raise ValueError("Fabricated descendant coverage")
        if len(trace) < 3 and trace[-1]["outcome"]:
            raise ValueError("Missing executed descendant")
        expected_output = len(trace) - 1 + int(len(trace) == 3 and trace[-1]["outcome"])
        if c["output"] != expected_output or c["fitness"] != fitness(target, trace):
            raise ValueError("Output/fitness mismatch")
    recomputed = summarize(archive)
    for key, value in recomputed.items():
        if result["summary"][key] != value:
            raise ValueError(f"Summary mismatch: {key}")
    if result["summary"]["method"] != method or result["summary"]["base_seed"] != seed:
        raise ValueError("Run identity mismatch")
    for i, optimizer_run in enumerate(result["optimizer_runs"]):
        chunk = archive[i * budget : (i + 1) * budget]
        if optimizer_run["target"] != TARGETS[i] or optimizer_run["seed"] != seed * 1000 + i:
            raise ValueError("Optimizer run schedule mismatch")
        if optimizer_run["evaluations"] != budget or optimizer_run["best_fitness"] != min(
            c["fitness"] for c in chunk
        ):
            raise ValueError("Optimizer accounting mismatch")
        hits = [c["evaluation"] for c in chunk if TARGETS[i] in outcomes(c["trace"])]
        if optimizer_run["target_hits_in_allocation"] != len(hits) or optimizer_run[
            "first_target_hit_in_allocation"
        ] != (hits[0] if hits else None):
            raise ValueError("Target discovery summary mismatch")
    if len(result["optimizer_runs"]) != len(TARGETS):
        raise ValueError("Missing optimizer runs")
    if result["suite"] != greedy(archive):
        raise ValueError("Noncanonical greedy suite")
    verified = replay(result["suite"])
    if (
        verified["covered"] != recomputed["covered"]
        or result["summary"]["suite_size"] != verified["fixture_calls"]
    ):
        raise ValueError("Suite failed to preserve archive coverage")
    for key, value in verified.items():
        if result["summary"]["replay"][key] != value:
            raise ValueError("Saved replay mismatch")
    return {"search_calls": len(archive), "audit_suite_replay_calls": verified["fixture_calls"]}


def audit(root: Path, output: Path) -> dict:
    manifest_path = root / "experiments/prerun_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    provenance = json.loads((output / "provenance.json").read_text())
    if sha(manifest_path) != provenance["manifest_sha256"]:
        raise ValueError("Manifest hash mismatch")
    for name, digest in manifest["source_sha256"].items():
        if sha(root / name) != digest:
            raise ValueError(f"Source hash mismatch: {name}")
    if (
        provenance["settings"] != manifest["settings"]
        or provenance["dependency_commit"] != DEPENDENCY_COMMIT
    ):
        raise ValueError("Provenance mismatch")
    for name, digest in json.loads((output / "hashes.json").read_text()).items():
        if sha(output / name) != digest:
            raise ValueError(f"Artifact hash mismatch: {name}")
    totals = {"search_calls": 0, "audit_suite_replay_calls": 0, "runs": 0}
    summaries = []
    for method in manifest["settings"]["methods"]:
        for seed in manifest["settings"]["base_seeds"]:
            stem = f"{method}-{seed:02}"
            result = json.loads(gzip.decompress((output / f"{stem}.json.gz").read_bytes()))
            counts = validate_archive(
                result, method, seed, manifest["settings"]["evaluations_per_target"]
            )
            if json.loads((output / "suites" / f"{stem}.json").read_text()) != result["suite"]:
                raise ValueError("Exported suite mismatch")
            for key in counts:
                totals[key] += counts[key]
            totals["runs"] += 1
            summaries.append(result["summary"])
    if summaries != json.loads((output / "summaries.json").read_text()):
        raise ValueError("Aggregate summaries mismatch")
    return totals
