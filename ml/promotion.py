from __future__ import annotations

from statistics import mean
from typing import List

from .registry import ModelRegistry
from .training import build_training_corpus


def _score_dataset(rows: List[dict[str, str]]) -> float:
    lengths = [len(row.get("NOME_CANDIDATO", "")) for row in rows]
    return mean(lengths) if lengths else 0.0


def evaluate_and_promote(candidate_version: str) -> None:
    registry = ModelRegistry()
    rows = build_training_corpus()
    score = _score_dataset(rows)
    registry.promote(candidate_version)
    registry.update_metrics(candidate_version, {"dataset_score": score})


def rollback(version: str) -> None:
    registry = ModelRegistry()
    registry.rollback(version)
