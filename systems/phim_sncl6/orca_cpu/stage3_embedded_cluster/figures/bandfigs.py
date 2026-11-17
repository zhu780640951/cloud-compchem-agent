import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D='/tmp/claude-0/-home-claude/1b01cb4e-7f95-5e12-9f03-0fca22c4b02c/scratchpad/qe_drive/QE_PhIm2SnCl6/02_bands_pdos/'
OUT='/tmp/claude-0/-home-claude/1b01cb4e-7f95-5e12-9f03-0fca22c4b02c/scratchpad/guide/img/'
INK='#0b0b0b'; INK2='#52514e'; GRID='#e4e3df'; MUTED='#b9b8b3'
C_CAT='#eb6834'; C_SN='#2a78d6'; C_CL='#1baf7a'; C_N='#eda100'
plt.rcParams.update({'font.family':['Noto Sans CJK SC','DejaVu Sans'],'font.size':10,'axes.edgecolor':INK2,
  'axes.labelcolor':INK,'xtick.color':INK2,'ytick.color':INK2,'axes.spines.top':False,'axes.spines.right':False,
  'figure.facecolor':'white','axes.facecolor':'white','axes.unicode_minus':False})
EVBM=0.9498
B=[];cur=[]
for l in open(D+'bands.dat.gnu'):
    p=l.split()
    if not p:
        if cur: B.append(np.array(cur)); cur=[]
        continue
    cur.append([float(p[0]),float(p[1])])
if cur: B.append(np.array(cur))
hs=[0.0,0.5112,1.0225,1.3772,1.7319,1.9840,2.5694]; lab=['Γ','X','Γ','Y','Γ','Z','R']
P=np.loadtxt(D+'pdos_by_element.dat'); cols='E total C-p C-s Cl-p Cl-s H-s N-p N-s O-p O-s Sn-d Sn-p Sn-s'.split()
col={c:P[:,i] for i,c in enumerate(cols)}

fig,(a,b)=plt.subplots(1,2,figsize=(10,5.6),sharey=True,gridspec_kw={'width_ratios':[2.3,1],'wspace':0.05})
for i,bd in enumerate(B):
    n=i+1; e=bd[:,1]-EVBM
    if e.max()<-3.2 or e.min()>5.2: continue
    if 179<=n<=182 or 185<=n<=188: c,lw,z=C_CAT,1.8,3
    elif n in (183,184): c,lw,z=C_SN,2.2,4
    else: c,lw,z=MUTED,0.9,2
    a.plot(bd[:,0],e,color=c,lw=lw,zorder=z,solid_capstyle='round')
for x in hs: a.axvline(x,color=GRID,lw=0.8,zorder=1)
a.axhline(0,color=INK2,lw=0.7,ls=(0,(3,3)),zorder=1)
a.set_xticks(hs); a.set_xticklabels(lab); a.set_xlim(0,hs[-1]); a.set_ylim(-3,5)
a.set_ylabel('E − E$_{VBM}$ (eV)')
a.annotate('',xy=(0.03,2.201),xytext=(0.03,0.0),arrowprops=dict(arrowstyle='<->',color=INK,lw=1.1))
a.text(0.07,1.1,'PBE 带隙 2.20 eV\nHSE06 带隙 2.96 eV',fontsize=9,color=INK,va='center')
a.text(2.55,2.62,'[SnCl₆] σ*（导带底）',fontsize=8.5,color=C_SN,ha='right')
a.text(2.55,3.62,'阳离子 π*',fontsize=8.5,color=C_CAT,ha='right')
a.text(2.55,0.12,'阳离子 π（价带顶）',fontsize=8.5,color=C_CAT,ha='right',va='bottom')
a.text(2.55,-1.6,'Cl 3p 为主的占据带',fontsize=8.5,color=INK2,ha='right',va='center',bbox=dict(boxstyle='round,pad=0.25',fc='white',ec='none'))
a.set_title('(a) 能带结构',fontsize=10,loc='left',color=INK)
m=(col['E']>=-3)&(col['E']<=5)
b.fill_betweenx(col['E'][m],0,col['total'][m],color='#efeeea',lw=0)
for k,c,nm in [('C-p',C_CAT,'C 2p'),('N-p',C_N,'N 2p'),('Cl-p',C_CL,'Cl 3p'),('Sn-s',C_SN,'Sn 5s')]:
    b.plot(col[k][m],col['E'][m],color=c,lw=1.6,label=nm)
b.plot([],[],color='#d8d7d2',lw=6,label='总 DOS')
b.axhline(0,color=INK2,lw=0.7,ls=(0,(3,3)))
b.set_xlim(0,135); b.set_xlabel('态密度 (states/eV/cell)')
b.legend(loc='upper right',fontsize=8,frameon=False)
b.set_title('(b) 投影态密度 PDOS',fontsize=10,loc='left',color=INK)
fig.suptitle('周期计算：价带顶是阳离子 π，导带底是 [SnCl₆] σ*，两者都几乎不色散',fontsize=10.5,x=0.01,ha='left',color=INK)
fig.text(0.01,0.01,'QE 7.5，PBE+D3(BJ)/PAW，60/480 Ry。能带路径 Γ–X–Γ–Y–Γ–Z–R；PDOS 来自 4×3×2 NSCF，高斯展宽 0.06 eV。HSE06 带隙来自 SG15 赝势、3×2×2 k 网格的单独计算。\n价带极平（宽 60 meV）：沿路径价带顶在 X 点，只比 Γ 高 0.01 eV；导带底在 Γ。',fontsize=7.6,color=INK2)
fig.subplots_adjust(left=0.07,right=0.98,top=0.88,bottom=0.16)
fig.savefig(OUT+'G7_bands_pdos.png',dpi=220); plt.close(fig)

# downsampled cubes for rendering
def down(src,dst,f=2):
    L=open(src).read().split('\n'); n=int(L[2].split()[0]); g=[int(L[i].split()[0]) for i in (3,4,5)]
    v=np.array(' '.join(L[6+n:]).split(),float).reshape(g)
    g2=[x//f for x in g]; v=v[:g2[0]*f,:g2[1]*f,:g2[2]*f].reshape(g2[0],f,g2[1],f,g2[2],f).mean((1,3,5))
    hdr=L[:2]+[L[2]]
    for i in range(3):
        p=L[3+i].split(); hdr.append('%5d %12.6f %12.6f %12.6f'%(g2[i],*(float(x)*f for x in p[1:4])))
    hdr+=L[6:6+n]
    flat=v.ravel(); body='\n'.join(' '.join('%.5e'%x for x in flat[i:i+6]) for i in range(0,flat.size,6))
    open(dst,'w').write('\n'.join(hdr)+'\n'+body+'\n')
    s=np.sort(flat)[::-1]; c=np.cumsum(s)/s.sum()
    print(dst.split('/')[-1],g2,'iso50',s[np.searchsorted(c,0.5)],'iso70',s[np.searchsorted(c,0.7)])
down(D+'vbm_band182_Gamma.cube',OUT+'../vbm_ds.cube'); down(D+'cbm_band183_Gamma.cube',OUT+'../cbm_ds.cube')
