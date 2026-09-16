from __future__ import annotations

import random

import numpy as np
import torch

from gaussian_pilot.splats import masked_mse


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def split_lights(num_lights: int, holdout_every: int = 4) -> tuple[list[int], list[int]]:
    held = [idx for idx in range(num_lights) if (idx + 1) % holdout_every == 0]
    train = [idx for idx in range(num_lights) if idx not in held]
    if not held and num_lights > 1:
        held = [num_lights - 1]
        train = list(range(num_lights - 1))
    return train, held


def train_model(
    model: torch.nn.Module,
    targets: torch.Tensor | dict[str, torch.Tensor],
    lights: torch.Tensor | None = None,
    mask: torch.Tensor | None = None,
    iterations: int = 100,
    lr: float = 0.03,
) -> dict[str, list[float]]:
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    device = next(model.parameters()).device
    if isinstance(targets, dict):
        targets = {key: value.to(device, dtype=torch.float32) for key, value in targets.items()}
    else:
        targets = targets.to(device, dtype=torch.float32)
    if mask is not None:
        mask = mask.to(device)
    if lights is not None:
        lights = lights.to(device, dtype=torch.float32)

    history: dict[str, list[float]] = {"loss": []}
    for _ in range(iterations):
        optimizer.zero_grad()
        pred = model(lights) if lights is not None else model()
        if isinstance(pred, dict):
            loss = masked_mse(pred["rgb"], targets["rgb"], mask) + masked_mse(
                pred["nir"][..., None],
                targets["nir"][..., None],
                mask,
            )
        else:
            if pred.ndim == 3 and targets.ndim == 4:
                pred_for_loss = pred.unsqueeze(0).expand_as(targets)
            else:
                pred_for_loss = pred
            loss = masked_mse(pred_for_loss, targets, mask)
        loss.backward()
        optimizer.step()
        history["loss"].append(float(loss.detach().cpu().item()))
    return history
