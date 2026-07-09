import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { readFileSync } from 'node:fs';
const DIR = new URL('../sample_data', import.meta.url).pathname;
const b64 = p => readFileSync(p).toString('base64');

const browser = await chromium.launch();
const page = await browser.newPage();
const errs = [];
page.on('pageerror', e => errs.push(e.message));
await page.goto(new URL('../index.html', import.meta.url).href);

// In-page helper: load file → run analysis with given flags → return flagged info
await page.evaluate(() => {
  window.__loadTable = async (name, b64str) => {
    const bin = atob(b64str); const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    const A = window.__anomaly;
    const raw = await A.readFile(new File([arr], name));
    const cols = window.__upload.dedupeColumns(raw.columns);
    return new A.TableWrapper(cols, raw.rows);
  };
  window.__runWith = async (table, flags, overrides) => {
    const A = window.__anomaly;
    const infos = A.ColumnAnalyzer.analyze(table);
    const nc = A.ColumnAnalyzer.buildNumericConfigs(table, infos);
    (overrides?.ranges || []).forEach(([name, lo, hi]) => {
      nc.forEach(c => { if (c.name === name) { c.allowMin = lo; c.allowMax = hi; } });
    });
    const cfg = Object.assign({
      missing: false, duplicate: false, range: false, change: false,
      iqr: false, zscore: false, iforest: false, lof: false, dbscan: false,
      changeRateThreshold: 100, zscoreThreshold: 3, isoContamination: 0.05,
      lofNeighbors: 20, dbscanEps: 0.5, dbscanMinSamples: 5, numericConfigs: nc,
    }, flags, overrides?.params || {});
    const res = await A.runAnalysis(table, cfg, () => {});
    const flagged = [];
    res.flags.forEach((f, i) => { if (f) flagged.push(i); });
    return { flagged, reasons: res.reasons.filter(r => r), types: infos.map(i => i.name + ':' + i.type), count: flagged.length };
  };
});

async function loadPair(base) {
  return await page.evaluate(async ({ base, csvB64, xlsxB64 }) => {
    window.__tblCsv = await window.__loadTable(base + '.csv', csvB64);
    window.__tblXlsx = await window.__loadTable(base + '.xlsx', xlsxB64);
    return { csvRows: window.__tblCsv.rows.length, xlsxRows: window.__tblXlsx.rows.length,
             csvCols: window.__tblCsv.columns, xlsxCols: window.__tblXlsx.columns };
  }, { base, csvB64: b64(`${DIR}/${base}.csv`), xlsxB64: b64(`${DIR}/${base}.xlsx`) });
}
async function runBoth(flags, overrides = null) {
  return await page.evaluate(async ({ flags, overrides }) => {
    const a = await window.__runWith(window.__tblCsv, flags, overrides);
    const b = await window.__runWith(window.__tblXlsx, flags, overrides);
    return { csv: a, xlsx: b };
  }, { flags, overrides });
}

const R = {};
let pass = 0, fail = 0;
function check(name, cond, detail) {
  if (cond) { pass++; console.log('  ✔', name); }
  else { fail++; console.log('  ✘ FAIL:', name, '|', detail); }
}

// ---- 01 결측치 ----
console.log('[01 결측치]');
let p = await loadPair('sample_01_결측치');
check('행수 일치(20)', p.csvRows === 20 && p.xlsxRows === 20, JSON.stringify(p));
let r = await runBoth({ missing: true });
check('결측 행 {2,6,10,14,17}', JSON.stringify(r.csv.flagged) === JSON.stringify([2,6,10,14,17]), JSON.stringify(r.csv.flagged));
check('CSV=XLSX', r.csv.count === r.xlsx.count && JSON.stringify(r.csv.flagged) === JSON.stringify(r.xlsx.flagged), JSON.stringify(r.xlsx.flagged));

// ---- 02 이상치 ----
console.log('[02 이상치]');
p = await loadPair('sample_02_이상치');
r = await runBoth({ iqr: true });
check('IQR 이상 = {9,19,29,39}', JSON.stringify(r.csv.flagged) === JSON.stringify([9,19,29,39]), JSON.stringify(r.csv.flagged));
check('CSV=XLSX', JSON.stringify(r.csv.flagged) === JSON.stringify(r.xlsx.flagged), '');
let rz = await runBoth({ zscore: true });
check('Z-Score 도 이상 감지(≥3행)', rz.csv.count >= 3, rz.csv.count);
let rif = await runBoth({ iforest: true, lof: true, dbscan: true });
check('ML 계열 이상 감지(≥3행)', rif.csv.count >= 3, rif.csv.count);

