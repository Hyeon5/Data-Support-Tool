"""컬럼 타입 정보 모델."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ColumnType(str, Enum):
    """자동 분석으로 판별한 컬럼의 데이터 타입."""

    NUMBER = "Number"
    STRING = "String"
    DATE = "Date"

    def __str__(self) -> str:  # noqa: D401 - 표시용 문자열
        return self.value


@dataclass
class ColumnInfo:
    """단일 컬럼에 대한 자동 분석 결과.

    Attributes:
        name: 컬럼명.
        col_type: 자동 판별된 컬럼 타입(숫자/문자열/날짜).
    """

    name: str
    col_type: ColumnType

    @property
    def is_numeric(self) -> bool:
        """숫자 컬럼 여부."""
        return self.col_type == ColumnType.NUMBER
