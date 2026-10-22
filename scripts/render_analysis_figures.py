"""Render explanatory figures. No experimental measurements are used."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Ellipse
import numpy as np
OUT=Path(__file__).resolve().parents[1]/'docs/assets/analysis'
OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none'})
ink='#213c3c'; teal='#17625c'; blue='#2b6694'; muted='#5d706d'
fig,ax=plt.subplots(figsize=(12,6.6));fig.subplots_adjust(.02,.02,.98,.98)
ax.set(xlim=(0,12),ylim=(0,6.6));ax.axis('off')
ax.text(.3,6.13,'From isolated flies to identity tracks',fontsize=20,color=ink)
ax.text(.3,5.73,'AMADEUS method overview · schematic examples',fontsize=11,color=muted)
boxes=[(.3,3.05,'1  SEGMENT','Separate isolated bodies'),(4.3,3.05,'2  SYNTHESISE','Create crossing examples'),(8.3,3.05,'3  DETECT','Fit body-oriented boxes')]
for x,y,title,sub in boxes:
 ax.add_patch(FancyBboxPatch((x,y),3.4,2.35,boxstyle='round,pad=.05',fc='#eff3ed',ec='#d9dfd5'))
 ax.text(x+.18,y+1.95,title,fontsize=12,color=ink,weight='bold');ax.text(x+.18,y+.18,sub,fontsize=10,color=muted)
for x,y,a in [(1.1,4.28,35),(2.65,3.98,-25),(5.7,4.13,35),(6.03,4.13,-40),(9.7,4.13,35),(10.05,4.13,-40)]:
 ax.add_patch(Ellipse((x,y),.65,.23,angle=a,fc=teal if x<5 else blue))
 if x>9:
  ax.add_patch(Rectangle((x-.39,y-.23),.8,.5,angle=a,rotation_point='center',fill=False,ec='#be673b',lw=1.5))
for x in (3.78,7.78):ax.annotate('',(x+.4,4.18),(x,4.18),arrowprops={'arrowstyle':'->','color':muted,'lw':1.5})
ax.add_patch(FancyBboxPatch((.3,.65),11.4,1.85,boxstyle='round,pad=.05',fc='#e9f0f7',ec='#ced9e4'))
ax.text(.55,2.02,'4  ASSOCIATE AND REVIEW',fontsize=12,color=ink,weight='bold')
for y,c,label in [(1.5,teal,'ID 1'),(1.03,blue,'ID 2')]:
 ax.plot([.8,1.4,2,2.6,3.2,3.8],[y,y+.1,y-.07,y+.02,y+.16,y+.07],'-o',color=c,lw=2,ms=4)
 ax.text(4.1,y,label,color=c,fontsize=11)
ax.text(5.3,1.48,'Link detections over time; inspect identity at contact.',fontsize=11,color=ink)
ax.text(5.3,1.03,'Reviewed CSV → arena target and movement analysis',fontsize=11,color=ink)
fig.savefig(OUT/'tracking-method.svg',facecolor='white');plt.close(fig)
fig,ax=plt.subplots(figsize=(12,4.3));fig.subplots_adjust(.1,.22,.97,.8)
ax.set_xlim(0,12);ax.set_ylim(-.1,1.4);ax.set_yticks([]);ax.spines[['top','left','right']].set_visible(False)
ax.spines['bottom'].set_color('#c2cdc8');ax.set_xlabel('Time from trial start (s)',fontsize=11,color=ink);ax.set_xticks(range(0,13,2));ax.tick_params(colors=muted)
ax.barh(.65,6,left=0,height=.38,color='#e4e9e3');ax.barh(.65,3,left=6,height=.38,color='#b5d8cd');ax.barh(.65,3,left=9,height=.38,color='#eff3ed')
ax.text(3,.65,'Outside target',ha='center',va='center',color=ink);ax.text(7.5,.65,'3 s continuous dwell',ha='center',va='center',color=ink)
for x,label in [(6,'Entry'),(9,'First success')]:
 ax.axvline(x,ymin=.12,ymax=.7,color=teal,ls='--');ax.text(x,.08,label,ha='center',color=teal,fontsize=11)
ax.annotate('Time to target = 9 s',xy=(9,1.06),xytext=(0,1.06),arrowprops={'arrowstyle':'->','color':blue},fontsize=12,color=blue)
fig.suptitle('Entry and completed dwell are different events',x=.1,ha='left',fontsize=18,color=ink)
fig.text(.1,.035,'Illustrative example. Movement inside the target is allowed; leaving resets dwell.',fontsize=10,color=muted)
fig.savefig(OUT/'target-dwell.svg',facecolor='white');plt.close(fig)
# Interface guides describe the source's controls. They are not screenshots.
def panel(ax,x,y,w,h,title,lines=(),fill='#eef3f6',head='#2b6694'):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.03',fc=fill,ec='#ccd7dd'))
 ax.text(x+.2,y+h-.35,title,fontsize=12,color=head,weight='bold')
 for i,line in enumerate(lines):ax.text(x+.2,y+h-.73-i*.32,line,fontsize=10,color=ink)
def guide(title,h=8):
 f,a=plt.subplots(figsize=(12,h));f.subplots_adjust(.02,.02,.98,.98);a.set(xlim=(0,12),ylim=(0,h));a.axis('off')
 a.text(.3,h-.4,title,fontsize=18,color=ink)
 a.text(.3,h-.75,'Interface guide based on the supplied v1.3.0 code · not a screenshot',fontsize=9,color=muted)
 return f,a
f,a=guide('Analysis GUI · where each step happens',9)
panel(a,.3,6.75,11.4,1.1,'1  FILES',['Choose CSV     •     Choose video     •     Draw / load cool boxes'])
panel(a,.3,4.8,11.4,1.7,'2  ANALYSIS SETTINGS',['Mode / Target / Inside target / FPS','Trial 1 start / Target order / Scale (px/cm)','Video offset / Missing-data gap / Moving speed / Flag jump'])
panel(a,.3,3.78,11.4,.8,'3  FLIES INCLUDED IN ANALYSIS',[])
a.text(5.3,4.07,'ID checkboxes   •   All / None',fontsize=11,color=ink)
a.text(.4,3.36,'Recalculate     Export CSV     Choose export...     Export MP4',fontsize=12,color=teal,weight='bold')
panel(a,.3,.65,6.3,2.42,'4  VIDEO AND PLAYBACK',['Original frames with identity overlay','Play / step / frame slider / exact frame','Display one fly or all flies'])
panel(a,6.9,.65,4.8,2.42,'5  ANALYSIS PANELS',['Selected fly occupancy','First reach time by fly','Flies reaching target / current dwell'])
f.savefig(OUT/'gui-overview.svg',facecolor='white');plt.close(f)
f,a=guide('Target editor · register A–D in camera coordinates',7)
panel(a,.3,1.15,7.25,4.55,'REFERENCE FRAME',[])
a.add_patch(Ellipse((3.9,3.15),4.3,3.35,fc='#fffdf8',ec='#9baea7',lw=1.6))
for (x,y,label,c) in [(2.7,3.7,'A','#a74b31'),(4.3,3.7,'B',blue),(2.7,2.2,'C',teal),(4.3,2.2,'D','#655185')]:
 a.add_patch(Rectangle((x,y),.8,.7,fc='none',ec=c,lw=2));a.text(x+.4,y+.35,label,color=c,ha='center',va='center',fontsize=13)
a.text(3.9,1.53,'Synthetic layout only',ha='center',color=muted,fontsize=9)
panel(a,7.85,1.15,3.85,4.55,'CHOOSE A BOX, THEN DRAG',['Cool Box A / B / C / D','Draw in any order','Redraw to replace a box','Delete selected box','Clear all / Cancel / Use Boxes'])
a.text(.4,.6,'Frame slider     •     ±1 s     •     Previous / next frame     •     Exact frame → Go',fontsize=11,color=ink)
f.savefig(OUT/'gui-boxes.svg',facecolor='white');plt.close(f)
f,a=guide('Export chooser · select only the files you need',7.3)
panel(a,.3,1.25,5.55,4.95,'DATA FILES',['Framewise tracks CSV','Per-fly trial metrics CSV','Trial summary CSV','Fly colour key CSV','Analysis metadata JSON','Jump review CSV','Workflow and metric text'])
panel(a,6.15,1.25,5.55,4.95,'PLOTS (JPEG)',['Separate trajectory for every fly','All flies per trial','Combined trial trajectories','Individual time-to-target plots','Combined time-to-target plot','Trial time summary'])
a.text(.5,.65,'Select all     •     Clear all',fontsize=12,color=teal)
a.text(9,.65,'Cancel     Continue',fontsize=12,color=teal)
f.savefig(OUT/'gui-exports.svg',facecolor='white');plt.close(f)
