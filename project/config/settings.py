"""프로그램 전역 상수 및 기본값.

한 곳에서 관리하여 유지보수를 쉽게 한다.
"""

from __future__ import annotations


class Settings:
    """전역 상수 모음."""

    APP_NAME: str = "AI 기반 데이터 이상치 탐지 프로그램"
    APP_VERSION: str = "1.0.0"

    # 지원 파일 형식
    SUPPORTED_EXTENSIONS: tuple[str, ...] = (".xlsx", ".xls", ".csv")
    FILE_DIALOG_FILTER: str = "데이터 파일 (*.xlsx *.xls *.csv);;모든 파일 (*.*)"

    # Excel 결과 관련
    RESULT_SHEET_NAME: str = "Result"
    ANOMALY_SHEET_NAME: str = "Anomaly"
    ANOMALY_FLAG_COLUMN: str = "이상치 여부"
    ANOMALY_REASON_COLUMN: str = "이상치 사유"
    ANOMALY_FLAG_VALUE: str = "이상"
    ANOMALY_HIGHLIGHT_COLOR: str = "FFF2CC"  # 연한 노란색(ARGB 앞 2자리는 자동 처리)

    # 기본 알고리즘 파라미터
    DEFAULT_CHANGE_RATE_THRESHOLD: float = 100.0
    DEFAULT_ZSCORE_THRESHOLD: float = 3.0
    DEFAULT_ISO_CONTAMINATION: float = 0.05
    DEFAULT_LOF_N_NEIGHBORS: int = 20
    DEFAULT_DBSCAN_EPS: float = 0.5
    DEFAULT_DBSCAN_MIN_SAMPLES: int = 5

    # 컬럼 타입 자동 분석 시 날짜 판별에 사용할 최소 성공 비율
    DATE_DETECTION_MIN_RATIO: float = 0.8
    # 숫자 판별에 사용할 최소 성공 비율
    NUMBER_DETECTION_MIN_RATIO: float = 0.8
