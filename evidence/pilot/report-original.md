# Gaussian Pilot Result Report

## Data Used

- RTI / multi-light: DiLiGenT single-view `ballPNG`, 24 lights, held-out every 4th light.
- RGB-NIR: EPFL RGB-NIR browser subset `nirscene0/jpg1/country_0000.jpg`, parsed as left RGB / right NIR.
- Smoke fixtures were also generated for pipeline checks, but they are not used as research evidence.

## RTI-Gaussian Result

Output folder:

```text
outputs/rti_gaussian/
```

Key files:

- `rti_panel.png`
- `loss_curve.png`
- `metrics.json`
- `report.md`

Held-out light metrics on DiLiGenT `ball`:

| Model | Held-out MAE | Held-out PSNR |
| --- | ---: | ---: |
| Fixed RGB Gaussian | 0.02898 | 28.92 |
| Lambertian Gaussian | 0.03623 | 27.08 |
| RTI-Gaussian | 0.02628 | 29.44 |

Interpretation: in this small real-data subset, the polynomial RTI-Gaussian gives lower held-out error than fixed RGB and the simple Lambertian baseline. This supports the narrow claim that per-Gaussian light response can be useful beyond memorized color.

## RGB-NIR Gaussian Cue Check

Output folder:

```text
outputs/rgb_nir_gaussian/
```

Key files:

- `rgb_nir_panel.png`
- `metrics.json`
- `report.md`

Metrics on EPFL `country_0000`:

| Model / Branch | MAE | PSNR |
| --- | ---: | ---: |
| RGB-only reconstruction | 0.0426 | 25.24 |
| Shared RGB+NIR RGB reconstruction | 0.0425 | 24.92 |
| Shared RGB+NIR NIR reconstruction | 0.0406 | n/a |

Interpretation: the RGB/NIR reflectance difference heatmap highlights broad material/vegetation/road regions that differ between visible RGB and NIR. This is a cue-check, not a relighting result.

## Unity Viewer

Unity viewer files are in:

```text
unity_viewer/
```

The local Unity editor was found, and batch project creation was attempted. Unity reported no valid local license in `Editor.log`, so I could not open/run the viewer automatically. The viewer scaffold is still present:

- `unity_viewer/Assets/Scripts/ResultPanelViewer.cs`
- `unity_viewer/Assets/Editor/CreateViewerScene.cs`
- `unity_viewer/README.md`

Once Unity is licensed, open `unity_viewer`, run `Gaussian Pilot > Create Result Viewer Scene`, press Play, and browse PNG outputs with left/right keys.

## Failures And Limits

- This is 2D image-plane splatting, not full 3DGS.
- Visibility, occlusion, camera projection, view dependence, and full BRDF estimation are out of scope.
- The RTI polynomial can fit empirical light response without physical material meaning.
- DiLiGenT is controlled lighting, not natural in-the-wild illumination.
- EPFL RGB-NIR is paired spectral data, not a relighting dataset.
- Active RGB-NIR inverse-rendering data was not publicly downloadable from the checked project page, so EPFL was used.
