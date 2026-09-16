from __future__ import annotations

import math

import torch
from torch import nn
import torch.nn.functional as F

from gaussian_pilot.splats import (
    gaussian_weights,
    light_basis,
    make_pixel_grid,
    normalized_splat,
)


def _initial_positions(num_splats: int) -> torch.Tensor:
    side = math.ceil(math.sqrt(num_splats))
    coords = torch.linspace(-0.85, 0.85, side)
    yy, xx = torch.meshgrid(coords, coords, indexing="ij")
    positions = torch.stack([xx.flatten(), yy.flatten()], dim=-1)
    return positions[:num_splats].contiguous()


class GaussianGeometryModel(nn.Module):
    def __init__(self, height: int, width: int, num_splats: int):
        super().__init__()
        self.height = height
        self.width = width
        self.num_splats = num_splats
        self.positions = nn.Parameter(_initial_positions(num_splats))
        init_scale = max(0.12, 1.8 / math.sqrt(num_splats))
        self.log_scales = nn.Parameter(torch.full((num_splats, 2), math.log(init_scale)))
        self.opacity_logits = nn.Parameter(torch.full((num_splats,), 2.0))

    def weights(self) -> torch.Tensor:
        grid = make_pixel_grid(self.height, self.width, self.positions.device)
        return gaussian_weights(grid, self.positions, self.log_scales, self.opacity_logits)

    def splat(self, values: torch.Tensor) -> torch.Tensor:
        return normalized_splat(self.weights(), values)


class FixedRGBGaussianModel(GaussianGeometryModel):
    def __init__(self, height: int, width: int, num_splats: int):
        super().__init__(height, width, num_splats)
        self.color_logits = nn.Parameter(torch.zeros(num_splats, 3))

    def forward(self) -> torch.Tensor:
        colors = torch.sigmoid(self.color_logits)
        return self.splat(colors)


class LambertianGaussianModel(GaussianGeometryModel):
    def __init__(self, height: int, width: int, num_splats: int):
        super().__init__(height, width, num_splats)
        self.albedo_logits = nn.Parameter(torch.zeros(num_splats, 3))
        self.normal_raw = nn.Parameter(torch.tensor([[0.0, 0.0, 1.0]]).repeat(num_splats, 1))
        self.ambient_logits = nn.Parameter(torch.full((num_splats, 1), -2.0))

    def forward(self, lights: torch.Tensor) -> torch.Tensor:
        lights = F.normalize(lights.to(self.positions.device, dtype=torch.float32), dim=-1)
        normals = F.normalize(self.normal_raw, dim=-1)
        albedo = torch.sigmoid(self.albedo_logits)
        ambient = F.softplus(self.ambient_logits)
        diffuse = torch.clamp(lights @ normals.T, min=0.0).T
        values = albedo[:, None, :] * (ambient[:, None, :] + diffuse[:, :, None])
        return torch.stack([self.splat(values[:, light_idx, :]) for light_idx in range(lights.shape[0])], dim=0)


class RTIGaussianModel(GaussianGeometryModel):
    def __init__(self, height: int, width: int, num_splats: int):
        super().__init__(height, width, num_splats)
        self.coefficients = nn.Parameter(torch.zeros(num_splats, 7, 3))
        with torch.no_grad():
            self.coefficients[:, 0, :] = -0.7

    def forward(self, lights: torch.Tensor) -> torch.Tensor:
        basis = light_basis(lights.to(self.positions.device)).to(self.positions.device)
        raw_values = torch.einsum("lb,nbc->lnc", basis, self.coefficients)
        values = F.softplus(raw_values)
        return torch.stack([self.splat(values[light_idx]) for light_idx in range(lights.shape[0])], dim=0)


class RGBNIRGaussianModel(GaussianGeometryModel):
    def __init__(self, height: int, width: int, num_splats: int):
        super().__init__(height, width, num_splats)
        self.rgb_logits = nn.Parameter(torch.zeros(num_splats, 3))
        self.nir_logits = nn.Parameter(torch.zeros(num_splats, 1))

    def forward(self) -> dict[str, torch.Tensor]:
        rgb = self.splat(torch.sigmoid(self.rgb_logits))
        nir = self.splat(torch.sigmoid(self.nir_logits))[..., 0]
        return {"rgb": rgb, "nir": nir}

    def reflectance_difference(self) -> torch.Tensor:
        rgb_gray = torch.sigmoid(self.rgb_logits).mean(dim=-1, keepdim=True)
        diff = torch.abs(torch.sigmoid(self.nir_logits) - rgb_gray)
        return self.splat(diff)[..., 0]
