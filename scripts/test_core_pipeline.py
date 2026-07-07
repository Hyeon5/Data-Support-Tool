"""GUI 없이 핵심 파이프라인을 검증하는 스크립트."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from project.export import ExcelExporter
from project.models import AnalysisConfig
from project.services import AnalysisService
from project.utils import ColumnAnalyzer, FileReader


def main() -> None:
    sample = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample.csv")
    )

    reader = FileReader()
    df = reader.read(sample)
    print(f"[읽기] shape={df.shape}")

    analyzer = ColumnAnalyzer()
    infos = analyzer.analyze(df)
    print("[컬럼 타입]")
    for info in infos:
        print(f"  - {info.name}: {info.col_type}")

    numeric_configs = analyzer.build_numeric_configs(df, infos)
    print("[숫자 컬럼 설정]")
    for cfg in numeric_configs:
        print(
            f"  - {cfg.name}: 실제[{cfg.actual_min}, {cfg.actual_max}] "
            f"허용[{cfg.allow_min}, {cfg.allow_max}]"
        )

    # 수행률 허용 범위를 0~100 으로 조정하여 범위 초과 유도
    for cfg in numeric_configs:
        if cfg.name == "수행률":
            cfg.allow_min, cfg.allow_max = 0.0, 100.0

    config = AnalysisConfig(numeric_configs=numeric_configs)

    def progress(pct: int, msg: str) -> None:
        print(f"  [{pct:3d}%] {msg}")

    service = AnalysisService(column_analyzer=analyzer)
    result = service.analyze(df, config, progress_callback=progress)

    print(f"\n[결과] 전체 {result.total_count}행, 이상 {result.anomaly_count}행")
    print("[이상 행 상세]")
    for pos, (flag, reason) in enumerate(
        zip(result.anomaly_flags, result.anomaly_reasons)
    ):
        if flag:
            print(f"  행{pos}: {reason}")

    out = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "sample_data", "result.xlsx")
    )
    saved = ExcelExporter().export(result, out)
    print(f"\n[저장] {saved}")


if __name__ == "__main__":
    main()
