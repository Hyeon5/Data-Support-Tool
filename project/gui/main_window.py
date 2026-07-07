"""메인 윈도우.

파일 선택, 분석 옵션, 알고리즘 파라미터, 숫자 컬럼 설정,
진행률 표시, 결과 저장 위치 선택 등 전체 GUI 를 구성한다.
"""

from __future__ import annotations

import os

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..config import Settings
from ..models import AnalysisConfig, NumericColumnConfig
from ..utils import ColumnAnalyzer, FileReader, FileReadError
from .numeric_config_widget import NumericConfigWidget
from .worker import AnalysisWorker


class MainWindow(QWidget):
    """애플리케이션 메인 윈도우."""

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__()
        self._settings = settings or Settings()
        self._reader = FileReader(self._settings)
        self._analyzer = ColumnAnalyzer(self._settings)

        # 상태
        self._df: pd.DataFrame | None = None
        self._numeric_configs: list[NumericColumnConfig] = []
        self._input_path: str = ""
        self._output_path: str = ""
        self._worker: AnalysisWorker | None = None

        self._build_ui()

    # ------------------------------------------------------------------
    # UI 구성
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self.setWindowTitle(f"{self._settings.APP_NAME} v{self._settings.APP_VERSION}")
        self.resize(880, 780)

        outer = QVBoxLayout(self)

        # 스크롤 영역(옵션이 많으므로)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        scroll.setWidget(container)
        outer.addWidget(scroll)

        layout = QVBoxLayout(container)
        layout.addWidget(self._build_file_group())
        layout.addWidget(self._build_options_group())
        layout.addWidget(self._build_params_group())
        layout.addWidget(self._build_numeric_group())
        layout.addWidget(self._build_output_group())
        layout.addStretch(1)

        # 하단 고정: 진행률 + 실행 버튼
        outer.addWidget(self._build_run_area())

    def _build_file_group(self) -> QGroupBox:
        group = QGroupBox("① 파일 선택 (xlsx / xls / csv)")
        layout = QHBoxLayout(group)
        self._file_path_edit = QLineEdit()
        self._file_path_edit.setReadOnly(True)
        self._file_path_edit.setPlaceholderText("분석할 파일을 선택하세요.")
        select_btn = QPushButton("파일 선택")
        select_btn.clicked.connect(self._on_select_file)
        layout.addWidget(self._file_path_edit)
        layout.addWidget(select_btn)
        return group

    def _build_options_group(self) -> QGroupBox:
        group = QGroupBox("② 분석 옵션")
        grid = QGridLayout(group)

        self._chk_missing = QCheckBox("결측치 탐지")
        self._chk_duplicate = QCheckBox("중복 데이터 탐지")
        self._chk_range = QCheckBox("범위 검사")
        self._chk_change_rate = QCheckBox("증감률 검사")
        self._chk_iqr = QCheckBox("IQR")
        self._chk_zscore = QCheckBox("Z-Score")
        self._chk_iso = QCheckBox("Isolation Forest")
        self._chk_lof = QCheckBox("Local Outlier Factor (LOF)")
        self._chk_dbscan = QCheckBox("DBSCAN")

        checkboxes = [
            self._chk_missing,
            self._chk_duplicate,
            self._chk_range,
            self._chk_change_rate,
            self._chk_iqr,
            self._chk_zscore,
            self._chk_iso,
            self._chk_lof,
            self._chk_dbscan,
        ]
        for chk in checkboxes:
            chk.setChecked(True)

        # 3열 배치
        for idx, chk in enumerate(checkboxes):
            grid.addWidget(chk, idx // 3, idx % 3)
        return group

    def _build_params_group(self) -> QGroupBox:
        group = QGroupBox("알고리즘 파라미터")
        form = QFormLayout(group)

        self._spin_change_rate = QDoubleSpinBox()
        self._spin_change_rate.setRange(0.0, 100000.0)
        self._spin_change_rate.setValue(self._settings.DEFAULT_CHANGE_RATE_THRESHOLD)
        self._spin_change_rate.setSuffix(" %")
        self._spin_change_rate.setDecimals(1)

        self._spin_zscore = QDoubleSpinBox()
        self._spin_zscore.setRange(0.1, 20.0)
        self._spin_zscore.setValue(self._settings.DEFAULT_ZSCORE_THRESHOLD)
        self._spin_zscore.setSingleStep(0.1)
        self._spin_zscore.setDecimals(2)

        self._spin_contamination = QDoubleSpinBox()
        self._spin_contamination.setRange(0.001, 0.5)
        self._spin_contamination.setValue(self._settings.DEFAULT_ISO_CONTAMINATION)
        self._spin_contamination.setSingleStep(0.01)
        self._spin_contamination.setDecimals(3)

        self._spin_lof_neighbors = QSpinBox()
        self._spin_lof_neighbors.setRange(1, 1000)
        self._spin_lof_neighbors.setValue(self._settings.DEFAULT_LOF_N_NEIGHBORS)

        self._spin_dbscan_eps = QDoubleSpinBox()
        self._spin_dbscan_eps.setRange(0.01, 1000.0)
        self._spin_dbscan_eps.setValue(self._settings.DEFAULT_DBSCAN_EPS)
        self._spin_dbscan_eps.setSingleStep(0.1)
        self._spin_dbscan_eps.setDecimals(2)

        self._spin_dbscan_min_samples = QSpinBox()
        self._spin_dbscan_min_samples.setRange(1, 1000)
        self._spin_dbscan_min_samples.setValue(self._settings.DEFAULT_DBSCAN_MIN_SAMPLES)

        form.addRow("증감률 임계치", self._spin_change_rate)
        form.addRow("Z-Score 임계치", self._spin_zscore)
        form.addRow("Isolation Forest contamination", self._spin_contamination)
        form.addRow("LOF n_neighbors", self._spin_lof_neighbors)
        form.addRow("DBSCAN eps", self._spin_dbscan_eps)
        form.addRow("DBSCAN min_samples", self._spin_dbscan_min_samples)
        return group

    def _build_numeric_group(self) -> QGroupBox:
        group = QGroupBox("숫자 컬럼 설정 (범위 검사)")
        layout = QVBoxLayout(group)
        info = QLabel(
            "파일을 읽으면 숫자 컬럼이 자동 추출됩니다. "
            "허용 최소/최대값을 수정하고 '사용'을 체크하세요."
        )
        info.setWordWrap(True)
        self._numeric_table = NumericConfigWidget()
        self._numeric_table.setMinimumHeight(180)
        layout.addWidget(info)
        layout.addWidget(self._numeric_table)
        return group

    def _build_output_group(self) -> QGroupBox:
        group = QGroupBox("⑤ 결과 저장 위치")
        layout = QHBoxLayout(group)
        self._output_path_edit = QLineEdit()
        self._output_path_edit.setReadOnly(True)
        self._output_path_edit.setPlaceholderText("결과 Excel 파일 저장 위치를 선택하세요.")
        output_btn = QPushButton("저장 위치 선택")
        output_btn.clicked.connect(self._on_select_output)
        layout.addWidget(self._output_path_edit)
        layout.addWidget(output_btn)
        return group

    def _build_run_area(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # ④ 진행률
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._status_label = QLabel("대기 중")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ③ 분석 시작
        self._run_btn = QPushButton("분석 시작")
        self._run_btn.setMinimumHeight(40)
        self._run_btn.clicked.connect(self._on_run)

        layout.addWidget(self._status_label)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._run_btn)
        return widget

    # ------------------------------------------------------------------
    # 이벤트 핸들러
    # ------------------------------------------------------------------
    def _on_select_file(self) -> None:
        """파일 선택 후 읽기 + 컬럼 분석 + 설정 테이블 갱신."""
        path, _ = QFileDialog.getOpenFileName(
            self, "데이터 파일 선택", "", self._settings.FILE_DIALOG_FILTER
        )
        if not path:
            return

        try:
            df = self._reader.read(path)
        except FileReadError as exc:
            self._show_error("파일 읽기 실패", str(exc))
            return

        self._df = df
        self._input_path = path
        self._file_path_edit.setText(path)

        # 컬럼 분석 및 숫자 설정 테이블 갱신
        column_infos = self._analyzer.analyze(df)
        self._numeric_configs = self._analyzer.build_numeric_configs(df, column_infos)
        self._numeric_table.load_configs(self._numeric_configs)

        # 기본 저장 경로 제안
        base = os.path.splitext(path)[0]
        self._suggest_output(f"{base}_result.xlsx")

        numeric_count = len(self._numeric_configs)
        self._set_status(
            f"파일 로드 완료: {df.shape[0]}행 × {df.shape[1]}열 "
            f"(숫자 컬럼 {numeric_count}개)"
        )

    def _on_select_output(self) -> None:
        """결과 저장 위치 선택."""
        default = self._output_path or "result.xlsx"
        path, _ = QFileDialog.getSaveFileName(
            self, "결과 저장 위치", default, "Excel 파일 (*.xlsx)"
        )
        if path:
            self._suggest_output(path)

    def _on_run(self) -> None:
        """분석 시작."""
        if self._df is None:
            self._show_error("파일 없음", "먼저 분석할 파일을 선택하세요.")
            return
        if not self._output_path:
            self._show_error("저장 위치 없음", "결과 저장 위치를 선택하세요.")
            return

        config = self._collect_config()

        # UI 잠금
        self._run_btn.setEnabled(False)
        self._progress_bar.setValue(0)

        self._worker = AnalysisWorker(self._df, config, self._output_path)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_progress(self, pct: int, msg: str) -> None:
        self._progress_bar.setValue(pct)
        self._set_status(msg)

    def _on_finished(self, result: object, saved_path: str) -> None:
        self._run_btn.setEnabled(True)
        self._progress_bar.setValue(100)
        total = getattr(result, "total_count", 0)
        anomaly = getattr(result, "anomaly_count", 0)
        self._set_status(f"완료: 전체 {total}행 중 이상 {anomaly}행")
        QMessageBox.information(
            self,
            "분석 완료",
            f"분석이 완료되었습니다.\n\n"
            f"전체 행: {total}\n이상 행: {anomaly}\n\n"
            f"저장 위치:\n{saved_path}",
        )

    def _on_failed(self, message: str) -> None:
        self._run_btn.setEnabled(True)
        self._set_status("분석 실패")
        self._show_error("분석 실패", message)

    # ------------------------------------------------------------------
    # 헬퍼
    # ------------------------------------------------------------------
    def _collect_config(self) -> AnalysisConfig:
        """현재 GUI 입력값으로 AnalysisConfig 를 구성한다."""
        numeric_configs = self._numeric_table.collect_configs(self._numeric_configs)
        return AnalysisConfig(
            check_missing=self._chk_missing.isChecked(),
            check_duplicate=self._chk_duplicate.isChecked(),
            check_range=self._chk_range.isChecked(),
            check_change_rate=self._chk_change_rate.isChecked(),
            check_iqr=self._chk_iqr.isChecked(),
            check_zscore=self._chk_zscore.isChecked(),
            check_isolation_forest=self._chk_iso.isChecked(),
            check_lof=self._chk_lof.isChecked(),
            check_dbscan=self._chk_dbscan.isChecked(),
            change_rate_threshold=self._spin_change_rate.value(),
            zscore_threshold=self._spin_zscore.value(),
            iso_contamination=self._spin_contamination.value(),
            lof_n_neighbors=self._spin_lof_neighbors.value(),
            dbscan_eps=self._spin_dbscan_eps.value(),
            dbscan_min_samples=self._spin_dbscan_min_samples.value(),
            numeric_configs=numeric_configs,
        )

    def _suggest_output(self, path: str) -> None:
        self._output_path = path
        self._output_path_edit.setText(path)

    def _set_status(self, message: str) -> None:
        self._status_label.setText(message)

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)
