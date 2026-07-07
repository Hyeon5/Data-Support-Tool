"""범위 검사 알고리즘."""

from __future__ import annotations

import pandas as pd

from ..models import AnomalyFinding
from .base import BaseDetector, DetectionContext
from .formatting import format_number


class RangeCheckDetector(BaseDetector):
    """사용자가 지정한 허용 최소/최대 범위를 벗어난 값을 탐지한다.

    숫자 컬럼 설정 화면에서 use=True 로 지정된 컬럼만 검사한다.
    사유 예) "범위 초과 [예산] (허용:0~1000000, 실제:1300000)"
    """

    name = "범위 초과"

    def detect(self, context: DetectionContext) -> list[AnomalyFinding]:
        findings: list[AnomalyFinding] = []
        enabled_configs = context.config.enabled_range_configs()
        if not enabled_configs:
            return findings

        for cfg in enabled_configs:
            if cfg.name not in context.numeric_frame.columns:
                continue
            series = context.numeric_frame[cfg.name]
            for pos, value in enumerate(series.tolist()):
                if pd.isna(value):
                    continue  # 결측치는 결측치 탐지에서 처리
                if value < cfg.allow_min or value > cfg.allow_max:
                    reason = (
                        f"범위 초과 [{cfg.name}] "
                        f"(허용:{format_number(cfg.allow_min)}~{format_number(cfg.allow_max)}, "
                        f"실제:{format_number(value)})"
                    )
                    findings.append(AnomalyFinding(row_index=pos, reason=reason))
        return findings
