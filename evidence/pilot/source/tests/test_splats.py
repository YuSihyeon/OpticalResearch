import torch

from gaussian_pilot.splats import (
    gaussian_weights,
    light_basis,
    make_pixel_grid,
    normalized_splat,
    psnr,
)


def test_light_basis_matches_rti_polynomial_terms():
    lights = torch.tensor([[1.0, 2.0, 3.0], [-0.5, 0.25, 1.0]])
    basis = light_basis(lights)
    expected = torch.tensor(
        [
            [1.0, 1.0, 2.0, 3.0, 1.0, 4.0, 2.0],
            [1.0, -0.5, 0.25, 1.0, 0.25, 0.0625, -0.125],
        ]
    )
    assert torch.allclose(basis, expected)


def test_gaussian_weights_shape_and_center_dominance():
    grid = make_pixel_grid(5, 5, "cpu")
    positions = torch.tensor([[0.0, 0.0]])
    log_scales = torch.log(torch.tensor([[0.25, 0.25]]))
    opacity_logits = torch.tensor([4.0])
    weights = gaussian_weights(grid, positions, log_scales, opacity_logits)
    assert weights.shape == (1, 5, 5)
    assert weights[0, 2, 2] > weights[0, 0, 0]


def test_normalized_splat_preserves_constant_value():
    grid = make_pixel_grid(4, 4, "cpu")
    positions = torch.tensor([[0.0, 0.0], [0.25, -0.25]])
    log_scales = torch.log(torch.full((2, 2), 0.5))
    opacity_logits = torch.ones(2)
    weights = gaussian_weights(grid, positions, log_scales, opacity_logits)
    values = torch.tensor([[0.2, 0.4, 0.6], [0.2, 0.4, 0.6]])
    image = normalized_splat(weights, values)
    assert image.shape == (4, 4, 3)
    assert torch.allclose(image[1, 1], torch.tensor([0.2, 0.4, 0.6]), atol=1e-5)


def test_psnr_is_high_for_identical_images():
    image = torch.full((4, 4, 3), 0.5)
    assert psnr(image, image) > 80.0
