# 광학·분광·재조명 연구 기록


**독립 연구 저장소:** [GitHub](https://github.com/YuSihyeon/OpticalResearch) · [전체 데이터와 복원 범위](DATA_AND_RESTORE.md)

이 연구의 중심 질문은 **“Gaussian에 보이는 RGB만 저장하는 대신 조명 반응과 파장별 재질 정보를 담으면, 새로운 조명에서도 더 타당한 영상을 만들 수 있는가?”**이다. 자료는 ① 실측 RGB/NIR·다중조명 데이터의 작은 2D 실험, ② 합성 스펙트럼 장면을 통한 메타머리즘 검증, ③ 다중시점 CNN 특징 집계 실험, ④ 스펙트럼 후보 분포를 유지하는 3DGS 확장 제안으로 이어진다.

현재 성과는 완성된 분광 3DGS 모델이 아니다. 조명 반응을 Gaussian 속성으로 표현하는 가능성, RGB 관측의 모호성, 다중시점 특징 집계의 안정성을 각각 다른 수준에서 확인한 연구 기록이다. 아래에서는 실제 저장된 결과, 합성 PoC, 제안, 미확인을 구분한다.

> 정리 기준: 2026-09-16에 남아 있는 로컬 보고서·코드·CSV/JSON·이미지·PDF를 교차 검토했다. 기존 실험을 재학습하지 않았다. 특히 “실제 실행된 실험”과 “실세계에서 촬영한 데이터”는 같은 뜻이 아니다. Mitsuba와 Lego 실험은 실행 산출물이 남아 있지만 합성 장면이다. 원본은 수정하지 않았다.

2026-09-16 후속 원본 보존 조사에서는 Ubuntu-22.04의 canonical `spectral-relighting-3dgs` 코드·데이터셋·checkpoint를 추가로 확인했다. 7,575개 파일(2,073,810,252바이트)을 광학 연구 폴더에 직접 추출하고 archive 내용과 해시를 대조했다. checkpoint 확장자 파일 50개가 있다는 사실은 전체 posterior 모델의 완성이나 성능 검증을 뜻하지 않는다. [추가로 보존한 데이터와 복원 경로](DATA_AND_RESTORE.md)를 확인한다.

## 1. 먼저 볼 자료와 성과 수준

| 연구 축 | 실제 입력 | 남아 있는 산출물 | 현재 확인할 수 있는 것 | 주장하면 안 되는 것 |
|---|---|---|---|---|
| RTI-Gaussian | 공개 실측 DiLiGenT `ball`, 24개 조명 중 18개 학습 | 코드, JSON, 결과 패널, 손실 곡선 | 첫 홀드아웃 조명에서 RTI MAE 0.02628, 고정 RGB 0.02898 | 전체 홀드아웃 평균, 다중 물체 일반화, 완전한 3DGS 재조명 |
| RGB-NIR Gaussian | 공개 실측 EPFL `country_0000` 한 쌍 | 코드, JSON, 패널 | 공유 2D Gaussian으로 RGB/NIR 표현 및 차이 시각화 | 보정된 반사율 복원, 재질 분류 정확도, 재조명 성공 |
| Spectral metamerism | Nikon 응답을 적용한 합성 World A/B, Mitsuba spectral GT | 6조명 CSV/JSON, 그림, 연구 미팅 PDF | D65에서 RGB가 같은 서로 다른 스펙트럼이 LED-RGB1에서 GT 차이 0.53035를 보임 | 모델이 두 스펙트럼을 독립 복원했다는 주장 |
| View-to-Gaussian | 합성 Lego RGB 36뷰, 알려진 카메라, 제공된 점/Gaussian 중심 | 코드, 44,304 관측의 요약 CSV, 그림 | 다중시점 평균 특징이 단일시점보다 held-out cosine에 유리 | HSI 복원, spectral head 효과, 실측 COLMAP 정확도 |
| 후보 분포 기반 spectral 3DGS | 위 관찰에서 출발한 설계 | 8쪽 연구 제안 PDF | 확장 구조와 연구 의도 | 전체 posterior network·spectral PBR의 구현 또는 성능 검증 |

핵심 원문: [메타머리즘 미팅 자료, 6쪽](evidence/reports/metamerism-meeting-2026-08-13.pdf), [Multi-view Spectrum 연구 제안, 8쪽](evidence/reports/multiview-spectrum-proposal.pdf), [초기 pilot 설계](evidence/pilot/design.md), [메타머리즘 최종 검증 보고서](evidence/metamerism/causal_metamerism_validation.md), [특징 집계 보고서](evidence/multiview/REPORT.md).

## 2. 연구 의도와 방향이 변한 과정

### 2.1 처음에는 “무엇을 Gaussian에 저장할 것인가”를 작게 검증했다

2026-07-15로 기록된 설계와 Git 이력에서는 계산량을 줄이기 위해 카메라 투영·3D 가림을 제거하고, 이미지 평면 위 Gaussian의 속성 표현만 비교했다. 고정 RGB, Lambertian albedo/normal, 다항식 조명 반응, RGB/NIR 두 분기를 구분하면 “표현할 정보”의 차이를 빠르게 볼 수 있기 때문이다. 완전한 3D 엔진 구축보다 먼저 연구 가설을 좁힌 선택이었다. [설계 근거](evidence/pilot/design.md)

DiLiGenT는 실제 촬영한 다중조명 데이터이고 조명 방향·세기·mask가 있어 선택했다. DiLiGenT-MV와 OpenIllumination은 더 큰 다중시점 확장 대상으로 남겼다. RGB-NIR은 실제 페어 영상을 소규모로 확보할 수 있는 EPFL browser subset을 사용했다. Active RGB-NIR 데이터는 당시 접근 가능한 다운로드 링크를 찾지 못했다는 기록이 있어 대체했다. 이는 **당시 조사 상황의 기록**이며, 현재의 공개 여부를 새로 검증한 결론은 아니다.

### 2.2 재조명 오류의 원인을 RGB 정보의 모호성으로 좁혔다

메타머리즘 자료에서는 기하·카메라·노출·장면은 같고 반사 스펙트럼만 다른 World A/B를 만들었다. 기준 D65 아래 Nikon D5100 응답으로 계산한 RGB를 같게 맞추면, RGB 모델이 볼 수 있는 정보와 실제 숨겨진 스펙트럼을 분리할 수 있다. 이후 조명만 바꾸어 spectral GT의 A/B 차이를 확인했다.

2026-08-13 미팅 PDF의 마지막 쪽에는 두 방향이 정리되어 있다. 첫째는 기존 모델에 추가 정보·제약을 넣는 방법 개발이고, 둘째는 RGB 모델이 재질·조명·기하를 어떻게 분해하는지 분석하여 spectral GT에 가까워지는 보정 경로를 만드는 것이다. 문서에는 **두 번째 방향을 먼저 수행하고 첫 번째로 확장**하겠다는 의도가 명시되어 있다. 목표 학회와 다음 작업 항목은 비어 있어 확정된 일정으로 복원하지 않았다. [PDF 6쪽](evidence/reports/metamerism-meeting-2026-08-13.pdf)

### 2.3 이후에는 하나의 정답 spectrum 대신 후보 집합을 유지하는 쪽으로 확장했다

Multi-view Spectrum 제안은 기존 R3DG의 geometry와 alpha splatting을 유지하면서, Gaussian별 재질 표현과 다중시점 특징 집계를 확장한다. RGB 세 값으로 하나의 spectrum을 확정하기보다, 관측과 모순되지 않는 여러 후보와 그 가중치를 유지하려는 것이다. 이 설계의 앞단인 “동일 3D 점의 여러 RGB 특징을 모으면 안정성이 좋아지는가”만 Lego PoC로 실제 확인했다. spectral 후보 생성과 최종 재조명까지 구현했다고 해석하면 안 된다.

## 3. RTI-Gaussian: 실측 다중조명 데이터로 한 속성 비교

### 입력과 전처리

DiLiGenT single-view `ball`의 24개 조명 영상을 사용했다. 저장된 설정은 해상도 60×72, Gaussian 96개, 학습 100 iteration이다. 0부터 시작하는 인덱스 기준 `[3, 7, 11, 15, 19, 23]`을 홀드아웃으로 지정하여 18개 조명으로 학습했다. 로더는 조명 방향 정규화, 제공된 조명 세기로 영상 나눗셈, `[0,1]` 범위 제한, mask 리사이즈를 수행한다. [수치·분할](evidence/pilot/results/rti_gaussian/metrics.json), [로더](evidence/pilot/source/gaussian_pilot/datasets.py)

### 처리와 도구 선택

Python/PyTorch에서 학습 가능한 2D 위치·축별 크기·opacity를 가진 Gaussian을 조밀한 weight map으로 표현했다. 픽셀은 `Σ weight_i × value_i / Σ weight_i`로 합성한다. 이 합성은 깊이 순서에 따른 3D alpha compositing이 아니다. Adam과 mask 기반 제곱오차를 사용해 작은 CPU 실험이 가능한 구조로 만들었다. [수학·지표](evidence/pilot/source/gaussian_pilot/splats.py), [학습](evidence/pilot/source/gaussian_pilot/train.py)

| 모델 | Gaussian에 담는 값 | 비교하는 이유 |
|---|---|---|
| Fixed RGB | 조명과 무관한 RGB 3개 | 평균 appearance를 기억하는 기준선 |
| Lambertian | RGB albedo, 단위 normal, ambient | 단순하지만 해석 가능한 광학 모델과 비교 |
| RTI | RGB 각 채널에 7개 계수 | 조명 방향에 따른 경험적 반응을 직접 학습 |

RTI basis는 `[1, lx, ly, lz, lx², ly², lx·ly]`이고 계수 결합 뒤 softplus로 음수 출력을 막는다. 다항식 계수가 그림자나 highlight까지 흡수할 수 있어 곧바로 물리적인 BRDF가 되는 것은 아니다. [모델 정의](evidence/pilot/source/gaussian_pilot/models.py)

### 저장된 결과와 코드에서 확인한 평가 범위

| 모델 | 첫 홀드아웃 조명 MAE ↓ | 같은 조명 PSNR ↑ |
|---|---:|---:|
| Fixed RGB | 0.028975 | 28.9196 dB |
| Lambertian | 0.036233 | 27.0825 dB |
| RTI | 0.026276 | 29.4450 dB |

RTI는 이 조명에서 Fixed RGB보다 MAE가 약 9.32% 작고 PSNR이 약 0.525 dB 높다. 그러나 실행 코드를 보면 `held_target = held_images[0]`, `rti(held_lights[:1])[0]`만 지표에 넣는다. 따라서 **홀드아웃 6개를 나눴다는 사실과 6개 전체를 평가했다는 주장은 구분해야 한다.** 이 표는 전체 평균이 아니다. [평가 코드](evidence/pilot/source/experiment_rti_gaussian.py)

![실측 DiLiGenT의 작은 RTI 실험](evidence/pilot/results/rti_gaussian/rti_panel.png)

위 그림은 원본 저장 패널을 그대로 보존했다. 전체적으로 어둡고 작은 물체 영역만 표현되므로 정성 판단에는 한계가 있다. 학습 진행은 [손실 곡선](evidence/pilot/results/rti_gaussian/loss_curve.png)에서 확인할 수 있지만, 낮아지는 학습 loss만으로 새로운 조명 전반의 성능을 입증하지는 않는다.

### 현재 의미와 다음 검증

이 결과는 “고정 색보다 조명 반응 속성을 저장하는 것이 유리할 수 있다”는 좁은 가설을 지지한다. 단일 물체·작은 해상도·한 평가 조명의 결과이며 seed 반복과 통계적 신뢰구간은 없다. Lambertian이 낮게 나온 원인이 모델의 본질적 열세인지, 초기화·100 iteration 예산·전처리 때문인지도 분리되지 않았다.

다음에는 모든 홀드아웃 조명과 여러 물체에 대해 개별/평균 오차를 기록하고, 학습 seed와 수렴 수준을 함께 비교해야 한다. 방사측정 범위, 영상 bit depth·전달함수, 조명 세기 정규화도 고정해야 한다. 이후에야 3D Gaussian 투영·가시성·다중시점 일관성을 추가한 결과와 연결할 수 있다.

## 4. RGB-NIR Gaussian: 재질 단서 탐색

### 입력 → 처리 → 출력

입력은 EPFL browser subset의 `country_0000.jpg` 한 파일이다. 좌우에 RGB/NIR가 함께 들어 있어 로더가 밝기 기반으로 검은 테두리를 자르고 왼쪽 RGB·오른쪽 NIR를 분리한다. JSON에 RGB 경로와 NIR 경로가 같은 이유는 같은 이미지를 두 입력으로 잘못 쓴 것이 아니라 **한 패널에서 두 영역을 추출하기 때문**이다. 최종 해상도는 64×96, Gaussian은 96개, 학습은 100 iteration이다. [로더](evidence/pilot/source/gaussian_pilot/datasets.py), [결과 JSON](evidence/pilot/results/rgb_nir_gaussian/metrics.json)

RGB-only 모델과 RGB/NIR geometry 공유 모델을 각각 학습한다. 공유 모델은 위치·크기·opacity를 함께 사용하면서 RGB 3개 값과 NIR 1개 값을 별도로 가진다. RGB/NIR 차이 그림은 각 Gaussian의 `abs(NIR - mean(R,G,B))`를 다시 splatting한 값이다. 코드가 `reflectance`라고 이름 붙였어도 카메라·노출·광원 보정을 거친 물리 반사율이라고 볼 근거는 없다. [실행 코드](evidence/pilot/source/experiment_rgb_nir_gaussian.py), [분기·차이 정의](evidence/pilot/source/gaussian_pilot/models.py)

### 현재 JSON을 기준으로 한 결과

| 평가 | MAE ↓ | PSNR ↑ |
|---|---:|---:|
| RGB-only의 RGB 재구성 | 0.034878 | 25.1659 dB |
| RGB+NIR 공유 모델의 RGB 재구성 | 0.034175 | 25.3651 dB |
| RGB+NIR 공유 모델의 NIR 재구성 | 0.036244 | 저장되지 않음 |

이는 학습에 사용한 한 페어에 대한 재구성 오차다. held-out 장면 일반화 실험이 아니다. 현재 저장 결과에서는 공유 모델의 RGB MAE가 약 2.02% 작지만, 한 실행만으로 보편적인 성능 개선을 주장하지 않는다.

**기존 보고서와 불일치:** [당시 종합 REPORT](evidence/pilot/report-original.md)는 0.0426 / 0.0425 / 0.0406과 다른 PSNR을 적고 있다. 현재 `metrics.json` 및 개별 `report.md`는 위 표와 일치한다. 어느 시점의 실행이 종합 표에 반영되었는지 확정할 로그가 없어, 두 결과를 섞지 않고 현재 원자료를 표의 기준으로 삼았다.

![RGB와 NIR 공유 Gaussian 표현](evidence/pilot/results/rgb_nir_gaussian/rgb_nir_panel.png)

나무·잔디 등 넓은 영역의 RGB/NIR 차이는 다음 재질 prior 실험을 위한 후보 단서다. 다만 차이에는 분광 반응 외에도 등록 오차, 처리·노출 차이, 모델의 저해상도 표현이 섞일 수 있다. 현재는 재질 정답 라벨·정량 분리 지표·새 조명 GT가 없으므로 “재질 cue를 시각화했다”는 범위가 적절하다. 후속은 다중 페어 및 registration 검증, 일관된 radiometric calibration, 재질별 분리 평가 순서가 타당하다.

Unity viewer도 만들어졌지만 역할은 결과 PNG 탐색이다. 원 보고서에는 라이선스 부재로 자동 실행에 실패했다고 기록되어 있다. Unity에서 분광 3DGS가 동작했다는 근거로 사용하지 않는다.

## 5. Spectral metamerism: 동일 RGB가 감추는 두 세계

### 의도와 실험 구조

RGB는 조명 SPD, 반사 spectrum, 센서 감도의 결합 결과다. 이 연구는 같은 D65 RGB를 만드는 서로 다른 반사 spectrum을 구성하고, 새로운 조명에서 두 정답이 갈라지는 상황을 만든다. Mitsuba 3는 파장별 정답 렌더링, Nikon D5100 공개 응답은 카메라 RGB 적분, R3DG·GS-IR는 RGB만 보는 비교 모델의 역할을 담당한다. Nikon 실물 카메라로 이 장면을 촬영했다는 뜻이 아니다. [연구 미팅 PDF 2~4쪽](evidence/reports/metamerism-meeting-2026-08-13.pdf)

![입력과 비교 구조](evidence/metamerism/figures/04_experiment_design_logic.png)

1. 기하·카메라·노출이 같은 World A/B를 만들고 spectrum만 바꾼다.
2. D65·Nikon source RGB를 수치적으로 같게 맞춘다.
3. 6개 조명에서 각 세계의 spectral GT를 생성한다.
4. 동일 D65 RGB 학습 입력에서 각 모델별로 하나의 공통 예측을 만든다.
5. 조명마다 그 공통 예측을 GT A, GT B, 두 GT의 중간값과 비교한다.

조명은 D65, D50, D75, Illuminant A, LED-B5, LED-RGB1이다. 포즈는 8개다. 평가는 linear RGB와 고정 노출을 사용하며 LED-RGB1에서 유도한 동일 ROI를 다른 조명에도 적용한다. 지표는 `||A-B|| / ((||A||+||B||)/2 + 1e-12)`인 대칭 상대 L2다. PNG의 sRGB 표현은 보기용이며 수치 평가 대상이 아니다. [메타데이터와 지표 정의](evidence/metamerism/causal_metamerism_validation.json)

### GT에서 확인된 분리

| 조명 | A/B 상대 L2 평균 | 8포즈 표준편차 |
|---|---:|---:|
| D65 | 0.019484 | 0.000220 |
| D50 | 0.047751 | 0.000392 |
| D75 | 0.027038 | 0.000296 |
| Illuminant A | 0.154200 | 0.000542 |
| LED-B5 | 0.118625 | 0.000312 |
| LED-RGB1 | 0.530354 | 0.001015 |

source 수준의 D65 RGB 상대 차이는 약 `8.32e-16`이다. 반면 렌더링된 D65 GT ROI에는 약 0.01948의 잔차가 남는다. source identity와 최종 렌더의 완전 동일성을 혼동하지 않아야 한다. LED-RGB1에서는 약 0.53035로 분리가 훨씬 커진다. 이 값은 인식 정확도나 퍼센트 오차율이 아니라 위 상대 L2 정의에 따른 값이다. [조명별 CSV](evidence/metamerism/illuminant_separation.csv), [D65 대조](evidence/metamerism/exact_d65_control.csv)

### 모델 결과와 최종 판정

| 조명 | R3DG → A | R3DG → B | R3DG → 중간값 | GS-IR → A | GS-IR → B | GS-IR → 중간값 |
|---|---:|---:|---:|---:|---:|---:|
| D65 | 0.4238 | 0.4236 | 0.4236 | 0.4707 | 0.4707 | 0.4707 |
| D50 | 0.4533 | 0.4290 | 0.4406 | 0.4469 | 0.4594 | 0.4528 |
| D75 | 0.4121 | 0.4223 | 0.4170 | 0.4828 | 0.4748 | 0.4787 |
| Illuminant A | 0.5736 | 0.4921 | 0.5283 | 0.3929 | 0.3674 | 0.3751 |
| LED-B5 | 0.3901 | 0.4562 | 0.4215 | 0.5029 | 0.4433 | 0.4708 |
| LED-RGB1 | 0.7150 | 0.2923 | 0.5335 | 0.3346 | 0.5481 | 0.3706 |

각 방법은 조명마다 **공통 예측 하나**를 가진다. 따라서 위 표의 A/B 열은 모델이 A/B 출력을 두 개 만들었다는 뜻이 아니다. LED-RGB1의 기존 0.503632(R3DG)와 0.441353(GS-IR)는 각각 공통 예측에서 두 GT로의 평균 오차이며, 모델 A/B 분리가 아니다. [원자료](evidence/metamerism/prediction_vs_gt.csv), [baseline 정의](evidence/metamerism/baseline_reproduction.json)

![공통 모델 출력과 두 세계의 정답](evidence/metamerism/figures/05_representative_world_outputs.png)

최종 검증 JSON은 `INCONCLUSIVE`로 판정한다. 실행 자체가 실패했다는 뜻이 아니라, 현재 출력 구조에서는 `Pred_A - Pred_B`나 GT delta와의 방향 상관을 정의할 수 없다는 뜻이다. 직접적인 모델 분리와 Pearson/Spearman, delta 부호 일치 항목은 `null`/NA다. GT에서 메타머 분리가 확인되었다는 결론은 유지되지만, 모델이 숨은 spectrum을 복원했다는 주장은 지지되지 않는다.

원 보고서는 R3DG 6×8, GS-IR 6×8로 총 96개의 linear 예측 배열을 생성했다고 기록한다. 다만 현재 Windows의 검토 폴더에는 그 NPY, checkpoint, 완전한 학습 소스가 없고 집계 자료와 시각 기록이 남아 있다. **96개 배열의 원자료를 이번 정리에서 직접 재검산한 것은 아니다.**

### 조명 proxy와 실행 과정에서 드러난 문제

RGB 방법이 SPD와 유한 면적 광원을 그대로 받지 못해, 보드 중심 irradiance를 맞춘 direction-only 환경 조명 proxy를 만들었다. 중심 일치는 전체 면의 광량 일치를 보장하지 않았다.

| D65 위치 | R3DG proxy 상대 오차 | GS-IR proxy 상대 오차 |
|---|---:|---:|
| 중심 | 0.2409% | 0.6966% |
| 가장자리 | 7.4789% | 7.9674% |
| 모서리 | 15.0410% | 15.5639% |

이는 학습 방법의 단독 성능 점수가 아니라 finite-area 광원과 위치 독립적인 direction-only proxy 사이의 기하 차이를 진단한 값이다. [proxy CSV](evidence/metamerism/proxy_error.csv)

2026-08-12 시각 기록에는 더 구체적인 시행착오가 남아 있다.

- R3DG stage 1의 30k와 NeILF stage 2의 50k 시각화가 있다. GS-IR은 공식 teaser HDRI와 raw/fixed-exposure proxy를 나눠 비교했다.
- R3DG에 GS-IR의 lat-long convention을 그대로 넣은 경우와, R3DG EnvLight convention에 맞게 교정한 경우를 비교했다. 조명 좌표계의 잘못된 변환이 모델 오류로 오인될 수 있음을 보여주는 진단이다.
- GS-IR linear NPY는 gamma/tone 변환 전이지만 공식 shading 내부 `[0,1]` clamp 이후라는 제한을 기록했다. R3DG capture는 sRGB encoding/clipping 전이라고 구분했다. 두 pipeline의 출력 계약을 동등하게 확인해야 한다.
- IRGS는 stage 1 결과가 있으나 WSL OptiX runtime 때문에 stage 2/render가 막힌 상태로 기록되었다. 성공 방법 목록에 넣지 않는다.
- 고정 5k iteration의 nested view-count 그림은 stage 1의 train-only RGB 진단이다. 시점 수가 spectral 식별성을 개선했다는 증거가 아니다.
- seed 0/1/2 반복은 요청되었지만 공식 entry point의 seed 0 고정 때문에 실행되지 않았다고 기록되어 있다. 실제 seed 분산은 추정되지 않았다.

근거: [시각 기록 설명](evidence/metamerism/visual-history/README.md), [선별 이력 인덱스](evidence/metamerism/visual-history/INDEX.md), [좌표계 교정 그림](evidence/metamerism/visual-history/05_r3dg_proxy_relighting/latlong_convention_diagnostic_test01.png), [seed 대조](evidence/metamerism/seed_control.csv). 이 기록의 `INDEX.md`는 원래 묶음 전체의 역사적 인덱스이므로, 여기서 선별하지 않은 파일도 이름이 나올 수 있다.

### 후속 해석에서 지켜야 할 경계

동일한 입력으로 같은 모델을 두 번 학습해 출력이 달라졌다고 해도, 그것이 숨겨진 World A/B를 식별했다는 뜻은 아니다. 추가 관측이나 명시적인 세계별 조건 없이 정답 세계를 알아맞힐 수 있는지와, 학습 변동으로 임의의 다른 설명을 만드는지는 다른 문제다. 기존 보고서가 제안한 `Pred_A/Pred_B` 인터페이스는 재질·spectrum 조건의 영향을 분리하는 데에는 유용하지만, 그 조건을 준 실험을 다시 RGB-only 복원 성공으로 부르면 안 된다.

가장 먼저 필요한 것은 원본 NPY·scene·SPD·센서 응답·exposure·camera convention·checkpoint와 평가 코드를 함께 회수하는 일이다. 그 다음 proxy 오차, 렌더링 D65 잔차, 모델 학습 오차를 분리한 대조 실험을 구성해야 한다.

## 6. View-to-Gaussian 특징 집계: 제안의 앞단을 검증한 합성 PoC

### 왜 이 실험으로 좁혔는가

HS-NeRF Tools/Origami, 이후 Caladium의 원시 HSI를 확보하려 했으나 당시 접근 가능한 링크를 찾지 못했고, 환경에는 COLMAP도 없었다고 기록되어 있다. 대신 NeRF Synthetic Lego의 알려진 Blender pose와 제공된 `lego.ply`를 사용했다. 따라서 대응 관계 자체를 RGB에서 새로 추정하는 단계는 건너뛰고 **알려진 기하로 올바른 위치를 투영한 다음 특징을 모으는 단계**를 검증했다. [실험 README](evidence/multiview/README.md)

### 입력 → 처리

| 항목 | 저장된 실행 설정 |
|---|---|
| 입력 | Lego RGBA 36뷰, 흰 배경에 합성한 pseudo-RGB |
| 영상 크기 | 256 |
| 특징 | 공식 pretrained ResNet18 가중치, `layer3`; torchvision 없이 구현 |
| 기하 | 알려진 Blender 카메라 변환, 50,000개 제공 점/Gaussian 중심 |
| 선별 | 최소 4뷰 조건에서 최대 1,800개 점 선정, seed 7 |
| 가시성 근사 | alpha ≥ 0.2, 점군 z-buffer 및 깊이 허용차 0.08 |
| 샘플링 | 투영 좌표에서 CNN feature를 bilinear sampling, L2 정규화 |
| 평가 | 한 관측을 제외하고 나머지로 집계한 leave-one-out |
| 관측 수 | 44,304행, 1,800개 점; 실제 track 길이 8~36뷰 |

근거: [설정](evidence/multiview/configs/lego_fallback.json), [가시성 근사](evidence/multiview/src/tracks.py), [샘플링·평가](evidence/multiview/src/evaluate.py), [집계 구현](evidence/multiview/src/aggregation.py), [실행 요약](evidence/multiview/results/run_summary.json).

Runtime 보고서는 Windows 11, Python 3.12.13, torch 2.13.0+cpu라고 적는다. RTX 5060 Ti가 있었지만 설치된 torch가 CPU 버전이어서 GPU를 사용한 실험은 아니었다. 실행 요약의 약 45.19초는 해당 로컬 실행 기록이며 일반적 속도 benchmark로 사용하지 않는다.

### 비교와 결과

| 방법 | held-out cosine 평균 ↑ | L2 평균 ↓ | 역할 |
|---|---:|---:|---|
| Single-view | 0.577799 | 0.904653 | 같은 점의 다른 관측 하나를 무작위 선택 |
| Multi-view mean | 0.748193 | 0.658599 | 같은 점의 나머지 관측을 단순 평균 |
| Weighted multi-view | 0.724858 | 0.684736 | radial view-angle heuristic을 가중치로 사용 |
| Random correspondence | 0.604918 | 0.809914 | 다른 점의 여러 관측 평균을 잘못 연결 |

![특징 집계 비교](evidence/multiview/results/summary_bar.png)

원시 `heldout_scores.csv`를 읽어 다시 집계한 결과, mean이 single보다 높은 cosine을 낸 비율은 **90.83%**, random보다 높은 비율은 **91.52%**다. cosine 평균 차이는 single 대비 +0.170394, random 대비 +0.143275다. 이는 재학습이 아니라 기존 CSV의 산술 재검산이며 [감사 JSON](evidence/review/aggregation-audit.json)에 기록했다. [원래 집계 CSV](evidence/multiview/results/summary.csv)

### 잘된 부분과 남은 오차를 함께 해석하기

여러 관측을 모으면 이 장면에서 단일 관측보다 안정적인 특징을 만들 수 있었다. 그러나 cosine 대상 자체가 pretrained CNN feature이므로, 좋아진 것이 실제 반사 spectrum이나 물리 재질 추정인지까지 말할 수는 없다.

Random correspondence가 single보다 높은 평균을 보이는 점도 중요하다. 코드상 random은 “다른 점의 여러 관측 평균”이고 single은 “같은 점의 관측 하나”여서 집계 횟수까지 같게 통제된 대조군은 아니다. 또한 ResNet `layer3`가 공간적으로 거칠고 의미 정보를 담아, 서로 다른 Lego/배경 점도 비슷할 수 있다. 따라서 random이 0이 아니라고 오류로 단정하거나, multi 개선 전부를 정확한 3D 대응의 효과라고 단정하지 않는다.

Weighted가 단순 mean보다 낮았다는 점은 가중치 설계를 개선할 근거다. radial 방향은 실제 표면 normal이나 visibility가 아니므로, 재투영 오차·진짜 렌더 깊이·alpha contribution을 반영한 가중치가 후속 과제다. 경계·실루엣·가림 주변에서는 점군 z-buffer의 근사로 잘못된 표면이나 배경 특징이 섞일 수 있다. [대표 대응 그림 1](evidence/multiview/results/point_visualizations/point_32721_consistency.png), [대표 대응 그림 2](evidence/multiview/results/point_visualizations/point_5602_consistency.png)

44,304행은 독립적인 44,304개 장면이 아니다. 같은 1,800점과 36개 카메라의 관측이 반복되므로, 통계 검증을 확장할 때는 장면·점 단위 의존성을 고려해야 한다. `by_view_count`는 track 길이가 다른 점 집단을 비교한 그래프이며, 동일 점에서 시점 수만 조절한 통제 실험은 아니다.

원 보고서의 “8~27뷰” 표현과 달리 CSV 감사 결과 및 그래프는 8~36뷰를 포함한다. 이번 문서는 원자료의 범위를 따른다. [뷰 수별 결과](evidence/multiview/results/by_view_count.csv)

## 7. 제안한 spectral 3DGS의 전체 구조와 미구현 부분

[8쪽 연구 제안](evidence/reports/multiview-spectrum-proposal.pdf)의 흐름은 다음과 같다.

1. Multi-view RGB와 camera pose를 입력한다.
2. CNN 특징을 추출하고 보이는 Gaussian 위치에서 sampling하여 여러 시점의 특징을 통합한다. **이 앞단만 Lego PoC로 부분 검증했다.**
3. MLP/Transformer posterior network가 Gaussian별 spectral 후보와 상대 가중치를 만든다.
4. spectrum 전체 대신 basis coefficient를 사용해 표현량을 줄인다.
5. global direct light와 Gaussian별 local indirect light를 분광 표현으로 추정한다.
6. Gaussian별 spectral PBR 계산과 alpha splatting을 수행한다.
7. 카메라 응답 적분으로 RGB를 만들고 관측과 재구성 오차를 계산한다.
8. 후보별 재조명 영상, spectrum, 후보 확률/entropy, 영상 평균·분산 등으로 불확실성을 보고한다.

문서가 참고했다고 밝힌 아이디어는 One-to-Many Spectral Upsampling의 다중 후보, HyperGS의 고차원 스펙트럼 압축, HSCNN+의 주변 공간 특징이다. 이는 작성 당시의 착안 관계를 보존한 설명이다. 이 저장소에서 해당 논문들을 모두 재현했거나, 참고 논문의 주장 전체를 이번에 독립 검증했다는 뜻은 아니다.

미구현 또는 확인되지 않은 핵심은 spectral head 학습, 후보 가중치 calibration, spectral GT를 사용한 radiance/reflectance 평가, spectral direct/indirect light, 3DGS end-to-end 통합이다. 단순 mean feature가 좋아졌다는 사실만으로 RGB의 스펙트럼 비식별성이 해소되지는 않는다. texture·semantic prior가 후보를 좁혀 줄 가능성과, 실제 새로운 독립 분광 관측을 얻는 것은 구분해서 평가해야 한다.

## 8. 다음 연구를 위한 구체적인 우선순위

| 우선순위 | 수행할 일 | 끝났다고 판단할 근거 |
|---|---|---|
| 1 | 원본 수치와 실행 계약 회수 | spectral NPY, scene/SPD/응답, checkpoint, 버전, 노출·clamp·좌표계가 연결된 manifest |
| 2 | 현재 평가 범위 보완 | RTI 모든 홀드아웃/다중 물체/seed, RGB-NIR 다중 페어와 registration, 보고서와 JSON 자동 일치 |
| 3 | 메타머리즘 오차 분리 | exact input 대조, D65 render 잔차, finite-area/proxy 대조, seed 분산을 별도로 보고 |
| 4 | 집계의 기하 신뢰도 개선 | 실제 COLMAP/학습된 GS와 true visibility, 동일 집계 수 negative, 점 고정 view subsampling |
| 5 | 후보 기반 spectral head의 최소 검증 | 알려진 GT에서 RGB 일치, spectrum 오차, 새로운 조명 오차, 후보 coverage/calibration을 함께 측정 |
| 6 | 이후 전체 3DGS 통합 | 3D 렌더 결과와 처리비용, ablation, held-out 장면·조명의 재현 가능한 비교 |

한 개 spectrum이 정답이라고 단정하는 모델과 여러 후보를 보존하는 모델을 비교할 때는 평균 RGB 오차뿐 아니라 **정답 후보 포함률, 새로운 SPD에서의 예측 불확실성, 잘못된 확신**도 평가 대상이 되어야 한다. 추가 NIR·다중광원·분광 단서가 사용된다면 RGB-only 조건과 분리하여 정보 증가의 효과를 측정해야 한다.

## 9. 선별 보존과 재현성 상태

핵심 PDF 2개, 설계/보고서, 작은 CSV/JSON, 대표 이미지, 자체 실험 코드를 복사했다. 대형 데이터셋, pretrained weight, `.venv`, cache, 전체 third-party 저장소와 중복 ZIP은 제외했다. 로컬 전용 `evidence/source-map.json`은 원본 절대경로·SHA-256·선별 이유·복사/추출/경로제거 여부를 보관하며 공개 저장소에서 제외한다. public README의 근거 링크는 공개된 이 폴더 안의 상대 경로를 사용한다.

일부 JSON의 로컬 절대경로는 공개 본문과 분리하기 위해 placeholder로 바꾸고 원래 값을 source-map에 남겼다. 수치 필드는 그대로다. 원래 보고서 안의 역사적 해석이나 경로가 현재 정리와 다를 수 있어, 위 각 절의 평가 범위 정정이 우선한다.

검토 시점에 pilot 로컬 Git의 마지막 커밋은 `3f31a19`(2026-07-15)이며 remote 설정이 없었다. View-to-Gaussian 폴더와 그 테스트는 untracked 상태였다. RelightGS는 `.git`은 있으나 커밋과 remote가 없었다. 이 정보는 당시 로컬 상태이며, 이번 정리에서 GitHub 게시나 학습 소스 전체의 존재를 확인했다는 뜻이 아니다.

열화상 카메라 캡처, intensity 기반 height field, FireSight 합성 레이더 평면 분리는 광학 연구의 연계 탐색으로 발견되었으나 별도의 열화상 연구 문서로 분리한다. RGB/NIR 반사 단서, LWIR 열 영상, radar 기하를 하나의 센서 실험 성과로 합치지 않는다.
