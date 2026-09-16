from __future__ import annotations

import argparse
from pathlib import Path

import torch

from gaussian_pilot.datasets import create_smoke_rgb_nir_pair, find_epfl_pairs, load_rgb_nir_pair
from gaussian_pilot.models import FixedRGBGaussianModel, RGBNIRGaussianModel
from gaussian_pilot.splats import mae, psnr
from gaussian_pilot.train import set_seed, train_model
from gaussian_pilot.visualize import error_map, save_rgb_nir_panel, write_json, write_markdown_report


EPFL_HELP = """EPFL RGB-NIR data was not found.

Manual download:
  https://www.epfl.ch/labs/ivrl/research/downloads/rgb-nir-scene-dataset/

Expected folder examples:
  data/EPFL_RGB_NIR/.../sample_rgb.png
  data/EPFL_RGB_NIR/.../sample_nir.png

The loader pairs files whose names or parent folders contain RGB and NIR tokens.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="2D shared Gaussian RGB-NIR cue-check experiment.")
    parser.add_argument("--smoke", action="store_true", help="Run on a tiny generated fixture for pipeline checks.")
    parser.add_argument("--data", type=Path, default=Path("data/EPFL_RGB_NIR"))
    parser.add_argument("--pair-index", type=int, default=0)
    parser.add_argument("--output", type=Path, default=Path("outputs/rgb_nir_gaussian"))
    parser.add_argument("--max-size", type=int, default=96)
    parser.add_argument("--num-splats", type=int, default=64)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--lr", type=float, default=0.04)
    parser.add_argument("--seed", type=int, default=11)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    set_seed(args.seed)
    args.output.mkdir(parents=True, exist_ok=True)

    data_root = args.data
    if args.smoke:
        data_root = create_smoke_rgb_nir_pair(args.output / "_smoke_data")

    pairs = find_epfl_pairs(data_root) if data_root.exists() else []
    if not pairs:
        raise SystemExit(EPFL_HELP)
    pair = pairs[min(args.pair_index, len(pairs) - 1)]
    data = load_rgb_nir_pair(pair[0], pair[1], max_size=args.max_size)
    rgb = data["rgb"].float()
    nir = data["nir"].float()
    height, width = rgb.shape[:2]

    rgb_only = FixedRGBGaussianModel(height, width, args.num_splats)
    shared = RGBNIRGaussianModel(height, width, args.num_splats)

    rgb_hist = train_model(rgb_only, rgb.unsqueeze(0), iterations=args.iterations, lr=args.lr)
    shared_hist = train_model(
        shared,
        {"rgb": rgb, "nir": nir},
        iterations=args.iterations,
        lr=args.lr,
    )

    with torch.no_grad():
        rgb_only_pred = rgb_only()
        shared_pred = shared()
        rgb_recon = shared_pred["rgb"]
        nir_recon = shared_pred["nir"]
        difference = shared.reflectance_difference()

    metrics = {
        "dataset": "smoke" if args.smoke else "EPFL RGB-NIR",
        "rgb_path": data["rgb_path"],
        "nir_path": data["nir_path"],
        "resolution": [height, width],
        "num_splats": args.num_splats,
        "iterations": args.iterations,
        "rgb_only_mae": mae(rgb_only_pred, rgb),
        "rgb_only_psnr": psnr(rgb_only_pred, rgb),
        "shared_rgb_mae": mae(rgb_recon, rgb),
        "shared_rgb_psnr": psnr(rgb_recon, rgb),
        "shared_nir_mae": mae(nir_recon[..., None], nir[..., None]),
    }

    save_rgb_nir_panel(
        args.output / "rgb_nir_panel.png",
        {
            "rgb_target": rgb,
            "rgb_recon": rgb_recon,
            "nir_target": nir,
            "nir_recon": nir_recon,
            "rgb_error": error_map(rgb_only_pred, rgb),
            "shared_error": error_map(rgb_recon, rgb),
            "difference": difference,
        },
    )
    write_json(
        args.output / "metrics.json",
        {**metrics, "loss_rgb_only": rgb_hist["loss"], "loss_shared": shared_hist["loss"]},
    )
    write_markdown_report(
        args.output / "report.md",
        "RGB-NIR Gaussian Cue Check Report",
        {
            "Summary": (
                "This run shares 2D Gaussian geometry between RGB and NIR branches and "
                "visualizes where learned RGB and NIR reflectance disagree."
            ),
            "Metrics": (
                f"RGB-only MAE: {metrics['rgb_only_mae']:.4f}. "
                f"Shared RGB MAE: {metrics['shared_rgb_mae']:.4f}. "
                f"Shared NIR MAE: {metrics['shared_nir_mae']:.4f}."
            ),
            "Interpretation": (
                "Bright regions in the RGB/NIR difference heatmap are candidate material cues. "
                "They do not prove relighting, but they can guide material priors in a full inverse-rendering system."
            ),
        },
    )
    print(f"Wrote RGB-NIR outputs to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
