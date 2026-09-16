from __future__ import annotations

import math

import torch
import torch.nn.functional as F


def light_basis(lights: torch.Tensor) -> torch.Tensor:
    lights = torch.as_tensor(lights, dtype=torch.float32)
    lx, ly, lz = lights[..., 0], lights[..., 1], lights[..., 2]
    return torch.stack(
        [torch.ones_like(lx), lx, ly, lz, lx * lx, ly * ly, lx * ly],
        dim=-1,
    )


def make_pixel_grid(
    height: int,
    width: int,
    device: torch.device | str = "cpu",
) -> torch.Tensor:
    ys = torch.linspace(-1.0, 1.0, height, device=device)
    xs = torch.linspace(-1.0, 1.0, width, device=device)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    return torch.stack([xx, yy], dim=-1)


def gaussian_weights(
    grid: torch.Tensor,
    positions: torch.Tensor,
    log_scales: torch.Tensor,
    opacity_logits: torch.Tensor,
) -> torch.Tensor:
    positions = positions.to(grid.device)
    log_scales = log_scales.to(grid.device)
    opacity_logits = opacity_logits.to(grid.device)
    scales = F.softplus(log_scales).clamp_min(1e-3)
    diff = grid.unsqueeze(0) - positions[:, None, None, :]
    exponent = -0.5 * ((diff / scales[:, None, None, :]) ** 2).sum(dim=-1)
    opacity = torch.sigmoid(opacity_logits)[:, None, None]
    return opacity * torch.exp(exponent)


def normalized_splat(
    weights: torch.Tensor,
    values: torch.Tensor,
    eps: float = 1e-6,
) -> torch.Tensor:
    numerator = torch.einsum("nhw,nc->hwc", weights, values)
    denominator = weights.sum(dim=0).unsqueeze(-1).clamp_min(eps)
    return numerator / denominator


def masked_mse(
    pred: torch.Tensor,
    target: torch.Tensor,
    mask: torch.Tensor | None = None,
) -> torch.Tensor:
    if mask is None:
        return torch.mean((pred - target) ** 2)
    if mask.ndim == 2:
        mask = mask[..., None]
    mask = mask.to(dtype=pred.dtype, device=pred.device)
    return (((pred - target) ** 2) * mask).sum() / mask.sum().clamp_min(1.0)


def _masked_values(
    pred: torch.Tensor,
    target: torch.Tensor,
    mask: torch.Tensor | None,
) -> tuple[torch.Tensor, torch.Tensor]:
    if mask is None:
        return pred, target
    if mask.ndim == 2:
        mask = mask[..., None]
    mask = mask.to(dtype=torch.bool, device=pred.device)
    expanded = mask.expand_as(pred)
    return pred[expanded], target[expanded]


def mae(
    pred: torch.Tensor,
    target: torch.Tensor,
    mask: torch.Tensor | None = None,
) -> float:
    pred_v, target_v = _masked_values(pred, target, mask)
    return torch.mean(torch.abs(pred_v - target_v)).detach().cpu().item()


def psnr(
    pred: torch.Tensor,
    target: torch.Tensor,
    mask: torch.Tensor | None = None,
) -> float:
    pred_v, target_v = _masked_values(pred, target, mask)
    mse = torch.mean((pred_v - target_v) ** 2).detach().cpu().item()
    if mse <= 1e-12:
        return 99.0
    return 20.0 * math.log10(1.0 / math.sqrt(mse))
