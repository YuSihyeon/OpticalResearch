# 전체 데이터와 복원 자료

이 저장소는 광학 연구의 설명, 선별 근거와 결과를 담는다. 전체 원본 작업 폴더·실행 환경·모델 상태는 별도의 개인 보존 묶음에 둔다. GitHub clone만으로 모든 실험 입력과 checkpoint가 복원되는 구조는 아니다.

아래 경로는 이 저장소가 개인 보존 묶음의 `04-OpticalResearch/repository/`에 있을 때의 상대경로다. 공개 Git에는 해당 private 원본을 포함하지 않는다. 파일 복사와 해시 검증의 최종 상태는 보존 묶음의 관리 기록에서 확인한다.

| 개인 보존 위치 | 내용 |
|---|---|
| `../originals/gs_windows/` | RTI/RGB-NIR·Lego PoC 전체 코드, 미추적 파일, 입력·중간 NPZ·outputs·가중치·Git·venv |
| `../originals/relight_windows/` | causal 검증 CSV/JSON/PNG 및 visual manifest ZIP, 원래 Git 객체 |
| `../originals/spectral_windows_home/` | Windows에 남은 continuation plan과 빈 디렉터리; Linux 전체 프로젝트와 별개 |
| `../originals/download-originals/` | 원래 연구 계획·미팅 PDF |
| `../originals/wsl-home/spectral-relighting-3dgs/` | Ubuntu-22.04에서 확인하고 직접 추출한 canonical 소스·datasets·outputs·third_party, 7,575파일 / 2,073,810,252 bytes |
| `../../_shared/wsl/Ubuntu-22.04.tar.zst` | 위 Linux 프로젝트와 환경의 전체 배포판 보존본. Linux 권한·링크 의미는 이 archive로 유지 |
| `../../_shared/originals/previous-research-archive/` | 이전 통합 아카이브의 로컬 자료 및 provenance |

## 어떤 입력이 필요한가

Windows 파일럿에는 DiLiGenT 원 ZIP·압축 해제본, 10물체×96조명 이미지와 mask/광원/법선 GT가 있다. EPFL nirscene0는 RGB/NIR 병렬 패널 자료로, jpg1/jpg2 각각 477장을 포함한다. 해당 파일럿이 실제 사용한 부분집합과 전체 보유 데이터의 크기는 구분해야 한다.

Lego PoC는 raw image/pose/PLY, processed 이미지, `resnet18-f37072fd.pth`, `projected_observations.npz`, `resnet18_features.npz`, 설정·CSV·run summary가 필요하다. PoC 소스 일부는 미커밋이므로 원본 작업 폴더를 포함해야 한다. 같은 이름의 외부 benchmark 데이터가 있어도 이 실험의 선택·전처리와 같다고 가정하지 않는다.

spectral relighting의 Windows ZIP은 선별 preview다. 재학습에는 WSL canonical 프로젝트의 spectral arrays, Mitsuba scene/config, `datasets/plane_exact`의 linear NPY·노출·pose·mask·nested split, 각 방법의 third_party source 및 학습 checkpoint/로그가 필요하다. ZIP의 INDEX manifest가 일부 source path와 hash를 제공하지만 전체 Linux 보존 검증을 대신하지는 않는다.

2026-09-16 후속 보존에서 **Ubuntu-22.04의 canonical 프로젝트가 실제로 존재함을 확인하고 직접 접근 가능한 폴더로 추출했다.** tar의 정규 파일 7,278개와 내부 hardlink 297개를 독립된 정규 파일로 보관하여 총 7,575파일 / 2,073,810,252 bytes가 되었다. 모든 파일은 archive payload 또는 hardlink 참조 원본의 SHA-256과 목적지 재읽기 SHA-256이 일치했다. 오류·충돌·미해결 링크는 0개다. 비공개 collection의 `_control/manifests/optical-wsl-extracted-summary.json`과 파일별 JSONL이 검증 근거다.

`datasets/`는 1,072파일 / 358,239,771 bytes, `outputs/`는 825파일 / 1,498,066,667 bytes이며 소스·설정·테스트·분광 NPZ도 포함한다. `.pt`/`.pth`/`.ckpt` 확장자 파일은 50개다. 대표 linear NPY는 256×256×3 float32의 유한한 값으로 읽혔고, Nikon exact-metamer NPZ의 321개 파장/반사율 배열도 안전한 배열 로더로 읽었다. checkpoint를 역직렬화하거나 학습·렌더를 다시 실행하지는 않았다.

이 결과는 **Ubuntu-22.04**에 해당한다. 별도의 **Ubuntu** 배포판의 동명 경로는 비어 있었고, Windows `spectral_windows_home`은 계획 문서 1개를 포함한 별도 조각이다. 세 위치를 같은 데이터로 취급하지 않는다.

## 복원할 때

1. 개인 보존 묶음의 복사 manifest와 SHA-256을 확인한다. 보관본은 수정하지 않고 별도 작업 복제를 만든다.
2. canonical 프로젝트의 직접 추출본은 파일별 해시 검증을 마쳤다. 실행 환경이 필요하면 전체 WSL export를 별도 배포판으로 복원하고 데이터·환경·외부 mount와 링크 대상을 확인한다. 배포판 import와 새 머신에서의 실험 실행 성공은 아직 검증하지 않았다.
3. Windows venv는 원래 Python 설치 경로에 의존할 수 있다. 보존한 base runtime이나 package/version 목록으로 작업 환경을 재구성하고 CPU smoke 실행부터 확인한다. CUDA 확장은 새 머신 환경에서 따로 검증한다.
4. 과거 설정·seed·split을 맞추고 새 출력 경로로 실행한다. 기존 결과와 입력을 덮어쓰지 않는다.

원래 Git에 HEAD가 없어도 dangling 객체가 남을 수 있다. 보관본에서 `git gc`, `git prune`, `git clean`을 실행하지 않는다. 과거 REPORT와 코드/JSON의 차이, spectral 검증의 `INCONCLUSIVE` 상태는 README의 분석을 함께 읽는다. 이 안내는 외장 저장장치 복사 완료나 모든 실험의 완전 재현을 의미하지 않는다.
