"""분석 작업을 백그라운드에서 실행하는 QThread 워커.

GUI 가 멈추지 않도록 분석/저장을 별도 스레드에서 수행하고,
진행률·완료·오류를 시그널로 통지한다.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QThread, Signal

from ..export import ExcelExporter
from ..models import AnalysisConfig, AnalysisResult
from ..services import AnalysisService


class AnalysisWorker(QThread):
    """분석 실행 + Excel 저장을 담당하는 워커 스레드."""

    #: (진행률 0~100, 상태 메시지)
    progress = Signal(int, str)
    #: (분석 결과, 저장된 파일 경로)
    finished_ok = Signal(object, str)
    #: 오류 메시지
    failed = Signal(str)

    def __init__(
        self,
        df: pd.DataFrame,
        config: AnalysisConfig,
        output_path: str,
        service: AnalysisService | None = None,
        exporter: ExcelExporter | None = None,
    ) -> None:
        super().__init__()
        self._df = df
        self._config = config
        self._output_path = output_path
        self._service = service or AnalysisService()
        self._exporter = exporter or ExcelExporter()

    def run(self) -> None:  # noqa: D401 - QThread 진입점
        """스레드 본체. 분석 후 결과를 저장한다."""
        try:
            result: AnalysisResult = self._service.analyze(
                self._df,
                self._config,
                progress_callback=self._on_progress,
            )
            self.progress.emit(100, "결과 저장 중...")
            saved_path = self._exporter.export(result, self._output_path)
            self.finished_ok.emit(result, saved_path)
        except Exception as exc:  # noqa: BLE001 - GUI 로 오류 전달
            self.failed.emit(str(exc))

    def _on_progress(self, pct: int, msg: str) -> None:
        """서비스 진행률 콜백을 시그널로 중계한다."""
        self.progress.emit(pct, msg)
