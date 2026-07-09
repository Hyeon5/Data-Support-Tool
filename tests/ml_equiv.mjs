import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(new URL('../index.html', import.meta.url).href);
const res = await page.evaluate(async () => {
  const A = window.__anomaly;
  function gen(n, dim, seed) {
    let s=seed>>>0; const rnd=()=>{s=(s+0x6D2B79F5)|0;let t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};
    const cols=[]; for(let j=0;j<dim;j++) cols.push('c'+j); const rows=[];
    for(let i=0;i<n;i++){ const row=[]; const cl=Math.floor(rnd()*3); for(let j=0;j<dim;j++) row.push([0,10,20][cl]+(rnd()-0.5)*2); if(rnd()<0.05) for(let j=0;j<dim;j++) row[j]=-30+rnd()*80; rows.push(row.map(x=>Math.round(x*1000)/1000)); }
    return new A.TableWrapper(cols, rows);
  }
  const anomSet=(res,rule)=>{const s=new Set();res.findings.forEach((fs,r)=>{if(fs)fs.forEach(f=>{if(f.rule===rule)s.add(r);});});return s;};
  const eq=(a,b)=>{if(a.size!==b.size)return false;for(const x of a)if(!b.has(x))return false;return true;};
  const base={ missing:0,duplicate:0,range:0,change:0,iqr:0,zscore:0,iforest:0,lof:0,dbscan:0,changeRateThreshold:100,zscoreThreshold:3,isoContamination:0.05,lofNeighbors:20,dbscanEps:0.8,dbscanMinSamples:5,numericConfigs:[],missingAllowCols:[] };
  const out=[];
  for (const [n,dim] of [[500,2],[2000,2],[5000,2],[8000,3]]) {
    const t=gen(n,dim,123);
    const lB=await A.runAnalysis(t,{...base,lof:1,mlForce:'brute'},()=>{}); const lG=await A.runAnalysis(t,{...base,lof:1,mlForce:'grid'},()=>{});
    const dB=await A.runAnalysis(t,{...base,dbscan:1,mlForce:'brute'},()=>{}); const dG=await A.runAnalysis(t,{...base,dbscan:1,mlForce:'grid'},()=>{});
    out.push({n,dim, lofEq:eq(anomSet(lB,'lof'),anomSet(lG,'lof')), lofN:anomSet(lB,'lof').size, dbEq:eq(anomSet(dB,'dbscan'),anomSet(dG,'dbscan')), dbN:anomSet(dB,'dbscan').size});
  }
  return out;
});
let pass=0,fail=0;
for(const e of res){
  const okL=e.lofEq, okD=e.dbEq;
  console.log(`  ${okL?'✔':'✘'} LOF n=${e.n} d=${e.dim} 동일(${e.lofN}건)`, okL?'':JSON.stringify(e));
  console.log(`  ${okD?'✔':'✘'} DBSCAN n=${e.n} d=${e.dim} 동일(${e.dbN}건)`, okD?'':JSON.stringify(e));
  pass+=(okL?1:0)+(okD?1:0); fail+=(okL?0:1)+(okD?0:1);
}
console.log('\n동치 결과:', pass,'/',pass+fail);
await browser.close();
process.exit(fail?1:0);
