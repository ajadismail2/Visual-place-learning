from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from PIL import Image

OUT = Path(__file__).resolve().parents[1] / 'docs/assets'
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none'})
fig, ax = plt.subplots(figsize=(20, 17.333333), dpi=300)
fig.subplots_adjust(0, 0, 1, 1)
ax.set(xlim=(0,180), ylim=(156,0), aspect='equal')
ax.axis('off')
C = {'ink':'#16303D','muted':'#506674','line':'#D2DEE3','signal':'#087F83',
     'power':'#BD601C','radio':'#7750A8','sense':'#778A96',
     'controlfill':'#EAF6F5','powerfill':'#FFF2E2','loadfill':'#F1F5F7'}

def text(x,y,s,size=13,color=None,weight='normal',ha='center',va='center',**kw):
    return ax.text(x,y,s,fontsize=size,color=color or C['ink'],weight=weight,
                   ha=ha,va=va,linespacing=1.35,zorder=8,**kw)

def rect(x,y,w,h,fill='white',edge=None,r=.8,lw=1.2,z=2):
    p=FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0,rounding_size={r}',
        facecolor=fill,edgecolor=edge or C['line'],linewidth=lw,zorder=z)
    ax.add_patch(p)
    return p

def node(x,y,w,h,title,sub=None,kind='load',size=13):
    fill={'controller':C['controlfill'],'power':C['powerfill'],
          'driver':C['powerfill'],'load':C['loadfill'],'sensor':'#ECF3FA'}[kind]
    edge={'controller':'#8CC7C6','power':'#E0B283','driver':'#E0B283',
          'load':'#B8CAD4','sensor':'#A7C1D4'}[kind]
    rect(x,y,w,h,fill,edge)
    if sub:
        text(x+w/2,y+h*.37,title,size,weight='bold')
        text(x+w/2,y+h*.73,sub,size-2.5,color=C['muted'])
    else:
        text(x+w/2,y+h/2,title,size,weight='bold')

def path(points,kind='signal',arrow=True,lw=2.1,z=4):
    col=C[kind]
    style={'radio':(0,(5,3)), 'sense':(0,(1.5,3))}.get(kind,'solid')
    if len(points)>2:
        ax.plot(*zip(*points[:-1]),color=col,lw=lw,linestyle=style,
                solid_capstyle='round',solid_joinstyle='round',zorder=z)
    if arrow:
        a=FancyArrowPatch(points[-2],points[-1],arrowstyle='-|>',mutation_scale=14,
                          color=col,lw=lw,linestyle=style,shrinkA=0,shrinkB=1,zorder=z)
        ax.add_patch(a)
    else:
        ax.plot(*zip(*points[-2:]),color=col,lw=lw,linestyle=style,zorder=z)

def label(x,y,s,kind='signal',size=10.5,ha='center'):
    return text(x,y,s,size,color=C[kind],ha=ha,
                bbox=dict(facecolor='white',edgecolor='none',pad=1.6))

def card(x,y,w,h,num,title):
    rect(x,y,w,h,'white',C['line'],r=1.2,lw=1.3,z=0)
    ax.add_patch(Circle((x+4.1,y+4.3),1.9,facecolor=C['ink'],edgecolor='none',zorder=2))
    text(x+4.1,y+4.3,str(num),10.5,color='white',weight='bold')
    text(x+7.4,y+4.3,title,13.6,weight='bold',ha='left')

# Header and compact legend.
text(7,6,'Visual place-learning arena',31,weight='bold',ha='left')
text(7,12,'Electrical architecture and signal flow',16,color=C['muted'],ha='left')
for x,kind,title in [(7,'power','DC power'),(42,'signal','Wired control / data'),
                     (91,'radio','Wireless command'),(139,'sense','Temperature sensing')]:
    path([(x,19),(x+7,19)],kind,lw=2)
    text(x+9,19,title,11.2,ha='left',color=C['muted'])

card(7,30,103,58,1,'FOUR INDEPENDENT PELTIER TARGETS')
card(117,30,56,58,2,'VISUAL DISPLAY')
card(7,94,51,52,3,'BACKGROUND HEATING')
card(64,94,46,52,4,'THERMAL RING')
card(117,94,56,52,5,'RECORDING')

# Experiment controller and four independent bidirectional power stages.
node(13,50,23,13,'ESP32','Experiment controller',kind='controller',size=15)
node(13,39,23,6,'USB / logic DC',kind='power',size=11.8)
path([(24.5,45),(24.5,50)],'power')
text(24.5,67,'Trial timing & target selection',10.2,color=C['muted'])
text(24.5,70.3,'USB: setup / commands',10.2,color=C['muted'])
node(48,39,26,6,'Target DC supply',kind='power',size=12)
path([(61,45),(61,47)],'power')
rect(48,47,26,28,C['powerfill'],'#E0B283')
text(61,50,'4 × H-bridge drivers',11.6,weight='bold')
for i,letter in enumerate('ABCD'):
    y=53+i*6
    if i:
        ax.plot([50,72],[y-1.5,y-1.5],color='#E7CBAA',lw=.8,zorder=3)
    text(61,y+1.3,f'Channel {letter}',11.5)
    node(91,y-1.4,13,5.4,f'Tile {letter}',size=12)
    path([(74,y+1.3),(91,y+1.3)],'power')
