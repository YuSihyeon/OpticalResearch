from __future__ import annotations

from pathlib import Path
import re

import numpy as np
from PIL import Image
import torch


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def _write_image(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(array, 0.0, 1.0)
    Image.fromarray((clipped * 255.0).astype(np.uint8)).save(path)


def _read_image(path: Path, mode: str = "RGB") -> np.ndarray:
    with Image.open(path) as image:
        if mode:
            image = image.convert(mode)
        return np.asarray(image).astype(np.float32) / 255.0


def _resize_array(array: np.ndarray, max_size: int, nearest: bool = False) -> np.ndarray:
    height, width = array.shape[:2]
    scale = min(1.0, float(max_size) / float(max(height, width)))
    if scale >= 1.0:
        return array
    new_size = (max(1, int(round(width * scale))), max(1, int(round(height * scale))))
    mode = "L" if array.ndim == 2 else "RGB"
    pil = Image.fromarray((np.clip(array, 0.0, 1.0) * 255.0).astype(np.uint8), mode=mode)
    resample = Image.Resampling.NEAREST if nearest else Image.Resampling.BILINEAR
    return np.asarray(pil.resize(new_size, resample=resample)).astype(np.float32) / 255.0


def _normalize_light_table(table: np.ndarray) -> np.ndarray:
    table = np.asarray(table, dtype=np.float32)
    if table.ndim == 1:
        table = table.reshape(1, -1)
    if table.shape[0] == 3 and table.shape[1] != 3:
        table = table.T
    return table[:, :3]


def _object_dir(root: Path, object_name: str) -> Path:
    root = Path(root)
    names = [object_name]
    if not object_name.lower().endswith("png"):
        names.append(f"{object_name}PNG")
    candidates = [
        base / name
        for base in (root, root / "pmsData", root / "DiLiGenT" / "pmsData")
        for name in names
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"Could not find DiLiGenT object '{object_name}' under {root}. "
        "Expected a folder like data/DiLiGenT/pmsData/ball with mask.png, "
        "light_directions.txt, light_intensities.txt, filenames.txt, and images."
    )


def create_smoke_rti_dataset(
    root: Path,
    height: int = 32,
    width: int = 32,
    lights: int = 8,
) -> Path:
    root = Path(root)
    object_dir = root / "smoke"
    object_dir.mkdir(parents=True, exist_ok=True)
    yy, xx = np.meshgrid(
        np.linspace(-1.0, 1.0, height, dtype=np.float32),
        np.linspace(-1.0, 1.0, width, dtype=np.float32),
        indexing="ij",
    )
    radius2 = xx * xx + yy * yy
    mask = radius2 <= 0.85**2
    zz = np.sqrt(np.clip(1.0 - radius2, 0.0, 1.0))
    normals = np.stack([xx, yy, zz], axis=-1)
    normals /= np.linalg.norm(normals, axis=-1, keepdims=True).clip(1e-6)
    albedo = np.stack(
        [
            0.45 + 0.25 * (xx > 0),
            0.35 + 0.25 * (yy < 0),
            0.30 + 0.25 * (xx * yy > 0),
        ],
        axis=-1,
    ).astype(np.float32)
    angles = np.linspace(0.0, 2.0 * np.pi, lights, endpoint=False, dtype=np.float32)
    light_dirs = np.stack(
        [0.55 * np.cos(angles), 0.55 * np.sin(angles), np.full_like(angles, 0.75)],
        axis=-1,
    )
    light_dirs /= np.linalg.norm(light_dirs, axis=-1, keepdims=True)
    filenames = []
    for idx, light in enumerate(light_dirs, start=1):
        shading = np.clip((normals * light).sum(axis=-1), 0.0, 1.0)
        image = albedo * (0.08 + 0.92 * shading[..., None])
        image *= mask[..., None]
        filename = f"{idx:03d}.png"
        _write_image(object_dir / filename, image)
        filenames.append(filename)
    _write_image(object_dir / "mask.png", mask.astype(np.float32))
    np.savetxt(object_dir / "light_directions.txt", light_dirs, fmt="%.8f")
    np.savetxt(object_dir / "light_intensities.txt", np.ones((lights, 3), dtype=np.float32), fmt="%.8f")
    (object_dir / "filenames.txt").write_text("\n".join(filenames), encoding="utf-8")
    normals_vis = (normals * 0.5 + 0.5) * mask[..., None]
    _write_image(object_dir / "Normal_gt.png", normals_vis)
    return root


def _image_paths_from_filenames(object_dir: Path) -> list[Path]:
    filenames_file = object_dir / "filenames.txt"
    if filenames_file.exists():
        names = [line.strip() for line in filenames_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        paths = [object_dir / name for name in names]
        existing = [path for path in paths if path.exists()]
        if existing:
            return existing
    ignored = {"mask", "normal_gt", "normal"}
    paths = []
    for path in sorted(object_dir.rglob("*")):
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        stem = path.stem.lower()
        if any(token in stem for token in ignored):
            continue
        paths.append(path)
    return paths


def load_diligent_object(
    root: Path,
    object_name: str,
    max_size: int = 96,
    max_lights: int | None = None,
) -> dict[str, torch.Tensor | str | list[str]]:
    object_dir = _object_dir(root, object_name)
    light_path = object_dir / "light_directions.txt"
    if not light_path.exists():
        raise FileNotFoundError(f"Missing {light_path}")
    lights = _normalize_light_table(np.loadtxt(light_path))
    intensities_path = object_dir / "light_intensities.txt"
    intensities = None
    if intensities_path.exists():
        intensities = _normalize_light_table(np.loadtxt(intensities_path))
    paths = _image_paths_from_filenames(object_dir)
    if not paths:
        raise FileNotFoundError(f"No DiLiGenT images found in {object_dir}")
    count = min(len(paths), len(lights))
    if max_lights is not None:
        count = min(count, max_lights)
    paths = paths[:count]
    lights = lights[:count]
    if intensities is not None:
        intensities = intensities[:count]

    images = []
    for idx, path in enumerate(paths):
        image = _resize_array(_read_image(path, "RGB"), max_size)
        if intensities is not None:
            scale = np.maximum(intensities[idx].reshape(1, 1, 3), 1e-6)
            image = np.clip(image / scale, 0.0, 1.0)
        images.append(image)
    stack = np.stack(images, axis=0).astype(np.float32)

    mask_path = object_dir / "mask.png"
    if mask_path.exists():
        mask = _resize_array(_read_image(mask_path, "L"), max_size, nearest=True) > 0.5
    else:
        mask = np.ones(stack.shape[1:3], dtype=bool)

    normal = None
    for normal_name in ("Normal_gt.png", "normal_gt.png", "normal.png"):
        normal_path = object_dir / normal_name
        if normal_path.exists():
            normal_image = _resize_array(_read_image(normal_path, "RGB"), max_size)
            normal = normal_image * 2.0 - 1.0
            break

    result: dict[str, torch.Tensor | str | list[str]] = {
        "images": torch.from_numpy(stack),
        "lights": torch.from_numpy(lights.astype(np.float32)),
        "mask": torch.from_numpy(mask.astype(np.float32)),
        "object": object_name,
        "paths": [str(path) for path in paths],
    }
    if normal is not None:
        result["normal"] = torch.from_numpy(normal.astype(np.float32))
    return result


def create_smoke_rgb_nir_pair(root: Path) -> Path:
    root = Path(root)
    scene_dir = root / "smoke_scene"
    scene_dir.mkdir(parents=True, exist_ok=True)
    height, width = 32, 32
    yy, xx = np.meshgrid(
        np.linspace(0.0, 1.0, height, dtype=np.float32),
        np.linspace(0.0, 1.0, width, dtype=np.float32),
        indexing="ij",
    )
    rgb = np.stack([xx, yy, 0.45 + 0.1 * np.sin(xx * np.pi * 4.0)], axis=-1)
    material_patch = ((xx > 0.35) & (xx < 0.75) & (yy > 0.25) & (yy < 0.65)).astype(np.float32)
    nir = 0.35 + 0.25 * yy + 0.35 * material_patch
    _write_image(scene_dir / "sample_rgb.png", rgb)
    _write_image(scene_dir / "sample_nir.png", nir)
    return root


def _image_files(root: Path) -> list[Path]:
    return [path for path in sorted(Path(root).rglob("*")) if path.suffix.lower() in IMAGE_EXTENSIONS]


def _modality(path: Path) -> str | None:
    filename = path.stem.lower()
    if re.search(r"(^|[_\-])nir([_\-]|$)", filename) or "nearinfrared" in filename:
        return "nir"
    if re.search(r"(^|[_\-])rgb([_\-]|$)", filename) or "visible" in filename or "color" in filename:
        return "rgb"

    text = "/".join(part.lower() for part in path.parent.parts)
    if re.search(r"(^|[_\-/])nir([_\-/.]|$)", text) or "nearinfrared" in text:
        return "nir"
    if re.search(r"(^|[_\-/])rgb([_\-/.]|$)", text) or "visible" in text or "color" in text:
        return "rgb"
    return None


def _pair_key(path: Path) -> str:
    text = "/".join(part.lower() for part in path.with_suffix("").parts)
    text = re.sub(r"(^|[_\-/])(rgb|nir)([_\-/]|$)", "/", text)
    text = text.replace("nearinfrared", "").replace("visible", "").replace("color", "")
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def find_epfl_pairs(root: Path) -> list[tuple[Path, Path]]:
    rgb_by_key: dict[str, Path] = {}
    nir_by_key: dict[str, Path] = {}
    for path in _image_files(root):
        modality = _modality(path)
        if modality == "rgb":
            rgb_by_key.setdefault(_pair_key(path), path)
        elif modality == "nir":
            nir_by_key.setdefault(_pair_key(path), path)

    pairs = []
    for key, rgb_path in rgb_by_key.items():
        nir_path = nir_by_key.get(key)
        if nir_path is not None:
            pairs.append((rgb_path, nir_path))

    if not pairs:
        rgb_paths = [path for path in _image_files(root) if _modality(path) == "rgb"]
        nir_paths = [path for path in _image_files(root) if _modality(path) == "nir"]
        pairs = list(zip(sorted(rgb_paths), sorted(nir_paths)))
    if not pairs:
        for folder in sorted(Path(root).rglob("jpg1")):
            panel_paths = [path for path in sorted(folder.iterdir()) if path.suffix.lower() in IMAGE_EXTENSIONS]
            pairs.extend((path, path) for path in panel_paths)
    return pairs


def _segments_from_columns(active: np.ndarray) -> list[tuple[int, int]]:
    segments = []
    start = None
    for idx, value in enumerate(active):
        if value and start is None:
            start = idx
        elif not value and start is not None:
            segments.append((start, idx))
            start = None
    if start is not None:
        segments.append((start, len(active)))
    return segments


def _split_side_by_side_panel(path: Path, max_size: int) -> tuple[np.ndarray, np.ndarray]:
    panel = _read_image(path, "RGB")
    row_energy = panel.mean(axis=(1, 2))
    row_active = row_energy > max(0.02, float(row_energy.max()) * 0.08)
    row_segments = [segment for segment in _segments_from_columns(row_active) if segment[1] - segment[0] > panel.shape[0] * 0.1]
    if row_segments:
        top, bottom = row_segments[0][0], row_segments[-1][1]
        panel = panel[top:bottom, :, :]
    column_energy = panel.mean(axis=(0, 2))
    active = column_energy > max(0.02, float(column_energy.max()) * 0.08)
    segments = [segment for segment in _segments_from_columns(active) if segment[1] - segment[0] > panel.shape[1] * 0.1]
    if len(segments) >= 2:
        left = segments[0]
        right = segments[-1]
        rgb = panel[:, left[0] : left[1], :]
        nir_rgb = panel[:, right[0] : right[1], :]
    else:
        midpoint = panel.shape[1] // 2
        rgb = panel[:, :midpoint, :]
        nir_rgb = panel[:, midpoint:, :]
    nir = nir_rgb.mean(axis=-1)
    rgb = _resize_array(rgb, max_size)
    nir = _resize_array(nir, max_size)
    if nir.shape != rgb.shape[:2]:
        pil = Image.fromarray((np.clip(nir, 0.0, 1.0) * 255.0).astype(np.uint8), mode="L")
        pil = pil.resize((rgb.shape[1], rgb.shape[0]), Image.Resampling.BILINEAR)
        nir = np.asarray(pil).astype(np.float32) / 255.0
    return rgb, nir


def load_rgb_nir_pair(
    rgb_path: Path,
    nir_path: Path,
    max_size: int = 96,
) -> dict[str, torch.Tensor | str]:
    rgb_path = Path(rgb_path)
    nir_path = Path(nir_path)
    if rgb_path.resolve() == nir_path.resolve():
        rgb, nir = _split_side_by_side_panel(rgb_path, max_size)
    else:
        rgb = _resize_array(_read_image(rgb_path, "RGB"), max_size)
        nir = _resize_array(_read_image(nir_path, "L"), max_size)
    if nir.shape != rgb.shape[:2]:
        nir = _resize_array(nir, max(rgb.shape[:2]), nearest=False)
        if nir.shape != rgb.shape[:2]:
            pil = Image.fromarray((np.clip(nir, 0.0, 1.0) * 255.0).astype(np.uint8), mode="L")
            pil = pil.resize((rgb.shape[1], rgb.shape[0]), Image.Resampling.BILINEAR)
            nir = np.asarray(pil).astype(np.float32) / 255.0
    return {
        "rgb": torch.from_numpy(rgb.astype(np.float32)),
        "nir": torch.from_numpy(nir.astype(np.float32)),
        "rgb_path": str(rgb_path),
        "nir_path": str(nir_path),
    }
