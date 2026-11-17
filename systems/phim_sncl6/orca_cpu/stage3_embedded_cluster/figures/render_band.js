const { chromium } = require('playwright');
const fs = require('fs');
// usage: node render_band.js <cube> <out.png> <iso> <color> rx ry rz
(async () => {
  const [cube, out, iso, color, rx='0', ry='0', rz='0'] = process.argv.slice(2);
  const lib = fs.readFileSync(__dirname + '/node_modules/3dmol/build/3Dmol-min.js', 'utf8');
  const data = fs.readFileSync(cube, 'utf8');
  const L = data.split('\n'); const B=0.529177;
  const ax=[3,4,5].map(i=>{const p=L[i].trim().split(/\s+/).map(Number); return [p[1]*p[0]*B,p[2]*p[0]*B,p[3]*p[0]*B];});
  const browser = await chromium.launch({ args: ['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 760, height: 680 }, deviceScaleFactor: 2 });
  await page.setContent(`<html><body style="margin:0;background:#fff"><div id="v" style="width:760px;height:680px;position:relative"></div><script>${lib}</script></body></html>`);
  await page.evaluate(([data, iso, color, ax, rx, ry, rz]) => {
    const v = $3Dmol.createViewer(document.getElementById('v'), { backgroundColor: 'white', antialias: true });
    v.addModel(data, 'cube');
    v.setStyle({}, { stick: { radius: 0.1, colorscheme: 'Jmol' }, sphere: { scale: 0.15, colorscheme: 'Jmol' } });
    v.setStyle({ elem: 'Sn' }, { stick: { radius: 0.1, colorscheme: 'Jmol' }, sphere: { scale: 0.32, colorscheme: 'Jmol' } });
    v.addVolumetricData(data, 'cube', { isoval: parseFloat(iso), color: color, opacity: 0.85 });
    const add=(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]]; const O=[0,0,0];
    const C=[O,ax[0],ax[1],ax[2],add(ax[0],ax[1]),add(ax[0],ax[2]),add(ax[1],ax[2]),add(add(ax[0],ax[1]),ax[2])];
    const E=[[0,1],[0,2],[0,3],[1,4],[1,5],[2,4],[2,6],[3,5],[3,6],[4,7],[5,7],[6,7]];
    for (const [i,j] of E) v.addLine({start:{x:C[i][0],y:C[i][1],z:C[i][2]},end:{x:C[j][0],y:C[j][1],z:C[j][2]},color:'#555555'});
    v.zoomTo();
    v.rotate(parseFloat(rx), 'x'); v.rotate(parseFloat(ry), 'y'); v.rotate(parseFloat(rz), 'z');
    v.render(); window.__done = true;
  }, [data, iso, color, ax, rx, ry, rz]);
  await page.waitForFunction(() => window.__done === true);
  await page.waitForTimeout(1200);
  await page.locator('#v').screenshot({ path: out });
  await browser.close();
})();
