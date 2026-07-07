"""Z-Score 기반 이상치 탐지 알고리즘."""

from __future__ import annotations

import numpy as np

from ..models import AnomalyFinding
from .base import BaseDetector, DetectionContext
from .formatting import format_number


class ZScoreDetector(BaseDetector):
    """Z-Score 기반으로 이상치를 탐지한다.

    각 숫자 컬럼에 대해 z = (x - mean) / std 를 계산하고,
    |z| 가 임계치(기본 3.0)를 초과하면 이상으로 판정한다.
    사유 예) "Z-Score 이상 [예산] (Z=4.27)"
    """

    name = "Z-Score"

    def detect(self, context: DetectionContext) -> list[AnomalyFinding]:
        findings: list[AnomalyFinding] = []
        threshold = context.config.zscore_threshold

        for col in context.numeric_columns:
            series = context.numeric_frame[col]
            valid = series.dropna()
            if len(valid) < 2:
                continue
            mean = valid.mean()
            std = valid.std(ddof=0)  # 모표준편차
            if std == 0 or np.isnan(std):
                continue

            for pos, value in enumerate(series.tolist()):
                if value != value:  # NaN
                    continue
                z = (value - mean) / std
                if abs(z) > threshold:
                    reason = f"Z-Score 이상 [{col}] (Z={format_number(round(abs(z), 2))})"
                    findings.append(AnomalyFinding(row_index=pos, reason=reason))
        return findings
