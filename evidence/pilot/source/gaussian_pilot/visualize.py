from __future__ import annotations

from pathlib import Path
import json
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import torch


def to_numpy(value: Any) -> np.ndarray:
    if isinstance(value, torch.Tensor):
        value = value.detach().cpu().numpy()
    return np.asarray(value)


def image01(value: Any) -> np.ndarray:
    array = to_numpy(value).astype(np.float32)
    return np.clip(array, 0.0, 1.0)


def error_map(pred: Any, target: Any) -> np.ndarray:
    pred_arr = image01(pred)
    target_arr = image01(target)
    diff = np.abs(pred_arr - target_arr)
    if diff.ndim == 3:
        diff = diff.mean(axis=-1)
    return diff


def _show_image(ax: plt.Axes, title: str, value: Any, cmap: str | None = None) -> None:
    array = image01(value)
    ax.imshow(array, cmap=cmap, vmin=0.0, vmax=1.0)
    ax.set_title(title, fontsize=9)
    ax.axis("off")


def _save_panel(output_path: Path, rows: list[tuple[str, Any, str | None]], cols: int) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    nrows = int(np.ceil(len(rows) / cols))
    fig, axes = plt.subplots(nrows, cols, figsize=(3.0 * cols, 2.8 * nrows), squeeze=False)
    for ax in axes.ravel():
        ax.axis("off")
    for ax, (title, value, cmap) in zip(axes.ravel(), rows):
        _show_image(ax, title, value, cmap)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def save_rti_panel(output_path: Path, payload: dict[str, Any]) -> None:
    rows = [
        ("Train target", payload["train_target"], None),
        ("Train RTI", payload["train_rti"], None),
        ("Held target", payload["held_target"], None),
        ("Fixed RGB", payload["fixed_pred"], None),
        ("Lambertian", payload["lambertian_pred"], None),
        ("RTI-Gaussian", payload["rti_pred"], None),
        ("Fixed error", payload["fixed_error"], "magma"),
        ("RTI error", payload["rti_error"], "magma"),
    ]
    _save_panel(output_path, rows, cols=4)

    loss_curve = payload.get("loss_curve")
    if loss_curve is not None:
        loss_path = Path(output_path).with_name("loss_curve.png")
        fig, ax = plt.subplots(figsize=(5, 3))
        for label, values in loss_curve.items():
            ax.plot(values, label=label)
        ax.set_xlabel("Iteration")
        ax.set_ylabel("MSE")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(loss_path, dpi=150)
        plt.close(fig)


def save_rgb_nir_panel(output_path: Path, payload: dict[str, Any]) -> None:
    rows = [
        ("RGB target", payload["rgb_target"], None),
        ("RGB recon", payload["rgb_recon"], None),
        ("NIR target", payload["nir_target"], "gray"),
        ("NIR recon", payload["nir_recon"], "gray"),
        ("RGB-only error", payload["rgb_error"], "magma"),
        ("RGB+NIR error", payload["shared_error"], "magma"),
        ("RGB/NIR diff", payload["difference"], "viridis"),
    ]
    _save_panel(output_path, rows, cols=4)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    def default(value: Any) -> Any:
        if isinstance(value, torch.Tensor):
            return value.detach().cpu().tolist()
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.floating):
            return float(value)
        if isinstance(value, np.integer):
            return int(value)
        raise TypeError(f"Cannot serialize {type(value)!r}")

    path.write_text(json.dumps(data, indent=2, default=default), encoding="utf-8")


def write_markdown_report(path: Path, title: str, sections: dict[str, str]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", ""]
    for heading, body in sections.items():
        lines.extend([f"## {heading}", "", body.strip(), ""])
    path.write_text("\n".join(lines), encoding="utf-8")
