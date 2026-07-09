import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { readFileSync } from 'node:fs';
const DIR = new URL('../sample_data', import.meta.url).pathname;
const b64 = p => readFileSync(p).toString('base64');
const browser = await chromium.launch();
const page = await browser.newPage();
const errs = [];
page.on('console', m => { if (m.type() === 'error') errs.push('[err] ' + m.text()); });
page.on('pageerror', e => errs.push('[pageerror] ' + e.message));
await page.goto(new URL('../index.html', import.meta.url).href);
// UX-1 접이식 패널: 테스트는 컨트롤을 직접 조작하므로 접힘 숨김을 무력화한다.
await page.addStyleTag({ content: '.panel.coll.collapsed>:not(h2){display:block !important}' });
let pass = 0, fail = 0;
const check = (n, c, d) => { if (c) { pass++; console.log('  ✔', n); } else { fail++; console.log('  ✘', n, '|', d); } };

const upload = (b64s, name) => page.evaluate(async ({ b64s, name }) => {
  const bin = atob(b64s); const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  await window.__upload.handleFiles([new File([arr], name)]);
  await new Promise(r => setTimeout(r, 80));
}, { b64s, name });

console.log('[기능 #2 초기 비활성 상태]');
check('IF/LOF/DBSCAN 미체크 → 파라미터 disabled',
  await page.$eval('#p_contam', e => e.disabled) && await page.$eval('#p_neighbors', e => e.disabled) &&
  await page.$eval('#p_eps', e => e.disabled) && await page.$eval('#p_minsamples', e => e.disabled), '');
check('체크된 알고리즘(증감률/Z) 파라미터 enabled',
  !(await page.$eval('#p_change', e => e.disabled)) && !(await page.$eval('#p_zscore', e => e.disabled)), '');
// 체크 → 활성화, 해제 → 비활성 + 값 유지
await page.check('#opt_dbscan');
check('DBSCAN 체크 시 eps/min_samples 활성', !(await page.$eval('#p_eps', e => e.disabled)) && !(await page.$eval('#p_minsamples', e => e.disabled)), '');
await page.fill('#p_eps', '0.8');
await page.uncheck('#opt_dbscan');
check('DBSCAN 해제 시 다시 disabled + 값 유지(0.8)',
  await page.$eval('#p_eps', e => e.disabled) && await page.$eval('#p_eps', e => e.value) === '0.8', await page.$eval('#p_eps', e => e.value));
check('.param 회색 클래스(set-off) 적용', await page.$eval('#p_eps', e => e.closest('.param').classList.contains('set-off')), '');

console.log('[기능 #1 결측 허용 컬럼]');
await upload(b64(`${DIR}/sample_01_결측치.csv`), 'sample_01_결측치.csv');
const maCols = await page.$$eval('#missingAllowList input.ma-col', els => els.map(e => e.value));
check('컬럼 목록 자동 로드(5개)', maCols.length === 5, JSON.stringify(maCols));
check('기본 모두 해제', await page.$$eval('#missingAllowList input.ma-col', els => els.every(e => !e.checked)), '');
// 기준 분석: 허용 없음 → 결측 5행
let r0 = await page.evaluate(async () => {
  document.getElementById('btnRun').click();
  await new Promise(res => { const iv = setInterval(() => { if (/완료|실패|문제/.test(document.getElementById('status').textContent)) { clearInterval(iv); res(); } }, 50); });
  return Array.from(document.querySelectorAll('#resultTable tbody tr.anomaly')).length;
});
check('허용 없음: 결측 이상 행 존재(≥5)', r0 >= 5, r0);
// '이름','부서','이메일','온도' 등 결측 컬럼을 전체 선택 → 결측 이상 사라짐
await page.click('#maSelectAll');
check('전체 선택 동작', await page.$$eval('#missingAllowList input.ma-col', els => els.every(e => e.checked)), '');
let r1 = await page.evaluate(async () => {
  // 결측치만 켜고 나머지 끄기 → 순수 결측 효과 확인
  for (const id of ['opt_duplicate','opt_range','opt_change','opt_iqr','opt_zscore','opt_iforest','opt_lof','opt_dbscan'])
    document.getElementById(id).checked = false;
  document.getElementById('opt_missing').checked = true;
  document.getElementById('btnRun').click();
  await new Promise(res => { const iv = setInterval(() => { if (/완료|실패|문제/.test(document.getElementById('status').textContent)) { clearInterval(iv); res(); } }, 50); });
  return { anom: Array.from(document.querySelectorAll('#resultTable tbody tr.anomaly')).length,
           reasons: Array.from(document.querySelectorAll('#resultTable tbody tr')).map(tr => tr.textContent).filter(t => t.includes('결측치')).length };
});
check('모든 컬럼 결측 허용 → 결측치 이상 0건', r1.reasons === 0, JSON.stringify(r1));
// 일부만 허용: '이름'만 해제(체크 해제하면 이름 컬럼만 결측 검사)
await page.click('#maClearAll');
check('전체 해제 동작', await page.$$eval('#missingAllowList input.ma-col', els => els.every(e => !e.checked)), '');

