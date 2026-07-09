import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { readFileSync } from 'node:fs';
const SC = '/tmp/claude-0/-home-user-Data-Anomaly-Detection/2e295653-921d-55ec-88c5-b48f8fa158f3/scratchpad';
const b64 = p => readFileSync(p).toString('base64');
const browser = await chromium.launch();
const page = await browser.newPage();
const errs=[]; page.on('pageerror',e=>errs.push(e.message)); page.on('console',m=>{if(m.type()==='error')errs.push('c:'+m.text());});
const DIR = new URL('../sample_data', import.meta.url).pathname;
await page.goto(new URL('../index.html', import.meta.url).href);
await page.addStyleTag({ content: '.panel.coll.collapsed>:not(h2){display:block !important}' });
let pass=0,fail=0; const check=(n,c,d)=>{if(c){pass++;console.log('  ✔',n);}else{fail++;console.log('  ✘',n,'|',d);}};
const up = (id, b, name) => page.evaluate(async ({id,b,name})=>{
  const bin=atob(b);const arr=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)arr[i]=bin.charCodeAt(i);
  if(id==='single'){ await window.__upload.handleFiles([new File([arr],name)]); }
  await new Promise(r=>setTimeout(r,120));
},{id,b,name});

console.log('[단일 분석: 다중 시트 드롭다운]');
await up('single', b64(`${SC}/multi.xlsx`), 'multi.xlsx');
check('시트 드롭다운 노출', !(await page.$eval('#sheetRow', e=>e.classList.contains('hidden'))), '');
check('옵션 3개', (await page.$$eval('#sheetSelect option', o=>o.map(x=>x.textContent))).join(',')==='Sheet1,데이터,빈시트', '');
check('기본 Sheet1 로드(이름/점수)', (await page.textContent('#fileInfo')).includes('이름(String)') && (await page.textContent('#fileInfo')).includes("시트 'Sheet1'"), await page.textContent('#fileInfo'));
// 시트 변경 → 데이터 시트
await page.selectOption('#sheetSelect', '1');
await page.waitForTimeout(100);
check('시트 변경 시 컬럼 갱신(코드/수량/단가)', (await page.textContent('#fileInfo')).includes('코드(String)') && (await page.textContent('#fileInfo')).includes('단가(Number)'), await page.textContent('#fileInfo'));
check('숫자 컬럼 설정표도 갱신(수량,단가)', (await page.$$eval('#numTableBody tr td:first-child', t=>t.map(x=>x.textContent))).join(',').includes('수량'), '');
// 빈 시트 선택
await page.selectOption('#sheetSelect', '2');
await page.waitForTimeout(100);
check('빈 시트 선택 시 안내', (await page.textContent('#status')).includes('데이터가 없습니다'), await page.textContent('#status'));
// 분석 실행 확인(데이터 시트로 되돌려서)
await page.selectOption('#sheetSelect', '1');
await page.waitForTimeout(100);
await page.evaluate(()=>document.getElementById('btnRun').click());
await page.waitForFunction(()=>/완료|실패/.test(document.getElementById('status').textContent),{timeout:10000});
check('선택 시트로 분석 완료', (await page.textContent('#status')).includes('완료'), await page.textContent('#status'));

console.log('[단일 시트 파일은 드롭다운 숨김]');
await up('single', b64(DIR+'/sample_02_이상치.csv'), 'x.csv');
check('CSV: 시트 드롭다운 숨김', await page.$eval('#sheetRow', e=>e.classList.contains('hidden')), '');

console.log('[비교 검증: 시트 선택 후 비교]');
await page.click('#railCompare');
// A = multi.xlsx (데이터 시트), B = multi.xls (둘째장)
await page.evaluate(async ({a,b})=>{
  const mk=(s,n)=>{const bin=atob(s);const arr=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)arr[i]=bin.charCodeAt(i);return new File([arr],n);};
  await window.__compare.handleSlotFile('A', mk(a,'multi.xlsx'));
  await window.__compare.handleSlotFile('B', mk(b,'multi.xls'));
  await new Promise(r=>setTimeout(r,150));
},{a:b64(`${SC}/multi.xlsx`), b:b64(`${SC}/multi.xls`)});
check('A 시트 드롭다운 노출(3옵션)', !(await page.$eval('#sheetRowA',e=>e.classList.contains('hidden'))) && (await page.$$eval('#sheetA option',o=>o.length))===3, '');
check('B 시트 드롭다운 노출(2옵션)', !(await page.$eval('#sheetRowB',e=>e.classList.contains('hidden'))) && (await page.$$eval('#sheetB option',o=>o.length))===2, '');
// A → 데이터 시트(코드,수량,단가), B → 둘째장(x,y,z)
await page.selectOption('#sheetA','1'); await page.waitForTimeout(80);
await page.selectOption('#sheetB','1'); await page.waitForTimeout(80);
const aInfo = await page.textContent('#dzAText');
check('비교 버튼 활성', !(await page.$eval('#btnCompare',e=>e.disabled)), '');
// 기준 컬럼 확인(둘 다 코드/x 다르지만 자동 or 수동). 그냥 비교 실행되는지
await page.click('#btnCompare');
await page.waitForFunction(()=>document.getElementById('cmpStatus').textContent.includes('완료'),{timeout:10000}).catch(()=>{});
check('선택 시트 기준으로 비교 완료', (await page.textContent('#cmpStatus')).includes('완료'), await page.textContent('#cmpStatus'));

console.log('\n결과:', pass,'/',pass+fail,'| 오류:', errs.join(';')||'없음');
await browser.close();
process.exit(fail||errs.length?1:0);
