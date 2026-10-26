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
assert protocol['schema_version']==3
assert protocol['minimum_sequence_length']==1 and protocol['maximum_sequence_length']==16
assert protocol['required_sequence_length'] is None
assert protocol['final_all_heating_trials']==0 and protocol['each_step_cools_selected_target']
assert protocol['preheat_s']+len(protocol['example_sequence'])*protocol['trial_duration_s']==3600
assert protocol['cooling_boost']=={'pwm':150,'duration_s':23}
assert protocol['cooling_boost']['duration_s']+protocol['cooling_hold']['duration_s']==300
assert protocol['cooling_hold']['first_selection_pwm']==106
assert protocol['cooling_hold']['repeat_selection_pwm']==120
expected={'A':(3,27,14,23,22),'B':(2,25,26,13,15),'C':(4,19,18,2,16),'D':(1,32,33,4,5)}
for target,values in expected.items():
 assert tuple(protocol['targets'][target][k] for k in ['channel','rpwm','lpwm','ren','len'])==values
assert protocol['display']['horizontal_rows_inclusive']==[[0,10],[22,31]]
assert protocol['display']['horizontal_length_px']*protocol['display']['pitch_mm']==344
assert protocol['thermal_camera']['frame_bytes']==2+32*24*2
assert not (ROOT/'research/sociability/index.html').exists()
for line in (ROOT/'downloads/SHA256SUMS').read_text().splitlines():
 digest,name=line.split('  ',1)
 assert hashlib.sha256((ROOT/'downloads'/name).read_bytes()).hexdigest()==digest,f'Download checksum mismatch: {name}'
if errors:
 raise SystemExit('\n'.join(errors))
print(f'PASS: {len(docs)} HTML pages; internal links, anchors, assets, search, protocol metadata, and checksums.')
