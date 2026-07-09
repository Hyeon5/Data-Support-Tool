import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { readFileSync, readdirSync } from 'node:fs';
const SC = '/tmp/claude-0/-home-user-Data-Anomaly-Detection/2e295653-921d-55ec-88c5-b48f8fa158f3/scratchpad';
const DIR = new URL('../sample_data', import.meta.url).pathname;
const b64 = p => readFileSync(p).toString('base64');
const browser = await chromium.launch();
const page = await browser.newPage();
const errs = [];
page.on('pageerror', e => errs.push(e.message));
await page.goto(new URL('../index.html', import.meta.url).href);
let pass=0, fail=0;
const check=(n,c,d)=>{ if(c){pass++;console.log('  ✔',n);}else{fail++;console.log('  ✘',n,'|',d);} };

await page.evaluate(() => {
  window.__wb = async (b64, name) => {
    const bin = atob(b64); const arr = new Uint8Array(bin.length);
    for (let i=0;i<bin.length;i++) arr[i]=bin.charCodeAt(i);
    const wb = await window.__readers.loadWorkbook(new File([arr], name));
    return { sheets: wb.sheets, multi: wb.multi, sheetData: wb.sheets.map((_,i)=>{ const t=wb.readSheet(i); return {cols:t.columns, n:t.rows.length, first:t.rows[0]}; }) };
  };
  window.__rf = async (b64, name) => {
    const bin = atob(b64); const arr = new Uint8Array(bin.length);
    for (let i=0;i<bin.length;i++) arr[i]=bin.charCodeAt(i);
    return await window.__readers.readFile(new File([arr], name));
  };
});

console.log('[다중 시트 xlsx]');
let r = await page.evaluate((b)=>window.__wb(b,'multi.xlsx'), b64(`${SC}/multi.xlsx`));
check('시트 3개 이름', JSON.stringify(r.sheets)===JSON.stringify(['Sheet1','데이터','빈시트']), JSON.stringify(r.sheets));
check('multi=true', r.multi===true, '');
check('Sheet1 컬럼', JSON.stringify(r.sheetData[0].cols)===JSON.stringify(['이름','점수']) && r.sheetData[0].n===4, JSON.stringify(r.sheetData[0]));
check('데이터 시트 컬럼', JSON.stringify(r.sheetData[1].cols)===JSON.stringify(['코드','수량','단가']) && r.sheetData[1].n===4, JSON.stringify(r.sheetData[1]));

console.log('[제목/빈행/빈열 오프셋 xlsx 자동탐지]');
r = await page.evaluate((b)=>window.__wb(b,'offset.xlsx'), b64(`${SC}/offset.xlsx`));
check('헤더 자동탐지(산단명/주소/업체수)', JSON.stringify(r.sheetData[0].cols)===JSON.stringify(['산단명','주소','업체수']), JSON.stringify(r.sheetData[0].cols));
check('데이터 5행', r.sheetData[0].n===5, r.sheetData[0].n);
check('첫 데이터=구미/경북/120', JSON.stringify(r.sheetData[0].first)===JSON.stringify(['구미','경북',120]), JSON.stringify(r.sheetData[0].first));

console.log('[다중 시트 xls]');
r = await page.evaluate((b)=>window.__wb(b,'multi.xls'), b64(`${SC}/multi.xls`));
check('xls 시트 2개', JSON.stringify(r.sheets)===JSON.stringify(['첫번째','둘째장']), JSON.stringify(r.sheets));
check('첫번째 컬럼 a,b n=3', JSON.stringify(r.sheetData[0].cols)===JSON.stringify(['a','b']) && r.sheetData[0].n===3, JSON.stringify(r.sheetData[0]));
check('둘째장 컬럼 x,y,z n=2', JSON.stringify(r.sheetData[1].cols)===JSON.stringify(['x','y','z']) && r.sheetData[1].n===2, JSON.stringify(r.sheetData[1]));

console.log('[CSV 헤더 자동탐지]');
let t = await page.evaluate((b)=>window.__rf(b,'blanktop.csv'), b64(`${SC}/blanktop.csv`));
check('앞쪽 빈 행 무시', JSON.stringify(t.columns)===JSON.stringify(['산단명','주소','업체수']) && t.rows.length===3, JSON.stringify(t.columns)+' n='+t.rows.length);
t = await page.evaluate((b)=>window.__rf(b,'titled.csv'), b64(`${SC}/titled.csv`));
check('제목행 무시', JSON.stringify(t.columns)===JSON.stringify(['산단명','주소','업체수']) && t.rows.length===4, JSON.stringify(t.columns)+' n='+t.rows.length);

console.log('[기존 22개 샘플 회귀 (readFile 결과 불변)]');
const samples = readdirSync(DIR).filter(f=>/\.(csv|xlsx)$/.test(f));
let regFail=0;
for (const f of samples) {
  const res = await page.evaluate((o)=>window.__rf(o.b,o.n).then(t=>({cols:t.columns.length, rows:t.rows.length})).catch(e=>({err:e.message})), {b:b64(`${DIR}/${f}`), n:f});
  if (res.err) { console.log('  ✘', f, res.err); regFail++; }
}
check('22개 샘플 전부 오류 없이 읽힘', regFail===0, regFail+'건 실패');

console.log('\n결과:', pass,'/',pass+fail,'| 오류:', errs.join(';')||'없음');
await browser.close();
process.exit(fail||errs.length?1:0);
