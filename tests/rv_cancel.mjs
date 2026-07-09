import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { readFileSync } from 'node:fs';
const DIR=new URL('../sample_data', import.meta.url).pathname;
const b64=p=>readFileSync(p).toString('base64');
const browser=await chromium.launch();
const page=await browser.newPage();
const errs=[]; page.on('pageerror',e=>errs.push(e.message));
let acceptNext=false;
page.on('dialog', async d=>{ if(acceptNext && d.type()==='confirm'){ acceptNext=false; await d.accept(); } else { await d.dismiss(); } });
await page.goto(new URL('../index.html', import.meta.url).href);
let pass=0,fail=0; const check=(n,c,d)=>{if(c){pass++;console.log('  ✔',n);}else{fail++;console.log('  ✘',n,'|',d);}};
const upload=(b,name)=>page.evaluate(async({b,name})=>{const bin=atob(b);const arr=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)arr[i]=bin.charCodeAt(i);await window.__upload.handleFiles([new File([arr],name)]);await new Promise(r=>setTimeout(r,100));},{b,name});
const runDone=()=>page.waitForFunction(()=>/완료|취소|실패/.test(document.getElementById('status').textContent),{timeout:20000});

console.log('[작업3 localStorage 저장/복원]');
// 1차: 분석 → 첫 이상행 오탐 + 메모
await upload(b64(`${DIR}/sample_01_결측치.csv`),'sample_01_결측치.csv');
await page.click('#btnRun'); await runDone();
await page.selectOption('#resultTable select.rv-status >> nth=0', '오탐');
await page.fill('#resultTable input.rv-memo >> nth=0', '테스트메모');
await page.waitForTimeout(50);
const savedKeys = await page.evaluate(()=>Object.keys(localStorage).filter(k=>k.startsWith('davReview:')));
check('localStorage에 검토 저장됨', savedKeys.length>=1, JSON.stringify(savedKeys));
// 2차: 같은 파일 재분석 → confirm 수락 → 복원
acceptNext=true;
await upload(b64(`${DIR}/sample_01_결측치.csv`),'sample_01_결측치.csv');
await page.click('#btnRun'); await runDone();
await page.waitForTimeout(100);
const restoredStatus = await page.$eval('#resultTable select.rv-status >> nth=0', e=>e.value).catch(()=>'');
const restoredMemo = await page.$eval('#resultTable input.rv-memo >> nth=0', e=>e.value).catch(()=>'');
check('오탐 상태 복원', restoredStatus==='오탐', restoredStatus);
check('메모 복원', restoredMemo==='테스트메모', restoredMemo);

console.log('[작업6 분석 취소 메커니즘(결정적)]');
const cancelRes = await page.evaluate(async ()=>{
  const A=window.__anomaly;
  let s=5>>>0; const rnd=()=>{s=(s+0x6D2B79F5)|0;let t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};
  const rows=[]; for(let i=0;i<400;i++) rows.push([Math.round(rnd()*100*1000)/1000, Math.round(rnd()*100*1000)/1000]);
  const t=new A.TableWrapper(['x','y'],rows);
  const cfg={ missing:1,duplicate:1,range:0,change:0,iqr:1,zscore:1,iforest:1,lof:1,dbscan:1,changeRateThreshold:100,zscoreThreshold:3,isoContamination:0.05,lofNeighbors:20,dbscanEps:0.5,dbscanMinSamples:5,numericConfigs:[],missingAllowCols:[] };
  // ML 단계 진입 시 취소 요청 → 그 이후 검사는 수행되지 않아야 함
  let sawStat=false;
  const res = await A.runAnalysis(t, cfg, (pct,msg,extra)=>{ if(extra&&extra.stage==='ml'){ window.ANALYSIS_CANCELLED=true; } if(extra&&extra.stage==='stat') sawStat=true; });
  return { cancelled: res.cancelled, used: res.usedAlgos, sawStat };
});
check('취소 플래그로 cancelled=true', cancelRes.cancelled===true, JSON.stringify(cancelRes));
check('취소 이후 ML 검사 미수행', !cancelRes.used.includes('LOF') && !cancelRes.used.includes('DBSCAN'), JSON.stringify(cancelRes.used));
check('취소 전 규칙/통계는 수행', cancelRes.used.includes('결측치') && cancelRes.used.includes('IQR'), JSON.stringify(cancelRes.used));

check('콘솔 오류 없음', errs.length===0, errs.join(';'));
console.log('\n결과:', pass,'/',pass+fail);
await browser.close();
process.exit(fail?1:0);
