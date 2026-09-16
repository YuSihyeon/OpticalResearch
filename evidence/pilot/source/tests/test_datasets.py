from pathlib import Path
import shutil

import numpy as np
from PIL import Image

from gaussian_pilot.datasets import (
    create_smoke_rgb_nir_pair,
    create_smoke_rti_dataset,
    find_epfl_pairs,
    load_diligent_object,
    load_rgb_nir_pair,
)


def test_smoke_rti_dataset_loads(tmp_path: Path):
    root = create_smoke_rti_dataset(tmp_path)
    data = load_diligent_object(root, "smoke", max_size=24, max_lights=6)
    assert data["images"].shape[0] == 6
    assert data["images"].shape[-1] == 3
    assert data["lights"].shape == (6, 3)
    assert data["mask"].shape == data["images"].shape[1:3]


def test_diligent_png_suffix_alias_loads(tmp_path: Path):
    root = create_smoke_rti_dataset(tmp_path)
    shutil.move(root / "smoke", root / "ballPNG")
    data = load_diligent_object(root, "ball", max_size=24, max_lights=3)
    assert data["object"] == "ball"
    assert data["images"].shape[0] == 3


def test_smoke_rgb_nir_pair_discovery_and_load(tmp_path: Path):
    root = create_smoke_rgb_nir_pair(tmp_path)
    pairs = find_epfl_pairs(root)
    assert len(pairs) == 1
    data = load_rgb_nir_pair(pairs[0][0], pairs[0][1], max_size=24)
    assert data["rgb"].shape[-1] == 3
    assert data["nir"].ndim == 2


def test_epfl_browser_side_by_side_panel_loads(tmp_path: Path):
    jpg1 = tmp_path / "nirscene0" / "jpg1"
    jpg1.mkdir(parents=True)
    rgb = np.zeros((16, 20, 3), dtype=np.uint8)
    rgb[..., 0] = 180
    nir = np.zeros((16, 20, 3), dtype=np.uint8)
    nir[..., :] = 90
    panel = np.concatenate([rgb, np.zeros((16, 2, 3), dtype=np.uint8), nir], axis=1)
    Image.fromarray(panel).save(jpg1 / "country_0000.jpg")

    pairs = find_epfl_pairs(tmp_path)
    assert pairs == [(jpg1 / "country_0000.jpg", jpg1 / "country_0000.jpg")]
    data = load_rgb_nir_pair(pairs[0][0], pairs[0][1], max_size=32)
    assert data["rgb"].shape[:2] == data["nir"].shape
    assert data["rgb"][..., 0].mean() > data["nir"].mean()
