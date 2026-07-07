"""컬럼 타입 자동 분석 유틸리티.

각 컬럼의 값을 검사하여 숫자 / 문자열 / 날짜 타입을 자동 판별한다.
사용자가 타입을 직접 지정하지 않아도 되도록 한다.
"""

from __future__ import annotations

import warnings

import pandas as pd
from pandas.api import types as ptypes

from ..config import Settings
from ..models import ColumnInfo, ColumnType, NumericColumnConfig


class ColumnAnalyzer:
    """DataFrame 의 각 컬럼 타입을 자동 분석하는 클래스."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()

    def analyze(self, df: pd.DataFrame) -> list[ColumnInfo]:
        """모든 컬럼의 타입을 분석하여 ColumnInfo 목록을 반환한다."""
        return [ColumnInfo(name=str(col), col_type=self._detect_type(df[col])) for col in df.columns]

    def _detect_type(self, series: pd.Series) -> ColumnType:
        """단일 컬럼(Series)의 타입을 판별한다.

        판별 순서:
            1) 이미 숫자형 dtype 이면 Number.
            2) 이미 날짜형 dtype 이면 Date.
            3) 값 대부분이 숫자로 변환되면 Number.
            4) 값 대부분이 날짜로 변환되면 Date.
            5) 그 외에는 String.
        """
        non_null = series.dropna()
        # 값 자체가 공백 문자열인 경우도 제거하여 판별 정확도를 높인다.
        non_null = non_null[non_null.astype(str).str.strip() != ""]
        if non_null.empty:
            return ColumnType.STRING

        # 1) 이미 숫자형인 경우 (bool 은 숫자로 취급하지 않음)
        if ptypes.is_bool_dtype(series):
            return ColumnType.STRING
        if ptypes.is_numeric_dtype(series):
            return ColumnType.NUMBER

        # 2) 이미 날짜형인 경우
        if ptypes.is_datetime64_any_dtype(series):
            return ColumnType.DATE

        total = len(non_null)

        # 3) 숫자 변환 성공 비율 검사
        numeric_converted = pd.to_numeric(non_null, errors="coerce")
        numeric_ratio = numeric_converted.notna().sum() / total
        if numeric_ratio >= self._settings.NUMBER_DETECTION_MIN_RATIO:
            return ColumnType.NUMBER

        # 4) 날짜 변환 성공 비율 검사
        try:
            with warnings.catch_warnings():
                # 형식 자동 추론 경고는 판별 로직상 무해하므로 억제한다.
                warnings.simplefilter("ignore")
                date_converted = pd.to_datetime(non_null, errors="coerce")
            date_ratio = date_converted.notna().sum() / total
        except Exception:  # noqa: BLE001 - 날짜 파싱 실패는 문자열로 처리
            date_ratio = 0.0
        if date_ratio >= self._settings.DATE_DETECTION_MIN_RATIO:
            return ColumnType.DATE

        # 5) 기본값
        return ColumnType.STRING

    def numeric_column_names(self, column_infos: list[ColumnInfo]) -> list[str]:
        """숫자 컬럼명 목록을 반환한다."""
        return [info.name for info in column_infos if info.is_numeric]

    def build_numeric_configs(
        self, df: pd.DataFrame, column_infos: list[ColumnInfo]
    ) -> list[NumericColumnConfig]:
        """숫자 컬럼에 대한 기본 범위 설정 목록을 생성한다.

        실제 최소/최대값을 계산하고, 허용 최소/최대값을 동일하게 초기화한다.
        """
        configs: list[NumericColumnConfig] = []
        for info in column_infos:
            if not info.is_numeric:
                continue
            numeric_series = pd.to_numeric(df[info.name], errors="coerce").dropna()
            if numeric_series.empty:
                # 값이 전부 결측인 숫자 컬럼은 0~0 으로 초기화
                actual_min = actual_max = 0.0
            else:
                actual_min = float(numeric_series.min())
                actual_max = float(numeric_series.max())
            configs.append(
                NumericColumnConfig.from_bounds(info.name, actual_min, actual_max)
            )
        return configs
