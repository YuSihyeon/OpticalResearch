from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class Camera:
    width: int
    height: int
    focal: float
    c2w: np.ndarray
    image_name: str = ""

    @property
    def cx(self) -> float:
        return self.width * 0.5

    @property
    def cy(self) -> float:
        return self.height * 0.5

    @property
    def w2c(self) -> np.ndarray:
        return np.linalg.inv(self.c2w)

    @property
    def center(self) -> np.ndarray:
        return self.c2w[:3, 3]


def focal_from_camera_angle(width: int, camera_angle_x: float) -> float:
    return 0.5 * width / np.tan(0.5 * camera_angle_x)


def load_blender_cameras(
    transforms_path: str | Path,
    width: int,
    height: int,
    image_names: set[str] | None = None,
    scale: float = 1.0,
) -> list[Camera]:
    transforms_path = Path(transforms_path)
    with transforms_path.open("r", encoding="utf-8") as f:
        meta = json.load(f)

    focal = focal_from_camera_angle(width, float(meta["camera_angle_x"])) * scale
    cameras: list[Camera] = []
    for frame in meta["frames"]:
        raw_name = Path(frame["file_path"]).name
        image_name = f"{raw_name}.png"
        if image_names is not None and image_name not in image_names:
            continue
        c2w = np.asarray(frame["transform_matrix"], dtype=np.float64)
        cameras.append(
            Camera(
                width=width,
                height=height,
                focal=focal,
                c2w=c2w,
                image_name=image_name,
            )
        )
    return cameras


def project_points(points: np.ndarray, camera: Camera) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Project world-space points into a NeRF/Blender OpenGL-style camera.

    Blender NeRF transforms use camera-to-world matrices where the camera looks
    along -Z, x points right, and y points up. Returned depth is positive in
    front of the camera.
    """
    points = np.asarray(points, dtype=np.float64)
    ones = np.ones((points.shape[0], 1), dtype=np.float64)
    hom = np.concatenate([points, ones], axis=1)
    cam = (camera.w2c @ hom.T).T[:, :3]

    depth = -cam[:, 2]
    eps = 1e-8
    uv = np.empty((points.shape[0], 2), dtype=np.float64)
    uv[:, 0] = camera.focal * (cam[:, 0] / np.maximum(depth, eps)) + camera.cx
    uv[:, 1] = camera.focal * (-cam[:, 1] / np.maximum(depth, eps)) + camera.cy

    valid = (
        (depth > eps)
        & (uv[:, 0] >= 0.0)
        & (uv[:, 0] <= camera.width - 1)
        & (uv[:, 1] >= 0.0)
        & (uv[:, 1] <= camera.height - 1)
    )
    return uv, depth, valid


def estimate_radial_view_weights(points: np.ndarray, cameras: list[Camera], point_indices: np.ndarray, view_indices: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float64)
    weights = np.ones(point_indices.shape[0], dtype=np.float32)
    for k, (point_idx, view_idx) in enumerate(zip(point_indices, view_indices)):
        point = points[int(point_idx)]
        normal = point / (np.linalg.norm(point) + 1e-8)
        view_dir = cameras[int(view_idx)].center - point
        view_dir = view_dir / (np.linalg.norm(view_dir) + 1e-8)
        weights[k] = float(np.clip(np.dot(normal, view_dir), 0.05, 1.0))
    return weights
