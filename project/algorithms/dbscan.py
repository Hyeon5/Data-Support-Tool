"""DBSCAN 기반 이상치(노이즈) 탐지 알고리즘."""

from __future__ import annotations

from sklearn.cluster import DBSCAN

from ..models import AnomalyFinding
from .base import BaseDetector, DetectionContext
from .ml_base import build_feature_matrix


class DBSCANDetector(BaseDetector):
    """sklearn 의 DBSCAN 으로 노이즈(이상치)를 탐지한다.

    eps, min_samples 를 GUI 에서 조절할 수 있다.
    어떤 군집에도 속하지 못한 노이즈 포인트(label == -1)를 이상으로 판정한다.
    거리 기반 알고리즘이므로 특징을 표준화하여 사용한다.
    """

    name = "DBSCAN"

    def detect(self, context: DetectionContext) -> list[AnomalyFinding]:
        features, valid_positions = build_feature_matrix(context, scale=True)
        if features.shape[0] < 1 or features.shape[1] == 0:
            return []

        model = DBSCAN(
            eps=context.config.dbscan_eps,
            min_samples=context.config.dbscan_min_samples,
        )
        labels = model.fit_predict(features)

        findings: list[AnomalyFinding] = []
        for local_idx, label in enumerate(labels):
            if label == -1:  # 노이즈
                pos = valid_positions[local_idx]
                findings.append(AnomalyFinding(row_index=pos, reason="DBSCAN 이상"))
        return findings
