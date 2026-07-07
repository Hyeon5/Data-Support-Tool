"""Local Outlier Factor(LOF) 기반 이상치 탐지 알고리즘."""

from __future__ import annotations

from sklearn.neighbors import LocalOutlierFactor

from ..models import AnomalyFinding
from .base import BaseDetector, DetectionContext
from .ml_base import build_feature_matrix


class LOFDetector(BaseDetector):
    """sklearn 의 LocalOutlierFactor 로 이상치를 탐지한다.

    n_neighbors(이웃 수)를 GUI 에서 조절할 수 있다.
    거리 기반 알고리즘이므로 특징을 표준화하여 사용한다.
    """

    name = "LOF"

    def detect(self, context: DetectionContext) -> list[AnomalyFinding]:
        features, valid_positions = build_feature_matrix(context, scale=True)
        n_samples = features.shape[0]
        if n_samples < 2 or features.shape[1] == 0:
            return []

        # n_neighbors 는 표본 수보다 작아야 한다.
        n_neighbors = min(context.config.lof_n_neighbors, n_samples - 1)
        if n_neighbors < 1:
            return []

        model = LocalOutlierFactor(n_neighbors=n_neighbors)
        # -1: 이상치, 1: 정상
        predictions = model.fit_predict(features)

        findings: list[AnomalyFinding] = []
        for local_idx, pred in enumerate(predictions):
            if pred == -1:
                pos = valid_positions[local_idx]
                findings.append(AnomalyFinding(row_index=pos, reason="LOF 이상"))
        return findings
