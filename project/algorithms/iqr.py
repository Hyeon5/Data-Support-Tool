"""IQR(사분위 범위) 기반 이상치 탐지 알고리즘."""

from __future__ import annotations

from ..models import AnomalyFinding
from .base import BaseDetector, DetectionContext


class IQRDetector(BaseDetector):
    """IQR 기반으로 이상치를 탐지한다.

    각 숫자 컬럼에 대해:
        Q1 = 25 백분위수
        Q3 = 75 백분위수
        IQR = Q3 - Q1
        허용 범위 = [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
    허용 범위를 벗어난 값을 이상으로 판정한다.
    """

    name = "IQR"

    def detect(self, context: DetectionContext) -> list[AnomalyFinding]:
        findings: list[AnomalyFinding] = []

        for col in context.numeric_columns:
            series = context.numeric_frame[col].dropna()
            if len(series) < 4:
                # 표본이 너무 적으면 사분위 계산이 무의미하므로 건너뛴다.
                continue
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0:
                # 값이 거의 일정하면 이상치 판정이 무의미하다.
                continue
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            full = context.numeric_frame[col]
            for pos, value in enumerate(full.tolist()):
                if value != value:  # NaN 체크
                    continue
                if value < lower or value > upper:
                    findings.append(
                        AnomalyFinding(row_index=pos, reason=f"IQR 이상 [{col}]")
                    )
        return findings