// ---- 03 중복 ----
console.log('[03 중복]');
p = await loadPair('sample_03_중복데이터');
r = await runBoth({ duplicate: true });
check('중복 행 {5,6,14,15,16}', JSON.stringify(r.csv.flagged) === JSON.stringify([5,6,14,15,16]), JSON.stringify(r.csv.flagged));
check('CSV=XLSX', JSON.stringify(r.csv.flagged) === JSON.stringify(r.xlsx.flagged), '');

// ---- 04 타입추론 ----
console.log('[04 타입추론]');
p = await loadPair('sample_04_타입추론');
r = await runBoth({});
const expectTypes = ['정수형:Number','실수형:Number','날짜_ISO:Date','날짜_슬래시:Date','불리언:String','문자열:String','숫자문자혼합:String'];
check('CSV 타입', JSON.stringify(r.csv.types) === JSON.stringify(expectTypes), JSON.stringify(r.csv.types));
check('XLSX 타입', JSON.stringify(r.xlsx.types) === JSON.stringify(expectTypes), JSON.stringify(r.xlsx.types));

// ---- 05 품질점수(복합) ----
console.log('[05 품질점수]');
p = await loadPair('sample_05_품질점수');
r = await runBoth({ missing: true, duplicate: true, iqr: true, zscore: true });
const rs = r.csv.reasons.join(' | ');
check('결측 포함', rs.includes('결측치'), rs.slice(0,120));
check('중복 포함', rs.includes('중복 데이터'), '');
check('이상치 포함(IQR)', rs.includes('IQR'), '');
check('CSV=XLSX', r.csv.count === r.xlsx.count, r.csv.count + ' vs ' + r.xlsx.count);

// ---- 06 기술통계 ----
console.log('[06 기술통계]');
p = await loadPair('sample_06_기술통계');
const statChk = await page.evaluate(() => {
  const A = window.__anomaly;
  const infos = A.ColumnAnalyzer.analyze(window.__tblCsv);
  const nc = A.ColumnAnalyzer.buildNumericConfigs(window.__tblCsv, infos);
  return nc.map(c => ({ n: c.name, min: c.actualMin, max: c.actualMax }));
});
check('숫자 컬럼 4개(학번 포함) min/max 계산', statChk.length === 4 && statChk.every(c => c.min <= c.max), JSON.stringify(statChk));

// ---- 07 상관관계 ----
console.log('[07 상관관계]');
p = await loadPair('sample_07_상관관계');
r = await runBoth({ iforest: true });
check('로드 + IF 동작(0~5행 이상)', r.csv.count >= 0 && r.csv.count <= 5, r.csv.count);
check('숫자 5컬럼', r.csv.types.filter(t => t.endsWith('Number')).length === 5, JSON.stringify(r.csv.types));

// ---- 08 분포분석 ----
console.log('[08 분포분석]');
p = await loadPair('sample_08_분포분석');
const riqr = await runBoth({ iqr: true });
const rzs = await runBoth({ zscore: true });
check('치우친 분포에서 IQR 탐지 ≥1', riqr.csv.count >= 1, riqr.csv.count);
check('IQR 과 Z-Score 결과가 다름(분포 영향)', riqr.csv.count !== rzs.csv.count, riqr.csv.count + ' vs ' + rzs.csv.count);

// ---- 09 파라미터 테스트 ----
console.log('[09 파라미터테스트]');
p = await loadPair('sample_09_파라미터테스트');
const z25 = await runBoth({ zscore: true }, { params: { zscoreThreshold: 2.5 } });
const z30 = await runBoth({ zscore: true }, { params: { zscoreThreshold: 3.0 } });
check('Z 2.5(3행) > Z 3.0(2행)', z25.csv.count === 3 && z30.csv.count === 2, z25.csv.count + ' vs ' + z30.csv.count);
const c50 = await runBoth({ change: true }, { params: { changeRateThreshold: 50 } });
const c100 = await runBoth({ change: true }, { params: { changeRateThreshold: 100 } });
const c200 = await runBoth({ change: true }, { params: { changeRateThreshold: 200 } });
check('증감률 50(3)>100(2)>200(1)', c50.csv.count === 3 && c100.csv.count === 2 && c200.csv.count === 1,
  [c50.csv.count, c100.csv.count, c200.csv.count].join('/'));

