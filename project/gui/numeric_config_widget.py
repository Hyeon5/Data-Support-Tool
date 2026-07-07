"""숫자 컬럼 범위 설정 테이블 위젯.

파일을 읽은 뒤 숫자 컬럼만 추출하여 설정 테이블을 보여준다.
사용자는 허용 최소/최대값을 수정하고, 체크박스로 검사 여부를 선택한다.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from ..models import NumericColumnConfig

# 컬럼 인덱스 상수
_COL_NAME = 0
_COL_ACTUAL_MIN = 1
_COL_ACTUAL_MAX = 2
_COL_ALLOW_MIN = 3
_COL_ALLOW_MAX = 4
_COL_USE = 5


class NumericConfigWidget(QTableWidget):
    """숫자 컬럼 설정 테이블.

    열: 컬럼명 | 실제 최소 | 실제 최대 | 허용 최소 | 허용 최대 | 사용
    허용 최소/최대 및 사용 체크박스만 편집 가능하다.
    """

    _HEADERS = ["컬럼명", "실제 최소", "실제 최대", "허용 최소", "허용 최대", "사용"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._checkboxes: list[QCheckBox] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setColumnCount(len(self._HEADERS))
        self.setHorizontalHeaderLabels(self._HEADERS)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
        )
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        header = self.horizontalHeader()
        header.setSectionResizeMode(_COL_NAME, QHeaderView.ResizeMode.Stretch)
        for col in (_COL_ACTUAL_MIN, _COL_ACTUAL_MAX, _COL_ALLOW_MIN, _COL_ALLOW_MAX):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(_COL_USE, QHeaderView.ResizeMode.ResizeToContents)

    def load_configs(self, configs: list[NumericColumnConfig]) -> None:
        """설정 목록으로 테이블을 채운다."""
        self.setRowCount(0)
        self._checkboxes.clear()
        self.setRowCount(len(configs))

        for row, cfg in enumerate(configs):
            # 컬럼명(읽기 전용)
            name_item = QTableWidgetItem(cfg.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, _COL_NAME, name_item)

            # 실제 최소/최대(읽기 전용)
            actual_min_item = self._readonly_item(self._fmt(cfg.actual_min))
            actual_max_item = self._readonly_item(self._fmt(cfg.actual_max))
            self.setItem(row, _COL_ACTUAL_MIN, actual_min_item)
            self.setItem(row, _COL_ACTUAL_MAX, actual_max_item)

            # 허용 최소/최대(편집 가능)
            self.setItem(row, _COL_ALLOW_MIN, QTableWidgetItem(self._fmt(cfg.allow_min)))
            self.setItem(row, _COL_ALLOW_MAX, QTableWidgetItem(self._fmt(cfg.allow_max)))

            # 사용 체크박스(가운데 정렬을 위해 래퍼 위젯 사용)
            checkbox = QCheckBox()
            checkbox.setChecked(cfg.use)
            self._checkboxes.append(checkbox)
            wrapper = QWidget()
            layout = QHBoxLayout(wrapper)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            self.setCellWidget(row, _COL_USE, wrapper)

    def collect_configs(self, base_configs: list[NumericColumnConfig]) -> list[NumericColumnConfig]:
        """테이블의 현재 입력값을 반영한 설정 목록을 반환한다.

        base_configs 의 순서/개수와 테이블 행이 일치한다고 가정한다.
        허용 최소/최대 파싱 실패 시 기존 값을 유지한다.
        """
        updated: list[NumericColumnConfig] = []
        for row, cfg in enumerate(base_configs):
            allow_min = self._parse_cell(row, _COL_ALLOW_MIN, cfg.allow_min)
            allow_max = self._parse_cell(row, _COL_ALLOW_MAX, cfg.allow_max)
            # 최소 > 최대 인 경우 자동으로 교정
            if allow_min > allow_max:
                allow_min, allow_max = allow_max, allow_min
            use = self._checkboxes[row].isChecked() if row < len(self._checkboxes) else cfg.use
            updated.append(
                NumericColumnConfig(
                    name=cfg.name,
                    actual_min=cfg.actual_min,
                    actual_max=cfg.actual_max,
                    allow_min=allow_min,
                    allow_max=allow_max,
                    use=use,
                )
            )
        return updated

    def clear_configs(self) -> None:
        """테이블을 비운다."""
        self.setRowCount(0)
        self._checkboxes.clear()

    # --- 내부 헬퍼 ---
    def _parse_cell(self, row: int, col: int, default: float) -> float:
        item = self.item(row, col)
        if item is None:
            return default
        try:
            return float(item.text().replace(",", "").strip())
        except (ValueError, AttributeError):
            return default

    @staticmethod
    def _readonly_item(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    @staticmethod
    def _fmt(value: float) -> str:
        """숫자를 표시용 문자열로 변환(정수는 소수점 제거)."""
        if value == int(value):
            return str(int(value))
        return f"{value:.4f}".rstrip("0").rstrip(".")
