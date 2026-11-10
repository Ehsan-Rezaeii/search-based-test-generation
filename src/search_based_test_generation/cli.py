"""Explicit commands: never run a full study on package import."""

import argparse
import json
from pathlib import Path

from .evidence import audit, freeze, reachability, study, write_json
from .runner import run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "freeze", "reachability", "study", "audit"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "smoke":
        for method in ("ga", "random"):
            result = run(method, 0, budget=3)
            print(json.dumps({k: v for k, v in result["summary"].items() if k != "curve"}))
    elif args.command == "freeze":
        freeze(root, root / "experiments/prerun_manifest.json")
    elif args.command == "reachability":
        result = reachability()
        write_json(args.output or root / "results/reachability.json", result)
        print(json.dumps({k: v for k, v in result.items() if k != "witnesses_validation_only"}))
    elif args.command == "study":
        study(root, args.output or root / "results/study")
    else:
        print(json.dumps(audit(root, args.output or root / "results/study"), sort_keys=True))


if __name__ == "__main__":
    main()
