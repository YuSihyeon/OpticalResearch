# RTI / RGB-NIR Gaussian Pilot Experiment Design

## Goal

Build a small, real-data pilot that tests whether Gaussian primitives become more useful for relighting / inverse rendering when they store light or wavelength response instead of only memorizing RGB color.

This is not a full 3D Gaussian Splatting renderer. The experiment intentionally uses 2D Gaussian splats on the image plane so the comparison is about the Gaussian attribute model:

- fixed RGB or Lambertian attributes
- polynomial light response coefficients
- shared RGB/NIR geometry with separate spectral reflectance branches

## Dataset Decisions

### Primary RTI / Multi-Light Dataset

Use DiLiGenT single-view first.

Reference: https://sites.google.com/site/photometricstereodata/single

Reasons:

- It is real captured multi-light data, not synthetic-only.
- It is smaller and simpler than DiLiGenT-MV.
- It has 10 objects, 96 lighting conditions per object, masks, light directions, light intensities, filenames, and ground-truth normals.
- A single object and 16-32 light directions are enough for this pilot.

If automatic Google Drive download fails, the code will print manual download instructions and expected folder layout.

### Secondary Multi-Light Dataset

Keep DiLiGenT-MV and OpenIllumination as optional fallback / extension targets.

References:

- https://sites.google.com/site/photometricstereodata/mv
- https://oppo-us-research.github.io/OpenIllumination/
- https://huggingface.co/datasets/OpenIllumination/OpenIllumination

DiLiGenT-MV is larger and adds multi-view complexity. OpenIllumination is much larger overall, although Hugging Face object/light-level files can be sampled later. Neither should block the primary pilot.

### RGB-NIR Dataset

Use EPFL RGB-NIR Scene Dataset first.

Reference: https://www.epfl.ch/labs/ivrl/research/downloads/rgb-nir-scene-dataset/

Reasons:

- It provides paired RGB and NIR real images.
- The page exposes a small browser subset and a larger full dataset.
- It is enough for a cue-check experiment even though it is not a relighting dataset.

### Active RGB-NIR Dataset

Reference: https://arxiv.org/html/2605.30250

The related project page describes active RGB-NIR inverse rendering, but no public dataset download link was found during the initial check. Treat it as unavailable unless a download link is later provided. Do not block the project on it.

## Experiment A: RTI-Gaussian With Real Multi-Light Data

### Input

For one DiLiGenT object:

- multiple same-view images under different known lighting directions
- object mask
- light directions and intensities
- optional ground-truth normal map

The loader should support small subsets:

- image resolution downsampled to 64-128 px on the long side by default
- 16-32 lights by default
- deterministic train / held-out light split

### Models

All models use 2D Gaussian splats over the image plane. Each Gaussian has:

- position `(x, y)`
- scale `(sx, sy)` or isotropic `sigma`
- opacity

The renderer uses normalized weighted blending into an image-sized RGB output:

```text
image[p] = sum_i weight_i[p] * value_i / (sum_i weight_i[p] + eps)
```

The initial implementation can use a dense differentiable Gaussian weight map because the target resolution is small.

#### Baseline 1: Fixed RGB Gaussian

Each Gaussian stores one RGB color independent of light.

Purpose:

- show that a color-memorizing Gaussian model can fit average appearance but struggles with held-out lighting changes

#### Baseline 2: Lambertian Gaussian

Each Gaussian stores:

- diffuse RGB albedo
- normal vector

Given light direction `l`, brightness is approximately `max(0, dot(n, l))`, optionally with a learned ambient term.

Purpose:

- compare the RTI polynomial response with a physically interpretable but simple inverse-rendering baseline

#### RTI-Gaussian

Each Gaussian stores RGB polynomial response coefficients. For each channel:

```text
response(l) = a0 + a1 lx + a2 ly + a3 lz + a4 lx^2 + a5 ly^2 + a6 lx ly
```

The response passes through `softplus` before compositing so gradients remain stable while predicted radiance stays non-negative.

Purpose:

- test whether per-Gaussian light response improves held-out light reconstruction compared with fixed RGB and simple Lambertian attributes

### Training

Train on a subset of lighting directions and evaluate on held-out lights.

Default training setup:

- Adam optimizer
- masked MSE reconstruction loss
- short CPU/GPU-friendly run
- deterministic seeds
- command-line flags for object name, resolution, splat count, light count, iterations, and output directory

### Outputs

Save a compact figure to `outputs/rti_gaussian/`:

