from __future__ import annotations

import json
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from view_to_gaussian_poc.src.evaluate import load_feature_npz, run_leave_one_out, sample_observation_features, write_csv
from view_to_gaussian_poc.src.geometry import load_blender_cameras
from view_to_gaussian_poc.src.nerf_synthetic import (
    download_lego_subset,
    load_masks,
    prepare_pseudo_rgb,
    read_ply_xyz,
)
from view_to_gaussian_poc.src.plots import (
    plot_by_view_count,
    plot_cosine_hist,
    plot_point_visualizations,
    plot_summary,
)
from view_to_gaussian_poc.src.resnet18_features import ensure_resnet18_weights, extract_features
from view_to_gaussian_poc.src.tracks import build_projected_observations, select_points_by_track_length


DEFAULT_CONFIG = {
    "scene": "nerf_synthetic_lego",
    "max_images": 36,
    "image_size": 256,
    "resnet_layer": "layer3",
    "feature_batch_size": 6,
    "max_cloud_points": 50000,
    "max_eval_points": 1800,
    "min_views": 4,
    "alpha_threshold": 0.2,
    "z_tolerance": 0.08,
    "seed": 7,
}


def run(config: dict) -> dict:
    start_time = time.time()
    output_root = ROOT / "outputs" / "lego_fallback"
    output_root.mkdir(parents=True, exist_ok=True)
    (ROOT / "configs").mkdir(parents=True, exist_ok=True)
    with (ROOT / "configs" / "lego_fallback.json").open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    data_info = download_lego_subset(ROOT, max_images=int(config["max_images"]))
    processed_info = prepare_pseudo_rgb(
        data_info["train_dir"],
        ROOT / "data" / "processed" / "lego",
        data_info["image_names"],
        image_size=int(config["image_size"]),
    )
    image_names = list(data_info["image_names"])
    image_dir = Path(processed_info["image_dir"])
    mask_dir = Path(processed_info["mask_dir"])
    image_paths = [image_dir / name for name in image_names]

    weights_path = ensure_resnet18_weights(ROOT / "data" / "weights" / "resnet18-f37072fd.pth")
    feature_path = ROOT / "outputs" / "lego_fallback" / "resnet18_features.npz"
    extract_features(
        image_paths,
        feature_path,
        weights_path=weights_path,
        image_size=int(config["image_size"]),
        batch_size=int(config["feature_batch_size"]),
        output_layer=str(config["resnet_layer"]),
    )

    cameras = load_blender_cameras(
        data_info["transforms_path"],
        width=int(config["image_size"]),
        height=int(config["image_size"]),
        image_names=set(image_names),
    )
    points = read_ply_xyz(data_info["ply_path"], max_points=int(config["max_cloud_points"]), seed=int(config["seed"]))
    masks = load_masks(mask_dir, image_names)
    observations = build_projected_observations(
        points,
        cameras,
        masks,
        alpha_threshold=float(config["alpha_threshold"]),
        z_tolerance=float(config["z_tolerance"]),
    )
    selected_points = select_points_by_track_length(
        observations,
        min_views=int(config["min_views"]),
        max_points=int(config["max_eval_points"]),
        seed=int(config["seed"]),
    )
    observations = observations.subset_points(selected_points)

    obs_table_path = output_root / "projected_observations.npz"
    np.savez_compressed(
        obs_table_path,
        point_indices=observations.point_indices,
        view_indices=observations.view_indices,
        uv=observations.uv,
        depth=observations.depth,
        weights=observations.weights,
        selected_points=selected_points,
    )

    feature_maps, image_size = load_feature_npz(feature_path)
    observations_by_point, weights_by_point, meta_by_point = sample_observation_features(
        observations,
        feature_maps,
        image_names,
        image_size=image_size,
        normalize=True,
    )
    eval_result = run_leave_one_out(observations_by_point, weights_by_point, output_root)

    meta_rows = [item for values in meta_by_point.values() for item in values]
    write_csv(output_root / "projected_correspondences.csv", meta_rows)

    plot_summary(eval_result["summary_rows"], output_root / "summary_bar.png")
    plot_by_view_count(eval_result["by_view_rows"], output_root / "by_view_count.png")
    plot_cosine_hist(eval_result["rows"], output_root / "cosine_hist.png")
    point_figs = plot_point_visualizations(
        meta_by_point,
        observations_by_point,
        weights_by_point,
        image_dir,
        output_root / "point_visualizations",
        max_points=5,
        seed=int(config["seed"]),
    )

    summary = {
        "scene": config["scene"],
        "fallback_reason": "HS-NeRF raw HSI download link was not accessible from the official page/search/API checks; using NeRF Synthetic Lego for geometric validation only.",
        "num_images": len(image_names),
        "num_loaded_points": int(len(points)),
        "num_selected_points": int(len(selected_points)),
        "num_observations": int(len(observations.point_indices)),
        "num_leave_one_out_rows": int(len(eval_result["rows"])),
        "feature_path": str(feature_path),
        "observation_path": str(obs_table_path),
        "score_path": str(eval_result["score_path"]),
        "summary_path": str(eval_result["summary_path"]),
        "by_view_path": str(eval_result["by_view_path"]),
        "point_visualizations": [str(path) for path in point_figs],
        "elapsed_sec": time.time() - start_time,
    }
    with (output_root / "run_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary


if __name__ == "__main__":
    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    config = dict(DEFAULT_CONFIG)
    if config_path is not None:
        with config_path.open("r", encoding="utf-8") as f:
            config.update(json.load(f))
    result = run(config)
    print(json.dumps(result, indent=2))
