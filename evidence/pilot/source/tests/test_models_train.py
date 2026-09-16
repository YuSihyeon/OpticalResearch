import torch

from gaussian_pilot.models import FixedRGBGaussianModel, RTIGaussianModel
from gaussian_pilot.train import split_lights, train_model


def test_split_lights_is_deterministic_and_keeps_holdouts():
    train, held = split_lights(10, holdout_every=3)
    assert held == [2, 5, 8]
    assert train == [0, 1, 3, 4, 6, 7, 9]


def test_fixed_rgb_training_reduces_loss_on_constant_image():
    target = torch.full((1, 8, 8, 3), 0.35)
    model = FixedRGBGaussianModel(height=8, width=8, num_splats=4)
    history = train_model(model, target, iterations=25, lr=0.05)
    assert history["loss"][0] > history["loss"][-1]
    pred = model()
    assert pred.shape == (8, 8, 3)


def test_rti_model_accepts_light_batch():
    lights = torch.tensor([[0.0, 0.0, 1.0], [1.0, 0.0, 0.0]])
    model = RTIGaussianModel(height=6, width=7, num_splats=3)
    pred = model(lights)
    assert pred.shape == (2, 6, 7, 3)