label(82.5,48.6,'Switched power','power',9.8)
path([(36,56.5),(48,56.5)])
label(42,53.2,'PWM +','signal',9.8)
label(42,60,'enable','signal',9.8)
text(61,77.3,'One driver and one output pair per tile',10.4,color=C['muted'])
node(13,80,23,5,'Fan DC supply',kind='power',size=11.3)
node(48,80,56,5,'Underside fans → heat-sink cooling',size=11.7)
path([(36,82.5),(48,82.5)],'power')

# Wireless master-to-display link, routed outside the component panels.
path([(13,55),(3.5,55),(3.5,26),(113.5,26),(113.5,52.5),(123,52.5)],'radio',lw=2)
label(64,25.6,'ESP-NOW  •  selected target / visual state','radio',11.7)

# LED signal and power are separate connections.
node(123,39,20,6,'USB / logic DC',kind='power',size=11)
path([(133,45),(133,48)],'power')
node(123,48,21,9,'ESP32','Display controller',kind='controller',size=13)
node(148,48,18,9,'Panel DC','Supply',kind='power',size=12)
node(123,64,43,10,'P4 LED panorama','8 HUB75 panels · 64 × 32 pixels each',size=13.5)
path([(130,57),(130,64)])
label(129.8,60.5,'HUB75','signal',10.3)
path([(157,57),(157,64)],'power')
node(123,80,18,5,'IR-light supply',kind='power',size=10.5)
node(148,80,18,5,'IR illumination',size=10.5)
path([(141,82.5),(148,82.5)],'power')

def feedback(x,kind):
    if kind=='background':
        left=x+5; right=x+29; lw=16; rw=17
        sensor='TMP117'; interface='I²C'; load='60 Peltiers'; sub='series circuit'
        stage='Power stage'; supply='Background DC'
    else:
        left=x+5; right=x+26; lw=15; rw=15
        sensor='Temp. sensor'; interface='OneWire'; load='Ring heater'; sub='perimeter'
        stage='MOSFET'; supply='Heater DC'
    node(right,103,rw,6,supply,kind='power',size=10.8)
    node(left,103,lw,6,'USB / logic DC',kind='power',size=9.4)
    path([(left+lw/2,109),(left+lw/2,115)],'power')
    node(left,115,lw,10,'Arduino','PID controller',kind='controller',size=12.6)
    node(right,115,rw,10,stage,'Power switching',kind='driver',size=12)
    node(right,134,rw,8,load,sub,size=12)
    node(left,134,lw,8,sensor,'Feedback',kind='sensor',size=11.4)
    path([(right+rw/2,109),(right+rw/2,115)],'power')
    path([(left+lw,120),(right,120)])
    label((left+lw+right)/2,117,'PWM','signal',9.3)
    path([(right+rw/2,125),(right+rw/2,134)],'power')
    path([(right,138),(left+lw,138)],'sense')
    path([(left+lw/2,134),(left+lw/2,125)])
    label(left+lw/2,130,interface,'signal',10)
feedback(7,'background')
feedback(64,'ring')

# Independent thermal and behavioural data streams.
node(123,105,19,10,'MLX90640','Thermal sensor',kind='sensor',size=12.1)
node(150,105,17,10,'ESP32','Acquisition',kind='controller',size=13.2)
path([(142,110),(150,110)])
label(146,106.8,'I²C','signal',10.2)
text(132.5,119,'32 × 24 temperature map',9.5,color=C['muted'])
node(123,132,19,10,'Camera','Behaviour video',size=12.5)
node(150,132,17,10,'Computer','Recordings',kind='controller',size=12.5)
path([(158.5,115),(158.5,132)])
path([(162,132),(162,115)],'power')
label(160.2,124,'USB','signal',10.5)
path([(142,137),(150,137)])
label(146,133.7,'USB','signal',10.1)

# Ground and board power are stated once, rather than drawn as crossing buses.
ax.plot([7,173],[149.2,149.2],color=C['line'],lw=1)
text(7,151.7,'Controller power: USB or board-compatible regulated DC. Signal grounds are shared within each wired subsystem.',
     10.9,color=C['muted'],ha='left')
text(7,154.5,'Functional overview. Sensor power, common grounds and return wires are omitted; supply ratings must match the installed hardware.',
     10.9,color=C['muted'],ha='left')

fig.savefig(OUT/'arena-wiring-conference.png',dpi=300,facecolor='white')
fig.savefig(OUT/'arena-wiring-conference.svg',facecolor='white')
plt.close(fig)
with Image.open(OUT/'arena-wiring-conference.png') as im:
    im.resize((1800,1560),Image.Resampling.LANCZOS).save(OUT/'preview.png')
    print({'size':im.size,'dpi':im.info.get('dpi'),'bytes':(OUT/'arena-wiring-conference.png').stat().st_size})
