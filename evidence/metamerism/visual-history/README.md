# Visual records

이 폴더는 연구 과정에서 판단 근거가 되는 이미지만 원본 위치에서 복사해 모아 둔 기록용 폴더다. 원본 산출물은 이동하거나 덮어쓰지 않았다. 전체 파일의 원본 경로, 상태, 의미, SHA-256은 `INDEX.json`에서 확인한다.

## 읽는 순서

1. `01_problem_definition/`: exact-metamer 문제, spectral separation, 노출 계약, 카메라 chart.
2. `02_spectral_ground_truth/`: LED-RGB1 World A/B authoritative spectral target과 metric ROI.
3. `03_method_training_progress/`: R3DG, GS-IR, IRGS의 checkpoint 진행 기록. IRGS 이미지는 stage-1 artifact이며 stage-2 blocker가 해소됐다는 뜻이 아니다.
4. `04_gsir_proxy_relighting/`: official teaser HDRI, raw center proxy, fixed-exposure proxy의 GS-IR 비교.
5. `05_r3dg_proxy_relighting/`: R3DG EnvLight convention으로 생성한 raw/fixed proxy 예측과 GS-IR convention 오입력 진단 비교.
6. `06_final_study_summary/`: primary spectral claim, runnable R3DG/GS-IR sensitivity, finite-area adapter error, IRGS blocker를 한 장으로 요약한 최종 범위 그림.
7. `07_view_count_robustness/`: fixed-5k nested view-count 보조 분석. 두 공식 RGB pipeline의 train-only 진단이며 spectral/held-out 성능 그림이 아니다.

상태 의미는 `primary`(authoritative spectral result), `control`(interface/검증용), `proxy`(SPD-to-HDR 근사 sensitivity), `blocked`(실행 blocker가 남은 method artifact), `summary`(이 폴더에서 생성한 contact sheet)다.

HDR 파일 옆의 preview/contact sheet는 시각 확인 전용이다. 수치 평가는 HDR preview가 아니라 원본 linear NPY와 JSON report를 사용한다. 특히 GS-IR proxy NPY는 gamma/tone/PNG 변환 전 capture이지만 공식 `pbr_shading(tone=False)` 내부 `[0,1]` clamp 이후라는 점을 기억한다.
R3DG proxy NPY는 공식 `pbr_env` 계산 뒤 `rgb_to_srgb` 출력 encoding/clipping 직전에 capture한 선형 RGB다. R3DG proxy의 최종 수치는 `05_r3dg_proxy_relighting` 이미지가 아니라 `outputs/logs/r3dg/view_3_stage2_neilf/`의 R3DGCONV JSON report를 사용한다.

최종 해석 범위는 `docs/final_experiment_scope.md`를 기준으로 한다. `06_final_study_summary/` 그림은 leaderboard가 아니라 primary/proxy/blocked/control 경계를 시각적으로 기록한 summary다.
`07_view_count_robustness/` 그림은 view 수와 고정 iteration budget의 관계를 기록한 보조 진단이며, 더 많은 view가 spectral identifiability를 개선한다고 해석하지 않는다.

마지막으로 결과를 인용할 때는 이 폴더의 복사본보다 `source`에 기록된 원본 artifact와 해당 report를 기준으로 한다.
