"""사유 문자열 생성에 사용하는 숫자 포맷 헬퍼."""

from __future__ import annotations


def format_number(value: float) -> str:
    """숫자를 사유 문자열용으로 보기 좋게 포맷한다.

    - 정수 값이면 소수점을 표시하지 않는다(130.0 -> "130").
    - 소수 값이면 불필요한 0 을 제거한다.
    """
    try:
        f = float(value)
    except (ValueError, TypeError):
        return str(value)

    if f == int(f):
        return str(int(f))
    # 소수 둘째 자리까지 표시하되 뒤쪽 0 제거
    text = f"{f:.4f}".rstrip("0").rstrip(".")
    return text
