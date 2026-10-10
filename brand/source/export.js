// Render each SVG to a transparent high-res PNG and a vector PDF
const { chromium } = require('playwright');
const fs=require('fs'), path=require('path');
(async () => {
  const dir=process.argv[2];
  const b = await chromium.launch();
  for (const f of fs.readdirSync(dir).filter(f=>f.endsWith('.svg'))) {
    const svg=fs.readFileSync(path.join(dir,f),'utf8');
    const [,w,h]=svg.match(/viewBox="0 0 (\d+) (\d+)"/).map(Number);
    const p=await b.newPage({viewport:{width:w,height:h},deviceScaleFactor:Math.max(1,3000/Math.max(w,h))});
    const html=`<html><head><style>@page{size:${w}px ${h}px;margin:0}html,body{margin:0;background:transparent}</style></head><body>${svg.replace(/width="\d+" height="\d+"/,`width="${w}" height="${h}"`)}</body></html>`;
    await p.setContent(html);
    const base=f.replace('.svg','');
    await p.screenshot({path:path.join(dir,'png',base+'.png'),omitBackground:true,clip:{x:0,y:0,width:w,height:h}});
    await p.pdf({path:path.join(dir,'pdf',base+'.pdf'),width:`${w}px`,height:`${h}px`,printBackground:true,pageRanges:'1'});
    await p.close();
  }
  await b.close();
})();