console.log('[기능 #1 × #2 상호작용: opt_missing 해제 시 목록 잠금]');
await page.uncheck('#opt_missing');
check('opt_missing 해제 → 목록/버튼 disabled',
  await page.$$eval('#missingAllowList input.ma-col', els => els.every(e => e.disabled)) &&
  await page.$eval('#maSelectAll', e => e.disabled) && await page.$eval('#missingAllowPanel', e => e.classList.contains('set-off')), '');
await page.check('#opt_missing');
check('opt_missing 재선택 → 목록 활성', !(await page.$$eval('#missingAllowList input.ma-col', els => els.some(e => e.disabled))), '');

console.log('[기능 #2 범위 검사 → 숫자 컬럼 표]');
await page.uncheck('#opt_range');
check('범위 해제 → 숫자표 입력 disabled', await page.$$eval('#numTableBody input', els => els.length > 0 && els.every(e => e.disabled)), '');
await page.check('#opt_range');
check('범위 선택 → 숫자표 입력 활성', !(await page.$$eval('#numTableBody input', els => els.some(e => e.disabled))), '');

console.log('[재업로드 시 결측 목록 갱신]');
await upload(b64(`${DIR}/sample_10_종합1_2023산단현황.csv`), 'sample_10.csv');
const maCols2 = await page.$$eval('#missingAllowList input.ma-col', els => els.length);
check('재업로드 → 컬럼 목록 갱신(11개)', maCols2 === 11, maCols2);

console.log('[#3 비교 검증 흐름(파일 A/B → 비교 → 결과)]');
await page.click('#railCompare');   // 데스크톱: 좌측 레일(상단 탭은 모바일 폴백으로 숨김)
check('탭 텍스트 "비교 검증"', (await page.textContent('#tabCompare')) === '비교 검증', await page.textContent('#tabCompare'));
await page.evaluate(async ({ a, b }) => {
  const mk = (s, n) => { const bin = atob(s); const arr = new Uint8Array(bin.length);
    for (let i=0;i<bin.length;i++) arr[i]=bin.charCodeAt(i); return new File([arr], n); };
  await window.__compare.handleSlotFile('A', mk(a, 'A.csv'));
  await window.__compare.handleSlotFile('B', mk(b, 'B.xlsx'));
  await new Promise(r => setTimeout(r, 120));
}, { a: b64(`${DIR}/sample_10_종합1_2023산단현황.csv`), b: b64(`${DIR}/sample_11_종합2_2024산단현황.xlsx`) });
check('비교 버튼 활성화', !(await page.$eval('#btnCompare', e => e.disabled)), '');
check('cmpStatus 갱신됨(null 아님)', (await page.textContent('#cmpStatus')).includes('기준 컬럼'), await page.textContent('#cmpStatus'));
await page.click('#btnCompare');
await page.waitForFunction(() => document.getElementById('cmpStatus').textContent.includes('완료'), { timeout: 10000 });
check('비교 완료 + 요약(35행)', (await page.textContent('#cmpSummary')).includes('35'), '');
// 비교 #2: opt_cmp_z 해제 → p_cmp_z disabled
await page.uncheck('#opt_cmp_z');
check('비교 Z 해제 → p_cmp_z disabled', await page.$eval('#p_cmp_z', e => e.disabled), '');
await page.check('#opt_cmp_z');
check('비교 Z 선택 → p_cmp_z 활성', !(await page.$eval('#p_cmp_z', e => e.disabled)), '');

console.log('\n결과:', pass, '/', pass + fail, '| 콘솔오류:', errs.length ? errs.join(' ;; ') : '없음');
await browser.close();
process.exit(fail || errs.length ? 1 : 0);
