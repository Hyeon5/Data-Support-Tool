"""Isolation Forest 기반 이상치 탐지 알고리즘."""

from __future__ import annotations

from sklearn.ensemble import IsolationForest

from ..models import AnomalyFinding
from .base import BaseDetector, DetectionContext
from .ml_base import build_feature_matrix


class IsolationForestDetector(BaseDetector):
    """sklearn 의 IsolationForest 로 이상치를 탐지한다.

    contamination(이상치 비율)을 GUI 에서 조절할 수 있다.
    숫자 컬럼 전체를 다변량 특징으로 사용한다.
    """

    name = "Isolation Forest"

    def detect(self, context: DetectionContext) -> list[AnomalyFinding]:
        features, valid_positions = build_feature_matrix(context, scale=True)
        if features.shape[0] < 2 or features.shape[1] == 0:
            return []

        contamination = context.config.iso_contamination
        model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
        )
        # -1: 이상치, 1: 정상
        predictions = model.fit_predict(features)

        findings: list[AnomalyFinding] = []
        for local_idx, pred in enumerate(predictions):
            if pred == -1:
                pos = valid_positions[local_idx]
                findings.append(
                    AnomalyFinding(row_index=pos, reason="Isolation Forest 이상")
                )
        return findings
