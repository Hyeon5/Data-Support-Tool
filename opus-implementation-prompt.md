# Claude Code(Opus 4.8) 구현 프롬프트

> 이 문서를 그대로 Claude Code에 입력하면 됩니다. 근거 문서: `review.md`, `improvement-plan.md`.

---

당신은 이 저장소(단일 HTML 데이터 이상치 탐지 도구)의 유지보수 엔지니어입니다.
아래 작업을 **순서대로** 구현하세요.

## 절대 원칙 (위반 금지)
1. 결과물은 **index.html 단일 파일**로 동작. 외부 JS/CSS/CDN/폰트/네트워크 요청 코드 추가 금지.
2. **기존 기능 무손실**: 9종 탐지, 다중 시트, 헤더 자동 탐지, 비교 검증, 검토 워크플로우, 대시보드, Excel 다운로드, Worker 분석, file:// 폴백이 전부 이전과 동일하게 동작해야 함.
3. 기존 보안 훼손 금지: escapeHtml 경유 렌더링, 수식(`=`,`@`) 무력화, 매직바이트 검증, zip 해제 상한.
4. 변경 범위 최소화. 요구되지 않은 리팩토링 금지. 신규 CSS는 기존 파스텔 원칙(연한 배경 + `#1a1a1a` 글자, WCAG AA) 준수.
5. 모든 신규 UI 텍스트는 한국어 존댓말.
6. 각 단계 완료 시 헤드리스 브라우저(file://)로 검증 후 다음 단계 진행. 콘솔 오류 0건 유지.

## 사전 파악 (구현 전 필독)
- `<script id="engineScript">`: DOM 무의존 엔진(Values/ColumnAnalyzer/Detectors/runAnalysis/Worker 진입점). 메인과 Worker에서 공용.
- 메인 스크립트: 리더(loadWorkbook/readFile) → XlsxWriter(buildWorkbook) → UI IIFE(전역 노출: `window.__anomaly/__upload/__readers/__compare`).
- 결과 구조: `flags[r]`, `reasons[r]`, `findings[r][] = {rule, category, column, evidence, evidenceText}`.
- 검토 상태: `reviewState`(localStorage `davReview:` 키), Excel 다운로드에 판정 근거/검토 상태/메모 컬럼 포함.

---

## A. Major 버그 수정

### A-1. 수치 파라미터 검증 (BUG-1 + BUG-2)
- **대상**: 메인 IIFE `collectConfig()` 및 비교 탭 `btnCompare` 핸들러의 파라미터 수집부.
- **구현**: 헬퍼 추가 후 전 파라미터 교체.
```js
function readNum(id, def, lo, hi) {
  let v = parseFloat($(id).value);
  if (!Number.isFinite(v)) v = def;
  v = Math.min(hi, Math.max(lo, v));
  $(id).value = v; // 클램프 결과를 입력창에 반영해 사용자가 인지하게 함
  return v;
}
```
- 범위: p_change[0,100000] · p_zscore[0.1,20] · p_contam[0.001,0.5] · p_neighbors[1,1000] 정수 · p_eps[0.01,1000] · p_minsamples[1,1000] 정수 · p_cmp_rate[1,100000] · p_cmp_z[0.1,20].
- **주의**: `|| 기본값` 패턴을 모두 제거(0 입력 허용).

### A-2. 분석 취소 즉시성 (BUG-5)
- **대상**: engineScript의 `lof`/`dbscan`/`isolationForest` 내 청크 진행 지점, UI `btnCancel`.
- **구현**:
  1. 엔진에 `function checkCancelled(){ if (ANALYSIS_CANCELLED) throw new Error("사용자 취소"); }` 추가. 각 ML 검사 루프의 기존 `(i & 4095) === 0` 진행 보고 지점에서 호출.
  2. `runAnalysis`의 detector try/catch에서 메시지가 "사용자 취소"인 경우 skipped에 `{name, message:"사용자 취소로 건너뜀"}`으로 기록하고 `cancelled=true` 설정 후 루프 탈출(이미 완료된 검사 결과는 보존).
  3. Worker `onmessage`의 `cancel` 처리는 현행 유지(플래그 설정). **워커가 동기 루프 중이라 메시지가 늦게 처리되는 문제**는, UI 취소 버튼을 두 단계로: 1차 클릭 = 정상 취소 요청(현행), 5초 내 미반응 시 버튼이 "즉시 중단(결과 폐기)"으로 바뀌고 클릭 시 `worker.terminate()` + `analysisWorker=undefined`(다음 실행 시 재생성) + UI 초기화.
- **주의**: terminate 경로에서는 부분 결과가 없음을 상태 문구로 안내.

### A-3. 검토 일괄 적용 시 필터 유지 (BUG-3)
- `rvApply` 핸들러에서 `renderResult(result)` 대신: 적용 후 `renderReviewBar(result)` 전에 `const keep=$("rvFilter").value` 보존 → 재생성 후 `$("rvFilter").value=keep` 복원 → `renderPreview(result)`.

## B. UX/운영 개선 묶음

### B-1. 설정 패널 접이식 (UX-1)
- **대상**: 단일 분석 뷰의 패널들(분석 옵션/결측 허용/파라미터/숫자 컬럼/저장).
- **구현**: 각 패널 `<h2>`를 클릭 토글로(대시보드 `dash-head` 패턴 재사용, ▼/▶ 표시). 파일 로드 성공 시 '분석 옵션'만 펼치고 나머지는 접기. 접힘 상태는 세션 내 유지(메모리 변수로 충분).
- **주의**: 패널 내부 요소 id/이벤트는 변경 금지(display만 토글).

### B-2. 소소한 개선 일괄
- 분석 완료 시 `$("resultPanel").scrollIntoView({behavior:"smooth"})` (UX-2)
- 분석 실패 alert → `skipNote` 스타일의 인라인 배너로 교체 (UX-3)
- 결과 테이블 `rv-check`/`rv-status`/`rv-memo`에 `aria-label="{행번호}행 선택/검토 상태/검토 메모"`, 스텝 인디케이터 active에 `aria-current="step"` (UX-4)
- 페이지 하단 `※ 모든 처리는...` 문구 옆에 `v2.0 (빌드일)` 표기 (UX-5) — 버전 상수 1곳 정의
- `location.hash === "#debug"`이면 `DEBUG=true` (OPS-2)
- 검토바에 [검토 데이터 전체 삭제] 버튼: `davReview:` 접두 키 일괄 제거 + confirm (보안 잔여-1)
- `renderHistogram`용 컬럼 숫자 배열 캐시: `lastResult._numCache = {}`에 컬럼별 lazy 저장 (PERF-1)
- XlsReader FORMULA의 `isText` 데드코드 제거 (QUAL-4)

## C. 신규 기능 — 개인정보 비식별 처리 (review.md 별첨 설계 준수)

### C-1. 엔진 (engineScript에 추가, DOM 무의존)
```
const DeidEngine = { detect(columns, rows), transform(rows, plan), SHA256(text) }
```
- `detect`: 컬럼별 {type, confidence, sample}. 신호 = 컬럼명 사전(성명/이름/대표자/담당자, 주민등록번호, 외국인등록번호, 운전면허, 여권, 휴대전화/핸드폰/연락처, 전화, 이메일, 주소/소재지, 생년월일, 사업자등록번호, 법인등록번호, 계좌, 카드, IP) 0.5 + 값 패턴 매칭률(비결측 표본 최대 1,000행) 0.5.
  - 패턴: 주민 `\d{6}-?[1-4]\d{6}`, 휴대폰 `01[016789]-?\d{3,4}-?\d{4}`, 이메일 표준, 사업자 `\d{3}-?\d{2}-?\d{5}`, 법인 `\d{6}-?\d{7}`, 카드 `\d{4}(-?\d{4}){3}`+Luhn, 일반전화 `0\d{1,2}-?\d{3,4}-?\d{4}`, 생년월일(YYYYMMDD·YYYY-MM-DD, 1900~올해 범위 검증), 계좌(10~14자리 숫자, 컬럼명에 '계좌' 있을 때만), IP v4, 한국 성명 `^[가-힣]{2,4}$`(컬럼명 신호 있을 때만 채택 — 지역명 오탐 방지).
  - 도메인 규칙: 산단명/공장명/기업명/업체명 컬럼은 자동 탐지 **제외**(개인정보 아님). 사업자등록번호는 신뢰도 '중'.
- `transform(rows, plan)`: plan = [{colIdx, method, options}]. 원본 불변(새 배열 반환). 방식:
  1. `mask`: 유형별 형식 보존 — 성명 `홍*동`(2자면 `홍*`), 휴대폰 `010-****-1234`, 일반전화 국번 마스킹, 이메일 `ab***@도메인`, 주민 `123456-*******`, 사업자 `123-**-*****`, 카드 `****-****-****-1234`, 계좌 앞3·뒤2 외 `*`, 주소는 시·군·구까지만+이하 `***`, 기타 유형 앞1·뒤1 외 `*`.
  2. `delete`: 빈 값.
  3. `pseudonym`: 동일 원본→동일 가명 Map("담당자001" — 접두어는 탐지 유형별: 사용자/연락처/메일 등). 파일 내 일관성 유지.
  4. `generalize`: 생년월일→`1980년대`, 주소→시·군·구 절단, 나이 숫자→`20대`.
  5. `hash`: 자체 구현 SHA-256(외부/WebCrypto 의존 금지 — file:// 확실성) + **솔트 입력 필수**, hex 16자 절단. UI에 "복원 불가·전수대입 재식별 위험" 경고문.
- 기본 방식 매핑: 주민/외국인/여권/면허=`delete`, 성명/전화/이메일/카드/계좌=`mask`, 생년월일/주소=`generalize`, 그 외=`mask`.

### C-2. UI — 3번째 모드 + 좌측 슬림 레일 전환 (review.md §8 Case 1 조건 충족)
- 모드가 3개가 되므로 상단 `mode-tabs`를 **좌측 슬림 레일**로 전환:
  - 접힘 52px(아이콘+툴팁)/펼침 180px, 기본 접힘, 하단 토글(≡). 메뉴: 이상치 분석 / 비교 검증 / 비식별 처리.
  - 기존 `switchMode`·`viewSingle`/`viewCompare` id와 동작 유지(신규 `viewDeid` 추가). 탭 요소 id(`tabSingle`/`tabCompare`)는 레일 항목으로 이동하되 id 보존(기존 테스트 호환).
  - 모바일(≤720px)은 레일 대신 기존 상단 탭 폴백.
- 비식별 화면 흐름(기존 스타일 재사용): ① 파일 업로드(dropzone 패턴 + `validateUploadFile` + `loadWorkbook` + 시트 선택 재사용) → ② 탐지 결과 표: 컬럼|탐지 유형|신뢰도(상/중/하 배지)|샘플 값|처리 방식 select|적용 체크(자동 탐지 '상'만 기본 체크, **모든 컬럼 나열**해 수동 추가 가능) → ③ [미리보기] 상위 20행 원본→변환 2열 비교 → ④ [비식별 파일 다운로드] `XlsxWriter.buildWorkbook`으로 `비식별결과`+`처리요약`(처리 컬럼/방식/처리 건수/제외 컬럼) 2시트 → ⑤ 처리 후 요약 카드 표시.
- 성능: 5만 행 이상이면 미리보기는 표본, 변환은 전체(O(n) 문자열 처리라 메인 스레드로 충분하되 5만 행 초과 시 청크+진행률 표시).
- 상태 격리: 기존 분석/비교 상태와 완전 분리(자체 변수, `deid-` CSS 접두).

## D. 검증 (각 단계 후 실행, 최종 전체 재실행)

### 체크리스트
- [ ] 기존 샘플 22종 로드·분석 결과가 수정 전과 동일(탐지 건수 불변)
- [ ] 비교 검증(종합1↔종합2): 총35/동일16/변경11/추가4/삭제4/이상4 불변
- [ ] Worker 경로(http)와 메인 폴백(file://) 모두 분석 성공
- [ ] 취소: ML 실행 중 1차 취소가 5초 내 반영(청크 체크), 미반응 시 즉시 중단 동작
- [ ] 파라미터 0/음수/공백 입력 시 클램프·인지 가능
- [ ] 비식별: 자동 탐지(성명/휴대폰/주민/사업자/이메일 표본 파일), 방식 5종 변환 정확성, 원본 불변, 미리보기, 2시트 다운로드(openpyxl 등으로 열어 확인), 가명 일관성(동일 값→동일 가명)
- [ ] 레일 전환 후 기존 탭 id·switchMode 동작 유지, 모바일 폴백
- [ ] 콘솔 오류 0 · 외부 네트워크 요청 0 (Network 계측)
- [ ] 신규 배지/배경 전부 검은 글자 대비 4.5:1 이상(계산 검증)
- [ ] 더블클릭(file://) 실행 정상

### 완료 조건
위 체크리스트 전부 통과 + `tests/`에 검증 스크립트 커밋(TEST-1) + README에 비식별 기능·버전 표기 반영.

### 주의사항
- engineScript는 Worker에서도 실행됨 — DOM API 사용 금지 유지.
- `escapeHtml` 미경유 innerHTML 삽입 금지(신규 코드 포함 전수 확인).
- 비식별 다운로드에도 기존 수식 무력화(`=`,`@` 접두) 규칙이 자동 적용됨(XlsxWriter 재사용) — 우회 금지.
- 사용자 커스텀 텍스트/CSS(헤더 문구, 탭명 "비교 검증", params2 3열 등) 변경 금지.
