import json, pickle, math, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, LinearSegmentedColormap
from matplotlib.patches import Rectangle, Circle

SP='/tmp/claude-0/-home-claude/1b01cb4e-7f95-5e12-9f03-0fca22c4b02c/scratchpad/'
OUT=SP+'guide/img/'
import os; os.makedirs(OUT,exist_ok=True)
JOB='/mnt/attach/outputs/b5/jobs/04c2_SOC_ZORA_at_T1geom_CatA/'

INK='#0b0b0b'; INK2='#52514e'; MUTED='#8a8984'; GRID='#e4e3df'; SURF='#ffffff'
C_A='#eb6834'; C_B='#1baf7a'; C_SN='#2a78d6'; C_W='#e87ba4'
NEG='#2a78d6'; POS='#e34948'
FR=['CatA','CatB','SnCl6','H2O']; FC={'CatA':C_A,'CatB':C_B,'SnCl6':C_SN,'H2O':C_W}
FL={'CatA':'阳离子 A','CatB':'阳离子 B','SnCl6':'[SnCl₆]²⁻','H2O':'H₂O'}
plt.rcParams.update({'font.family':['Noto Sans CJK SC','DejaVu Sans'],'font.size':10,'axes.edgecolor':INK2,
  'axes.labelcolor':INK,'xtick.color':INK2,'ytick.color':INK2,'axes.spines.top':False,'axes.spines.right':False,
  'figure.facecolor':SURF,'axes.facecolor':SURF,'axes.unicode_minus':False,'mathtext.fontset':'dejavusans'})

def frag(i): return 'SnCl6' if i<7 else 'CatA' if i<27 else 'CatB' if i<47 else 'H2O'

# ---------- data
L=open(JOB+'qm_cluster.xyz').read().splitlines()
qm=[(l.split()[0],np.array(list(map(float,l.split()[1:4])))) for l in L[2:2+int(L[0])]]
P=open(JOB+'mm_charges.pc').read().split('\n')
pc=np.array([list(map(float,l.split())) for l in P[1:1+int(P[0])]])
q=pc[:,0]; R=pc[:,1:4]
QX=np.array([x for _,x in qm])

# ---------- G1: embedded-cluster model (two projections)
fig,axs=plt.subplots(1,2,figsize=(10,4.6),gridspec_kw={'width_ratios':[1.25,1]})
ax=axs[0]
o=np.argsort(np.abs(q))
ax.scatter(R[o,0],R[o,1],s=3,c=np.where(q[o]<0,NEG,POS),alpha=0.35,lw=0)
ax.scatter(QX[:,0],QX[:,1],s=10,c=INK,lw=0)
lo=QX.min(0)-1.5; hi=QX.max(0)+1.5
ax.add_patch(Rectangle(lo[:2],*(hi-lo)[:2],fill=False,ec=INK,lw=1.2))
ax.set_aspect('equal'); ax.set_xlabel('x (Å)'); ax.set_ylabel('y (Å)')
ax.set_title('(a) 11,077 个点电荷包围 53 原子的量子区（黑框）',fontsize=10,loc='left',color=INK)
ax.scatter([],[],s=18,c=NEG,label='负电荷（多在 Cl 上）'); ax.scatter([],[],s=18,c=POS,label='正电荷（多在 H、Sn 上）')
ax.scatter([],[],s=18,c=INK,label='量子区原子')
ax.legend(loc='lower left',fontsize=8,frameon=True,framealpha=0.9,edgecolor=GRID)
ax=axs[1]
near=np.all((R>lo-4)&(R<hi+4),axis=1)
ax.scatter(R[near,0],R[near,1],s=np.clip(np.abs(q[near])*40,3,40),c=np.where(q[near]<0,NEG,POS),alpha=0.35,lw=0)
for i,(e,x) in enumerate(qm):
    for j in range(i+1,len(qm)):
        r={'H':0.31,'C':0.76,'N':0.71,'O':0.66,'Cl':1.02,'Sn':1.39}
        if np.linalg.norm(x-qm[j][1])<1.2*(r[e]+r[qm[j][0]]):
            ax.plot([x[0],qm[j][1][0]],[x[1],qm[j][1][1]],color=FC[frag(i)],lw=1.6,solid_capstyle='round',zorder=3)
for f in FR:
    idx=[i for i in range(len(qm)) if frag(i)==f]
    sz=[60 if qm[i][0]=='Sn' else 26 if qm[i][0]=='Cl' else 6 if qm[i][0]=='H' else 14 for i in idx]
    ax.scatter(QX[idx,0],QX[idx,1],s=sz,c=FC[f],ec='white',lw=0.6,zorder=4,label=FL[f])
