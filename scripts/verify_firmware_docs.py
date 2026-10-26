"""Cross-check displayed code, downloadable files, bundle and documented source revision."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json
import re
import zipfile

root=Path(__file__).resolve().parents[1]
site=root/'site'
downloads=site/'downloads'
manifest=json.loads((downloads/'firmware-manifest.json').read_text())
assert manifest['uploaded_sketch_count']==len(manifest['files'])==7
page_for={'Closedloop_60peltier.ino':'background','Display_Controller.ino':'display','Thermal_ring.ino':'ring','thermal_camera.ino':'camera','SinglePanelTest.ino':'panel-test'}
class Source(HTMLParser):
 def __init__(self,text):
  super().__init__();self.inside=False;self.code=False;self.parts=[];self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='details' and a.get('class')=='source-code':self.inside=True
  if tag=='code' and self.inside:self.code=True
 def handle_endtag(self,tag):
  if tag=='code':self.code=False
  if tag=='details':self.inside=False
 def handle_data(self,data):
  if self.inside and self.code:self.parts.append(data)
with zipfile.ZipFile(downloads/'arena-firmware-2026-10-17.zip') as archive:
 assert all(not x.endswith('/local_config.h') for x in archive.namelist())
 assert all('hot_slave' not in x for x in archive.namelist())
 for item in manifest['files']:
  path=downloads/item['path'];data=path.read_bytes()
  assert hashlib.sha256(data).hexdigest()==item['sha256'],item['filename']
  assert archive.read(str(Path(item['path']).relative_to('firmware')))==data,item['filename']
  if item['filename'] not in page_for:continue
  html=(site/'firmware'/page_for[item['filename']]/'index.html').read_text()
  assert [line.rstrip() for line in ''.join(Source(html).parts).splitlines()]==[line.rstrip() for line in data.decode().splitlines()],f'Displayed source differs: {item["filename"]}'
 for path in (downloads/'firmware').rglob('*'):
  if path.is_file():assert archive.read(path.relative_to(downloads/'firmware').as_posix())==path.read_bytes()
experiment=(downloads/'firmware/Experiment_Controller/Experiment_Controller.ino').read_text()
assert '#include "local_config.h"' in experiment
assert not re.search(r'static\s+(?:uint8_t\s+DISPLAY_MAC|const\s+char\*\s+AP_(?:SSID|PASS))',experiment)
assert 'ledcWrite(LPWM_PIN[idx], pwm);' in experiment
assert '#define PRE_HOT_DURATION_MS (5UL' in experiment
assert '#define MAX_STEPS           16' in experiment
assert '#define COOL_BOOST_PWM     150' in experiment
assert '#define COOL_HOLD_PWM       106' in experiment
assert '#define COOL_HOLD_PWM_REPEAT 120' in experiment
ring=(downloads/'firmware/Thermal_ring/Thermal_ring.ino').read_text()
fixed=(downloads/'firmware/Thermal_ring_syntax_fixed/Thermal_ring_syntax_fixed.ino').read_text()
assert 'float Kd = 150;3' in ring
assert fixed==ring.replace('float Kd = 150;3','float Kd = 150;')
old=json.loads((downloads/'protocol-2026-10-15.json').read_text())
assert old['final_all_heating_trials']==1
assert not (site/'firmware/experiment/index.html').exists()
assert not (site/'firmware/four-peltier/index.html').exists()
print('PASS: five displayed sketches match downloads; all seven downloads match ZIP; configuration is excluded; syntax correction and revision boundary are explicit.')
