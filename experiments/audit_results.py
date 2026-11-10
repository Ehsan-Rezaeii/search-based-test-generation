"""Audit saved evidence without invoking optimizers; suite replays count separately."""

import json
from pathlib import Path

from search_based_test_generation.evidence import audit

if __name__ == "__main__":
    print(json.dumps(audit(Path.cwd(), Path("results/study")), indent=2))
