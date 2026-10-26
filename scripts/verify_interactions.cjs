/* Check numerical geometry and navigation/search behavior without a browser. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Element {
 constructor(){this.value='';this.textContent='';this.hidden=true;this.children=[];this.events={};this.attrs={};this.classes=new Set();this.classList={toggle:(k,on)=>on?this.classes.add(k):this.classes.delete(k),remove:k=>this.classes.delete(k)};}
 addEventListener(name,fn){(this.events[name]||=[]).push(fn);}
 async fire(name,e={}){for(const fn of this.events[name]||[])await fn({target:this,...e});}
 setAttribute(k,v){this.attrs[k]=v;}getAttribute(k){return this.attrs[k];}
 append(...els){this.children.push(...els);}replaceChildren(){this.children=[];}focus(){}
}
const selectors=['.menu-toggle','#primary-nav','#site-search','#search-input','.search-toggle','#search-close','#search-results','#search-status','[data-angle-calculator]','#distance-mm','#height-mm','#angle-deg','#angle-result'];
const elements=Object.fromEntries(selectors.map(k=>[k,new Element()]));
Object.entries({'#distance-mm':160,'#height-mm':0,'#angle-deg':15}).forEach(([k,v])=>elements[k].value=String(v));
const document={currentScript:{dataset:{searchIndex:'../../search/search_index.json',root:'../../'}},baseURI:'https://example.test/Visual-place-learning/hardware/visual-angle/',querySelector:s=>elements[s]||null,createElement:()=>new Element(),addEventListener(){}};
const sandbox={document,URL,module:{exports:{}},fetch:async()=>({ok:true,json:async()=>({docs:[{title:'Peltier temperature system',text:'Peltier-plate connections and independent drivers.',location:'hardware/peltier/#target-controller-pin-map'},{title:'Arena',text:'Wooden base and printed parts.',location:'hardware/arena/'}]})})};
vm.runInNewContext(fs.readFileSync('docs/assets/site.js','utf8'),sandbox);
(async()=>{
 const {horizontalWidth}=sandbox.module.exports;
 assert(Math.abs(horizontalWidth(160,0,15)-42.12879922796667)<1e-9);
 // Independent reference: tan(30 degrees) = 1/sqrt(3).
 assert(Math.abs(horizontalWidth(100,0,60)-200/Math.sqrt(3))<1e-9);
 assert(horizontalWidth(160,64,15)>horizontalWidth(160,0,15));
 for(const values of [[0,0,15],[160,0,0],[160,0,90],[NaN,0,15]])assert.equal(horizontalWidth(...values),null);
 assert.match(elements['#angle-result'].textContent,/42\.13 mm.*10\.53 pixel/);
 elements['#distance-mm'].value='0';await elements['[data-angle-calculator]'].fire('input');assert.match(elements['#angle-result'].textContent,/positive distance/);
 await elements['.menu-toggle'].fire('click');assert.equal(elements['.menu-toggle'].attrs['aria-expanded'],'true');
 await elements['.menu-toggle'].fire('click');assert.equal(elements['.menu-toggle'].attrs['aria-expanded'],'false');
 await elements['.search-toggle'].fire('click');assert.equal(elements['#site-search'].hidden,false);
 await elements['#search-close'].fire('click');assert.equal(elements['#site-search'].hidden,true);
 elements['#search-input'].value='peltier';await elements['#search-input'].fire('input');
 assert.equal(elements['#search-results'].children.length,1);
 assert.equal(elements['#search-results'].children[0].children[0].href,'https://example.test/Visual-place-learning/hardware/peltier/#target-controller-pin-map');
 elements['#search-input'].value='missing phrase';await elements['#search-input'].fire('input');assert.match(elements['#search-status'].textContent,/No matches/);
 console.log('PASS: visual-angle geometry, invalid inputs, menu, search visibility, nested links, and no-results state.');
})().catch(e=>{console.error(e);process.exit(1);});
