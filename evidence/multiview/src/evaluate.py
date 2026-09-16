from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .aggregation import leave_one_out_scores, summarize_by_view_count, summarize_scores
from .sampling import bilinear_sample_chw, image_to_feature_coords, l2_normalize
from .tracks import ObservationTable


def load_feature_npz(feature_path: str | Path) -> tuple[dict[str, np.ndarray], tuple[int, int]]:
    data = np.load(feature_path, allow_pickle=False)
    features = data["features"]
    image_names = [str(x) for x in data["image_names"]]
    image_size_arr = data["image_size"]
    image_size = (int(image_size_arr[0]), int(image_size_arr[1]))
    return {name: features[i] for i, name in enumerate(image_names)}, image_size


def sample_observation_features(
    observations: ObservationTable,
    feature_maps: dict[str, np.ndarray],
    image_names: list[str],
    image_size: tuple[int, int],
    normalize: bool = True,
) -> tuple[dict[int, np.ndarray], dict[int, np.ndarray], dict[int, list[dict[str, float | int | str]]]]:
    obs_by_point: dict[int, list[np.ndarray]] = {}
    weights_by_point: dict[int, list[float]] = {}
    meta_by_point: dict[int, list[dict[str, float | int | str]]] = {}

    for view_idx, image_name in enumerate(image_names):
        rows = np.where(observations.view_indices == view_idx)[0]
        if len(rows) == 0 or image_name not in feature_maps:
            continue
        feature_map = feature_maps[image_name]
        _, feat_h, feat_w = feature_map.shape
        coords = image_to_feature_coords(
            observations.uv[rows],
            image_size=(image_size[0], image_size[1]),
            feature_size=(feat_w, feat_h),
        )
        sampled = bilinear_sample_chw(feature_map, coords).astype(np.float32)
        if normalize:
            sampled = l2_normalize(sampled)
        for local_idx, row_idx in enumerate(rows):
            point_id = int(observations.point_indices[row_idx])
            obs_by_point.setdefault(point_id, []).append(sampled[local_idx])
            weights_by_point.setdefault(point_id, []).append(float(observations.weights[row_idx]))
            meta_by_point.setdefault(point_id, []).append(
                {
                    "point_id": point_id,
                    "view_idx": int(view_idx),
                    "image_name": image_name,
                    "u": float(observations.uv[row_idx, 0]),
                    "v": float(observations.uv[row_idx, 1]),
                    "depth": float(observations.depth[row_idx]),
                    "weight": float(observations.weights[row_idx]),
                }
            )

    obs_arrays = {pid: np.stack(values, axis=0) for pid, values in obs_by_point.items()}
    weight_arrays = {pid: np.asarray(values, dtype=np.float32) for pid, values in weights_by_point.items()}
    return obs_arrays, weight_arrays, meta_by_point


def write_csv(path: str | Path, rows: list[dict]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return path
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def run_leave_one_out(
    observations_by_point: dict[int, np.ndarray],
    weights_by_point: dict[int, np.ndarray],
    output_dir: str | Path,
) -> dict[str, Path | list[dict]]:
    output_dir = Path(output_dir)
    rows = leave_one_out_scores(observations_by_point, weights_by_point)
    summary_rows = summarize_scores(rows)
    by_view_rows = summarize_by_view_count(rows)

    score_path = write_csv(output_dir / "heldout_scores.csv", rows)
    summary_path = write_csv(output_dir / "summary.csv", summary_rows)
    by_view_path = write_csv(output_dir / "by_view_count.csv", by_view_rows)
    return {
        "rows": rows,
        "summary_rows": summary_rows,
        "by_view_rows": by_view_rows,
        "score_path": score_path,
        "summary_path": summary_path,
        "by_view_path": by_view_path,
    }
