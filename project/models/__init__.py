"""데이터 모델 패키지.

프로그램 전반에서 사용하는 값 객체(데이터 클래스)를 정의한다.
"""

from .column_info import ColumnInfo, ColumnType
from .numeric_config import NumericColumnConfig
from .analysis_config import AnalysisConfig
from .result import AnomalyFinding, AnalysisResult

__all__ = [
    "ColumnInfo",
    "ColumnType",
    "NumericColumnConfig",
    "AnalysisConfig",
    "AnomalyFinding",
    "AnalysisResult",
]
