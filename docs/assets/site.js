/* Progressive enhancements for build notes; no analytics or device control. */
(() => {
  'use strict';
  const script = document.currentScript;
  const menu = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#primary-nav');
  menu?.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded', String(open)); nav.classList.toggle('open', open);
  });
  const panel = document.querySelector('#site-search');
  const searchInput = document.querySelector('#search-input');
  const searchToggle = document.querySelector('.search-toggle');
  let searchData = null, searchRequest = null, searchRun = 0;
  const closeSearch = () => { panel.hidden = true; searchToggle?.setAttribute('aria-expanded','false'); searchToggle?.focus(); };
  searchToggle?.addEventListener('click', () => {
    if (!panel.hidden) { closeSearch(); return; }
    panel.hidden = false; searchToggle.setAttribute('aria-expanded','true'); searchInput.focus();
  });
  document.querySelector('#search-close')?.addEventListener('click', closeSearch);
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { if (!panel.hidden) closeSearch(); nav?.classList.remove('open'); menu?.setAttribute('aria-expanded', 'false'); }
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
        .sort((a,b) => Number(b.title.toLowerCase().includes(q)) - Number(a.title.toLowerCase().includes(q))).slice(0, 15);
      status.textContent = matches.length ? `${matches.length} matching sections${matches.length === 15 ? ' (first 15 shown)' : ''}` : 'No matches. Try a broader term such as “Peltier”.';
      const root = new URL(script.dataset.root, document.baseURI);
      matches.forEach(d => {
        const li = document.createElement('li'), a = document.createElement('a'), p = document.createElement('p');
        a.href = new URL(d.location, root).href; a.textContent = d.title;
        const clean = d.text.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');
        const at = Math.max(0, clean.toLowerCase().indexOf(words[0]) - 55);
        p.textContent = (at ? '…' : '') + clean.slice(at, at + 180) + (clean.length > at + 180 ? '…' : '');
        li.append(a,p); resultList.append(li);
      });
    } catch { if (run === searchRun) status.textContent = 'Search is unavailable. Use the contents to find a build chapter.'; }
  });
  function horizontalWidth(distance, height, angle) {
    if (![distance,height,angle].every(Number.isFinite) || distance <= 0 || angle <= 0 || angle >= 90) return null;
    return 2 * Math.hypot(distance,height) * Math.tan(angle*Math.PI/360);
  }
  const calculator=document.querySelector('[data-angle-calculator]');
  function updateAngle() {
    if (!calculator) return;
    const distance=Number(document.querySelector('#distance-mm').value),height=Number(document.querySelector('#height-mm').value),angle=Number(document.querySelector('#angle-deg').value);
    const width=horizontalWidth(distance,height,angle),out=document.querySelector('#angle-result');
    out.textContent=width===null ? 'Enter a positive distance and an angle greater than 0° and below 90°.' : `${width.toFixed(2)} mm · ${(width/4).toFixed(2)} pixel pitches at 4 mm pitch`;
  }
  calculator?.addEventListener('input',updateAngle);updateAngle();
  if (typeof module !== 'undefined') module.exports={horizontalWidth};
})();
