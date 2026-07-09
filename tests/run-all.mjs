// 전체 테스트 러너 — tests/ 의 모든 시나리오를 순차 실행하고 요약을 출력한다.
// 실행: node tests/run-all.mjs   (사전 요구: Playwright + Chromium)
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const suites = [
  'reader_test.mjs', // 파일 리더(csv/xlsx/xls)
  'samples.mjs',     // 탐지기 9종 + 비교 검증(샘플 데이터)
  'ml_equiv.mjs',    // LOF/DBSCAN 정확·근사 동치
  'feat.mjs',        // UI 기능(옵션/파라미터/비교 흐름)
  'sheet_ui.mjs',    // 다중 시트 UI
  'dash8.mjs',       // 대시보드
  'rv_cancel.mjs',   // 검토 상태 + 취소 엔진
  'fixes2.mjs',      // A-1 클램프 / A-2 2단계 취소 / A-3 필터 유지
  'deid.mjs',        // 개인정보 비식별 엔진(단위)
  'deid_ui.mjs',     // 개인정보 비식별 UI 흐름
  'ui3_changes.mjs', // 접이식 기본/비활성 접힘, 레일, 히스토그램 줌, 비식별 열 순서
  'xlsx_preserve.mjs', // 원본 xlsx 서식 보존 저장
  'ui_full.mjs',     // 전체 UI + 오프라인/네트워크 0
];

let failed = 0;
for (const s of suites) {
  process.stdout.write(`\n===== ${s} =====\n`);
  const r = spawnSync(process.execPath, [join(here, s)], { stdio: 'inherit' });
  if (r.status !== 0) { failed++; console.log(`!! ${s} 실패(exit ${r.status})`); }
}
console.log(`\n========================================`);
console.log(failed === 0 ? '모든 테스트 스위트 통과 ✅' : `${failed}개 스위트 실패 ❌`);
process.exit(failed ? 1 : 0);
