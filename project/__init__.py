"""AI 기반 데이터 이상치 탐지 프로그램.

내부망(오프라인) 환경에서 동작하는 데스크톱 애플리케이션.
엑셀/CSV 데이터를 분석하여 다양한 방식의 이상치를 탐지하고
결과를 Excel 로 저장한다.
"""

from .config import Settings

__all__ = ["Settings"]
__version__ = Settings.APP_VERSION
