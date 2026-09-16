# View-to-Gaussian Feature Aggregation PoC

This folder contains a minimal, executable proof-of-concept for testing whether
2D CNN features observed from multiple views can be aggregated onto the same 3D
point/Gaussian-like center and become more consistent with a held-out view.

## Dataset status

I first checked the HS-NeRF project page and related public search/API routes.
The official page exposes the paper, supplemental material, and qualitative
assets, but I could not locate an accessible raw HSI download link for Tools,
Origami, or Caladium from this environment. COLMAP is also not installed on this
machine.

Fallback used here:

- Dataset: NeRF Synthetic Lego from a Hugging Face mirror of the original NeRF
  synthetic/Blender dataset.
- Geometry: known Blender camera poses plus `lego.ply` point/Gaussian centers.
- Spectral evaluation: not available. This run is geometric/RGB feature
  validation only.

## Reproduce

From the repository root:

```powershell
.\.venv\Scripts\python.exe view_to_gaussian_poc\scripts\probe_environment.py
.\.venv\Scripts\python.exe -m pytest tests\test_view_to_gaussian_core.py -q
.\.venv\Scripts\python.exe view_to_gaussian_poc\run_lego_fallback.py
```

The main script downloads:

- `transforms_train.json`
- a 36-image subset of `lego/train/*.png`
- `lego.ply`
- official PyTorch ResNet18 weights

Then it composites RGBA images over white pseudo-RGB, extracts pretrained
ResNet18 `layer3` features, projects 3D centers into each view, filters by alpha
mask and point-cloud z-buffer, samples CNN features bilinearly, and runs
leave-one-out held-out-view evaluation.

Standalone helpers:

```powershell
.\.venv\Scripts\python.exe view_to_gaussian_poc\scripts\download_lego_fallback.py
.\.venv\Scripts\python.exe view_to_gaussian_poc\scripts\prepare_lego_pseudo_rgb.py
.\.venv\Scripts\python.exe view_to_gaussian_poc\scripts\hsi_npy_to_pseudo_rgb.py --cube cube.npy --wavelengths wavelengths.npy --output rgb.png
```

## Key outputs

`view_to_gaussian_poc/outputs/lego_fallback/`

- `heldout_scores.csv`: per held-out observation metrics.
- `summary.csv`: aggregate method comparison.
- `by_view_count.csv`: performance grouped by number of observing views.
- `projected_correspondences.csv`: point/view/pixel/depth/weight records.
- `summary_bar.png`, `by_view_count.png`, `cosine_hist.png`: comparison plots.
- `point_visualizations/*.png`: correspondence pixels and feature consistency.
- `run_summary.json`: run metadata.

## Methods compared

- Single-view: one randomly selected observed feature from the same 3D point.
- Multi-view mean: unweighted mean of the remaining same-point observations.
- Weighted multi-view: radial viewing-angle heuristic weight.
- Random correspondence: mean feature from a different 3D point.

## Current run summary

```text
images: 36
loaded points: 50,000
selected points with >=4 views: 1,800
projected observations: 44,304
leave-one-out rows: 44,304
```

Top-line result from `summary.csv`:

```text
single cosine:         0.5778
multi-view mean:       0.7482
weighted multi-view:   0.7249
random correspondence: 0.6049
```

Multi-view mean improved over single-view on about 90.8% of held-out cases and
over random correspondence on about 91.5% of cases.

## Limitations

- This is not an HS-NeRF spectral radiance experiment because raw HSI was not
  accessible.
- This is not a COLMAP sparse-track run because COLMAP is absent. The fallback
  uses known synthetic camera poses and a provided point/Gaussian cloud.
- Occlusion is approximated by alpha masking and point-cloud z-buffering, not by
  rendered alpha contribution from a trained 3DGS model.
- The weighted heuristic underperformed simple averaging, so weighting should be
  revisited with surface normals, reprojection error, or true visibility.

## COLMAP template

If COLMAP is installed and RGB/HSI pseudo-RGB images are available:

```powershell
powershell -ExecutionPolicy Bypass -File view_to_gaussian_poc\scripts\run_colmap_sparse.ps1 `
  -ImageDir path\to\images `
  -WorkspaceDir path\to\colmap_workspace
```
