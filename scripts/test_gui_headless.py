"""오프스크린 모드로 GUI 구성 및 워커 동작을 검증한다."""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication  # noqa: E402

from project.gui import MainWindow  # noqa: E402
from project.gui.worker import AnalysisWorker  # noqa: E402
from project.models import AnalysisConfig  # noqa: E402
from project.utils import ColumnAnalyzer, FileReader  # noqa: E402


def main() -> None:
    app = QApplication(sys.argv)

    # 1) 메인 윈도우 구성 검증
    window = MainWindow()
    window.show()
    print("[OK] MainWindow 구성 성공")

    # 2) 파일 로드 로직 직접 호출 검증
    sample = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample.xlsx")
    )
    df = FileReader().read(sample)
    infos = ColumnAnalyzer().analyze(df)
    configs = ColumnAnalyzer().build_numeric_configs(df, infos)
    window._df = df
    window._numeric_configs = configs
    window._numeric_table.load_configs(configs)
    print(f"[OK] 숫자 설정 테이블 로드: {window._numeric_table.rowCount()}행")

    collected = window._numeric_table.collect_configs(configs)
    print(f"[OK] 설정 수집: {[c.name for c in collected]}")

    # 3) 워커 동기 실행 검증(run() 직접 호출)
    out = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "sample_data", "gui_result.xlsx")
    )
    results = {}

    worker = AnalysisWorker(df, AnalysisConfig(numeric_configs=configs), out)
    worker.progress.connect(lambda p, m: None)
    worker.finished_ok.connect(lambda r, p: results.update({"result": r, "path": p}))
    worker.failed.connect(lambda m: results.update({"error": m}))
    worker.run()  # 스레드 없이 동기 실행

    if "error" in results:
        print(f"[FAIL] 워커 오류: {results['error']}")
        sys.exit(1)
    r = results["result"]
    print(f"[OK] 워커 완료: 전체 {r.total_count}행, 이상 {r.anomaly_count}행 -> {results['path']}")
    assert os.path.exists(results["path"]), "결과 파일이 생성되지 않음"
    print("[OK] 모든 GUI 헤드리스 검증 통과")


if __name__ == "__main__":
    main()
