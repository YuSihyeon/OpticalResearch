from __future__ import annotations

import math
import random
from typing import Mapping

import numpy as np


def aggregate_observations(observations: np.ndarray, weights: np.ndarray | None = None) -> np.ndarray:
    observations = np.asarray(observations, dtype=np.float32)
    if observations.ndim != 2:
        raise ValueError("observations must have shape NxC")
    if observations.shape[0] == 0:
        raise ValueError("cannot aggregate zero observations")
    if weights is None:
        return observations.mean(axis=0)

    weights = np.asarray(weights, dtype=np.float32)
    if weights.ndim != 1 or weights.shape[0] != observations.shape[0]:
        raise ValueError("weights must have shape N")
    denom = float(weights.sum())
    if denom <= 0.0:
        return observations.mean(axis=0)
    return (observations * weights[:, None]).sum(axis=0) / denom


def cosine_similarity(a: np.ndarray, b: np.ndarray, eps: float = 1e-8) -> float:
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    denom = max(float(np.linalg.norm(a) * np.linalg.norm(b)), eps)
    return float(np.dot(a, b) / denom)


def l2_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(np.asarray(a, dtype=np.float32) - np.asarray(b, dtype=np.float32)))


def leave_one_out_scores(
    observations_by_point: Mapping[int, np.ndarray],
    weights_by_point: Mapping[int, np.ndarray] | None = None,
    seed: int = 7,
) -> list[dict[str, float | int]]:
    rng = random.Random(seed)
    point_ids = [pid for pid, obs in observations_by_point.items() if len(obs) >= 3]
    rows: list[dict[str, float | int]] = []
    if len(point_ids) < 1:
        return rows

    for point_id in point_ids:
        obs = np.asarray(observations_by_point[point_id], dtype=np.float32)
        weights = None
        if weights_by_point is not None and point_id in weights_by_point:
            weights = np.asarray(weights_by_point[point_id], dtype=np.float32)

        n_views = obs.shape[0]
        for heldout_idx in range(n_views):
            context_idx = [i for i in range(n_views) if i != heldout_idx]
            heldout = obs[heldout_idx]

            single_idx = rng.choice(context_idx)
            single = obs[single_idx]
            multi = aggregate_observations(obs[context_idx])
            if weights is None:
                weighted = multi
            else:
                weighted = aggregate_observations(obs[context_idx], weights[context_idx])

            negative_candidates = [pid for pid in point_ids if pid != point_id]
            if negative_candidates:
                negative_pid = rng.choice(negative_candidates)
                negative_obs = np.asarray(observations_by_point[negative_pid], dtype=np.float32)
                negative = aggregate_observations(negative_obs)
                random_cosine = cosine_similarity(negative, heldout)
                random_l2 = l2_distance(negative, heldout)
            else:
                random_cosine = math.nan
                random_l2 = math.nan

            rows.append(
                {
                    "point_id": int(point_id),
                    "heldout_idx": int(heldout_idx),
                    "n_views": int(n_views),
                    "single_cosine": cosine_similarity(single, heldout),
                    "multi_cosine": cosine_similarity(multi, heldout),
                    "weighted_cosine": cosine_similarity(weighted, heldout),
                    "random_cosine": random_cosine,
                    "single_l2": l2_distance(single, heldout),
                    "multi_l2": l2_distance(multi, heldout),
                    "weighted_l2": l2_distance(weighted, heldout),
                    "random_l2": random_l2,
                }
            )
    return rows


def summarize_scores(rows: list[dict[str, float | int]]) -> list[dict[str, float | int | str]]:
    metrics = [
        ("single", "single_cosine", "single_l2"),
        ("multi_mean", "multi_cosine", "multi_l2"),
        ("weighted_multi", "weighted_cosine", "weighted_l2"),
        ("random_corr", "random_cosine", "random_l2"),
    ]
    out: list[dict[str, float | int | str]] = []
    for name, cos_key, l2_key in metrics:
        cos = np.array([float(r[cos_key]) for r in rows], dtype=np.float64)
        l2 = np.array([float(r[l2_key]) for r in rows], dtype=np.float64)
        out.append(
            {
                "method": name,
                "count": int(len(rows)),
                "mean_cosine": float(np.mean(cos)) if len(cos) else math.nan,
                "std_cosine": float(np.std(cos)) if len(cos) else math.nan,
                "mean_l2": float(np.mean(l2)) if len(l2) else math.nan,
                "std_l2": float(np.std(l2)) if len(l2) else math.nan,
            }
        )
    return out


def summarize_by_view_count(rows: list[dict[str, float | int]]) -> list[dict[str, float | int]]:
    out: list[dict[str, float | int]] = []
    counts = sorted({int(r["n_views"]) for r in rows})
    for n_views in counts:
        subset = [r for r in rows if int(r["n_views"]) == n_views]
        out.append(
            {
                "n_views": n_views,
                "count": len(subset),
                "single_cosine": float(np.mean([float(r["single_cosine"]) for r in subset])),
                "multi_cosine": float(np.mean([float(r["multi_cosine"]) for r in subset])),
                "weighted_cosine": float(np.mean([float(r["weighted_cosine"]) for r in subset])),
                "random_cosine": float(np.mean([float(r["random_cosine"]) for r in subset])),
                "single_l2": float(np.mean([float(r["single_l2"]) for r in subset])),
                "multi_l2": float(np.mean([float(r["multi_l2"]) for r in subset])),
                "weighted_l2": float(np.mean([float(r["weighted_l2"]) for r in subset])),
                "random_l2": float(np.mean([float(r["random_l2"]) for r in subset])),
            }
        )
    return out
