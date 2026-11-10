"""Derive descriptive tables and figures from saved, audited observations."""

import json
import statistics as stats
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def describe(values):
    return {
        "mean": stats.mean(values),
        "median": stats.median(values),
        "sd": stats.stdev(values),
        "min": min(values),
        "max": max(values),
    }


def main():
    root = Path.cwd()
    output = root / "results/study"
    rows = json.loads((output / "summaries.json").read_text())
    figures = root / "results/figures"
    figures.mkdir(exist_ok=True)
    groups = {m: [r for r in rows if r["method"] == m] for m in ("ga", "random")}
    metrics = (
        "coverage",
        "auc",
        "unique_inputs",
        "duplicate_rate",
        "runtime_seconds",
        "suite_size",
    )
    report = {
        m: {metric: describe([r[metric] for r in group]) for metric in metrics}
        for m, group in groups.items()
    }
    diffs = [
        (g["coverage"] - r["coverage"]) * 36
        for g, r in zip(groups["ga"], groups["random"], strict=True)
    ]
    report["comparison"] = {
        "ga_wins": sum(d > 0 for d in diffs),
        "ties": sum(d == 0 for d in diffs),
        "ga_losses": sum(d < 0 for d in diffs),
        "paired_outcome_differences": diffs,
    }
    (root / "results/statistics.json").write_text(json.dumps(report, indent=2) + "\n")
    colors = {"ga": "#335ccc", "random": "#cf701b"}
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for method, group in groups.items():
        for row in group:
            ax.plot([v / 36 for v in row["curve"]], color=colors[method], alpha=0.12, linewidth=0.7)
        means = [stats.mean(r["curve"][i] / 36 for r in group) for i in range(2161)]
        ax.plot(means, label=f"{method} mean (20 seeds)", color=colors[method])
    ax.set(
        xlabel="Actual search fixture executions", ylabel="Observed outcomes / 36", ylim=(0, 1.02)
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures / "coverage_curves.png", dpi=150)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4))
    for method, group in groups.items():
        ax.plot(
            [r["base_seed"] for r in group],
            [len(r["covered"]) for r in group],
            "o-",
            label=method,
            color=colors[method],
        )
    ax.set(xlabel="Base seed", ylabel="Final observed outcomes (of 36)", xticks=range(20))
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures / "final_by_seed.png", dpi=150)
    plt.close(fig)
    fixtures = list(rows[0]["per_fixture"])
    fig, ax = plt.subplots(figsize=(9, 4))
    for offset, (method, group) in zip((-0.18, 0.18), groups.items(), strict=True):
        ax.bar(
            [i + offset for i in range(6)],
            [stats.mean(r["per_fixture"][f] for r in group) for f in fixtures],
            width=0.36,
            label=method,
            color=colors[method],
        )
    ax.set(
        xticks=range(6), xticklabels=fixtures, ylabel="Mean observed outcomes (of 6)", ylim=(0, 6.5)
    )
    ax.tick_params(axis="x", rotation=20)
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures / "per_fixture.png", dpi=150)
    plt.close(fig)
    lines = [
        "# Measured results",
        "",
        "The full frozen primary experiment completed: 40 runs, 86,400 actual search calls. "
        "Each run used all 36 targets at 60 calls each. All 20 seeds are retained.",
        "",
        "Descriptive statistics below use sample SD. Coverage is observed decision outcomes / 36. "
        "AUC is the preregistered right-step normalized curve sum. No significance or causal guidance claim is made.",
        "",
        "| Method | Metric | Mean | Median | Sample SD | Min | Max |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for method in groups:
        for metric in metrics:
            d = report[method][metric]
            lines.append(
                f"| {method} | {metric} | "
                + " | ".join(f"{d[k]:.6f}" for k in ("mean", "median", "sd", "min", "max"))
                + " |"
            )
    c = report["comparison"]
    lines += [
        "",
        f"GA wins/ties/losses by paired base-seed final coverage: **{c['ga_wins']}/{c['ties']}/{c['ga_losses']}**. "
        "The methods share seed labels and initialization streams, not identical later candidates. "
        "Random Search is independent uniform testing under the same representation and schedule.",
        "",
        "| Seed | GA outcomes | Random outcomes | Difference | GA unique | Random unique | GA suite | Random suite | GA seconds | Random seconds |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for g, r, diff in zip(groups["ga"], groups["random"], diffs, strict=True):
        lines.append(
            f"| {g['base_seed']} | {len(g['covered'])} | {len(r['covered'])} | {diff:.0f} | {g['unique_inputs']} | {r['unique_inputs']} | {g['suite_size']} | {r['suite_size']} | {g['runtime_seconds']:.4f} | {r['runtime_seconds']:.4f} |"
        )
    lines += ["", "| Fixture | GA mean / 6 | Random mean / 6 |", "|---|---:|---:|"]
    for f in fixtures:
        lines.append(
            f"| {f} | {stats.mean(r['per_fixture'][f] for r in groups['ga']):.3f} | {stats.mean(r['per_fixture'][f] for r in groups['random']):.3f} |"
        )
    lines += [
        "",
        "![Coverage trajectories](../results/figures/coverage_curves.png)",
        "",
        "![Seed variability](../results/figures/final_by_seed.png)",
        "",
        "![Per-fixture performance](../results/figures/per_fixture.png)",
        "",
        "All first-hit outcome discovery times and full 2161-point per-run curves are in `results/study/summaries.json`. "
        "Each compressed run contains every candidate, operands, path, fitness and optimizer call summary. "
        "Unobserved targets remain absent from first-hit maps. Timing measures this environment and includes tracing, not export or suite minimization.",
        "",
        "The six hand-designed toy functions favor transparent distance guidance and do not establish effectiveness on real software. "
        "A 60-call allocation gives very few generations. Integer decoding creates plateaus; continuous GA clipping and repeated inputs consume budget. "
        "Comparison-level product/modulo distances do not equal input edit distances. No ablation isolates distance from selection or approach levels. "
        "Greedy set cover is deterministic but not guaranteed minimum. Snapshot outputs prove regression consistency, not correctness; "
        "independent handwritten tests provide a separate limited reference. This is white-box search with no ML holdout.",
    ]
    (root / "docs/RESULTS.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
