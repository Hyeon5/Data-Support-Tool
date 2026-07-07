"""이상치 탐지 알고리즘 패키지.

모든 알고리즘은 BaseDetector 공통 인터페이스를 따른다.
새 알고리즘을 추가하려면 BaseDetector 를 상속한 클래스를 만들고
아래 registry 에 등록하면 된다.
"""

from __future__ import annotations

from ..models import AnalysisConfig
from .base import BaseDetector, DetectionContext
from .missing import MissingValueDetector
from .duplicate import DuplicateRowDetector
from .range_check import RangeCheckDetector
from .change_rate import ChangeRateDetector
from .iqr import IQRDetector
from .zscore import ZScoreDetector
from .isolation_forest import IsolationForestDetector
from .lof import LOFDetector
from .dbscan import DBSCANDetector

__all__ = [
    "BaseDetector",
    "DetectionContext",
    "MissingValueDetector",
    "DuplicateRowDetector",
    "RangeCheckDetector",
    "ChangeRateDetector",
    "IQRDetector",
    "ZScoreDetector",
    "IsolationForestDetector",
    "LOFDetector",
    "DBSCANDetector",
    "build_active_detectors",
]


def build_active_detectors(config: AnalysisConfig) -> list[BaseDetector]:
    """설정에서 활성화된 알고리즘만 골라 인스턴스 목록을 반환한다.

    (활성화 플래그, detector 클래스) 매핑을 순서대로 확인한다.
    이 순서가 사유 문자열의 나열 순서가 된다.
    """
    registry: list[tuple[bool, type[BaseDetector]]] = [
        (config.check_missing, MissingValueDetector),
        (config.check_duplicate, DuplicateRowDetector),
        (config.check_range, RangeCheckDetector),
        (config.check_change_rate, ChangeRateDetector),
        (config.check_iqr, IQRDetector),
        (config.check_zscore, ZScoreDetector),
        (config.check_isolation_forest, IsolationForestDetector),
        (config.check_lof, LOFDetector),
        (config.check_dbscan, DBSCANDetector),
    ]
    return [cls() for enabled, cls in registry if enabled]
