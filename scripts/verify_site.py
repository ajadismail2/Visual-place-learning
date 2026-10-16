"""Check generated internal links, fragment targets, assets, and key metadata."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
import hashlib
ROOT=Path(__file__).resolve().parents[1]/'site'
class Document(HTMLParser):
 def __init__(self,text):
  super().__init__();self.links=[];self.ids=set();self.errors=[];self.h1=0;self.main=0;self.lang=False;self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:
   if a['id'] in self.ids:self.errors.append(f'duplicate id: {a["id"]}')
   self.ids.add(a['id'])
  if tag=='h1':self.h1+=1
  if tag=='main':self.main+=1
  if tag=='html':self.lang=a.get('lang')=='en'
  if tag=='img' and not a.get('alt'):self.errors.append('image without alt text')
  for attr in ('href','src'):
   if attr in a:self.links.append(a[attr])
errors=[];docs={p.resolve():Document(p.read_text()) for p in ROOT.rglob('*.html')}
for p,d in docs.items():
 if d.main!=1:errors.append(f'{p.relative_to(ROOT)}: expected one main landmark, got {d.main}')
 if d.h1!=1:errors.append(f'{p.relative_to(ROOT)}: expected one h1, got {d.h1}')
 if not d.lang:errors.append(f'{p.relative_to(ROOT)}: missing language')
 for error in d.errors:errors.append(f'{p.relative_to(ROOT)}: {error}')
 for link in d.links:
  u=urlsplit(link)
  if u.scheme or u.netloc or link.startswith('data:'):continue
  if u.path.startswith('/'):continue # 404 uses site-root absolute links from MkDocs
  target=(p.parent/unquote(u.path)).resolve() if u.path else p
  if target.is_dir():target=target/'index.html'
  if not target.exists():errors.append(f'{p.relative_to(ROOT)}: missing {link}')
  elif u.fragment and target in docs and unquote(u.fragment) not in docs[target].ids:errors.append(f'{p.relative_to(ROOT)}: missing fragment {link}')
search=json.loads((ROOT/'search/search_index.json').read_text())
assert len(search['docs'])>25,'Search index unexpectedly small'
assert 'sociability' not in json.dumps(search).lower(),'Excluded project remains in search'
protocol=json.loads((ROOT/'downloads/protocol.json').read_text())
assert protocol['required_sequence_length']==11
assert len(protocol['example_sequence'])==11
assert protocol['training_trials']==10 and protocol['final_all_heating_trials']==1
assert protocol['preheat_s']+11*protocol['trial_duration_s']==3480
assert [s['pwm'] for s in protocol['cooling_stages']]==[100,90,80,70]
assert sum(s['duration_s'] for s in protocol['cooling_stages'])==300
expected={'A':(2,25,26,13,15),'B':(4,19,18,2,16),'C':(1,32,33,4,5),'D':(3,27,14,22,23)}
for target,values in expected.items():
 assert tuple(protocol['targets'][target][k] for k in ['channel','rpwm','lpwm','ren','len'])==values
assert protocol['display']['pattern_height_px']==33
assert protocol['display']['horizontal_length_px']*protocol['display']['pitch_mm']==344
assert not (ROOT/'research/sociability/index.html').exists()
for line in (ROOT/'downloads/SHA256SUMS').read_text().splitlines():
 digest,name=line.split('  ',1)
 assert hashlib.sha256((ROOT/'downloads'/name).read_bytes()).hexdigest()==digest,f'Download checksum mismatch: {name}'
if errors:
 raise SystemExit('\n'.join(errors))
print(f'PASS: {len(docs)} HTML pages; internal links, anchors, assets, semantic landmarks, search, protocol metadata.')