ax.set_xlim(lo[0]-4,hi[0]+4); ax.set_ylim(lo[1]-4,hi[1]+4); ax.set_aspect('equal'); ax.set_xlabel('x (Å)')
ax.set_title('(b) 放大：量子区四个片段 + 近邻点电荷',fontsize=10,loc='left',color=INK)
ax.legend(handles=[plt.Line2D([],[],marker='o',ls='-',color=FC[f],ms=6,lw=1.6) for f in FR],labels=[FL[f] for f in FR],loc='upper right',fontsize=8,frameon=True,framealpha=0.9,edgecolor=GRID,ncol=2)
fig.text(0.01,0.01,'沿 z 轴投影。点电荷按整分子放置（7×5×3 晶胞块），每个分子的电荷由 B3LYP/def2-SVP 静电势拟合得到。',fontsize=8,color=INK2)
fig.tight_layout(rect=(0,0.04,1,1)); fig.savefig(OUT+'G1_embedded_model.png',dpi=220); plt.close(fig)

# ---------- G2: electrostatic potential from the crystal at each QM atom
K=14.399645  # e/Å -> V
V=np.array([np.sum(K*q/np.linalg.norm(R-x,axis=1)) for x in QX])
fig,ax=plt.subplots(figsize=(7.2,3.6))
rng=np.random.default_rng(1)
for k,f in enumerate(FR):
    idx=np.array([i for i in range(len(qm)) if frag(i)==f])
    xs=k+rng.uniform(-0.18,0.18,len(idx))
    ax.scatter(xs,V[idx],s=22,c=FC[f],ec='white',lw=0.6,zorder=3)
    m=V[idx].mean(); ax.plot([k-0.32,k+0.32],[m,m],color=INK,lw=2,zorder=4)
    ax.text(k+0.36,m,'%+.2f V'%m,va='center',fontsize=9,color=INK)
ax.axhline(0,color=INK2,lw=0.8)
ax.set_xticks(range(4)); ax.set_xticklabels([FL[f] for f in FR]); ax.set_xlim(-0.6,3.9)
ax.set_ylabel('晶体静电势 V (V)'); ax.grid(axis='y',color=GRID,lw=0.8); ax.set_axisbelow(True)
ax.set_title('晶体电场：阴离子处为正电势，把它的轨道整体压低',fontsize=10.5,loc='left',color=INK)
fig.text(0.01,0.01,'每个点 = 一个量子区原子处由全部点电荷产生的电势 V = Σ q/(4πε₀r)；横线 = 片段平均值。正电势使该片段的电子能量降低 eV 数值约等于 V。',fontsize=7.6,color=INK2)
fig.tight_layout(rect=(0,0.05,1,1)); fig.savefig(OUT+'G2_site_potential.png',dpi=220); plt.close(fig)
print('mean V',{f:round(V[[i for i in range(53) if frag(i)==f]].mean(),2) for f in FR})

# ---------- G3: hole / electron composition per state (S0 geometry, 02b)
he=pickle.load(open(SP+'he.pkl','rb'))['S0 geometry (02b)']
fS=[0.000648,0.0000926,0.00221,0.0904,1.0486,0.0400,0.0548,0.0299,0.0573,0.0120,0.1077,0.0768,0.0180,0.0701,0.00178]
fig=plt.figure(figsize=(10.5,7.6))
gs=fig.add_gridspec(1,2,wspace=0.42)
for p,(mult,title) in enumerate([('S','单重态（吸收）'),('T','三重态')]):
    rows=[r for r in he if r[0].startswith(mult)]
    sub=gs[p].subgridspec(1,2,wspace=0.06)
    for c,(key,name) in enumerate([(2,'空穴（电子从哪里来）'),(3,'电子（电子到哪里去）')]):
        ax=fig.add_subplot(sub[c])
        for k,r in enumerate(rows):
            y=len(rows)-1-k; left=0
            for f in FR:
                w=r[key][f]*100
                if w>0.3: ax.barh(y,w-0.6 if w>1 else w,left=left,height=0.72,color=FC[f],lw=0)
                left+=w
        ax.set_xlim(0,100); ax.set_ylim(-0.6,len(rows)-0.4)
        ax.set_xticks([0,50,100] if c==1 else [0,50]); ax.tick_params(axis='x',labelsize=8)
        ax.spines['left'].set_visible(False)
        if c==0:
            ax.set_yticks(range(len(rows))); ax.tick_params(axis='y',length=0)
            ax.set_yticklabels(['%s  %.2f eV'%(r[0].replace('S','S').replace('T','T'),r[1]) for r in rows[::-1]],fontsize=8.5)
        else:
            ax.set_yticks([])
            for k,r in enumerate(rows):
                y=len(rows)-1-k
                lab='%.0f%%'%(100*r[4])
                if mult=='S' and fS[k]>=0.05: lab+='  f=%.2f'%fS[k]
                ax.text(103,y,lab,va='center',fontsize=8,color=INK if r[4]>=0.5 else POS)
        ax.set_title(name,fontsize=9,color=INK2)
    fig.text(0.07+0.5*p,0.955,title,fontsize=11,color=INK)
