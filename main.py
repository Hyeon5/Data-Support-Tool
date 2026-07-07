"""AI 기반 데이터 이상치 탐지 프로그램 진입점.

실행:
    python main.py
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from project.config import Settings
from project.gui import MainWindow


def main() -> int:
    """애플리케이션을 실행한다."""
    app = QApplication(sys.argv)
    app.setApplicationName(Settings.APP_NAME)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
