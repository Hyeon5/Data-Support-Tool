import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const browser = await chromium.launch();
const page = await browser.newPage();
const errs = []; page.on('pageerror', e => errs.push(e.message));
await page.goto(new URL('../index.html', import.meta.url).href);
let pass=0, fail=0;
const ok=(c,m)=>{ if(c){pass++;console.log('  ✔',m);} else {fail++;console.log('  �’✘ FAIL',m);} };

// SHA-256 known vector
const sha = await page.evaluate(() => window.__anomaly.DeidEngine.SHA256('abc'));
ok(sha==='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad','SHA256("abc") 표준 벡터 일치');
const sha2 = await page.evaluate(() => window.__anomaly.DeidEngine.SHA256(''));
ok(sha2==='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855','SHA256("") 표준 벡터 일치');
const shaK = await page.evaluate(() => window.__anomaly.DeidEngine.SHA256('홍길동'));
ok(/^[0-9a-f]{64}$/.test(shaK),'SHA256 한글 입력 64 hex');

// detect
const det = await page.evaluate(() => {
  const D = window.__anomaly.DeidEngine;
  const cols = ['성명','휴대폰','이메일','주민등록번호','사업자등록번호','산단명','금액','주소'];
  const rows = [
    ['홍길동','010-1234-5678','hong@example.com','900101-1234567','123-45-67890','반월산업단지','1000','서울특별시 강남구 테헤란로 1'],
    ['김철수','010-9876-5432','kim@test.co.kr','850505-2234567','221-81-12345','시화산업단지','2000','경기도 성남시 분당구 2'],
    ['이영희','010-5555-6666','lee@abc.org','770303-2345678','111-22-33333','남동산업단지','3000','부산광역시 해운대구 3'],
  ];
  return D.detect(cols, rows).map(d=>({column:d.column,type:d.type,typeLabel:d.typeLabel,conf:d.confidence,method:d.method,detected:d.detected}));
});
const byCol = Object.fromEntries(det.map(d=>[d.column,d]));
ok(byCol['성명'].type==='name','성명 → name');
ok(byCol['휴대폰'].type==='phone','휴대폰 → phone');
ok(byCol['이메일'].type==='email','이메일 → email');
ok(byCol['주민등록번호'].type==='rrn' && byCol['주민등록번호'].method==='delete','주민등록번호 → rrn(삭제)');
ok(byCol['사업자등록번호'].type==='bizno' && byCol['사업자등록번호'].conf==='중간','사업자등록번호 → 중간');
ok(byCol['산단명'].detected===false,'산단명 제외(개인정보 아님)');
ok(byCol['금액'].detected===false,'금액 미탐지');
ok(byCol['주소'].type==='address' && byCol['주소'].method==='generalize','주소 → 일반화');

// transform: all 5 methods + consistency
const tr = await page.evaluate(() => {
  const D = window.__anomaly.DeidEngine;
  const rows = [
    ['홍길동','010-1234-5678','hong@example.com','900101-1234567','서울특별시 강남구 테헤란로 1','A'],
    ['홍길동','010-1234-5678','kim@test.com','850505-2234567','경기도 성남시 분당구 2','A'],
  ];
  const plan = [
    {index:0,type:'name',method:'mask'},
    {index:1,type:'phone',method:'hash',salt:'s1'},
    {index:2,type:'email',method:'pseudonym'},
    {index:3,type:'rrn',method:'delete'},
    {index:4,type:'address',method:'generalize'},
    {index:5,type:null,method:'none'},
  ];
  return D.transform(rows, plan);
});
ok(tr[0][0]==='홍**','mask 성명 홍**');
ok(/^H:[0-9a-f]{16}$/.test(tr[0][1]) && tr[0][1]===tr[1][1],'hash 일관성(동일 입력 동일 출력)');
ok(tr[0][2]!==tr[1][2] && tr[0][2].startsWith('익명'),'pseudonym 서로 다른 값');
ok(tr[0][3]==='','delete 주민번호 공백');
ok(tr[0][4]==='서울특별시 강남구','generalize 주소 시/도+시군구');
ok(tr[0][5]==='A','none 미변경');

// pseudonym consistency across same value
const tr2 = await page.evaluate(() => {
  const D = window.__anomaly.DeidEngine;
  const rows=[['홍길동'],['김철수'],['홍길동']];
  return D.transform(rows,[{index:0,type:'name',method:'pseudonym'}]);
});
ok(tr2[0][0]===tr2[2][0] && tr2[0][0]!==tr2[1][0],'pseudonym 동일 원본 동일 가명');

console.log(`\n결과: ${pass} passed / ${fail} failed`);
console.log('page errors:', errs.length?errs:'none');
await browser.close();
process.exit(fail?1:0);
