/* Pure DOM-fixture checks: no browser installation, server, or remote services. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Element {
 constructor(data={}){this.dataset=data;this.value='';this.textContent='';this.hidden=true;this.children=[];this.events={};this.attrs={};this.classes=new Set();this.classList={toggle:(k,on)=>on?this.classes.add(k):this.classes.delete(k),remove:k=>this.classes.delete(k)};}
 addEventListener(name,fn){(this.events[name]||=[]).push(fn);}
 async fire(name,e={}){for(const fn of this.events[name]||[])await fn({target:this,...e});}
 setAttribute(k,v){this.attrs[k]=v;}getAttribute(k){return this.attrs[k];}
 append(...els){this.children.push(...els);}replaceChildren(){this.children=[];}focus(){}contains(){return false;}
}
const selectors=['.menu-toggle','#primary-nav','#site-search','#search-input','.search-toggle','#search-close','#search-results','#search-status','#trial-number','#trial-target','#trial-time','#trial-offset','#panorama-state','#scale-result','#frame-result','#angle-result','[data-scale-calculator]','[data-angle-calculator]'];
const elements=Object.fromEntries(selectors.map(k=>[k,new Element()]));
Object.entries({'#diameter-px':916,'#diameter-cm':20,'#video-fps':24,'#distance-cm':16,'#height-cm':6.4,'#pitch-mm':4,'#angle-deg':15}).forEach(([k,v])=>{elements[k]=new Element();elements[k].value=String(v);});
const buttons=Array.from({length:10},(_,i)=>new Element({trial:String(i+1)}));
const tiles=Array.from('ABCD',tile=>new Element({tile}));
let pixelOutput;
elements['#panorama']={getContext:()=>({createImageData:()=>({data:new Uint8ClampedArray(256*64*4)}),putImageData:d=>pixelOutput=d.data})};
const document={currentScript:{dataset:{searchIndex:'../../search/search_index.json',root:'../../'}},baseURI:'https://example.test/Visual-place-learning/methods/analysis/',querySelector:s=>elements[s]||null,querySelectorAll:s=>s==='[data-trial]'?buttons:s==='[data-tile]'?tiles:[],createElement:()=>new Element(),addEventListener(){}};
const sandbox={document,URL,module:{exports:{}},fetch:async()=>({ok:true,json:async()=>({docs:[{title:'Thermal control',text:'Open-loop staged cooling and temperature.',location:'hardware/thermal_control_system/#current-staged-cooling-programme'},{title:'Identity',text:'Review fly identities.',location:'software/Behavioural_tracking/'}]})})};
vm.runInNewContext(fs.readFileSync('docs/assets/site.js','utf8'),sandbox);
(async()=>{
 assert.match(elements['#scale-result'].textContent,/45\.800 px\/cm.*0\.02183 cm\/px.*0\.2183 mm\/px/);
 assert.match(elements['#frame-result'].textContent,/7,200 frames.*72 frame samples/);
 assert(pixelOutput?.length===65536,'panorama draws on initialization');
 const {panoramaPixels}=sandbox.module.exports;
 const baseline=panoramaPixels(0);assert.equal(baseline.reduce((a,b)=>a+b,0),4547);
 assert(baseline.slice(32*256).every(v=>v===0),'upper virtual rows remain blank');
 for(const offset of [64,128,192]){
  const p=panoramaPixels(offset);assert.equal(p.reduce((a,b)=>a+b,0),4547);
  for(let y=0;y<64;y++)for(let x=0;x<256;x++)assert.equal(p[y*256+(x+offset)%256],baseline[y*256+x]);
 }
 for(let i=0;i<10;i++){
  await buttons[i].fire('click');const target='BCDCBADCBA'[i];
  assert.equal(elements['#trial-target'].textContent,`TARGET ${target}`);
  assert.equal(elements['#panorama-state'].textContent,`STATE:${target}`);
  assert.equal(buttons.filter(b=>b.attrs['aria-pressed']==='true').length,1);
  assert.equal(tiles.filter(t=>t.classes.has('cool')).length,1);
 }
 await elements['.menu-toggle'].fire('click');assert.equal(elements['.menu-toggle'].attrs['aria-expanded'],'true');
 await elements['.menu-toggle'].fire('click');assert.equal(elements['.menu-toggle'].attrs['aria-expanded'],'false');
 elements['#diameter-px'].value='0';await elements['[data-scale-calculator]'].fire('input');assert.match(elements['#scale-result'].textContent,/positive values/);
 elements['#height-cm'].value='0';await elements['[data-angle-calculator]'].fire('input');
 assert.match(elements['#angle-result'].textContent,/Horizontal extent: 10\.53 px.*Vertical extent: 10\.53 px/);
 elements['#height-cm'].value='6.4';await elements['[data-angle-calculator]'].fire('input');
 const numbers=[...elements['#angle-result'].textContent.matchAll(/([0-9.]+) px/g)].map(x=>Number(x[1]));
 assert(numbers[1]>numbers[0],'elevation changes vertical and horizontal extents differently');
 elements['#angle-deg'].value='90';await elements['[data-angle-calculator]'].fire('input');assert.match(elements['#angle-result'].textContent,/between 0° and 89°/);
 elements['#search-input'].value='thermal';await elements['#search-input'].fire('input');
 assert.equal(elements['#search-results'].children.length,1);
 assert.equal(elements['#search-results'].children[0].children[0].href,'https://example.test/Visual-place-learning/hardware/thermal_control_system/#current-staged-cooling-programme');
 elements['#search-input'].value='no-such-term';await elements['#search-input'].fire('input');assert.match(elements['#search-status'].textContent,/No matches/);
 console.log('PASS: ten trial states, source pixel count/rotation, scale and angle calculations, invalid inputs, menu, and search paths.');
})().catch(e=>{console.error(e);process.exit(1);});
