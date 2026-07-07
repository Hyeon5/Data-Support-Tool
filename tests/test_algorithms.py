"""알고리즘 및 파이프라인 단위 테스트.

실행:
    python -m unittest discover -s tests
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd

from project.algorithms import (
    ChangeRateDetector,
    DBSCANDetector,
    DetectionContext,
    DuplicateRowDetector,
    IQRDetector,
    IsolationForestDetector,
    LOFDetector,
    MissingValueDetector,
    RangeCheckDetector,
    ZScoreDetector,
)
from project.models import AnalysisConfig, NumericColumnConfig
from project.services import AnalysisService
from project.utils import ColumnAnalyzer


def _make_context(df: pd.DataFrame, config: AnalysisConfig) -> DetectionContext:
    analyzer = ColumnAnalyzer()
    infos = analyzer.analyze(df)
    numeric_cols = analyzer.numeric_column_names(infos)
    numeric_frame = pd.DataFrame(
        {c: pd.to_numeric(df[c], errors="coerce") for c in numeric_cols},
        index=df.index,
    )
    return DetectionContext(df, numeric_cols, numeric_frame, config)


def _rows(findings) -> set[int]:
    return {f.row_index for f in findings}


class TestRuleBasedDetectors(unittest.TestCase):
    def test_missing_detects_nan_empty_and_whitespace(self) -> None:
        df = pd.DataFrame({"a": [1, np.nan, 3], "b": ["x", "", "  "]})
        ctx = _make_context(df, AnalysisConfig())
        found = _rows(MissingValueDetector().detect(ctx))
        self.assertEqual(found, {1, 2})

    def test_duplicate_full_row_only(self) -> None:
        df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "x"]})
        # 행0, 행1 은 모든 값이 동일 -> 중복. 행2 는 다름.
        ctx = _make_context(df, AnalysisConfig())
        found = _rows(DuplicateRowDetector().detect(ctx))
        self.assertEqual(found, {0, 1})

    def test_range_check(self) -> None:
        df = pd.DataFrame({"score": [10, 50, 130]})
        cfg = AnalysisConfig(
            numeric_configs=[NumericColumnConfig("score", 10, 130, 0, 100, True)]
        )
        ctx = _make_context(df, cfg)
        findings = RangeCheckDetector().detect(ctx)
        self.assertEqual(_rows(findings), {2})
        self.assertIn("범위 초과", findings[0].reason)
        self.assertIn("실제:130", findings[0].reason)

    def test_range_check_disabled(self) -> None:
        df = pd.DataFrame({"score": [10, 50, 130]})
        cfg = AnalysisConfig(
            numeric_configs=[NumericColumnConfig("score", 10, 130, 0, 100, False)]
        )
        ctx = _make_context(df, cfg)
        self.assertEqual(RangeCheckDetector().detect(ctx), [])

    def test_change_rate(self) -> None:
        # 100 -> 100 -> 400: 마지막에서 +300%
        df = pd.DataFrame({"v": [100.0, 100.0, 400.0]})
        cfg = AnalysisConfig(change_rate_threshold=100.0)
        ctx = _make_context(df, cfg)
        findings = ChangeRateDetector().detect(ctx)
        self.assertEqual(_rows(findings), {2})
        self.assertIn("+300%", findings[0].reason)


class TestStatisticalDetectors(unittest.TestCase):
    def test_iqr_extreme(self) -> None:
        df = pd.DataFrame({"v": [10, 11, 12, 13, 12, 11, 10, 500]})
        ctx = _make_context(df, AnalysisConfig())
        found = _rows(IQRDetector().detect(ctx))
        self.assertIn(7, found)

    def test_zscore_extreme(self) -> None:
        values = [10.0] * 20 + [1000.0]
        df = pd.DataFrame({"v": values})
        ctx = _make_context(df, AnalysisConfig(zscore_threshold=3.0))
        findings = ZScoreDetector().detect(ctx)
        self.assertIn(20, _rows(findings))
        self.assertTrue(any("Z=" in f.reason for f in findings))


class TestMLDetectors(unittest.TestCase):
    def _blob_with_outlier(self) -> pd.DataFrame:
        rng = np.random.RandomState(1)
        base = rng.normal(0, 1, size=(50, 2))
        outlier = np.array([[50.0, 50.0]])
        data = np.vstack([base, outlier])
        return pd.DataFrame({"x": data[:, 0], "y": data[:, 1]})

    def test_isolation_forest(self) -> None:
        df = self._blob_with_outlier()
        ctx = _make_context(df, AnalysisConfig(iso_contamination=0.05))
        found = _rows(IsolationForestDetector().detect(ctx))
        self.assertIn(50, found)

    def test_lof(self) -> None:
        df = self._blob_with_outlier()
        ctx = _make_context(df, AnalysisConfig(lof_n_neighbors=20))
        found = _rows(LOFDetector().detect(ctx))
        self.assertIn(50, found)

    def test_dbscan(self) -> None:
        df = self._blob_with_outlier()
        ctx = _make_context(df, AnalysisConfig(dbscan_eps=0.8, dbscan_min_samples=5))
        found = _rows(DBSCANDetector().detect(ctx))
        self.assertIn(50, found)


class TestPipeline(unittest.TestCase):
    def test_multiple_reasons_joined(self) -> None:
        # 한 행이 여러 알고리즘에 걸리는 경우 사유가 쉼표로 연결되는지 확인.
        # 정상 값은 약간의 변동을 주어 통계/ML 알고리즘이 정상적으로 동작하게 한다.
        rng = np.random.RandomState(7)
        values = list(rng.uniform(40, 60, size=30)) + [100000.0]
        df = pd.DataFrame({"v": values})
        cfg = AnalysisConfig(
            numeric_configs=[NumericColumnConfig("v", 40, 100000, 0, 100, True)]
        )
        result = AnalysisService().analyze(df, cfg)
        last = len(values) - 1
        self.assertEqual(result.anomaly_flags[last], "이상")
        reason = result.anomaly_reasons[last]
        # 범위 초과 + IQR + Z-Score + 증감률 등 복수 사유가 쉼표로 연결됨
        self.assertIn(",", reason)
        self.assertIn("범위 초과", reason)

    def test_disabled_algorithms_skipped(self) -> None:
        df = pd.DataFrame({"a": [1, np.nan, 3]})
        cfg = AnalysisConfig(
            check_missing=False,
            check_duplicate=False,
            check_range=False,
            check_change_rate=False,
            check_iqr=False,
            check_zscore=False,
            check_isolation_forest=False,
            check_lof=False,
            check_dbscan=False,
        )
        result = AnalysisService().analyze(df, cfg)
        self.assertEqual(result.anomaly_count, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