- train light reconstruction
- held-out light target
- fixed RGB baseline held-out prediction
- Lambertian baseline held-out prediction
- RTI-Gaussian held-out prediction
- baseline error map
- RTI-Gaussian error map
- loss curve
- optional plot comparing learned response-derived dominant direction with ground-truth normals

Also save numeric metrics:

- train PSNR / MAE
- held-out PSNR / MAE
- model configuration
- dataset object and light split

## Experiment B: RGB-NIR Gaussian Cue Check

### Input

One paired EPFL RGB/NIR image pair.

The loader should:

- find RGB/NIR pairs from the EPFL folder structure
- resize to small resolution
- normalize intensities consistently
- fall back to a documented manual folder layout if automatic parsing fails

### Model

Use shared 2D Gaussian geometry:

- position
- scale
- opacity

Use separate reflectance heads:

- RGB branch: per-Gaussian RGB reflectance
- NIR branch: per-Gaussian scalar reflectance

### Comparison

Train:

- RGB-only Gaussian reconstruction
- shared RGB+NIR Gaussian reconstruction

The goal is not relighting. The goal is to inspect whether NIR separates regions that are visually similar in RGB.

### Outputs

Save a compact figure to `outputs/rgb_nir_gaussian/`:

- RGB target
- RGB reconstruction
- NIR target
- NIR reconstruction
- RGB-only error
- shared RGB+NIR RGB error
- RGB/NIR reflectance difference heatmap

Also save a short interpretation:

- where RGB and NIR disagree
- whether the disagreement looks material-related
- how this could become an inverse-rendering prior in full 3DGS

## Unity Viewer

Create a minimal Unity project under `unity_viewer/` only after the Python outputs exist.

Scope:

- load exported PNG result panels from `outputs/`
- display RTI and RGB-NIR panels in a simple scene
- provide keyboard or UI controls to switch between result images
- optionally expose a light-index slider if per-light RTI predictions are exported

This viewer is for inspection, not for running training or implementing 3D Gaussian rendering inside Unity.

Use the installed Unity editor if possible:

- `C:\Program Files\Unity\Hub\Editor\2022.3.62f3\Editor\Unity.exe`
- fallback: `C:\Program Files\Unity\Hub\Editor\6000.3.2f1\Editor\Unity.exe`

## Implementation Shape

Create:

- `experiment_rti_gaussian.py`
- `experiment_rgb_nir_gaussian.py`
- `gaussian_pilot/`
- `gaussian_pilot/datasets.py`
- `gaussian_pilot/splats.py`
- `gaussian_pilot/models.py`
- `gaussian_pilot/train.py`
- `gaussian_pilot/visualize.py`
- `tests/`
- `README.md`

Use Python + PyTorch. If PyTorch is missing, create a project-local virtual environment and install dependencies from `requirements.txt`.

## Testing And Verification

Use tests for:

- polynomial light basis shape and values
- 2D Gaussian weight map shape and normalization
- train / held-out light splitting
- RGB/NIR pair discovery on a tiny fixture
- plotting functions producing output files

Before claiming success:

- run unit tests
- run both experiment scripts on either real data or a tiny smoke fixture
- if real datasets download successfully, generate real-data figures
- record failures clearly in the report if downloads are blocked or incomplete
- open or batch-check Unity project if created

## Connection To 3DGS Relighting

Full 3DGS stores many anisotropic 3D Gaussians and renders them from camera views. This pilot removes camera geometry and 3D projection, but preserves the key question: what should each Gaussian store?

If fixed color fails on held-out lights while RTI response improves, that supports the idea that Gaussian attributes can encode view/light-dependent material response rather than only radiance. If shared RGB/NIR geometry exposes material differences that RGB alone misses, that supports adding spectral cues as an inverse-rendering prior.

## Extension To Full 3DGS

A real 3DGS extension would need:

- 3D Gaussian positions, covariance, and camera projection
- visibility / occlusion handling
- view-dependent appearance
- physically meaningful BRDF or learned reflectance model
- lighting parameter estimation
- multi-view consistency
- regularization tying response coefficients to normals/materials
- GPU-efficient rasterization

## Limitations

- 2D splats cannot validate multi-view geometry.
- The RTI polynomial is empirical and may fit shadows/specularities without physical interpretation.
- DiLiGenT single-view has controlled lighting, not arbitrary natural illumination.
- EPFL RGB-NIR is not a relighting dataset, so it only supports a cue-check claim.
- Small subsets are useful for fast iteration but not enough for strong quantitative conclusions.
- Unity viewer displays results but does not prove Unity-side 3DGS rendering.
