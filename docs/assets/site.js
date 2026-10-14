/* Local-only enhancements. No analytics, accounts, or third-party requests. */
(() => {
  'use strict';
  const script = document.currentScript;
  const menu = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#primary-nav');
  menu?.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded', String(open)); nav.classList.toggle('open', open);
  });
  const groups = [...document.querySelectorAll('.nav-group')];
  groups.forEach(group => group.addEventListener('toggle', () => {
    if (group.open) groups.filter(other => other !== group).forEach(other => { other.open = false; });
  }));
  document.addEventListener('click', e => { if (!nav?.contains(e.target)) groups.forEach(g => { g.open = false; }); });
  const panel = document.querySelector('#site-search');
  const searchInput = document.querySelector('#search-input');
  const searchToggle = document.querySelector('.search-toggle');
  let searchData = null, searchRequest = null, searchRun = 0;
  const closeSearch = () => { panel.hidden = true; searchToggle?.focus(); };
  searchToggle?.addEventListener('click', () => { panel.hidden = false; searchInput.focus(); });
  document.querySelector('#search-close')?.addEventListener('click', closeSearch);
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { if (!panel.hidden) closeSearch(); groups.forEach(g => { g.open = false; }); nav?.classList.remove('open'); menu?.setAttribute('aria-expanded', 'false'); }
  });
  searchInput?.addEventListener('input', async () => {
    const run = ++searchRun, q = searchInput.value.trim().toLowerCase();
    const resultList = document.querySelector('#search-results');
    const status = document.querySelector('#search-status'); resultList.replaceChildren();
    if (q.length < 2) { status.textContent = 'Enter at least two characters.'; return; }
    status.textContent = 'Searching…';
    try {
      if (!searchData) {
        searchRequest ||= fetch(script.dataset.searchIndex).then(r => { if (!r.ok) throw Error('Search unavailable'); return r.json(); }).catch(e => { searchRequest = null; throw e; });
        searchData = await searchRequest;
      }
      if (run !== searchRun) return;
      const words = q.split(/\s+/);
      const matches = searchData.docs.filter(d => words.every(w => `${d.title} ${d.text}`.toLowerCase().includes(w)))
        .sort((a,b) => Number(b.title.toLowerCase().includes(q)) - Number(a.title.toLowerCase().includes(q))).slice(0, 20);
      status.textContent = matches.length ? `${matches.length} matching sections${matches.length === 20 ? ' (first 20 shown)' : ''}` : 'No matches. Try a broader term such as “tracking”.';
      const root = new URL(script.dataset.root, document.baseURI);
      matches.forEach(d => {
        const li = document.createElement('li'), a = document.createElement('a'), p = document.createElement('p');
        a.href = new URL(d.location, root).href; a.textContent = d.title;
        const clean = d.text.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');
        const at = Math.max(0, clean.toLowerCase().indexOf(words[0]) - 65);
        p.textContent = (at ? '…' : '') + clean.slice(at, at + 210) + (clean.length > at + 210 ? '…' : '');
        li.append(a,p); resultList.append(li);
      });
    } catch { if (run === searchRun) status.textContent = 'Search could not load. Use the page navigation, or serve this site over HTTP when viewing a downloaded copy.'; }
  });
  const order = ['B','C','D','C','B','A','D','C','B','A'];
  const offsets = {A:192,B:0,C:64,D:128};
  // Faithful virtual-coordinate rendering of the supplied LED_Slave.ino.
  function panoramaPixels(offset) {
    const pixels = new Uint8Array(256 * 64);
    const put = (x,y) => { if(y>=0 && y<64) pixels[y*256+((x+offset)%256+256)%256]=1; };
    const rect = (x0,y0,x1,y1,off=0) => { for(let x=x0;x<=x1;x++)for(let y=y0;y<=y1;y++)put(off+x,y); };
    const para = (x0,x1,y0,y1,slant,off=0) => { for(let y=y0;y<=y1;y++){const dx=Math.trunc((y-y0)*slant/(y1-y0));for(let x=x0+dx;x<=x1+dx;x++)put(off+x,y);} };
    const stripes=(x0,x1,off=0)=>{rect(x0,0,x1,10,off);rect(x0,22,x1,31,off);};
    rect(11,0,21,30);rect(0,0,10,30,32);rect(21,0,31,30,32);
    para(11,21,0,31,-11,64);para(32,42,0,31,-11,64);para(53,63,0,31,-11,64);
    para(11,21,0,31,-11,128);stripes(22,31,128);stripes(0,31,160);stripes(0,31,192);stripes(0,11,224);rect(22,0,31,30,224);
    return pixels;
  }
  function drawPanorama(state) {
    const canvas=document.querySelector('#panorama'); if(!canvas)return;
    const ctx=canvas.getContext('2d'); if(!ctx)return;
    const data=ctx.createImageData(256,64), pixels=panoramaPixels(offsets[state]);
    pixels.forEach((on,i)=>{const rgb=on?[194,218,129]:[25,59,52];data.data.set([...rgb,255],i*4);});ctx.putImageData(data,0,0);
  }
  document.querySelectorAll('[data-trial]').forEach(button=>button.addEventListener('click',()=>{
    const n=Number(button.dataset.trial), target=order[n-1];
    document.querySelectorAll('[data-trial]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
    document.querySelector('#trial-number').textContent=String(n).padStart(2,'0');
    document.querySelector('#trial-target').textContent=`TARGET ${target}`;
    document.querySelector('#trial-time').textContent=`Training time ${String((n-1)*5).padStart(2,'0')}:00–${String(n*5).padStart(2,'0')}:00`;
    document.querySelector('#trial-offset').textContent=`${offsets[target]} px`;
    document.querySelector('#panorama-state').textContent=`STATE:${target}`;
    document.querySelectorAll('[data-tile]').forEach(tile=>{
      tile.classList.toggle('cool',tile.dataset.tile===target);tile.textContent=tile.dataset.tile;
      if(tile.dataset.tile===target){const s=document.createElement('small');s.textContent='COOL';tile.append(s);}
    });drawPanorama(target);
  }));drawPanorama('B');
  const scaleCalc=document.querySelector('[data-scale-calculator]');
  function updateScale(){
    if(!scaleCalc)return;
    const px=Number(document.querySelector('#diameter-px').value),cm=Number(document.querySelector('#diameter-cm').value),fps=Number(document.querySelector('#video-fps').value);
    const out=document.querySelector('#scale-result');
    if(!Number.isFinite(px+cm+fps)||px<=0||cm<=0||fps<=0){out.textContent='Enter positive values for all three inputs.';return;}
    out.textContent=`${(px/cm).toFixed(3)} px/cm · ${(cm/px).toFixed(5)} cm/px · ${(10*cm/px).toFixed(4)} mm/px`;
    document.querySelector('#frame-result').textContent=`A 5-minute trial spans ${Math.round(300*fps).toLocaleString()} frames; a 3-second occupancy threshold uses ${Math.ceil(3*fps-1e-12)} frame samples.`;
  }
  scaleCalc?.addEventListener('input',updateScale);updateScale();
  const angleCalc=document.querySelector('[data-angle-calculator]');
  function updateAngle(){
    if(!angleCalc)return;
    const d=Number(document.querySelector('#distance-cm').value),h=Number(document.querySelector('#height-cm').value),p=Number(document.querySelector('#pitch-mm').value)/10,a=Number(document.querySelector('#angle-deg').value),out=document.querySelector('#angle-result');
    if(!Number.isFinite(d+h+p+a)||d<=0||p<=0||a<=0||a>=89){out.textContent='Use a positive distance and pitch, and an angle between 0° and 89°.';return;}
    const theta=a*Math.PI/180,t=Math.tan(theta),horizontal=2*Math.hypot(d,h)*Math.tan(theta/2),vertical=2*t*(d*d+h*h)/(Math.sqrt(d*d+t*t*(d*d+h*h))+d);
    out.textContent=`Horizontal extent: ${(horizontal/p).toFixed(2)} px (${(horizontal*10).toFixed(1)} mm). Vertical extent: ${(vertical/p).toFixed(2)} px (${(vertical*10).toFixed(1)} mm).`;
  }
  angleCalc?.addEventListener('input',updateAngle);updateAngle();
  // Expose pure calculations only to the local verification harness.
  if(typeof module!=='undefined')module.exports={panoramaPixels};
})();
