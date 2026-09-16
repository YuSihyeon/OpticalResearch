# View-to-Gaussian Feature Aggregation PoC Report

## Executive Summary

HS-NeRF Tools/Origami/Caladium raw HSI could not be downloaded from the official
project page or public search/API checks in this environment, and COLMAP is not
installed. I therefore used the requested fallback: NeRF Synthetic Lego with
known camera poses and a public `lego.ply` point/Gaussian cloud. This means the
experiment validates the geometry/feature aggregation hypothesis only; it does
not evaluate spectral signature/radiance reconstruction.

Result: view-to-point/Gaussian aggregation worked in the fallback setting.
Multi-view mean features were substantially more consistent with held-out view
features than single-view features.

## Data and Environment

- Data attempted first: HS-NeRF Tools/Origami, then Caladium.
- Fallback data used: NeRF Synthetic Lego, 36 selected training views.
- RGB preparation: RGBA synthetic images composited over white pseudo-RGB.
- Geometry: known Blender camera transforms plus `lego.ply` point/Gaussian
  centers.
- Feature extractor: pretrained ResNet18, `layer3`, implemented without
  torchvision and loaded from official PyTorch weights.
- Runtime: Windows 11, Python 3.12.13 in `.venv`, torch 2.13.0+cpu.
- GPU present: RTX 5060 Ti, but installed torch is CPU-only. CUDA toolkit 12.3
  and NVIDIA driver CUDA 13.1 are present.
- COLMAP: not found on PATH.

## Quantitative Results

From `outputs/lego_fallback/summary.csv`:

| Method | Mean cosine up | Mean L2 down |
|---|---:|---:|
| Single-view | 0.5778 | 0.9047 |
| Multi-view mean | 0.7482 | 0.6586 |
| Weighted multi-view | 0.7249 | 0.6847 |
| Random correspondence | 0.6049 | 0.8099 |

Additional separation checks:

- Multi-view mean beat single-view in 90.8% of held-out cases.
- Multi-view mean beat random correspondence in 91.5% of held-out cases.
- Single-view beat random correspondence in only 38.3% of cases.
- Mean cosine margin, multi-view minus single-view: +0.1704.
- Mean cosine margin, multi-view minus random correspondence: +0.1433.

The view-count plot shows the same trend across track lengths from 8 to 27
observing views: multi-view mean remains consistently above single-view and
random correspondence.

## Visual Findings

The point visualizations show projected corresponding pixels across views,
pairwise feature cosine matrices, and held-out aggregation bars. They also show
failure cases: some points land near object boundaries or partially occluded
regions, where a wrong point can occasionally score high because coarse ResNet
features describe a nearby object/background region rather than the exact 3D
surface point.

## Required Questions

1. Did View-to-Gaussian correspondence actually work?

Yes, in the fallback geometric setting. A 3D point/Gaussian center could be
projected into multiple known camera views, CNN features could be bilinearly
sampled at the projected pixels, and same-point observations produced a coherent
aggregated descriptor.

2. Was multi-view aggregation better than single-view?

Yes. Multi-view mean improved cosine from 0.5778 to 0.7482 and reduced L2 from
0.9047 to 0.6586. It beat single-view in 90.8% of held-out observations.

3. Where did it fail?

It failed or weakened near object silhouettes, foreground/background boundaries,
and likely occluded or sparsely represented point-cloud regions. The random
correspondence baseline is not always very low because ResNet `layer3` features
are spatially coarse and semantic; nearby Lego/background regions can look
similar in feature space.

4. How did track errors and occlusion affect results?

There were no COLMAP track errors in the fallback because correspondences came
from known synthetic camera poses. However, occlusion remained approximate:
alpha masks removed background projections and a point-cloud z-buffer removed
many rear points, but this is weaker than true rendered depth/alpha contribution.
The visible failure cases are consistent with boundary/occlusion leakage.

5. Did the spectral head improve anything?

Not evaluated. Raw HS-NeRF HSI was not accessible, so there was no spectral
radiance ground truth. No reflectance recovery or spectral signature/radiance
reconstruction claim is made.

6. Is it worth integrating into R3DG next?

Yes, cautiously. The core aggregation hypothesis is supported: correct
multi-view correspondence yields more stable Gaussian/point features than a
single view. The next R3DG step should use real COLMAP tracks or trained 3DGS
Gaussians with rendered visibility/depth, and should replace the simple radial
weight with a visibility/reprojection-error/surface-normal-aware weight.

## Files

- Source: `view_to_gaussian_poc/src/`
- Runner: `view_to_gaussian_poc/run_lego_fallback.py`
- COLMAP template: `view_to_gaussian_poc/scripts/run_colmap_sparse.ps1`
- Environment: `view_to_gaussian_poc/environment_info.txt`
- CSV: `view_to_gaussian_poc/outputs/lego_fallback/*.csv`
- Plots: `view_to_gaussian_poc/outputs/lego_fallback/*.png`
- Correspondence figures:
  `view_to_gaussian_poc/outputs/lego_fallback/point_visualizations/`
