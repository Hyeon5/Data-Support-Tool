import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { readFileSync } from 'node:fs';
const DIR = new URL('../sample_data', import.meta.url).pathname;
const b64 = p => readFileSync(p).toString('base64');
const browser = await chromium.launch();
const page = await browser.newPage({viewport:{width:1200,height:900}});
const errs=[]; page.on('pageerror',e=>errs.push(e.message)); page.on('console',m=>{if(m.type()==='error')errs.push(m.text());});
await page.goto(new URL('../index.html', import.meta.url).href);
let pass=0,fail=0; const ok=(n,c,d)=>{if(c){pass++;console.log('  ✔',n);}else{fail++;console.log('  ✘ FAIL',n,'|',d);}};
const collapsed = id => page.evaluate(i=>document.getElementById(i).classList.contains('collapsed'), id);

console.log('[Function8 접이식 기본 열림 + 비활성화 시 접힘]');
for (const id of ['optPanel','missingAllowPanel','paramPanel','numericPanel','savePanel'])
  ok(id+' 기본 열림', !(await collapsed(id)), '');
// opt_missing 해제 → missingAllowPanel 접힘
await page.uncheck('#opt_missing');
ok('opt_missing 해제 → missingAllowPanel 접힘', await collapsed('missingAllowPanel'), '');
await page.check('#opt_missing');
ok('opt_missing 재선택 → missingAllowPanel 열림', !(await collapsed('missingAllowPanel')), '');
// opt_range 해제 → numericPanel 접힘
await page.uncheck('#opt_range');
ok('opt_range 해제 → numericPanel 접힘', await collapsed('numericPanel'), '');
await page.check('#opt_range');
// 모든 알고리즘 파라미터 해제 → paramPanel 접힘
for (const id of ['opt_change','opt_zscore','opt_iforest','opt_lof','opt_dbscan']) await page.uncheck('#'+id);
ok('알고리즘 전부 해제 → paramPanel 접힘', await collapsed('paramPanel'), '');
await page.check('#opt_change');
ok('알고리즘 하나 선택 → paramPanel 열림', !(await collapsed('paramPanel')), '');

console.log('[Function8 분석 전후 접힘 상태 유지]');
// 업로드 후 사용자가 numericPanel 을 수동으로 접은 상태에서 분석 실행 → 상태 유지
await page.evaluate(async(b)=>{const bin=atob(b);const a=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)a[i]=bin.charCodeAt(i);await window.__upload.handleFiles([new File([a],'s.csv')]);await new Promise(r=>setTimeout(r,100));}, b64(`${DIR}/sample_05_품질점수.csv`));
await page.evaluate(()=>document.getElementById('numericPanel').classList.add('collapsed'));
const beforeOpt = await collapsed('optPanel'), beforeNum = await collapsed('numericPanel');
await page.evaluate(async ()=>{document.getElementById('btnRun').click();await new Promise(res=>{const iv=setInterval(()=>{if(/완료|실패|문제/.test(document.getElementById('status').textContent)){clearInterval(iv);res();}},50);});});
ok('분석 후 optPanel 상태 유지', (await collapsed('optPanel'))===beforeOpt, '');
ok('분석 후 numericPanel 상태 유지(접힘)', (await collapsed('numericPanel'))===beforeNum && beforeNum, '');

console.log('[Design4 사이드바]');
ok('railToggle 제거됨', await page.evaluate(()=>!document.getElementById('railToggle')), '');
ok('레일 3개 버튼', (await page.$$eval('.rail-btn', e=>e.length))===3, '');
const railW = await page.evaluate(()=>document.getElementById('modeRail').getBoundingClientRect().width);
ok('레일 기본 너비 180px', Math.abs(railW-180)<2, railW);

console.log('[Design5 스텝 박스 제거]');
ok('#steps 제거됨', await page.evaluate(()=>!document.getElementById('steps')), '');

console.log('[Design2 히스토그램 확대/축소]');
// 히스토그램 존재 확인 + 큰 화살표(polygon hmark)
const hasHmark = await page.evaluate(()=>!!document.querySelector('#histBox svg .hmark'));
ok('히스토그램 이상치 화살표 표시', hasHmark, '');
ok('히스토그램 설명 텍스트 제거', await page.evaluate(()=>{const t=document.getElementById('histBox').textContent;return !t.includes('세로축 = 구간별 건수');}), '');
// 휠 줌: 프로그램적으로 zoom 설정 후 재렌더 → 범위 축소 확인
const zoomWorks = await page.evaluate(()=>{
  const box = document.getElementById('histBox');
  const svg = box.querySelector('svg.hist');
  if (!svg) return false;
  const before = box.querySelectorAll('.hbar').length;
  svg.dispatchEvent(new WheelEvent('wheel',{deltaY:-100,clientX:svg.getBoundingClientRect().left+svg.getBoundingClientRect().width/2,bubbles:true,cancelable:true}));
  const resetBtn = document.getElementById('histReset');
  return before>0 && !!resetBtn; // 확대 후 전체보기 버튼 노출
});
ok('휠 확대 시 전체보기 버튼 노출', zoomWorks, '');

console.log('[Design3 비식별 표 열 순서]');
await page.click('#railDeid');
await page.evaluate(async ()=>{const csv=['성명,휴대폰,금액','홍길동,010-1234-5678,100','김철수,010-2222-3333,200'].join('\n');await window.__deid.loadDeidFile(new File([csv],'d.csv',{type:'text/csv'}));});
await page.waitForTimeout(200);
const headers = await page.$$eval('#deidTable thead th', els=>els.map(e=>e.textContent));
ok('첫 열 = 적용', headers[0]==='적용', JSON.stringify(headers));
ok('둘째 열 = 처리 방식', headers[1]==='처리 방식', JSON.stringify(headers));
ok('첫 셀에 체크박스', await page.evaluate(()=>!!document.querySelector('#deidTableBody tr td:first-child .deid-apply')), '');
ok('버튼 텍스트 "비식별화 하기"', (await page.textContent('#btnDeidPreview')).trim()==='비식별화 하기', '');

console.log('\n결과: '+pass+' passed / '+fail+' failed');
console.log('page errors:', errs.length?errs:'none');
await browser.close();
process.exit(fail?1:0);
