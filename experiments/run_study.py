"""Run the frozen full experiment from the repository root."""

from pathlib import Path

from search_based_test_generation.evidence import study

if __name__ == "__main__":
    study(Path.cwd(), Path("results/study"))
