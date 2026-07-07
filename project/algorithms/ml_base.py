"""머신러닝 기반 탐지기 공통 헬퍼.

Isolation Forest / LOF / DBSCAN 은 모두 숫자 컬럼을 특징(feature)으로 사용하는
다변량 알고리즘이다. 결측치가 있는 행은 학습/예측에서 제외하고,
결과를 원본 행 위치로 되돌리는 로직을 공통으로 제공한다.
"""

from __future__ import annotations

import numpy as np
from sklearn.preprocessing import StandardScaler

from .base import DetectionContext


def build_feature_matrix(
    context: DetectionContext, scale: bool = True
) -> tuple[np.ndarray, list[int]]:
    """숫자 컬럼으로 특징 행렬을 구성한다.

    결측치(NaN)가 하나라도 있는 행은 제외한다.

    Args:
        context: 탐지 컨텍스트.
        scale: True 이면 StandardScaler 로 표준화한다(거리 기반 알고리즘용).

    Returns:
        (features, valid_positions) 튜플.
        - features: (n_valid, n_features) 형태의 float 배열.
        - valid_positions: features 각 행이 대응하는 원본 행 위치 리스트.
    """
    if not context.numeric_columns:
        return np.empty((0, 0)), []

    frame = context.numeric_frame[context.numeric_columns]
    # 결측이 없는 행만 유지
    mask = frame.notna().all(axis=1)
    valid_positions = [i for i, ok in enumerate(mask.tolist()) if ok]
    if not valid_positions:
        return np.empty((0, len(context.numeric_columns))), []

    features = frame.loc[mask].to_numpy(dtype=float)
    if scale and features.shape[0] > 0:
        features = StandardScaler().fit_transform(features)
    return features, valid_positions
