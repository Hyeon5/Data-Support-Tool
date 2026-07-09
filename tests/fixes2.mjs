import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { readFileSync } from 'node:fs';
const DIR = new URL('../sample_data', import.meta.url).pathname;
const b64 = p => readFileSync(p).toString('base64');
const browser = await chromium.launch();
const page = await browser.newPage();
const errs=[]; page.on('pageerror',e=>errs.push(e.message));
page.on('console', m=>{ if(m.type()==='error') errs.push('[console] '+m.text()); });
await page.clock.install();
await page.goto(new URL('../index.html', import.meta.url).href);
await page.addStyleTag({ content: '.panel.coll.collapsed>:not(h2){display:block !important}' });
let pass=0,fail=0; const ok=(n,c,d)=>{if(c){pass++;console.log('  ✔',n);}else{fail++;console.log('  ✘ FAIL',n,'|',d);}};

const upload = (b64s,name)=>page.evaluate(async ({b64s,name})=>{
  const bin=atob(b64s);const arr=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)arr[i]=bin.charCodeAt(i);
  await window.__upload.handleFiles([new File([arr],name)]);
  await new Promise(r=>setTimeout(r,80));
},{b64s,name});

console.log('[A-1 파라미터 클램프(0/음수/공백)]');
await upload(b64(`${DIR}/sample_10_종합1_2023산단현황.csv`),'s.csv');
// 잘못된 값 주입 후 분석 실행 → collectConfig 가 입력창에 보정값을 반영
await page.evaluate(()=>{ ['opt_iforest','opt_lof','opt_dbscan'].forEach(id=>{const e=document.getElementById(id);e.checked=true;e.dispatchEvent(new Event('change',{bubbles:true}));}); });
await page.fill('#p_change','-10');
await page.fill('#p_zscore','0');
await page.fill('#p_neighbors','0.5');
await page.fill('#p_contam','9');
await page.fill('#p_eps','0');
await page.fill('#p_minsamples','');
await page.evaluate(async ()=>{
  document.getElementById('btnRun').click();
  await new Promise(res=>{const iv=setInterval(()=>{if(/완료|실패|문제|취소/.test(document.getElementById('status').textContent)){clearInterval(iv);res();}},50);});
});
ok('p_change 음수 → 0 이상', parseFloat(await page.inputValue('#p_change'))>=0, await page.inputValue('#p_change'));
ok('p_zscore 0 → 0.1 이상', parseFloat(await page.inputValue('#p_zscore'))>=0.1, await page.inputValue('#p_zscore'));
ok('p_neighbors 0.5 → 정수 1 이상', Number.isInteger(parseFloat(await page.inputValue('#p_neighbors'))) && parseFloat(await page.inputValue('#p_neighbors'))>=1, await page.inputValue('#p_neighbors'));
ok('p_contam 9 → 0.5 이하', parseFloat(await page.inputValue('#p_contam'))<=0.5, await page.inputValue('#p_contam'));
ok('p_eps 0 → 0.01 이상', parseFloat(await page.inputValue('#p_eps'))>=0.01, await page.inputValue('#p_eps'));
ok('p_minsamples 공백 → 기본 5', parseFloat(await page.inputValue('#p_minsamples'))>=1, await page.inputValue('#p_minsamples'));

console.log('[A-3 일괄 적용 시 표시 필터 유지]');
// 결과가 있는 상태에서 rvFilter 를 '미검토'로 바꾸고 한 행 선택 후 일괄 적용
const hasReview = await page.evaluate(()=>!!document.getElementById('rvFilter'));
if (hasReview) {
  await page.selectOption('#rvFilter','미검토');
  await page.evaluate(()=>{ const cb=document.querySelector('#resultTable .rv-check'); if(cb) cb.checked=true; document.getElementById('rvBulk').value='확인됨'; document.getElementById('rvApply').click(); });
  ok('일괄 적용 후 rvFilter 값 유지(미검토)', (await page.inputValue('#rvFilter'))==='미검토', await page.inputValue('#rvFilter'));
} else { ok('일괄 적용 후 rvFilter 값 유지(미검토)', false, 'rvFilter 없음(이상 행 없음)'); }

console.log('[A-2 2단계 취소 버튼]');
await page.evaluate(()=>{ const b=document.getElementById('btnCancel'); b.classList.remove('hidden'); b.disabled=false; b.click(); });
ok('1차 클릭 → 즉시 비활성(취소 중)', await page.evaluate(()=>document.getElementById('btnCancel').disabled)===true, '');
await page.clock.fastForward(5100);
ok('5초 경과 → "즉시 중단(결과 폐기)"로 전환', (await page.textContent('#btnCancel')).includes('즉시 중단'), await page.textContent('#btnCancel'));
ok('전환 시 danger 클래스', await page.evaluate(()=>document.getElementById('btnCancel').classList.contains('danger')), '');
await page.evaluate(()=>document.getElementById('btnCancel').click());
ok('2차 클릭 → 버튼 초기화(분석 취소)+숨김', await page.evaluate(()=>{const b=document.getElementById('btnCancel');return b.textContent==='분석 취소'&&b.classList.contains('hidden');}), await page.textContent('#btnCancel'));
ok('즉시 중단 상태 문구 안내', (await page.textContent('#status')).includes('즉시 중단'), await page.textContent('#status'));

console.log('\n결과: '+pass+' passed / '+fail+' failed');
console.log('page errors:', errs.length?errs:'none');
await browser.close();
process.exit(fail?1:0);
