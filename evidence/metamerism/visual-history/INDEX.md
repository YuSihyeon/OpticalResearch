# Visual record index

각 파일의 자세한 원본 경로와 해석은 `INDEX.json`과 함께 확인한다.

| 순서 | 파일 | 상태 | 원본 | 의미 |
|---:|---|---|---|---|
| 10 | `01_problem_definition/paired_world_roi_summary.png` | `primary` | `outputs/plane_exact_all_lights_roi_summary.png` | Spectral World A/B separation and ambiguity lower bound across illuminants. |
| 20 | `01_problem_definition/nikon_exact_metamer_spectra.png` | `primary` | `outputs/validation/nikon_exact_metamer_spectra.png` | The two material spectra used to construct the Nikon exact-metamer pair. |
| 30 | `01_problem_definition/fixed_exposure_comparison.png` | `control` | `outputs/plane_validation_256/fixed_exposure_comparison.png` | Raw versus fixed-exposure image contract used by the authoritative targets. |
| 40 | `01_problem_definition/plane_chart_preview.png` | `control` | `outputs/plane_chart_preview/world_A_D65_train_01_preview.png` | Camera/scene chart used for the synthetic plane data and method exports. |
| 50 | `01_problem_definition/illuminants_test01_worldAB.png` | `summary` | `generated from the source artifacts listed in this manifest` | Same camera pose across six illuminants, with World A/B on adjacent rows. |
| 100 | `02_spectral_ground_truth/led_rgb1_world_A_test01.png` | `primary` | `datasets/plane_exact/eval/test_8/led_rgb1/world_A/preview/test_01.png` | Authoritative LED-RGB1 spectral target for World A, test_01. |
| 110 | `02_spectral_ground_truth/led_rgb1_world_B_test01.png` | `primary` | `datasets/plane_exact/eval/test_8/led_rgb1/world_B/preview/test_01.png` | Authoritative LED-RGB1 spectral target for World B, test_01. |
| 120 | `02_spectral_ground_truth/led_rgb1_roi_mask_overlay_test01.png` | `control` | `datasets/plane_exact/eval/test_8/led_rgb1/mask_overlays/test_01.png` | ROI used by the paired-world metric; it is not a prediction image. |
| 200 | `03_method_training_progress/r3dg_stage1_000001.png` | `control` | `outputs/logs/r3dg/view_3_full_render/visualize/000001.png` | R3DG stage-1 visualization near the beginning of full training. |
| 210 | `03_method_training_progress/r3dg_stage1_030000.png` | `control` | `outputs/logs/r3dg/view_3_full_render/visualize/030000.png` | R3DG stage-1 visualization at the 30k checkpoint. |
| 220 | `03_method_training_progress/r3dg_stage2_050000.png` | `control` | `outputs/logs/r3dg/view_3_stage2_neilf/visualize/050000.png` | R3DG NeILF stage-2 visualization at the 50k checkpoint. |
| 230 | `03_method_training_progress/gsir_stage2_train_teaser.png` | `control` | `outputs/logs/gsir/view_3_stage2_d65/train/ours_None/relight/00000_teaser.png` | GS-IR stage-2 training-camera relighting smoke using the official teaser HDRI. |
| 240 | `03_method_training_progress/irgs_stage1_000002.png` | `blocked` | `outputs/logs/irgs/view_3_full_refgaussian/visualize/000002.png` | IRGS stage-1 artifact; later stage-2/render remains blocked by the WSL OptiX runtime. |
| 250 | `03_method_training_progress/irgs_stage1_030000.png` | `blocked` | `outputs/logs/irgs/view_3_full_refgaussian/visualize/030000.png` | IRGS stage-1 final visualization; not evidence of successful stage-2 rendering. |
| 260 | `03_method_training_progress/irgs_stage1_030000_env.png` | `blocked` | `outputs/logs/irgs/view_3_full_refgaussian/visualize/030000_env.png` | IRGS learned environment visualization before the OptiX render gate. |
| 270 | `03_method_training_progress/checkpoint_progression.png` | `summary` | `generated from the source artifacts listed in this manifest` | Selected training and relighting checkpoints across the three official methods. |
| 300 | `04_gsir_proxy_relighting/gsir_teaser_test01.png` | `control` | `outputs/logs/gsir/view_3_stage2_d65/test/ours_None/relight/00000_teaser.png` | Official GS-IR external-HDRI test-camera interface control. |
| 310 | `04_gsir_proxy_relighting/gsir_raw_proxy_test01.png` | `proxy` | `outputs/logs/gsir/view_3_stage2_d65/test/ours_None/relight/00000_led_rgb1_center_proxy.png` | GS-IR output under the unscaled SPD-to-RGB center proxy; sensitivity only. |
| 320 | `04_gsir_proxy_relighting/gsir_fixed_exposure_proxy_test01.png` | `proxy` | `outputs/logs/gsir/view_3_stage2_d65/test/ours_None/relight/00000_led_rgb1_center_proxy_exposed.png` | GS-IR output under the fixed-exposure center proxy; still not primary ground truth. |
| 330 | `04_gsir_proxy_relighting/led_rgb1_center_proxy.hdr` | `proxy` | `outputs/method_lights/gsir/led_rgb1_center_proxy.hdr` | Raw SPD-derived GS-IR HDR input; use the manifest for its assumptions. |
| 340 | `04_gsir_proxy_relighting/led_rgb1_center_proxy_exposed.hdr` | `proxy` | `outputs/method_lights/gsir/led_rgb1_center_proxy_exposed.hdr` | Fixed-exposure SPD-derived GS-IR HDR input; use the manifest for its assumptions. |
| 345 | `05_r3dg_proxy_relighting/finite_area_vs_proxy_irradiance.png` | `control` | `outputs/logs/proxy_irradiance/finite_area_vs_proxy_irradiance.png` | Spatial diagnostic separating finite-area source geometry from the position-independent GS-IR/R3DG direction-only proxy. |
| 350 | `04_gsir_proxy_relighting/proxy_vs_ground_truth_test01.png` | `summary` | `generated from the source artifacts listed in this manifest` | Direct visual comparison of spectral targets and the three GS-IR lighting inputs. |
| 360 | `04_gsir_proxy_relighting/led_rgb1_center_proxy_preview.png` | `summary` | `generated from the source artifacts listed in this manifest` | Display-only preview of the raw center proxy with a shared HDR scale of 10.0. |
| 370 | `04_gsir_proxy_relighting/led_rgb1_center_proxy_exposed_preview.png` | `summary` | `generated from the source artifacts listed in this manifest` | Display-only preview of the fixed-exposure center proxy with the same HDR scale. |
| 400 | `06_final_study_summary/final_study_summary.png` | `summary` | `outputs/logs/final_study_summary.png` | Final scope summary separating the primary spectral claim, runnable RGB proxy sensitivity, finite-area adapter error, and IRGS runtime blocker. |
| 410 | `07_view_count_robustness/view_count_robustness_summary.png` | `summary` | `outputs/logs/view_count_robustness_summary.png` | Fixed-5k nested view-count stage-1 RGB diagnostics for R3DG and GS-IR; not a spectral or held-out performance figure. |
| 430 | `05_r3dg_proxy_relighting/r3dg_proxy_hdr_preview.png` | `summary` | `generated from the source artifacts listed in this manifest` | Display-only preview of the raw and fixed-exposure R3DG-specific HDR proxies using a common display scale of 10.0. |
| 440 | `05_r3dg_proxy_relighting/latlong_convention_diagnostic_test01.png` | `summary` | `generated from the source artifacts listed in this manifest` | The same R3DG checkpoint and fixed proxy scale with the wrong GS-IR map convention versus the corrected R3DG EnvLight convention. |
| 450 | `05_r3dg_proxy_relighting/proxy_predictions_test.png` | `summary` | `generated from the source artifacts listed in this manifest` | Display-only R3DG raw/fixed-exposure proxy predictions across all eight held-out poses; common HDR display scale 1.0, with no metric normalization. |
