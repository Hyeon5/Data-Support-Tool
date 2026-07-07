"""중복 데이터 탐지 알고리즘."""

from __future__ import annotations

from ..models import AnomalyFinding
from .base import BaseDetector, DetectionContext


class DuplicateRowDetector(BaseDetector):
    """중복 행을 탐지한다.

    "모든 컬럼 값이 동일한 행"만 중복으로 판단한다.
    중복 그룹에 속한 모든 행(첫 행 포함)을 이상으로 표시한다.
    """

    name = "중복 데이터"

    def detect(self, context: DetectionContext) -> list[AnomalyFinding]:
        df = context.df
        # keep=False 로 두면 중복 그룹의 모든 행이 True 가 된다.
        duplicated_mask = df.duplicated(keep=False)
        findings: list[AnomalyFinding] = []
        for pos, is_dup in enumerate(duplicated_mask.tolist()):
            if is_dup:
                findings.append(AnomalyFinding(row_index=pos, reason="중복 데이터"))
        return findings
