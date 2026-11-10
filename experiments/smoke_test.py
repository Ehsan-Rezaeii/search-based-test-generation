"""Small separate budget, never presented as a primary result."""

from search_based_test_generation.runner import run

if __name__ == "__main__":
    for method in ("ga", "random"):
        result = run(method, 0, budget=3)
        assert result["summary"]["evaluations"] == 108
        print(method, result["summary"]["coverage"])
