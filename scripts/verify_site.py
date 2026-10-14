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
assert len(search['docs'])>50,'Search index unexpectedly small'
protocol=json.loads((ROOT/'downloads/protocol.json').read_text())
assert protocol['target_sequence']==list('BCDCBADCBA')
assert sum(s['duration_s'] for s in protocol['cooling_stages'])==300
assert protocol['calibration_example']['diameter_px']/protocol['arena_inner_diameter_cm']==45.8
for line in (ROOT/'downloads/SHA256SUMS').read_text().splitlines():
 digest,name=line.split('  ',1)
 assert hashlib.sha256((ROOT/'downloads'/name).read_bytes()).hexdigest()==digest,f'Download checksum mismatch: {name}'
if errors:
 raise SystemExit('\n'.join(errors))
print(f'PASS: {len(docs)} HTML pages; internal links, anchors, assets, semantic landmarks, search, protocol metadata.')
