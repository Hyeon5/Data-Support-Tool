"""테스트용 샘플 데이터 생성 스크립트.

의도적으로 다양한 이상치를 포함한 CSV/XLSX 파일을 만든다.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd


def build_sample() -> pd.DataFrame:
    rng = np.random.RandomState(0)
    n = 60

    budget = rng.randint(1000, 5000, size=n).astype(float)
    rate = rng.uniform(15, 98, size=n)
    temp = rng.uniform(-5, 42, size=n)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    names = [f"부서-{i % 10}" for i in range(n)]

    df = pd.DataFrame(
        {
            "이름": names,
            "예산": budget,
            "수행률": rate,
            "온도": temp,
            "날짜": dates,
        }
    )

    # --- 의도적 이상치 삽입 ---
    # 범위 초과 & 통계 이상 (예산 폭증)
    df.loc[5, "예산"] = 985000
    # 증감률 이상
    df.loc[10, "예산"] = df.loc[9, "예산"] * 4
    # 범위 초과 (수행률 130%)
    df.loc[15, "수행률"] = 130
    # 결측치
    df.loc[20, "온도"] = np.nan
    df.loc[21, "이름"] = "   "  # 공백 문자열
    # Z-Score / IQR 이상 (온도 극단값)
    df.loc[25, "온도"] = 500
    # 중복 행 (30번을 31번에 복사)
    df.loc[31] = df.loc[30]

    return df


def main() -> None:
    out_dir = os.path.join(os.path.dirname(__file__), "..", "sample_data")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    df = build_sample()
    csv_path = os.path.join(out_dir, "sample.csv")
    xlsx_path = os.path.join(out_dir, "sample.xlsx")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_excel(xlsx_path, index=False)
    print(f"생성 완료:\n  {csv_path}\n  {xlsx_path}")


if __name__ == "__main__":
    main()
