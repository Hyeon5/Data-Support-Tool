"""이상치 탐지 알고리즘 공통 인터페이스.

모든 알고리즘은 BaseDetector 를 상속하여 detect() 를 구현한다.
공통 인터페이스를 사용하므로 향후 새 알고리즘을 쉽게 추가할 수 있다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from ..models import AnalysisConfig, AnomalyFinding


@dataclass
class DetectionContext:
    """detector 실행에 필요한 입력 데이터 묶음.

    Attributes:
        df: 원본 DataFrame.
        numeric_columns: 숫자 컬럼명 목록.
        numeric_frame: 숫자 컬럼만 숫자형으로 변환한 DataFrame
            (문자열 등은 NaN 으로 처리됨). ML/통계 알고리즘 공용.
        config: 분석 설정.
    """

    df: pd.DataFrame
    numeric_columns: list[str]
    numeric_frame: pd.DataFrame
    config: AnalysisConfig


class BaseDetector(ABC):
    """이상치 탐지 알고리즘의 추상 기반 클래스."""

    #: 사람이 읽을 수 있는 알고리즘 이름(로그/표시용).
    name: str = "Base"

    @abstractmethod
    def detect(self, context: DetectionContext) -> list[AnomalyFinding]:
        """이상치를 탐지하여 결과 목록을 반환한다.

        Args:
            context: 탐지에 필요한 데이터/설정.

        Returns:
            AnomalyFinding 목록. 각 항목은 (행 위치, 사유) 를 담는다.
            이상이 없으면 빈 목록을 반환한다.
        """
        raise NotImplementedError
