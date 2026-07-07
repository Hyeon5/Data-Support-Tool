"""분석 전체 설정 모델."""

from __future__ import annotations

from dataclasses import dataclass, field

from .numeric_config import NumericColumnConfig


@dataclass
class AnalysisConfig:
    """분석 실행에 필요한 모든 옵션과 파라미터.

    GUI의 분석 옵션 체크박스 및 파라미터 입력값을 담는다.
    각 detector 는 이 설정에서 필요한 값을 참조한다.
    """

    # --- 활성화 여부(체크박스) ---
    check_missing: bool = True
    check_duplicate: bool = True
    check_range: bool = True
    check_change_rate: bool = True
    check_iqr: bool = True
    check_zscore: bool = True
    check_isolation_forest: bool = True
    check_lof: bool = True
    check_dbscan: bool = True

    # --- 알고리즘 파라미터 ---
    change_rate_threshold: float = 100.0  # 증감률 임계치(%)
    zscore_threshold: float = 3.0         # Z-Score 임계치
    iso_contamination: float = 0.05       # Isolation Forest contamination
    lof_n_neighbors: int = 20             # LOF n_neighbors
    dbscan_eps: float = 0.5               # DBSCAN eps
    dbscan_min_samples: int = 5           # DBSCAN min_samples

    # --- 숫자 컬럼별 범위 설정 ---
    numeric_configs: list[NumericColumnConfig] = field(default_factory=list)

    def enabled_range_configs(self) -> list[NumericColumnConfig]:
        """범위 검사가 활성화(use=True)된 숫자 컬럼 설정만 반환한다."""
        return [c for c in self.numeric_configs if c.use]