fig.text(0.47,0.925,'局域比例',fontsize=8,color=INK2,ha='right'); fig.text(0.985,0.925,'局域比例',fontsize=8,color=INK2,ha='right')
for k,f in enumerate(FR):
    fig.patches.append(Rectangle((0.07+k*0.13,0.035),0.015,0.014,transform=fig.transFigure,color=FC[f]))
    fig.text(0.09+k*0.13,0.042,FL[f],fontsize=9,va='center',color=INK)
fig.text(0.01,0.008,'TDA-ωB97X-D3/def2-TZVP，基态结构（02b）。两条色带颜色一致 = 局域激发；不一致 = 电荷转移。局域比例 = Σ h_F·e_F，红字表示 < 50%（电荷转移为主）。',fontsize=7.8,color=INK2)
fig.subplots_adjust(left=0.1,right=0.93,top=0.9,bottom=0.09)
fig.savefig(OUT+'G3_hole_electron.png',dpi=220); plt.close(fig)

# ---------- G4: SOC matrix heatmaps, embedded vs isolated cation
d=json.load(open(SP+'guide/figdata.json'))
cmap=LinearSegmentedColormap.from_list('b',['#f4f8fe','#cde2fb','#86b6ef','#3987e5','#256abf','#104281'])
norm=LogNorm(0.01,400)
fig,axs=plt.subplots(1,2,figsize=(10.6,4.9))
for ax,(k,title) in zip(axs,[('03','(a) 嵌入团簇（含 [SnCl₆]²⁻）'),('03bA','(b) 只有一个阳离子（对照）')]):
    M=np.full((10,11),np.nan)
    for t,s,x in d[k]['socme']: M[t-1,s]=max(x,0.01)
    ax.imshow(M,cmap=cmap,norm=norm,aspect='auto',origin='upper')
    for t in range(10):
        for s in range(11):
            x=M[t,s]
            if x>=1: ax.text(s,t,('%.0f'%x) if x>=10 else '%.1f'%x,ha='center',va='center',fontsize=6.8,color='white' if x>30 else INK)
    ax.set_xticks(range(11)); ax.set_xticklabels(['S₀']+['S%d'%i for i in range(1,11)],fontsize=7.5)
    ax.set_yticks(range(10)); ax.set_yticklabels(['T%d'%i for i in range(1,11)],fontsize=7.5)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(length=0); ax.set_title(title,fontsize=10,loc='left',color=INK)
    if k=='03bA':
        ax.add_patch(Rectangle((0.5,-0.5),2,6,fill=False,ec=POS,lw=1.8))
        ax.text(2.65,2.5,'吸收态附近\nS₁、S₂ × T₁–T₆\n全部 ≤ 0.1',fontsize=7.5,color=POS,va='center',ha='left',linespacing=1.3,bbox=dict(boxstyle='round,pad=0.3',fc='white',ec=POS,lw=0.8))
cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=axs,fraction=0.025,pad=0.02)
cb.set_label('|⟨T|Ĥ_SO|S⟩| (cm⁻¹)，对数刻度',fontsize=8.5); cb.outline.set_visible(False)
fig.suptitle('旋轨耦合矩阵：有 [SnCl₆]²⁻ 时出现几十到几百 cm⁻¹ 的耦合，单个阳离子在吸收态附近只有 ≤ 0.1 cm⁻¹',fontsize=10.5,x=0.01,ha='left',color=INK)
fig.text(0.01,0.01,'ZORA SOC-TDA ωB97X-D3/ZORA-def2-TZVP（Sn: SARC-ZORA-TZVP）。数值为三个分量合成的总耦合；只标出 ≥ 1 cm⁻¹ 的格子。两图的态编号各按自身能量排序，不是一一对应的同一个态。',fontsize=7.6,color=INK2)
fig.subplots_adjust(left=0.05,right=0.89,top=0.86,bottom=0.12,wspace=0.18)
fig.savefig(OUT+'G4_SOC_heatmap.png',dpi=220); plt.close(fig)

