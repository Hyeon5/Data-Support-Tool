# 테스트 하네스

`index.html`(단일 배포 파일)의 회귀 검증용 헤드리스 브라우저 테스트입니다.
모든 테스트는 `file://` 로 `index.html` 을 직접 열어(=실제 배포 환경) 내부 API
(`window.__anomaly`, `window.__upload`, `window.__compare`, `window.__deid` 등)를
호출하거나 실제 UI 를 조작해 결과를 검증합니다.

## 사전 요구

- Node.js 18+ (ESM)
- Playwright + Chromium

이 저장소가 실행되는 환경에는 Playwright 가 `/opt/node22/lib/node_modules/playwright`
에 미리 설치되어 있어 각 테스트가 해당 경로에서 `chromium` 을 import 합니다.
다른 환경에서는 `npm i -D playwright && npx playwright install chromium` 후,
각 파일 상단의 import 경로를 `'playwright'` 로 바꾸면 됩니다.

경로는 `import.meta.url` 기준 상대 경로로 해석되므로, 저장소를 어디에 두든 그대로 동작합니다.

## 실행

```bash
node tests/run-all.mjs      # 전체 스위트 순차 실행
node tests/samples.mjs      # 개별 실행
```

## 스위트 개요

| 파일 | 검증 대상 |
|---|---|
| `reader_test.mjs` | CSV/XLSX/XLS 리더, 인코딩, 매직바이트 |
| `samples.mjs` | 탐지기 9종 + 두 파일 비교 검증(샘플 데이터 기준값) |
| `ml_equiv.mjs` | LOF/DBSCAN 정확·근사 결과 동치 |
| `feat.mjs` | 분석 옵션/파라미터 활성화, 비교 검증 흐름 |
| `sheet_ui.mjs` | 다중 시트 인식/선택 |
| `dash8.mjs` | 결과 요약 대시보드 |
| `rv_cancel.mjs` | 검토 상태 저장/복원 + 분석 취소 엔진 |
| `fixes2.mjs` | 파라미터 클램프(A-1) · 2단계 취소 버튼(A-2) · 필터 유지(A-3) |
| `deid.mjs` | 개인정보 비식별 엔진(SHA-256 표준벡터, 유형 추정, 5개 변환) |
| `deid_ui.mjs` | 비식별 UI 흐름(업로드→탐지표→미리보기→다운로드) + 열 순서 |
| `ui3_changes.mjs` | 접이식 기본 열림/비활성 접힘, 좌측 레일, 히스토그램 줌, 비식별 열 순서 |
| `xlsx_preserve.mjs` | 원본 xlsx 서식(글꼴·열너비·행높이) 보존 저장 (`fixtures/formatted.xlsx`) |
| `cleaner.mjs` | 데이터 정제 엔진(공백/제어/HTML/특수문자/`"-"→0`/빈값↔NULL/컬럼명) |
| `convert.mjs` | 4종 형식 변환(XLSX↔CSV) + CP949 자동 인식 + 형식 불일치 오류 (`fixtures/*.csv`, `messy.xlsx`) |
| `clean_ui.mjs` | 정제·변환 UI 배치 처리(다중 파일·성공/실패·진행률) + ZIP 다운로드 |
| `ui_full.mjs` | 전체 UI 통합 + 외부 네트워크 요청 0건 |

## 참고

- 접이식 설정 패널(UX-1) 때문에 일부 컨트롤은 기본 접힘 상태입니다.
  UI 조작 테스트는 시작 시 `.panel.coll.collapsed>:not(h2){display:block}` 스타일을
  주입해 컨트롤을 노출시킵니다.
- 데스크톱(≥721px)에서는 상단 탭이 숨겨지고 좌측 레일(`#railSingle/#railCompare/#railDeid`)이
  모드 전환을 담당합니다. `#tabSingle/#tabCompare` id 는 모바일 폴백으로 유지됩니다.
