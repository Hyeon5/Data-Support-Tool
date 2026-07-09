import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { readFileSync } from 'node:fs';
const S='/tmp/claude-0/-home-user-Data-Anomaly-Detection/2e295653-921d-55ec-88c5-b48f8fa158f3/scratchpad';
const DIR = new URL('../sample_data', import.meta.url).pathname;
const b64=p=>readFileSync(p).toString('base64');
const browser=await chromium.launch();
const page=await browser.newPage({viewport:{width:1050,height:900}});
page.on('dialog',d=>d.dismiss());
const errs=[]; page.on('pageerror',e=>errs.push(e.message));
await page.goto(new URL('../index.html', import.meta.url).href);
await page.evaluate(async(b)=>{const bin=atob(b);const arr=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)arr[i]=bin.charCodeAt(i);await window.__upload.handleFiles([new File([arr],'sample_05_품질점수.csv')]);await new Promise(r=>setTimeout(r,100));}, b64(DIR+'/sample_05_품질점수.csv'));
await page.check('#opt_iforest');
await page.click('#btnRun');
await page.waitForFunction(()=>document.getElementById('status').textContent.includes('완료'),{timeout:15000});
let pass=0,fail=0; const check=(n,c,d)=>{if(c){pass++;console.log('  ✔',n);}else{fail++;console.log('  ✘',n,'|',d);}};

// (a) 막대 폭 합 = 100%
const widths = await page.$$eval('.bar-fill', els=>els.map(e=>parseFloat(e.style.width)));
const sum = widths.reduce((a,b)=>a+b,0);
check('막대 폭 합 ≈ 100% ('+sum.toFixed(1)+'%)', Math.abs(sum-100)<1.5, JSON.stringify(widths));
check('건수+비율 라벨 표기', (await page.$$eval('.bar-row .val .pct', e=>e.length))>=1, '');
check('바 hover 툴팁(title)', (await page.$eval('.bar-row', e=>e.getAttribute('title')||'')).includes('전체의'), '');

// (b) 히스토그램 세로축/툴팁
check('세로축 눈금 라벨(≥2개)', (await page.$$eval('#histBox svg text', e=>e.filter(t=>t.getAttribute('text-anchor')==='end'&&parseFloat(t.getAttribute('font-size'))===9).length))>=2, '');
check('가로 눈금선 존재', (await page.$$eval('#histBox svg line', e=>e.length))>=3, '');
const barTitle = await page.$eval('#histBox .hbar title', e=>e.textContent);
check('막대 title=구간+건수+비율', /구간 .+ ~ .+/.test(barTitle) && /건수 \d/.test(barTitle) && /%/.test(barTitle), barTitle);
const markTitle = await page.$eval('#histBox .hmark title', e=>e.textContent).catch(()=>'');
check('이상치 표식 title=행+값', /이상치 · \d+행/.test(markTitle), markTitle);
// hover 색상 변경(CSS)
const hoverFill = await page.evaluate(()=>{ const r=document.querySelector('#histBox .hbar'); r.dispatchEvent(new MouseEvent('mouseover',{bubbles:true})); return true; });
check('hover CSS 규칙 존재', await page.evaluate(()=>{ for(const ss of document.styleSheets){ for(const r of ss.cssRules){ if(r.selectorText && r.selectorText.includes('.hbar:hover')) return true; } } return false; }), '');

const box=await page.$('#dashboard');
await box.screenshot({path:`${S}/shot_dash8.png`});
check('콘솔 오류 없음', errs.length===0, errs.join(';'));
console.log('결과:', pass,'/',pass+fail);
await browser.close();
process.exit(fail?1:0);
