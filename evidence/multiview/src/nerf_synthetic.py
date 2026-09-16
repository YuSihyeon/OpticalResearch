from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlretrieve

import numpy as np
from PIL import Image


HF_BASE = "https://huggingface.co/datasets/rishitdagli/nerf-gs-datasets/resolve/main/lego"


def download_file(url: str, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not output_path.exists() or output_path.stat().st_size == 0:
        urlretrieve(url, output_path)
    return output_path


def select_frame_indices(total: int, max_images: int) -> list[int]:
    if max_images >= total:
        return list(range(total))
    indices = np.linspace(0, total - 1, max_images, dtype=np.int64)
    return sorted(set(int(i) for i in indices))


def download_lego_subset(root: str | Path, max_images: int = 36) -> dict[str, Path | list[str]]:
    root = Path(root)
    raw_dir = root / "data" / "raw" / "nerf_synthetic" / "lego"
    train_dir = raw_dir / "train"
    train_dir.mkdir(parents=True, exist_ok=True)

    transforms_path = download_file(f"{HF_BASE}/transforms_train.json", raw_dir / "transforms_train.json")
    download_file(f"{HF_BASE}/README.txt", raw_dir / "README.txt")
    ply_path = download_file(f"{HF_BASE}/lego.ply", raw_dir / "lego.ply")

    with transforms_path.open("r", encoding="utf-8") as f:
        transforms = json.load(f)
    selected = select_frame_indices(len(transforms["frames"]), max_images)

    image_names: list[str] = []
    selected_frames = []
    for idx in selected:
        frame = transforms["frames"][idx]
        stem = Path(frame["file_path"]).name
        image_name = f"{stem}.png"
        image_names.append(image_name)
        selected_frames.append(frame)
        download_file(f"{HF_BASE}/train/{image_name}", train_dir / image_name)

    subset_transforms = dict(transforms)
    subset_transforms["frames"] = selected_frames
    subset_path = raw_dir / "transforms_train_subset.json"
    with subset_path.open("w", encoding="utf-8") as f:
        json.dump(subset_transforms, f, indent=2)

    return {
        "raw_dir": raw_dir,
        "train_dir": train_dir,
        "transforms_path": subset_path,
        "ply_path": ply_path,
        "image_names": image_names,
    }


def prepare_pseudo_rgb(
    raw_train_dir: str | Path,
    output_dir: str | Path,
    image_names: list[str],
    image_size: int = 256,
) -> dict[str, Path]:
    raw_train_dir = Path(raw_train_dir)
    output_dir = Path(output_dir)
    image_dir = output_dir / "images"
    mask_dir = output_dir / "masks"
    image_dir.mkdir(parents=True, exist_ok=True)
    mask_dir.mkdir(parents=True, exist_ok=True)

    for image_name in image_names:
        src = Image.open(raw_train_dir / image_name).convert("RGBA")
        src = src.resize((image_size, image_size), Image.Resampling.LANCZOS)
        rgba = np.asarray(src, dtype=np.float32) / 255.0
        rgb = rgba[..., :3]
        alpha = rgba[..., 3:4]
        composited = rgb * alpha + (1.0 - alpha)
        Image.fromarray(np.clip(composited * 255.0, 0, 255).astype(np.uint8)).save(image_dir / image_name)
        Image.fromarray(np.clip(alpha[..., 0] * 255.0, 0, 255).astype(np.uint8)).save(mask_dir / image_name)

    return {"image_dir": image_dir, "mask_dir": mask_dir}


def read_ply_xyz(ply_path: str | Path, max_points: int | None = None, seed: int = 7) -> np.ndarray:
    ply_path = Path(ply_path)
    with ply_path.open("rb") as f:
        header_lines: list[str] = []
        while True:
            line = f.readline()
            if not line:
                raise ValueError("PLY header is missing end_header")
            text = line.decode("ascii").strip()
            header_lines.append(text)
            if text == "end_header":
                break
        data_start = f.tell()

    fmt = None
    vertex_count = None
    properties: list[tuple[str, str]] = []
    in_vertex = False
    for line in header_lines:
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "format":
            fmt = parts[1]
        elif parts[0] == "element":
            in_vertex = parts[1] == "vertex"
            if in_vertex:
                vertex_count = int(parts[2])
        elif in_vertex and parts[0] == "property" and len(parts) == 3:
            properties.append((parts[2], parts[1]))

    if fmt is None or vertex_count is None:
        raise ValueError("PLY file must define format and vertex count")

    if fmt == "ascii":
        data = np.loadtxt(ply_path, skiprows=len(header_lines), max_rows=vertex_count)
        name_to_col = {name: i for i, (name, _) in enumerate(properties)}
        xyz = data[:, [name_to_col["x"], name_to_col["y"], name_to_col["z"]]].astype(np.float32)
    elif fmt == "binary_little_endian":
        dtype_map = {
            "char": "i1",
            "uchar": "u1",
            "short": "<i2",
            "ushort": "<u2",
            "int": "<i4",
            "uint": "<u4",
            "float": "<f4",
            "double": "<f8",
        }
        dtype = np.dtype([(name, dtype_map[prop_type]) for name, prop_type in properties])
        with ply_path.open("rb") as f:
            f.seek(data_start)
            data = np.fromfile(f, dtype=dtype, count=vertex_count)
        xyz = np.stack([data["x"], data["y"], data["z"]], axis=1).astype(np.float32)
    else:
        raise ValueError(f"Unsupported PLY format: {fmt}")

    xyz = xyz[np.all(np.isfinite(xyz), axis=1)]
    if max_points is not None and len(xyz) > max_points:
        rng = np.random.default_rng(seed)
        keep = rng.choice(len(xyz), size=max_points, replace=False)
        xyz = xyz[np.sort(keep)]
    return xyz


def load_masks(mask_dir: str | Path, image_names: list[str]) -> dict[str, np.ndarray]:
    mask_dir = Path(mask_dir)
    masks: dict[str, np.ndarray] = {}
    for image_name in image_names:
        mask = Image.open(mask_dir / image_name).convert("L")
        masks[image_name] = np.asarray(mask, dtype=np.float32) / 255.0
    return masks
