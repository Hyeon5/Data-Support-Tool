"""숫자 컬럼 범위 검사 설정 모델."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NumericColumnConfig:
    """숫자 컬럼 하나에 대한 범위 검사 설정.

    GUI의 "숫자 컬럼 설정 화면" 한 행에 대응한다.

    Attributes:
        name: 컬럼명.
        actual_min: 데이터에서 계산한 실제 최소값.
        actual_max: 데이터에서 계산한 실제 최대값.
        allow_min: 사용자가 지정한 허용 최소값(기본값=실제 최소값).
        allow_max: 사용자가 지정한 허용 최대값(기본값=실제 최대값).
        use: 이 컬럼에 범위 검사를 적용할지 여부.
    """

    name: str
    actual_min: float
    actual_max: float
    allow_min: float
    allow_max: float
    use: bool = True

    @classmethod
    def from_bounds(cls, name: str, actual_min: float, actual_max: float) -> "NumericColumnConfig":
        """실제 최소/최대값으로부터 기본 설정을 생성한다.

        허용 최소/최대값은 실제 최소/최대값으로 초기화된다.
        """
        return cls(
            name=name,
            actual_min=actual_min,
            actual_max=actual_max,
            allow_min=actual_min,
            allow_max=actual_max,
            use=True,
        )
