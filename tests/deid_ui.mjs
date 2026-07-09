import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const browser = await chromium.launch();
const page = await browser.newPage();
const errs=[]; page.on('pageerror', e=>errs.push(e.message));
let dl=null; page.on('download', d=>{dl=d;});
await page.goto(new URL('../index.html', import.meta.url).href);
let pass=0,fail=0; const ok=(c,m)=>{if(c){pass++;console.log('  ✔',m);}else{fail++;console.log('  ✘ FAIL',m);}};

// switch to deid mode via rail
await page.click('#railDeid');
ok(await page.evaluate(()=>!document.getElementById('viewDeid').classList.contains('hidden')),'레일 클릭 → viewDeid 표시');
ok(await page.evaluate(()=>document.getElementById('viewSingle').classList.contains('hidden')),'viewSingle 숨김');

// build CSV file in-page and load through __deid.loadDeidFile
await page.evaluate(async () => {
  const csv = ['성명,휴대폰,이메일,주민등록번호,산단명,금액,주소',
    '홍길동,010-1234-5678,hong@example.com,900101-1234567,반월산업단지,1000,서울특별시 강남구 테헤란로 1',
    '김철수,010-9876-5432,kim@test.co.kr,850505-2234567,시화산업단지,2000,경기도 성남시 분당구 2',
    '이영희,010-5555-6666,lee@abc.org,770303-2345678,남동산업단지,3000,부산광역시 해운대구 3'].join('\n');
  const f = new File([csv], 'test.csv', {type:'text/csv'});
  await window.__deid.loadDeidFile(f);
});
await page.waitForTimeout(200);
ok(await page.evaluate(()=>!document.getElementById('deidConfigPanel').classList.contains('hidden')),'설정 패널 표시');
const rowCount = await page.evaluate(()=>document.querySelectorAll('#deidTableBody tr').length);
ok(rowCount===7,'모든 7개 컬럼이 표에 나열됨 ('+rowCount+')');
const detTypes = await page.evaluate(()=>window.__deid.getDetections().map(d=>d.type));
ok(JSON.stringify(detTypes)===JSON.stringify(['name','phone','email','rrn',null,null,'address']),'유형 추정 정확: '+JSON.stringify(detTypes));

// preview
await page.click('#btnDeidPreview');
await page.waitForTimeout(100);
ok(await page.evaluate(()=>!document.getElementById('deidPreviewPanel').classList.contains('hidden')),'미리보기 패널 표시');
const previewHasArrow = await page.evaluate(()=>document.querySelector('#deidPreviewTable tbody').innerHTML.includes('→'));
ok(previewHasArrow,'미리보기에 원본→변환 표시');

// summary card
ok(await page.evaluate(()=>document.getElementById('deidSummary').textContent.includes('적용 컬럼')),'요약 카드 표시');

// download
await page.click('#btnDeidDownload');
await page.waitForTimeout(300);
ok(dl!==null,'다운로드 트리거됨');
if(dl) ok(dl.suggestedFilename().endsWith('.xlsx'),'파일명 .xlsx');

console.log(`\n결과: ${pass} passed / ${fail} failed`);
console.log('page errors:', errs.length?errs:'none');
await browser.close();
process.exit(fail?1:0);
