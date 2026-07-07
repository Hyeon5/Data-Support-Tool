"""결측치 탐지 알고리즘."""

from __future__ import annotations

import pandas as pd

from ..models import AnomalyFinding
from .base import BaseDetector, DetectionContext


class MissingValueDetector(BaseDetector):
    """결측치를 탐지한다.

    검사 대상:
        - NULL / None
        - NaN
        - 빈 문자열("")
        - 공백만 있는 문자열("   ")
    한 행에서 하나 이상의 컬럼이 결측이면 이상으로 판정한다.
    """

    name = "결측치"

    def detect(self, context: DetectionContext) -> list[AnomalyFinding]:
        df = context.df
        findings: list[AnomalyFinding] = []

        for pos in range(len(df)):
            missing_columns: list[str] = []
            for col in df.columns:
                if self._is_missing(df.iloc[pos][col]):
                    missing_columns.append(str(col))
            if missing_columns:
                reason = f"결측치 [{', '.join(missing_columns)}]"
                findings.append(AnomalyFinding(row_index=pos, reason=reason))
        return findings

    @staticmethod
    def _is_missing(value: object) -> bool:
        """단일 값이 결측인지 판단한다."""
        # NaN / None / NaT
        if value is None:
            return True
        try:
            if pd.isna(value):
                return True
        except (ValueError, TypeError):
            # 배열류 등 isna 판단이 애매한 값은 결측이 아닌 것으로 처리
            return False
        # 빈 문자열 / 공백 문자열
        if isinstance(value, str) and value.strip() == "":
            return True
        return False
