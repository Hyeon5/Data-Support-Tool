import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { readFileSync } from 'node:fs';
const b64 = p => readFileSync(p).toString('base64');
const fixture = new URL('./fixtures/formatted.xlsx', import.meta.url).pathname;
const browser = await chromium.launch();
const page = await browser.newPage();
const errs=[]; page.on('pageerror',e=>errs.push(e.message)); page.on('console',m=>{if(m.type()==='error')errs.push(m.text());});
let dl=null; page.on('download', async d=>{ dl=await d.path(); });
await page.goto(new URL('../index.html', import.meta.url).href);
let pass=0,fail=0; const ok=(n,c,d)=>{if(c){pass++;console.log('  ✔',n);}else{fail++;console.log('  ✘ FAIL',n,'|',d);}};

// 원본 styles/시트 지표
const orig = await page.evaluate(async (b64s)=>{
  const bin=atob(b64s);const arr=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)arr[i]=bin.charCodeAt(i);
  const wb = window.__anomaly.XlsxReader.open(arr);
  const dec = new TextDecoder('utf-8');
  const styles = dec.decode(wb.files['xl/styles.xml']);
  const sheet = dec.decode(wb.files[wb.sheets[0].path]);
  return {
    fonts:(styles.match(/<font>/g)||styles.match(/<font\/?>/g)||[]).length,
    fontsCountAttr:(styles.match(/<fonts count="(\d+)"/)||[])[1],
    fillsCountAttr:(styles.match(/<fills count="(\d+)"/)||[])[1],
    cols:(sheet.match(/<col /g)||[]).length,
    hasBoldFont: styles.includes('<b/>')||styles.includes('<b '),
  };
}, b64(fixture));
console.log('원본 지표:', JSON.stringify(orig));

// 업로드 → 분석
await page.evaluate(async (b64s)=>{
  const bin=atob(b64s);const arr=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)arr[i]=bin.charCodeAt(i);
  await window.__upload.handleFiles([new File([arr],'formatted.xlsx')]);
  await new Promise(r=>setTimeout(r,150));
}, b64(fixture));
// 이상치 탐지되도록 증감률/IQR/Z 켠 상태(기본) 그대로 실행
await page.evaluate(async ()=>{document.getElementById('btnRun').click();await new Promise(res=>{const iv=setInterval(()=>{if(/완료|실패|문제/.test(document.getElementById('status').textContent)){clearInterval(iv);res();}},50);});});
await page.waitForTimeout(200);
// 다운로드
await page.click('#btnDownload');
await page.waitForTimeout(500);
ok('다운로드 트리거', !!dl, String(dl));

// 다운로드 파일 재파싱
const outB64 = dl ? readFileSync(dl).toString('base64') : '';
const check = await page.evaluate(async (b64s)=>{
  const bin=atob(b64s);const arr=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)arr[i]=bin.charCodeAt(i);
  const A = window.__anomaly;
  const wb = A.XlsxReader.open(arr);
  const dec = new TextDecoder('utf-8');
  const styles = dec.decode(wb.files['xl/styles.xml']);
  const sheet = dec.decode(wb.files[wb.sheets[0].path]);
  // 값 재구성
  const grid = A.XlsxReader.grid(wb, 0);
  // gridToTable 은 전역 아님 → 간이 재구성: 헤더행 찾기
  return {
    sheetName: wb.sheets[0].name,
    styles, sheet,
    fontsCountAttr:(styles.match(/<fonts count="(\d+)"/)||[])[1],
    fillsCountAttr:(styles.match(/<fills count="(\d+)"/)||[])[1],
    cols:(sheet.match(/<col /g)||[]).length,
    hasBold: styles.includes('<b/>')||styles.includes('<b '),
    hasRowHt: /<row[^>]*ht="/.test(sheet),
    headerHasFlag: sheet.includes('이상치 여부'),
    hasReason: sheet.includes('이상치 사유'),
    hasSolidFill: styles.includes('FFFFF2CC'),
    gridRows: grid.length,
    gridW: Math.max(...grid.map(r=>r.length)),
    // 원본 데이터 보존 확인: '가나상사' 존재
    hasOrig: sheet.includes('가나상사') && sheet.includes('A-001'),
  };
}, outB64);

ok('시트 이름 보존(데이터)', check.sheetName==='데이터', check.sheetName);
ok('원본 글꼴 개수 보존', check.fontsCountAttr===orig.fontsCountAttr, check.fontsCountAttr+' vs '+orig.fontsCountAttr);
ok('볼드 글꼴 보존', check.hasBold, '');
ok('열 너비(col) 보존', parseInt(check.cols)>=4, check.cols);
ok('행 높이(ht) 보존', check.hasRowHt, '');
ok('이상 강조 fill 추가(FFF2CC)', check.hasSolidFill, '');
ok('fills count +1', parseInt(check.fillsCountAttr)===parseInt(orig.fillsCountAttr)+1, check.fillsCountAttr+' vs '+orig.fillsCountAttr);
ok('분석 컬럼 헤더(이상치 여부) 추가', check.headerHasFlag && check.hasReason, '');
ok('원본 데이터 보존(가나상사/A-001)', check.hasOrig, '');

console.log('\n결과: '+pass+' passed / '+fail+' failed');
console.log('page errors:', errs.length?errs:'none');
await browser.close();
process.exit(fail?1:0);
