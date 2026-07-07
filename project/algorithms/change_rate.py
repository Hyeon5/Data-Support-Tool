"""증감률 검사 알고리즘."""

from __future__ import annotations

import pandas as pd

from ..models import AnomalyFinding
from .base import BaseDetector, DetectionContext
from .formatting import format_number


class ChangeRateDetector(BaseDetector):
    """이전 행 대비 증감률이 임계치를 초과하는 값을 탐지한다.

    숫자 컬럼에 대해 (현재값 - 이전값) / |이전값| * 100 을 계산한다.
    절대값이 임계치(%)를 초과하면 이상으로 판정한다.
    사유 예) "증감률 이상 [예산] (+230%)"
    """

    name = "증감률 이상"

    def detect(self, context: DetectionContext) -> list[AnomalyFinding]:
        findings: list[AnomalyFinding] = []
        threshold = context.config.change_rate_threshold

        for col in context.numeric_columns:
            series = context.numeric_frame[col]
            values = series.tolist()
            prev = None
            for pos, current in enumerate(values):
                if pd.isna(current):
                    # 결측이면 기준점을 리셋한다(연속성 끊김).
                    prev = None
                    continue
                if prev is not None and prev != 0:
                    change = (current - prev) / abs(prev) * 100.0
                    if abs(change) > threshold:
                        sign = "+" if change >= 0 else "-"
                        reason = (
                            f"증감률 이상 [{col}] "
                            f"({sign}{format_number(abs(change))}%)"
                        )
                        findings.append(AnomalyFinding(row_index=pos, reason=reason))
                prev = current
        return findings
