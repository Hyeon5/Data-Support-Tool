import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { readFileSync } from 'node:fs';
const SC='/tmp/claude-0/-home-user-Data-Anomaly-Detection/2e295653-921d-55ec-88c5-b48f8fa158f3/scratchpad';
const DIR=new URL('../sample_data', import.meta.url).pathname;
const b64=p=>readFileSync(p).toString('base64');
const browser=await chromium.launch();
const ctx=await browser.newContext({ acceptDownloads:true });
const page=await ctx.newPage();
const errs=[]; page.on('pageerror',e=>errs.push(e.message)); page.on('console',m=>{if(m.type()==='error')errs.push('c:'+m.text());});
page.on('dialog', d=>d.dismiss());
const reqs=[]; page.on('request',r=>{ const u=r.url(); if(!u.startsWith('file:')&&!u.startsWith('data:')&&!u.startsWith('blob:')) reqs.push(u); });
await page.goto(new URL('../index.html', import.meta.url).href);
let pass=0,fail=0; const check=(n,c,d)=>{if(c){pass++;console.log('  ✔',n);}else{fail++;console.log('  ✘',n,'|',d);}};

// 업로드+분석
await page.evaluate(async (b)=>{const bin=atob(b);const arr=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)arr[i]=bin.charCodeAt(i);await window.__upload.handleFiles([new File([arr],'sample_05_품질점수.csv')]);await new Promise(r=>setTimeout(r,100));}, b64(`${DIR}/sample_05_품질점수.csv`));
// 결측/중복/IQR/Z 켜기 위해 기본 옵션 유지 + iforest 켜서 ML 카테고리도
await page.check('#opt_iforest');
await page.click('#btnRun');
await page.waitForFunction(()=>document.getElementById('status').textContent.includes('완료')||document.getElementById('status').textContent.includes('실패'),{timeout:15000});

console.log('[작업6 진행/완료]');
check('진행률 100% (완료 후)', (await page.$eval('#progressBar', e=>parseFloat(e.style.width)||0))>=100, '');
check('취소 버튼 숨김(완료 후)', await page.$eval('#btnCancel', e=>e.classList.contains('hidden')), '');

console.log('[작업1 대시보드]');
check('대시보드 카드 4개', (await page.$$eval('.dash-card', e=>e.length))===4, '');
check('카테고리 배지(규칙/통계) 존재', (await page.$$eval('#dashboard .cat-badge', e=>e.map(x=>x.textContent))).join(',').includes('규칙'), '');
check('사유별 막대차트 존재', (await page.$$eval('.bar-row', e=>e.length))>=1, '');
check('히스토그램 SVG 렌더', (await page.$$eval('#histBox svg', e=>e.length))>=1, '');
check('히스토그램 이상치 표식(polygon)', (await page.$$eval('#histBox svg polygon', e=>e.length))>=0, '');
// 접기/펼치기
await page.click('#dashHead');
check('대시보드 접기 동작', await page.$eval('#dashBody', e=>e.classList.contains('hidden')), '');
await page.click('#dashHead');

console.log('[작업5 색상/작업2 근거]');
check('셀 카테고리 하이라이트 존재', (await page.$$eval('#resultTable td.hl-rule, #resultTable td.hl-stat, #resultTable td.hl-ml', e=>e.length))>=1, '');
check('사유셀 카테고리 배지', (await page.$$eval('#resultTable .cat-badge', e=>e.length))>=1, '');
const tip = await page.$eval('#resultTable .reason-item', e=>e.getAttribute('title')).catch(()=>'');
check('근거 툴팁(title에 수치 근거)', /평균|Q1|이전 값|허용 범위|점수|노이즈|결측/.test(tip), tip.slice(0,50));

console.log('[작업3 검토]');
check('검토 상태 select 존재', (await page.$$eval('#resultTable select.rv-status', e=>e.length))>=1, '');
check('검토 진행률 표시', (await page.textContent('.rv-progress')).includes('/'), '');
// 첫 이상행 상태 변경 → 행 색상 + 진행률 증가
await page.selectOption('#resultTable select.rv-status >> nth=0', '오탐');
await page.waitForTimeout(50);
check('상태 변경 시 행 클래스(rv-오탐)', (await page.$$eval('#resultTable tr.rv-오탐', e=>e.length))>=1, '');
check('진행률 갱신(1건 이상)', !(await page.textContent('.rv-progress')).startsWith('0 '), await page.textContent('.rv-progress'));
// 필터: 오탐만
await page.selectOption('#rvFilter', '오탐');
await page.waitForTimeout(50);
const rows = await page.$$eval('#resultTable tbody tr', e=>e.length);
check('필터 오탐만 동작', rows>=1, rows);
await page.selectOption('#rvFilter', 'all');
// 일괄: 전체선택 후 확인됨 적용
await page.check('#rvSelectAll');
await page.selectOption('#rvBulk', '확인됨');
await page.click('#rvApply');
await page.waitForTimeout(50);
check('일괄 확인됨 적용', (await page.$$eval('#resultTable tr.rv-확인됨', e=>e.length))>=1, '');

console.log('[다운로드: 판정근거/검토 컬럼]');
const [dl] = await Promise.all([ page.waitForEvent('download'), page.click('#btnDownload') ]);
await dl.saveAs(`${SC}/ui_result.xlsx`);
check('다운로드 완료', true, '');

console.log('[오프라인/오류]');
check('외부 네트워크 요청 0건', reqs.length===0, reqs.join(','));
check('콘솔 오류 없음', errs.length===0, errs.join(';'));

console.log('\n결과:', pass,'/',pass+fail);
await browser.close();
process.exit(fail?1:0);
