#!/usr/bin/env python3
"""분석·비교 기능 테스트용 샘플 데이터 생성 스크립트.

11종의 샘플을 CSV / XLSX 두 형식(동일 데이터)으로 총 22개 생성한다.
개발용 스크립트이며, 프로그램 실행에는 필요하지 않다.

실행: python3 scripts/generate_samples.py
필요: openpyxl (xlsx 생성용, 개발 PC 에만 필요)
"""

from __future__ import annotations

import csv
import os
import random
from datetime import date, datetime, timedelta

from openpyxl import Workbook

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_data"))
random.seed(42)


def cell_to_csv(v):
    """CSV 셀 표기(XLSX 와 의미상 동일하게 유지)."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, date):
        return v.strftime("%Y-%m-%d")
    return v


def write_pair(name: str, columns: list[str], rows: list[list]) -> None:
    """같은 데이터를 name.csv / name.xlsx 로 저장한다."""
    with open(os.path.join(OUT, name + ".csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(columns)
        for r in rows:
            w.writerow([cell_to_csv(v) for v in r])
    wb = Workbook()
    ws = wb.active
    ws.title = "Data"
    ws.append(columns)
    for r in rows:
        ws.append(list(r))
    wb.save(os.path.join(OUT, name + ".xlsx"))
    print(f"  {name}.csv / .xlsx  ({len(rows)}행 × {len(columns)}열)")


# ---------------------------------------------------------------- 01 결측치
def s01_missing():
    cols = ["사번", "이름", "부서", "급여(만원)", "이메일"]
    names = ["김민준", "이서연", "박도윤", "최지우", "정하준", "강서아", "조은우", "윤지호",
             "임수아", "한시우", "오하린", "서준서", "신아윤", "권도현", "황유나", "안건우",
             "송다은", "홍시윤", "고예준", "문채원"]
    depts = ["영업", "개발", "인사", "재무"]
    rows = []
    for i, nm in enumerate(names):
        rows.append([1001 + i, nm, depts[i % 4], 3200 + (i * 37) % 900,
                     f"user{1001+i}@example.com"])
    rows[2][1] = ""            # 빈 문자열 이름
    rows[6][3] = None          # 급여 결측
    rows[10][2] = "   "        # 공백만 있는 부서
    rows[14][4] = None         # 이메일 결측
    rows[17][1] = None         # 이름 결측
    rows[17][4] = ""           # 같은 행에 이메일도 결측(복수 결측)
    write_pair("sample_01_결측치", cols, rows)


# ------------------------------------------------------------- 02 이상치
def s02_outlier():
    cols = ["측정번호", "온도(℃)", "압력(bar)", "유량(L/min)"]
    rows = []
    for i in range(50):
        rows.append([i + 1,
                     round(random.uniform(22, 26), 1),
                     round(random.uniform(4.8, 5.4), 2),
                     round(random.uniform(118, 126), 1)])
    # 명확한 이상치 4건(단일·복합)
    rows[9] = [10, 95.0, 5.1, 121.3]        # 온도 급등
    rows[19] = [20, 24.1, 18.5, 120.0]      # 압력 급등
    rows[29] = [30, 23.5, 5.0, 890.0]       # 유량 급등
    rows[39] = [40, 3.2, 1.1, 45.0]         # 전 항목 비정상(복합)
    write_pair("sample_02_이상치", cols, rows)


# --------------------------------------------------------- 03 중복 데이터
def s03_duplicate():
    cols = ["주문번호", "상품명", "수량", "단가(원)", "주문일"]
    items = ["노트북", "모니터", "키보드", "마우스", "프린터"]
    rows = []
    for i in range(18):
        rows.append([f"ORD-{2001+i}", items[i % 5], (i % 4) + 1,
                     50000 + (i * 1234) % 90000, date(2024, 3, 1) + timedelta(days=i)])
    rows[6] = list(rows[5])                    # 완전 중복 1쌍
    rows[15] = list(rows[14])                  # 완전 중복 3연속
    rows[16] = list(rows[14])
    write_pair("sample_03_중복데이터", cols, rows)


# ------------------------------------------------------ 04 데이터 타입 추론
def s04_types():
    cols = ["정수형", "실수형", "날짜_ISO", "날짜_슬래시", "불리언", "문자열", "숫자문자혼합"]
    words = ["가공", "조립", "검사", "포장", "출하"]
    rows = []
    for i in range(20):
        mixed = (i + 1) if i % 2 == 0 else words[i % 5]  # 50% 숫자 → String 판정 유도
        rows.append([i + 1,
                     round(random.uniform(0, 10), 2),
                     date(2024, 1, 1) + timedelta(days=i * 3),
                     f"2024/{(i % 12) + 1:02d}/{(i % 28) + 1:02d}",
                     i % 3 != 0,
                     f"{words[i % 5]}-{i+1:03d}",
                     mixed])
    write_pair("sample_04_타입추론", cols, rows)


# ------------------------------------------------- 05 데이터 품질 점수(종합 품질)
def s05_quality():
    cols = ["고객번호", "고객명", "나이", "구매금액(원)", "가입일"]
    rows = []
    for i in range(30):
        rows.append([f"C{101+i}", f"고객{101+i}", 25 + (i * 3) % 40,
                     30000 + (i * 4321) % 200000, date(2023, 1, 5) + timedelta(days=i * 11)])
    rows[4][2] = None                      # 결측 나이
    rows[9][1] = ""                        # 결측 이름
    rows[13][3] = None                     # 결측 구매금액
    rows[20] = list(rows[19])              # 중복 1쌍
    rows[24][2] = 250                      # 불가능한 나이(범위/이상치)
    rows[27][3] = 9500000                  # 구매금액 이상치
    write_pair("sample_05_품질점수", cols, rows)


# ------------------------------------------------------- 06 기술통계 분석
def s06_stats():
    cols = ["학번", "국어", "수학", "영어"]
    rows = []
    for i in range(50):
        kor = round(random.uniform(60, 100), 0)
        mat = round(max(0, min(100, random.gauss(75, 8))), 0)
        eng = round(random.uniform(50, 95), 0)
        rows.append([20240001 + i, kor, mat, eng])
    write_pair("sample_06_기술통계", cols, rows)


# ------------------------------------------------------- 07 상관관계 분석
def s07_correlation():
    cols = ["월", "광고비(만원)", "매출(만원)", "반품비용(만원)", "무관지표"]
    rows = []
    for i in range(40):
        ad = round(random.uniform(10, 100), 1)
        sales = round(ad * 3 + random.uniform(-15, 15), 1)       # 강한 양의 상관
        refund = round(200 - ad * 1.5 + random.uniform(-10, 10), 1)  # 음의 상관
        noise = round(random.uniform(0, 100), 1)                  # 무상관
        rows.append([i + 1, ad, sales, refund, noise])
    write_pair("sample_07_상관관계", cols, rows)


# --------------------------------------------------------- 08 분포 분석
def s08_distribution():
    cols = ["표본번호", "정규분포형", "치우친분포", "균등분포", "두봉우리분포"]
    rows = []
    for i in range(60):
        normal = round(random.gauss(50, 5), 1)
        skewed = round(random.expovariate(1 / 10), 1)             # 오른쪽 꼬리
        uniform = round(random.uniform(0, 100), 1)
        bimodal = round(random.gauss(30 if i % 2 == 0 else 70, 3), 1)
        rows.append([i + 1, normal, skewed, uniform, bimodal])
    write_pair("sample_08_분포분석", cols, rows)


# ---------------------------------------------- 09 알고리즘 파라미터 테스트
def s09_params():
    cols = ["측정순서", "측정값(Z-Score용)", "일별수치(증감률용)"]
    rows = []
    # 측정값: 97~103 균등 + 경계 이상치(임계 2.5 vs 3.0 에서 결과가 달라지도록 설계)
    vals = [round(random.uniform(97, 103), 1) for _ in range(52)]
    vals[15] = 117.0   # 경계 이상(z≈2.7 부근: 임계 2.5 에서만 탐지)
    vals[30] = 122.0   # 이상(z≈3.6 부근)
    vals[45] = 130.0   # 확실한 이상(z≈5)
    # 일별수치: +80% / +120% / +250% 스텝(임계 50/100/200 에서 개수 변화)
    daily = [1000.0]
    steps = [1.02, 0.98, 1.8, 1.01, 0.99, 2.2, 1.02, 0.97, 3.5, 1.01,
             0.98, 1.03, 0.99, 1.02, 0.98, 1.01, 1.03, 0.97, 1.02, 0.99,
             1.01, 0.98, 1.02, 0.99, 1.01, 0.98, 1.03, 0.97, 1.02, 0.99,
             1.01, 0.98, 1.02, 0.99, 1.01, 0.98, 1.03, 0.97, 1.02, 0.99,
             1.01, 0.98, 1.02, 0.99, 1.01, 0.98, 1.03, 0.97, 1.02, 0.99, 1.01]
    for s in steps:
        daily.append(round(daily[-1] * s, 1))
    for i in range(52):
        # 측정순서는 1001부터: 1→2(+100%) 같은 순번 증가가 증감률 검사에 걸리지 않도록 한다.
        rows.append([1001 + i, vals[i], daily[i]])
    write_pair("sample_09_파라미터테스트", cols, rows)


# ------------------------------------------- 10/11 종합(비교 검증 겸용)
BASE_COMPANIES = None


def build_base():
    """종합1(2023)과 종합2(2024)가 공유하는 기업 목록."""
    global BASE_COMPANIES
    kinds = ["기계", "전자", "화학", "식품", "섬유"]
    regions = ["구미", "창원", "반월", "시화", "울산"]
    en = ["Alpha Tech", "Beta Works", "Gamma Industry", "Delta Foods", "Epsilon Chem",
          "Zeta Motors", "Eta Textile", "Theta Electric", "Iota Machine", "Kappa Bio"]
    longtxt = ("본 업체는 2010년 설립 이후 지속적인 설비 투자와 연구개발을 통해 "
               "지역 산업단지 내에서 안정적인 성장세를 유지하고 있으며, 주요 거래처와의 "
               "장기 계약을 바탕으로 향후 5년간 연평균 5% 이상의 성장이 기대됩니다.")
    rows = []
    for i in range(30):
        code = f"GJ-{1001+i}"
        note = ""
        if i == 3:
            note = longtxt                                     # 긴 문자열
        elif i == 7:
            note = "협력사: O'Brien & Co. <해외> / 계약율 95% #1"  # 특수문자
        elif i == 12:
            note = "Global partner: \"Nova Systems\" (USA)"     # 영어+따옴표
        rows.append({
            "관리번호": code,
            "산단명": f"{regions[i % 5]}국가산업단지",
            "업체명": f"{kinds[i % 5]}기업{i+1:02d}",
            "업체명_EN": en[i % 10] + f" {i+1:02d}",
            "업종": kinds[i % 5],
            "지역": regions[i % 5],
            "매출액(백만원)": [300, 520, 410, 660, 200, 1000, 480, 850, 770, 390][i % 10] + i * 7,
            "종업원수": 20 + (i * 13) % 180,
            "가동여부": i % 6 != 5,
            "등록일": date(2015, 1, 10) + timedelta(days=i * 97),
            "비고": note,
        })
    # 의도적 데이터 품질 요소(종합1 기준)
    rows[1]["종업원수"] = None          # 결측 → 종합2에서 값 채움(결측값 변경)
    rows[16]["비고"] = None             # 결측 유지
    rows[21]["매출액(백만원)"] = 25000   # 이상치(매출 급증 기업)
    BASE_COMPANIES = rows
    return rows


def s10_comprehensive1():
    base = build_base()
    cols = list(base[0].keys())
    rows = [[c[k] for k in cols] for c in base]
    rows.append(list(rows[28]))   # 완전 중복 행 1건(GJ-1029)
    write_pair("sample_10_종합1_2023산단현황", cols, rows)


def s11_comprehensive2():
    base = [dict(c) for c in BASE_COMPANIES]
    removed = {"GJ-1003", "GJ-1011", "GJ-1027"}
    changes = {
        "GJ-1001": [("매출액(백만원)", lambda v: int(v * 1.5))],   # +50%
        "GJ-1005": [("매출액(백만원)", lambda v: v * 5)],          # +400% 급증
        "GJ-1008": [("매출액(백만원)", lambda v: int(v * 0.1))],   # -90% 급감
        "GJ-1010": [("매출액(백만원)", lambda v: int(v * 1.05))],  # +5% 소폭
        "GJ-1014": [("매출액(백만원)", lambda v: int(v * 2.2))],   # +120%
        "GJ-1002": [("종업원수", lambda v: 45)],                    # 결측 → 값
        "GJ-1006": [("종업원수", lambda v: None)],                  # 값 → 결측
        "GJ-1009": [("매출액(백만원)", lambda v: "비공개")],        # 숫자 → 문자(타입 변경)
        "GJ-1012": [("업체명", lambda v: v + "(주)")],              # 문자열 변경
        "GJ-1013": [("가동여부", lambda v: not v)],                 # Boolean 변경
        "GJ-1015": [("등록일", lambda v: v + timedelta(days=365))], # 날짜 변경
    }
    out = []
    for c in base:
        if c["관리번호"] in removed:
            continue
        c2 = dict(c)
        for col, fn in changes.get(c["관리번호"], []):
            c2[col] = fn(c2[col])
        out.append(c2)
    # 신규 4개사 추가
    for i, code in enumerate(["GJ-1031", "GJ-1032", "GJ-1033", "GJ-1034"]):
        out.append({
            "관리번호": code, "산단명": "구미국가산업단지",
            "업체명": f"신규기업{i+1:02d}", "업체명_EN": f"New Venture {i+1:02d}",
            "업종": "전자", "지역": "구미",
            "매출액(백만원)": 150 + i * 40, "종업원수": 12 + i * 5,
            "가동여부": True, "등록일": date(2024, 2, 1) + timedelta(days=i * 30),
            "비고": "2024년 신규 입주",
        })
    cols = list(out[0].keys())
    # 컬럼명 변경: 산단명 → 산업단지명(자동 추론 시연) + B 전용 컬럼 추가
    cols_b = ["관리번호", "산업단지명", "업체명", "업체명_EN", "업종", "지역",
              "매출액(백만원)", "종업원수", "가동여부", "등록일", "비고", "ESG등급"]
    grades = ["A", "B", "C"]
    rows = []
    for i, c in enumerate(out):
        rows.append([c["관리번호"], c["산단명"], c["업체명"], c["업체명_EN"], c["업종"],
                     c["지역"], c["매출액(백만원)"], c["종업원수"], c["가동여부"],
                     c["등록일"], c["비고"], grades[i % 3]])
    write_pair("sample_11_종합2_2024산단현황", cols_b, rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    print("샘플 데이터 생성 중...")
    s01_missing(); s02_outlier(); s03_duplicate(); s04_types(); s05_quality()
    s06_stats(); s07_correlation(); s08_distribution(); s09_params()
    s10_comprehensive1(); s11_comprehensive2()
    print("완료: 11종 × 2형식 = 22개 파일")


if __name__ == "__main__":
    main()
