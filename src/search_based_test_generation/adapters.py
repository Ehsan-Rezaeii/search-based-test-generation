"""Installed Project 1 optimizers, with a shared integer cell representation."""

import math

from metaheuristics_lab import GA, Problem, RandomSearch

DEPENDENCY_COMMIT = "6b4ef0fa3d72f608146f3dd7eabb84bf39fa896e"


def decode(vector) -> tuple[int, ...]:
    return tuple(max(-20, min(20, math.floor(float(v) + 0.5))) for v in vector)


def make_optimizer(method: str):
    if method == "ga":
        return GA(
            population_size=12,
            crossover_rate=0.9,
            mutation_rate=None,
            mutation_scale=0.1,
            tournament_size=3,
        )
    if method == "random":
        return RandomSearch(population_size=12, domain="continuous")
    raise ValueError(f"Unknown method: {method}")


def configuration(method: str) -> dict:
    optimizer = make_optimizer(method)
    return {
        "class": f"{type(optimizer).__module__}.{type(optimizer).__name__}",
        "domain": optimizer.domain,
        "settings": vars(optimizer).copy(),
        "bounds": [-20.5, 20.5],
        "decoder": "clamp(floor(v+0.5),-20,20)",
    }


def optimize(method: str, objective, arity: int, budget: int, seed: int):
    optimizer = make_optimizer(method)
    problem = Problem.continuous(objective, dimension=arity, lower=-20.5, upper=20.5)
    return optimizer.optimize(problem, max_evaluations=budget, seed=seed)
