# AI 기반 데이터 이상치 탐지 프로그램

내부망(오프라인) 환경에서 동작하는 데스크톱 애플리케이션입니다.
사용자가 업로드한 **엑셀/CSV** 데이터를 자동 분석하여 여러 방식으로 이상치를 탐지하고,
결과를 스타일이 적용된 **Excel** 파일로 저장합니다.

> XLSX, XLS, CSV — IQR, Z-Score, LOF, Isolation Forest, DBSCAN 등

---

## 주요 기능

| 구분 | 알고리즘 | 설명 |
|------|----------|------|
| 규칙 기반 | 결측치 탐지 | NULL / NaN / 빈 문자열 / 공백 검사 |
| 규칙 기반 | 중복 데이터 | 모든 컬럼 값이 동일한 행 탐지 |
| 규칙 기반 | 범위 검사 | 사용자가 지정한 허용 최소/최대 초과 탐지 |
| 규칙 기반 | 증감률 검사 | 이전 행 대비 증감률(%) 임계치 초과 탐지 |
| 통계 기반 | IQR | Q1-1.5·IQR ~ Q3+1.5·IQR 범위 초과 |
| 통계 기반 | Z-Score | \|z\| > 임계치(기본 3.0) |
| 머신러닝 | Isolation Forest | contamination 조절 가능 |
| 머신러닝 | Local Outlier Factor (LOF) | n_neighbors 조절 가능 |
| 머신러닝 | DBSCAN | eps / min_samples 조절, 노이즈 탐지 |

- **컬럼 타입 자동 분석**: 숫자 / 문자열 / 날짜를 자동 판별 (사용자 지정 불필요)
- **숫자 컬럼 설정 화면**: 숫자 컬럼만 추출하여 실제/허용 최소·최대값 표시 및 편집
- **복수 알고리즘 동시 판정**: 한 행이 여러 알고리즘에 걸리면 사유를 쉼표로 연결
- **진행률 표시** 및 **백그라운드 실행**(GUI 멈춤 방지)

---

## 개발 환경

- Python **3.12 이상** (본 저장소는 3.11 에서도 동작 확인)
- GUI: **PySide6**
- pandas / numpy / scipy / scikit-learn / openpyxl
- (선택) `.xls` 읽기용 **xlrd**

외부 인터넷 없이 로컬 PC 에서 실행됩니다.

지원 파일 형식: **xlsx / xls / csv**

---

## 설치

### 인터넷이 되는 환경
```bash
pip install -r requirements.txt
```

### 내부망(오프라인) 환경
인터넷이 되는 PC 에서 wheel 을 미리 내려받아 옮깁니다.
```bash
# (인터넷 PC) 의존성 wheel 다운로드
pip download -r requirements.txt -d ./wheels

# (오프라인 PC) 로컬 wheel 로 설치
pip install --no-index --find-links=./wheels -r requirements.txt
```

---

## 실행

```bash
python main.py
```

### 사용 순서
1. **① 파일 선택** — xlsx / xls / csv 파일을 선택합니다. 읽는 즉시 숫자 컬럼 설정 테이블이 채워집니다.
2. **② 분석 옵션** — 사용할 알고리즘을 체크합니다(기본 전체 선택).
3. **알고리즘 파라미터** — 증감률 임계치, Z-Score 임계치, contamination, n_neighbors, eps, min_samples 를 조절합니다.
4. **숫자 컬럼 설정** — 컬럼별 허용 최소/최대값을 수정하고 '사용'을 체크합니다.
5. **⑤ 결과 저장 위치** — 결과 Excel 저장 경로를 지정합니다(파일 선택 시 기본 경로 자동 제안).
6. **③ 분석 시작** — 진행률(④)이 표시되며, 완료되면 결과가 저장됩니다.

---

## 결과 Excel 구조

원본 데이터를 그대로 유지하고 마지막에 컬럼 2개를 추가합니다.

- **이상치 여부**: 이상이면 `이상`, 정상이면 공란
- **이상치 사유**: 예) `범위 초과 [수행률] (허용:0~100, 실제:130), IQR 이상 [수행률]`

| 시트 | 내용 |
|------|------|
| `Result` | 원본 + 이상치 여부/사유. **이상 행 전체를 연한 노란색(#FFF2CC)** 으로 표시 |
| `Anomaly` | 이상으로 판정된 행만 추출 |

---

## 프로젝트 구조

```
project/
├── gui/           # PySide6 GUI (메인 윈도우, 설정 테이블, 워커 스레드)
├── services/      # 분석 오케스트레이션 (파일→컬럼분석→알고리즘→집계)
├── algorithms/    # 이상치 탐지 알고리즘 (공통 인터페이스 BaseDetector)
├── utils/         # 파일 읽기, 컬럼 타입 자동 분석
├── models/        # 데이터 모델(설정, 결과 등 값 객체)
├── export/        # Excel 결과 저장(스타일 적용)
└── config/        # 전역 상수/기본값
main.py            # 진입점
tests/             # 단위 테스트
scripts/           # 샘플 데이터 생성 및 검증 스크립트
```

각 알고리즘은 `BaseDetector` 공통 인터페이스를 구현하는 **독립 클래스**입니다.
새 알고리즘을 추가하려면 `BaseDetector` 를 상속하여 `detect()` 를 구현하고
`algorithms/__init__.py` 의 registry 에 등록하면 됩니다.

---

## 개발자용

```bash
# 샘플 데이터 생성 (sample_data/sample.csv, sample.xlsx)
python scripts/generate_sample_data.py

# GUI 없이 핵심 파이프라인 검증
python scripts/test_core_pipeline.py

# 단위 테스트 실행
python -m unittest discover -s tests
```

---

## 설계 원칙

- 객체지향(OOP), 타입 힌트, 주석, 예외 처리
- 모듈화 및 확장 가능한 구조 (공통 인터페이스 기반 알고리즘 플러그인화)
- GUI / 서비스 / 알고리즘 / 저장 계층 분리