# ---------- G5: T1 spin population on CatA (04a2)
sp=d['04a2']['spin']; xyz=d['04a2']['xyz']
idx=list(range(7,27))
X=np.array([xyz[i][1:] for i in idx]); el=[xyz[i][0] for i in idx]; s=np.array([sp[i][2] for i in idx])
c0=X.mean(0); U,S_,Vt=np.linalg.svd(X-c0); P2=(X-c0)@Vt[:2].T
fig,ax=plt.subplots(figsize=(7.6,4.4))
r={'H':0.31,'C':0.76,'N':0.71,'O':0.66,'Cl':1.02}
for a in range(len(idx)):
    for b in range(a+1,len(idx)):
        if np.linalg.norm(X[a]-X[b])<1.2*(r[el[a]]+r[el[b]]):
            ax.plot(*P2[[a,b]].T,color=MUTED,lw=1.4,zorder=1)
for a in range(len(idx)):
    if abs(s[a])>0.02:
        ax.add_patch(Circle(P2[a],0.9*math.sqrt(abs(s[a])),color=POS if s[a]>0 else NEG,alpha=0.55,lw=0,zorder=2))
    ax.text(*P2[a],el[a],ha='center',va='center',fontsize=7 if el[a]=='H' else 8.5,color=INK if el[a]!='H' else MUTED,zorder=3)
    if abs(s[a])>=0.15: ax.text(P2[a][0],P2[a][1]-0.62,'%+.2f'%s[a],ha='center',va='top',fontsize=7.5,color=INK,zorder=3)
ax.set_aspect('equal'); ax.axis('off')
ax.set_title('T₁ 结构下的自旋布居：两个未成对电子全部在阳离子 A 上（总和 2.00）',fontsize=10.5,loc='left',color=INK)
ax.add_patch(Circle((0,0),0.001,color=POS,label='自旋向上（正）')); ax.add_patch(Circle((0,0),0.001,color=NEG,label='自旋向下（负）'))
h=[plt.Line2D([],[],marker='o',ls='',color=POS,alpha=0.6,ms=9),plt.Line2D([],[],marker='o',ls='',color=NEG,alpha=0.6,ms=9)]
ax.legend(h,['正自旋布居','负自旋布居'],loc='lower right',fontsize=8,frameon=False)
fig.text(0.01,0.01,'UKS-ωB97X-D3/def2-SVP（04a2），Mulliken 自旋布居投影到分子平面；圆面积 ∝ |布居|，只标出 |布居| ≥ 0.15 的原子。',fontsize=7.6,color=INK2)
fig.tight_layout(rect=(0,0.04,1,1)); fig.savefig(OUT+'G5_T1_spin.png',dpi=220); plt.close(fig)
print('spin sum CatA',round(s.sum(),3),'others',round(sum(x[2] for i,x in enumerate(sp) if i not in idx),3))

# ---------- G6: band-edge composition QE vs PWmat
cats=['C','N','Cl','Sn','其他']; cc={'C':C_A,'N':'#eda100','Cl':C_B,'Sn':C_SN,'其他':'#c3c2b7'}
data=[('QE  VBM',{'C':90,'N':9,'其他':1}),('PWmat  VBM',{'C':84,'N':7,'Cl':8,'其他':1}),
      ('QE  CBM',{'Cl':53,'Sn':42,'其他':5}),('PWmat  CBM',{'Cl':58,'Sn':27,'C':11,'其他':4})]
fig,ax=plt.subplots(figsize=(7.4,3.0))
for k,(lab,v) in enumerate(data):
    y=3-k-(0.4 if k>=2 else 0); left=0
    for c in cats:
        w=v.get(c,0)
        if w:
            ax.barh(y,w-0.7,left=left,height=0.62,color=cc[c],lw=0)
            if w>=7: ax.text(left+w/2,y,'%s %d'%(c,w),ha='center',va='center',fontsize=8,color='white' if c in('Sn','C') else INK)
        left+=w
ax.set_yticks([3,2,0.6,-0.4]); ax.set_yticklabels([x for x,_ in data]); ax.tick_params(axis='y',length=0)
ax.set_xlim(0,100); ax.set_xlabel('元素贡献 (%)'); ax.spines['left'].set_visible(False)
ax.set_title('两个程序都给出：价带顶是有机阳离子，导带底是 [SnCl₆]',fontsize=10.5,loc='left',color=INK)
fig.text(0.01,0.01,'QE：PBE+D3(BJ)/PAW，逐能带投影；PWmat：PBE+D3/SG15，DOS 能量窗口积分。PBE 带隙 2.20 / 2.21 eV（Γ 点直接）。',fontsize=7.6,color=INK2)
fig.tight_layout(rect=(0,0.06,1,1)); fig.savefig(OUT+'G6_band_edge_composition.png',dpi=220); plt.close(fig)
