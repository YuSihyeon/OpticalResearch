from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .geometry import Camera, estimate_radial_view_weights, project_points


@dataclass
class ObservationTable:
    point_indices: np.ndarray
    view_indices: np.ndarray
    uv: np.ndarray
    depth: np.ndarray
    weights: np.ndarray

    def subset_points(self, keep_point_ids: np.ndarray) -> "ObservationTable":
        keep = np.isin(self.point_indices, keep_point_ids)
        return ObservationTable(
            point_indices=self.point_indices[keep],
            view_indices=self.view_indices[keep],
            uv=self.uv[keep],
            depth=self.depth[keep],
            weights=self.weights[keep],
        )


def build_projected_observations(
    points: np.ndarray,
    cameras: list[Camera],
    masks: dict[str, np.ndarray],
    alpha_threshold: float = 0.2,
    z_tolerance: float = 0.08,
) -> ObservationTable:
    point_chunks: list[np.ndarray] = []
    view_chunks: list[np.ndarray] = []
    uv_chunks: list[np.ndarray] = []
    depth_chunks: list[np.ndarray] = []

    for view_idx, camera in enumerate(cameras):
        uv, depth, valid = project_points(points, camera)
        if camera.image_name in masks:
            mask = masks[camera.image_name]
            x = np.rint(uv[:, 0]).astype(np.int64)
            y = np.rint(uv[:, 1]).astype(np.int64)
            in_mask = valid.copy()
            valid_ids = np.where(valid)[0]
            x_valid = np.clip(x[valid_ids], 0, camera.width - 1)
            y_valid = np.clip(y[valid_ids], 0, camera.height - 1)
            alpha = mask[y_valid, x_valid]
            in_mask[valid_ids] = alpha >= alpha_threshold
            valid = in_mask

        ids = np.where(valid)[0]
        if len(ids) == 0:
            continue

        xi = np.rint(uv[ids, 0]).astype(np.int64)
        yi = np.rint(uv[ids, 1]).astype(np.int64)
        zbuf = np.full((camera.height, camera.width), np.inf, dtype=np.float32)
        np.minimum.at(zbuf, (yi, xi), depth[ids].astype(np.float32))
        visible = depth[ids] <= zbuf[yi, xi] + z_tolerance
        ids = ids[visible]
        if len(ids) == 0:
            continue

        point_chunks.append(ids.astype(np.int64))
        view_chunks.append(np.full(len(ids), view_idx, dtype=np.int64))
        uv_chunks.append(uv[ids].astype(np.float32))
        depth_chunks.append(depth[ids].astype(np.float32))

    if not point_chunks:
        empty_i = np.empty((0,), dtype=np.int64)
        empty_f = np.empty((0,), dtype=np.float32)
        return ObservationTable(empty_i, empty_i, np.empty((0, 2), dtype=np.float32), empty_f, empty_f)

    point_indices = np.concatenate(point_chunks)
    view_indices = np.concatenate(view_chunks)
    weights = estimate_radial_view_weights(points, cameras, point_indices, view_indices)
    return ObservationTable(
        point_indices=point_indices,
        view_indices=view_indices,
        uv=np.concatenate(uv_chunks),
        depth=np.concatenate(depth_chunks),
        weights=weights,
    )


def select_points_by_track_length(
    observations: ObservationTable,
    min_views: int,
    max_points: int,
    seed: int = 7,
) -> np.ndarray:
    point_ids, counts = np.unique(observations.point_indices, return_counts=True)
    eligible = point_ids[counts >= min_views]
    if len(eligible) > max_points:
        rng = np.random.default_rng(seed)
        eligible = rng.choice(eligible, size=max_points, replace=False)
    return np.sort(eligible.astype(np.int64))
