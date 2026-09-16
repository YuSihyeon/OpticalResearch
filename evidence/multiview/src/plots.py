from __future__ import annotations

from pathlib import Path
import random

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from .aggregation import aggregate_observations, cosine_similarity


def plot_summary(summary_rows: list[dict], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    labels = [str(row["method"]) for row in summary_rows]
    cos = [float(row["mean_cosine"]) for row in summary_rows]
    l2 = [float(row["mean_l2"]) for row in summary_rows]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar(labels, cos, color=["#4c78a8", "#59a14f", "#f28e2b", "#e15759"])
    axes[0].set_ylabel("Mean cosine similarity")
    axes[0].set_ylim(min(0.0, min(cos) - 0.05), min(1.0, max(cos) + 0.05))
    axes[0].tick_params(axis="x", rotation=20)
    axes[1].bar(labels, l2, color=["#4c78a8", "#59a14f", "#f28e2b", "#e15759"])
    axes[1].set_ylabel("Mean L2 distance")
    axes[1].tick_params(axis="x", rotation=20)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def plot_by_view_count(by_view_rows: list[dict], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    x = np.array([int(row["n_views"]) for row in by_view_rows], dtype=np.int32)
    fig, ax = plt.subplots(figsize=(7, 4))
    for key, label, color in [
        ("single_cosine", "Single-view", "#4c78a8"),
        ("multi_cosine", "Multi-view mean", "#59a14f"),
        ("weighted_cosine", "Weighted multi-view", "#f28e2b"),
        ("random_cosine", "Random correspondence", "#e15759"),
    ]:
        y = np.array([float(row[key]) for row in by_view_rows], dtype=np.float32)
        ax.plot(x, y, marker="o", label=label, color=color)
    ax.set_xlabel("Number of observing views")
    ax.set_ylabel("Mean held-out cosine similarity")
    ax.legend()
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def plot_cosine_hist(rows: list[dict], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    fig, ax = plt.subplots(figsize=(7, 4))
    for key, label, color in [
        ("single_cosine", "Single-view", "#4c78a8"),
        ("multi_cosine", "Multi-view mean", "#59a14f"),
        ("weighted_cosine", "Weighted multi-view", "#f28e2b"),
        ("random_cosine", "Random correspondence", "#e15759"),
    ]:
        values = [float(row[key]) for row in rows if not np.isnan(float(row[key]))]
        ax.hist(values, bins=40, alpha=0.42, label=label, color=color)
    ax.set_xlabel("Held-out cosine similarity")
    ax.set_ylabel("Count")
    ax.legend()
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def plot_point_visualizations(
    meta_by_point: dict[int, list[dict]],
    observations_by_point: dict[int, np.ndarray],
    weights_by_point: dict[int, np.ndarray],
    image_dir: str | Path,
    output_dir: str | Path,
    max_points: int = 5,
    seed: int = 7,
) -> list[Path]:
    image_dir = Path(image_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    eligible = [pid for pid, obs in observations_by_point.items() if len(obs) >= 4 and pid in meta_by_point]
    if len(eligible) > max_points:
        eligible = rng.sample(eligible, max_points)

    output_paths: list[Path] = []
    for point_id in eligible:
        obs = observations_by_point[point_id]
        meta = meta_by_point[point_id]
        chosen = list(range(min(6, len(meta))))
        sim = obs @ obs.T
        norms = np.linalg.norm(obs, axis=1, keepdims=True)
        sim = sim / np.maximum(norms @ norms.T, 1e-8)

        heldout = obs[0]
        context = obs[1:]
        mean = aggregate_observations(context)
        weights = weights_by_point.get(point_id)
        weighted = aggregate_observations(context, weights[1:]) if weights is not None else mean
        negative_candidates = [pid for pid in observations_by_point.keys() if pid != point_id]
        negative = aggregate_observations(observations_by_point[rng.choice(negative_candidates)])
        heldout_scores = [
            cosine_similarity(context[0], heldout),
            cosine_similarity(mean, heldout),
            cosine_similarity(weighted, heldout),
            cosine_similarity(negative, heldout),
        ]

        fig = plt.figure(figsize=(13, 6))
        grid = fig.add_gridspec(2, 6)
        for panel_idx, obs_idx in enumerate(chosen):
            ax = fig.add_subplot(grid[0, panel_idx])
            item = meta[obs_idx]
            image = Image.open(image_dir / str(item["image_name"])).convert("RGB")
            ax.imshow(image)
            ax.scatter([float(item["u"])], [float(item["v"])], c="red", s=28)
            ax.set_title(f"view {int(item['view_idx'])}")
            ax.axis("off")

        ax_sim = fig.add_subplot(grid[1, :3])
        im = ax_sim.imshow(sim, vmin=-1.0, vmax=1.0, cmap="viridis")
        ax_sim.set_title("Pairwise feature cosine by view")
        ax_sim.set_xlabel("observation")
        ax_sim.set_ylabel("observation")
        fig.colorbar(im, ax=ax_sim, fraction=0.046, pad=0.04)

        ax_bar = fig.add_subplot(grid[1, 3:])
        ax_bar.bar(["single", "mean", "weighted", "random"], heldout_scores, color=["#4c78a8", "#59a14f", "#f28e2b", "#e15759"])
        ax_bar.set_ylim(min(0.0, min(heldout_scores) - 0.05), min(1.0, max(heldout_scores) + 0.05))
        ax_bar.set_title("Aggregation vs held-out obs 0")
        ax_bar.set_ylabel("Cosine similarity")
        fig.suptitle(f"Projected correspondences for point {point_id}")
        fig.tight_layout()

        output_path = output_dir / f"point_{point_id}_consistency.png"
        fig.savefig(output_path, dpi=160)
        plt.close(fig)
        output_paths.append(output_path)
    return output_paths
