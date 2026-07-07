"""분석 오케스트레이션 서비스.

파일 읽기 -> 컬럼 분석 -> 활성 알고리즘 실행 -> 결과 집계까지의
전체 흐름을 담당한다. GUI 와 알고리즘 사이를 연결하는 계층이다.
"""

from __future__ import annotations

from typing import Callable

import pandas as pd

from ..algorithms import DetectionContext, build_active_detectors
from ..models import AnalysisConfig, AnalysisResult
from ..utils import ColumnAnalyzer

# 진행률 콜백 시그니처: (진행률 0~100, 상태 메시지)
ProgressCallback = Callable[[int, str], None]


class AnalysisService:
    """이상치 분석 전체 과정을 조율하는 서비스."""

    def __init__(self, column_analyzer: ColumnAnalyzer | None = None) -> None:
        self._column_analyzer = column_analyzer or ColumnAnalyzer()

    def analyze(
        self,
        df: pd.DataFrame,
        config: AnalysisConfig,
        progress_callback: ProgressCallback | None = None,
    ) -> AnalysisResult:
        """DataFrame 에 대해 활성화된 알고리즘을 실행하고 결과를 집계한다.

        Args:
            df: 원본 데이터.
            config: 분석 설정.
            progress_callback: 진행률 보고 콜백(선택).

        Returns:
            집계된 AnalysisResult.
        """

        def report(pct: int, msg: str) -> None:
            if progress_callback is not None:
                progress_callback(pct, msg)

        report(0, "컬럼 타입 분석 중...")

        # 1) 컬럼 타입 분석 및 숫자 프레임 구성
        column_infos = self._column_analyzer.analyze(df)
        numeric_columns = self._column_analyzer.numeric_column_names(column_infos)
        numeric_frame = self._build_numeric_frame(df, numeric_columns)

        context = DetectionContext(
            df=df,
            numeric_columns=numeric_columns,
            numeric_frame=numeric_frame,
            config=config,
        )

        # 2) 활성화된 detector 실행
        detectors = build_active_detectors(config)
        # 행 위치 -> 사유 리스트
        reasons_by_row: dict[int, list[str]] = {}

        total = max(len(detectors), 1)
        for idx, detector in enumerate(detectors):
            report(
                int((idx / total) * 90) + 5,
                f"{detector.name} 분석 중...",
            )
            try:
                findings = detector.detect(context)
            except Exception as exc:  # noqa: BLE001 - 한 알고리즘 실패가 전체를 막지 않도록
                # 실패한 알고리즘은 건너뛰고 계속 진행한다.
                report(
                    int((idx / total) * 90) + 5,
                    f"{detector.name} 분석 실패(건너뜀): {exc}",
                )
                continue
            for finding in findings:
                reasons_by_row.setdefault(finding.row_index, []).append(finding.reason)

        report(95, "결과 집계 중...")

        # 3) 결과 집계
        flags: list[str] = []
        reasons: list[str] = []
        for pos in range(len(df)):
            row_reasons = reasons_by_row.get(pos)
            if row_reasons:
                flags.append("이상")
                # 복수 탐지 시 쉼표로 연결
                reasons.append(", ".join(row_reasons))
            else:
                flags.append("")
                reasons.append("")

        report(100, "분석 완료")
        return AnalysisResult(data=df, anomaly_flags=flags, anomaly_reasons=reasons)

    @staticmethod
    def _build_numeric_frame(df: pd.DataFrame, numeric_columns: list[str]) -> pd.DataFrame:
        """숫자 컬럼을 숫자형으로 변환한 프레임을 만든다.

        변환 불가한 값은 NaN 이 된다. 인덱스는 원본과 동일하게 유지한다.
        """
        data = {col: pd.to_numeric(df[col], errors="coerce") for col in numeric_columns}
        return pd.DataFrame(data, index=df.index)
