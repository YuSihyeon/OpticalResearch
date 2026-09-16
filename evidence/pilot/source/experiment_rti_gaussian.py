from __future__ import annotations

import argparse
from pathlib import Path

import torch

from gaussian_pilot.datasets import create_smoke_rti_dataset, load_diligent_object
from gaussian_pilot.models import FixedRGBGaussianModel, LambertianGaussianModel, RTIGaussianModel
from gaussian_pilot.splats import mae, psnr
from gaussian_pilot.train import set_seed, split_lights, train_model
from gaussian_pilot.visualize import error_map, save_rti_panel, write_json, write_markdown_report


DILIGENT_HELP = """DiLiGenT single-view data was not found.

Manual download:
  https://sites.google.com/site/photometricstereodata/single

Expected folder example:
  data/DiLiGenT/pmsData/ball/
    mask.png
    light_directions.txt
    light_intensities.txt
    filenames.txt
    001.png ...
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="2D RTI-Gaussian pilot on DiLiGenT-style data.")
    parser.add_argument("--smoke", action="store_true", help="Run on a tiny generated fixture for pipeline checks.")
    parser.add_argument("--data", type=Path, default=Path("data/DiLiGenT/pmsData"))
    parser.add_argument("--object", default="ball")
    parser.add_argument("--output", type=Path, default=Path("outputs/rti_gaussian"))
    parser.add_argument("--max-size", type=int, default=72)
    parser.add_argument("--max-lights", type=int, default=16)
    parser.add_argument("--num-splats", type=int, default=64)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--lr", type=float, default=0.04)
    parser.add_argument("--holdout-every", type=int, default=4)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def _fit_model(model: torch.nn.Module, images: torch.Tensor, lights: torch.Tensor | None, mask: torch.Tensor, args):
    return train_model(model, images, lights=lights, mask=mask, iterations=args.iterations, lr=args.lr)


def _mask_image(image: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    return image * mask[..., None].to(image.device, dtype=image.dtype)


def main() -> int:
    args = parse_args()
    set_seed(args.seed)
    args.output.mkdir(parents=True, exist_ok=True)

    object_name = args.object
    data_root = args.data
    if args.smoke:
        data_root = create_smoke_rti_dataset(args.output / "_smoke_data", lights=max(args.max_lights, 8))
        object_name = "smoke"

    try:
        data = load_diligent_object(data_root, object_name, max_size=args.max_size, max_lights=args.max_lights)
    except FileNotFoundError as exc:
        raise SystemExit(f"{exc}\n\n{DILIGENT_HELP}") from exc

    images = data["images"].float()
    lights = torch.nn.functional.normalize(data["lights"].float(), dim=-1)
    mask = data["mask"].float()
    height, width = images.shape[1:3]
    train_idx, held_idx = split_lights(images.shape[0], holdout_every=args.holdout_every)
    if not held_idx:
        held_idx = [images.shape[0] - 1]
        train_idx = list(range(images.shape[0] - 1))

    train_images = images[train_idx]
    train_lights = lights[train_idx]
    held_images = images[held_idx]
    held_lights = lights[held_idx]

    fixed = FixedRGBGaussianModel(height, width, args.num_splats)
    lambertian = LambertianGaussianModel(height, width, args.num_splats)
    rti = RTIGaussianModel(height, width, args.num_splats)

    fixed_hist = _fit_model(fixed, train_images, None, mask, args)
    lambertian_hist = _fit_model(lambertian, train_images, train_lights, mask, args)
    rti_hist = _fit_model(rti, train_images, train_lights, mask, args)

    with torch.no_grad():
        fixed_pred = fixed()
        lambertian_pred = lambertian(held_lights[:1])[0]
        rti_pred = rti(held_lights[:1])[0]
        train_rti = rti(train_lights[:1])[0]
        held_target = held_images[0]
        train_target = train_images[0]

    metrics = {
        "dataset": "smoke" if args.smoke else "DiLiGenT single-view",
        "object": object_name,
        "resolution": [height, width],
        "num_splats": args.num_splats,
        "iterations": args.iterations,
        "train_indices": train_idx,
        "heldout_indices": held_idx,
        "fixed_heldout_mae": mae(fixed_pred, held_target, mask),
        "fixed_heldout_psnr": psnr(fixed_pred, held_target, mask),
        "lambertian_heldout_mae": mae(lambertian_pred, held_target, mask),
        "lambertian_heldout_psnr": psnr(lambertian_pred, held_target, mask),
        "rti_heldout_mae": mae(rti_pred, held_target, mask),
        "rti_heldout_psnr": psnr(rti_pred, held_target, mask),
    }

    save_rti_panel(
        args.output / "rti_panel.png",
        {
            "train_target": _mask_image(train_target, mask),
            "train_rti": _mask_image(train_rti, mask),
            "held_target": _mask_image(held_target, mask),
            "fixed_pred": _mask_image(fixed_pred, mask),
            "lambertian_pred": _mask_image(lambertian_pred, mask),
            "rti_pred": _mask_image(rti_pred, mask),
            "fixed_error": error_map(_mask_image(fixed_pred, mask), _mask_image(held_target, mask)),
            "rti_error": error_map(_mask_image(rti_pred, mask), _mask_image(held_target, mask)),
            "loss_curve": {
                "fixed": fixed_hist["loss"],
                "lambertian": lambertian_hist["loss"],
                "rti": rti_hist["loss"],
            },
        },
    )
    write_json(args.output / "metrics.json", metrics)
    write_markdown_report(
        args.output / "report.md",
        "RTI-Gaussian Pilot Report",
        {
            "Summary": (
                "This run compares fixed-color, Lambertian, and polynomial RTI 2D Gaussian "
                "attributes on train lights and held-out light reconstruction."
            ),
            "Metrics": (
                f"Fixed held-out MAE: {metrics['fixed_heldout_mae']:.4f}. "
                f"Lambertian held-out MAE: {metrics['lambertian_heldout_mae']:.4f}. "
                f"RTI held-out MAE: {metrics['rti_heldout_mae']:.4f}."
            ),
            "Limitations": (
                "This is a 2D image-plane pilot. It tests light-response attributes, "
                "not 3D visibility, camera projection, or full 3DGS rendering."
            ),
        },
    )
    print(f"Wrote RTI outputs to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