// ---- 10/11 종합 ----
console.log('[10 종합1 단일 분석]');
p = await loadPair('sample_10_종합1_2023산단현황');
r = await runBoth({ missing: true, duplicate: true, iqr: true, zscore: true });
const rs10 = r.csv.reasons.join(' | ');
check('결측/중복/이상치 모두 탐지', rs10.includes('결측치') && rs10.includes('중복 데이터') && rs10.includes('IQR'), rs10.slice(0,150));
check('CSV=XLSX', r.csv.count === r.xlsx.count, r.csv.count + ' vs ' + r.xlsx.count);
const types10 = r.csv.types.join(',');
check('날짜/숫자/문자 타입 혼합 인식', types10.includes('등록일:Date') && types10.includes('매출액(백만원):Number') && types10.includes('업체명:String'), types10);

// ---- 비교 검증: 종합1(A) vs 종합2(B) ----
console.log('[비교 검증: 종합1 vs 종합2]');
const cmp = await page.evaluate(async ({ aB64, bB64 }) => {
  const load = window.__loadTable;
  const tA = await load('a.csv', aB64);
  const tB = await load('b.xlsx', bB64);   // CSV ↔ XLSX 교차 비교
  const C = window.__compare;
  const hit = C.inferKeys(tA, tB);
  const result = C.compareTables(tA, tB, hit.i, hit.j, { useRate: true, useZ: true, useIqr: true, ratePct: 50, zTh: 3 });
  const anomalies = result.records.filter(r => r.tags.includes('이상 변동'))
    .map(r => r.key + ':' + r.cells.filter(c => c.anom && c.anom.length).map(c => c.col + '=' + c.anom.join('/')).join(','));
  return {
    keyA: tA.columns[hit.i], keyB: tB.columns[hit.j], score: Math.round(hit.score * 100) / 100,
    summary: result.summary, notes: result.notes, anomalies,
  };
}, { aB64: b64(`${DIR}/sample_10_종합1_2023산단현황.csv`), bB64: b64(`${DIR}/sample_11_종합2_2024산단현황.xlsx`) });

check('기준 컬럼 자동 추론 = 관리번호↔관리번호', cmp.keyA === '관리번호' && cmp.keyB === '관리번호', JSON.stringify([cmp.keyA, cmp.keyB, cmp.score]));
const s = cmp.summary;
check('총 35행', s.total === 35, s.total);
check('동일 16', s.same === 16, s.same);
check('변경 11', s.changed === 11, s.changed);
check('추가 4', s.added === 4, s.added);
check('삭제 4', s.removed === 4, s.removed);
// C-3: 결측치 변경도 이상 변동으로 판정 → 수치 이상 4행 + 결측 변경 2행 = 6행
check('이상 변동 6행(수치 4 + 결측 변경 2)', s.anomalyRows === 6, s.anomalyRows + ' :: ' + cmp.anomalies.join(' ; '));
check('결측값 변경 2셀', s.missingCells === 2, s.missingCells);
check('타입 변경 1셀', s.typeCells === 1, s.typeCells);
check('B전용 컬럼 안내(ESG등급)', cmp.notes.some(n => n.includes('ESG등급')), JSON.stringify(cmp.notes));
check('중복 키 안내', cmp.notes.some(n => n.includes('여러 번')), '');

// 같은 포맷(CSV↔CSV) 교차 검증
const cmp2 = await page.evaluate(async ({ aB64, bB64 }) => {
  const tA = await window.__loadTable('a.csv', aB64);
  const tB = await window.__loadTable('b.csv', bB64);
  const C = window.__compare;
  const hit = C.inferKeys(tA, tB);
  return C.compareTables(tA, tB, hit.i, hit.j, { useRate: true, useZ: true, useIqr: true, ratePct: 50, zTh: 3 }).summary;
}, { aB64: b64(`${DIR}/sample_10_종합1_2023산단현황.csv`), bB64: b64(`${DIR}/sample_11_종합2_2024산단현황.csv`) });
check('CSV↔CSV 결과 = CSV↔XLSX 결과', JSON.stringify(cmp2) === JSON.stringify(s), JSON.stringify(cmp2));

console.log('\n결과:', pass, 'passed /', fail, 'failed');
console.log('page errors:', errs.length ? errs.join('; ') : 'none');
await browser.close();
process.exit(fail ? 1 : 0);
