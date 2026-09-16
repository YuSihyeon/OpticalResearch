from __future__ import annotations

import numpy as np


def bilinear_sample_chw(feature_map: np.ndarray, coords_xy: np.ndarray) -> np.ndarray:
    """Sample a CxHxW feature map at floating point x/y coordinates."""
    feature_map = np.asarray(feature_map)
    coords_xy = np.asarray(coords_xy, dtype=np.float32)
    if feature_map.ndim != 3:
        raise ValueError("feature_map must have shape CxHxW")
    if coords_xy.ndim != 2 or coords_xy.shape[1] != 2:
        raise ValueError("coords_xy must have shape Nx2")

    _, height, width = feature_map.shape
    x = np.clip(coords_xy[:, 0], 0.0, width - 1.0)
    y = np.clip(coords_xy[:, 1], 0.0, height - 1.0)

    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    x1 = np.clip(x0 + 1, 0, width - 1)
    y1 = np.clip(y0 + 1, 0, height - 1)

    wx = x - x0
    wy = y - y0

    f00 = feature_map[:, y0, x0].T
    f10 = feature_map[:, y0, x1].T
    f01 = feature_map[:, y1, x0].T
    f11 = feature_map[:, y1, x1].T

    top = f00 * (1.0 - wx[:, None]) + f10 * wx[:, None]
    bottom = f01 * (1.0 - wx[:, None]) + f11 * wx[:, None]
    return top * (1.0 - wy[:, None]) + bottom * wy[:, None]


def image_to_feature_coords(uv: np.ndarray, image_size: tuple[int, int], feature_size: tuple[int, int]) -> np.ndarray:
    """Map image pixel coordinates to feature map coordinates using align-corners math."""
    uv = np.asarray(uv, dtype=np.float32)
    image_w, image_h = image_size
    feature_w, feature_h = feature_size
    out = np.empty_like(uv, dtype=np.float32)
    out[:, 0] = uv[:, 0] * (feature_w - 1) / max(image_w - 1, 1)
    out[:, 1] = uv[:, 1] * (feature_h - 1) / max(image_h - 1, 1)
    return out


def l2_normalize(features: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    features = np.asarray(features, dtype=np.float32)
    return features / np.maximum(np.linalg.norm(features, axis=-1, keepdims=True), eps)
