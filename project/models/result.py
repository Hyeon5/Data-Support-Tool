"""분석 결과 모델."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class AnomalyFinding:
    """단일 이상치 탐지 결과(한 행 × 한 알고리즘).

    Attributes:
        row_index: 원본 DataFrame 상의 행 위치(0-based positional index).
        reason: 이상치 사유 문자열. 예) "IQR 이상", "Z-Score 이상 (Z=4.27)".
    """

    row_index: int
    reason: str


@dataclass
class AnalysisResult:
    """전체 분석 결과.

    Attributes:
        data: 원본 데이터(변형 없이 유지).
        anomaly_flags: 행별 이상 여부 리스트("이상" 또는 "").
        anomaly_reasons: 행별 이상 사유 리스트(정상이면 "").
    """

    data: pd.DataFrame
    anomaly_flags: list[str] = field(default_factory=list)
    anomaly_reasons: list[str] = field(default_factory=list)

    @property
    def anomaly_count(self) -> int:
        """이상으로 판정된 행 개수."""
        return sum(1 for f in self.anomaly_flags if f)

    @property
    def total_count(self) -> int:
        """전체 행 개수."""
        return len(self.data)
