"""Recreate the descriptive figure from the explicitly labelled source CSV."""
from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
with (ROOT/'docs/downloads/preliminary_trial_times.csv').open() as f:
 rows=list(csv.DictReader(f))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none'})
fig,ax=plt.subplots(figsize=(9,4.7),facecolor='#f5f3ec')
ax.set_facecolor('#f5f3ec')
for row in rows:
 x,y=int(row['trial']),float(row['reported_time_s']);flag=bool(row['source_annotation'])
 ax.vlines(x,0,y,color='#a8b89d',linewidth=2)
 ax.scatter(x,y,s=65,facecolors='#f5f3ec' if flag else '#234e40',edgecolors='#234e40',linewidth=1.6,zorder=3)
 ax.annotate(f"{y:g}"+(' (nr)' if flag else ''),(x,y),xytext=(0,11),textcoords='offset points',ha='center',fontsize=9,color='#193c35')
ax.set(ylim=(0,300),xlim=(.4,8.6),xticks=range(1,9),yticks=range(0,301,60),xlabel='Trial',ylabel='Reported time to target (s)')
ax.spines[['top','right']].set_visible(False)
ax.spines[['bottom','left']].set_color('#a7b59b')
ax.tick_params(colors='#4b6150');ax.grid(axis='y',color='#d4dbcd',linewidth=.7);ax.set_axisbelow(True)
ax.set_title('Preliminary trial summaries',loc='left',fontweight='normal',fontsize=18,pad=28,color='#193c35')
fig.text(.125,.89,'Source values supplied 7 October 2026 · annotations retained · no inferred error bars',fontsize=9,color='#5f6d62')
fig.tight_layout(rect=(0,0,1,.90))
fig.savefig(ROOT/'docs/assets/preliminary-trials.svg',bbox_inches='tight',metadata={'Date':None,'Description':'Preliminary values; hollow points are source nr flags; no fitted trend.'})
