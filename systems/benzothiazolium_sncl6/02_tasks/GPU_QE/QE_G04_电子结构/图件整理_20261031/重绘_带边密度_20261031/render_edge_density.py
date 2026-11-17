"""Redraw QE band-edge pseudo-density cubes.
CBM: cell shifted by (0,1/2,1/2) so the SnCl6 octahedron sits at the cell centre.
VBM: original cell (the two cations already sit around the (1/2,1/2,1/2) inversion centre).
Isosurfaces at several fractions of the maximum; plus 2D slices through chosen planes.
Usage: python3 render_edge_density.py <CBM.cube> <VBM.cube> <outdir>
"""
import sys, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage.measure import marching_cubes
plt.rcParams['font.sans-serif']=['DejaVu Sans']
B2A=0.529177210903
Z2EL={50:'Sn',17:'Cl',16:'S',7:'N',6:'C',8:'O',1:'H'}
COL={'Sn':'#7d6a96','Cl':'#2ca02c','S':'#e0b000','N':'#3060d0','C':'#404040','O':'#d03020','H':'#f0f0f0'}
RAD={'Sn':180,'Cl':110,'S':110,'N':70,'C':60,'O':70,'H':18}

def read_cube(fn):
    with open(fn) as f:
        f.readline(); f.readline()
        t=f.readline().split(); nat=int(t[0])
        n=[];v=[]
        for _ in range(3):
            t=f.readline().split(); n.append(int(t[0])); v.append([float(x) for x in t[1:4]])
        Z=[];R=[]
        for _ in range(nat):
            t=f.readline().split(); Z.append(int(t[0])); R.append([float(x) for x in t[2:5]])
        data=np.fromstring(f.read(),sep=' ')
    n=np.array(n); V=np.array(v)*B2A; R=np.array(R)*B2A
    return data.reshape(n), V, [Z2EL[z] for z in Z], R

def prepare(fn, shift):
    rho,V,el,R=read_cube(fn)
    n=np.array(rho.shape); L=V*n[:,None]          # cell vectors (rows), Angstrom
    Li=np.linalg.inv(L)
    F=(R@Li+np.array(shift))%1.0
    roll=tuple(int(round(s*ni)) for s,ni in zip(shift,n))
    rho=np.roll(rho,roll,axis=(0,1,2))
    return rho,L,el,F

def bonds(el,F,L):
    X=F@L; out=[]
    for i in range(len(el)):
        for j in range(i+1,len(el)):
            a,b=el[i],el[j]
            cut=2.75 if 'Sn' in (a,b) else (1.25 if 'H' in (a,b) else 1.95)
            if np.linalg.norm(X[i]-X[j])<cut: out.append((i,j))
    return out

def draw_cell(ax,L):
    O=np.zeros(3)
    for a in range(3):
        for b in range(2):
            for c in range(2):
                o=[O,L[(a+1)%3]*b,L[(a+2)%3]*c]
                s=sum(o); e=s+L[a]
                ax.plot(*zip(s,e),color='0.55',lw=0.8)

def iso_panel(ax,rho,L,el,F,frac,color,title,stride=2,elev=18,azim=-62):
    r=rho[::stride,::stride,::stride]
    r=np.pad(r,((0,1),(0,1),(0,1)),mode='wrap')   # close surfaces at periodic faces
    lev=frac*rho.max()
    verts,faces,_,_=marching_cubes(r,level=lev)
    nsub=np.array(rho.shape)/stride
    X=(verts/nsub)@L
    pc=Poly3DCollection(X[faces],facecolor=color,edgecolor='none',alpha=0.42)
    ax.add_collection3d(pc)
    P=F@L
    for i,j in bonds(el,F,L):
        ax.plot(*zip(P[i],P[j]),color='0.35',lw=1.2,zorder=5)
    for e in RAD:
        m=[k for k,x in enumerate(el) if x==e]
        ax.scatter(*P[m].T,s=RAD[e]*0.55,c=COL[e],edgecolors='k',linewidths=0.4,depthshade=False)
    draw_cell(ax,L)
    allp=np.array([[i,j,k] for i in (0,1) for j in (0,1) for k in (0,1)])@L
    lo,hi=allp.min(0),allp.max(0); c=(lo+hi)/2; h=(hi-lo).max()/2
    ax.set_xlim(c[0]-h,c[0]+h); ax.set_ylim(c[1]-h,c[1]+h); ax.set_zlim(c[2]-h,c[2]+h)
    ax.set_box_aspect((1,1,1)); ax.view_init(elev=elev,azim=azim); ax.set_axis_off()
    ax.set_title(title,fontsize=11)

def trilinear(rho,fr):
    n=np.array(rho.shape); g=fr*n; i0=np.floor(g).astype(int); t=g-i0
    out=0
    for dx in (0,1):
        for dy in (0,1):
            for dz in (0,1):
                w=(t[...,0] if dx else 1-t[...,0])*(t[...,1] if dy else 1-t[...,1])*(t[...,2] if dz else 1-t[...,2])
                out=out+w*rho[(i0[...,0]+dx)%n[0],(i0[...,1]+dy)%n[1],(i0[...,2]+dz)%n[2]]
    return out

def slice_panel(ax,rho,L,el,F,idx,title,half=5.5,npts=220):
    """plane through atoms idx[0] (centre), idx[1], idx[2]"""
    P=F@L; c=P[idx[0]]; u=P[idx[1]]-c; u/=np.linalg.norm(u)
    w=P[idx[2]]-c; w-=u*(w@u); w/=np.linalg.norm(w)
    s=np.linspace(-half,half,npts); S,T=np.meshgrid(s,s)
    pts=c+S[...,None]*u+T[...,None]*w
    val=trilinear(rho,(pts@np.linalg.inv(L))%1.0)/rho.max()
    im=ax.contourf(S,T,val,levels=np.linspace(0,val.max(),30),cmap='magma')
    ax.contour(S,T,val,levels=[0.03,0.06,0.12],colors=['#9ecae1','#4292c6','white'],linewidths=0.8)
    nrm=np.cross(u,w)
    for k,e in enumerate(el):
        d=P[k]-c; d=d-np.round((d@np.linalg.inv(L)))@L
        if abs(d@nrm)<0.6 and abs(d@u)<half and abs(d@w)<half:
            ax.scatter(d@u,d@w,s=RAD[e]*0.5,c=COL[e],edgecolors='w',linewidths=0.6,zorder=5)
            if e!='H': ax.annotate(e,(d@u,d@w),xytext=(4,4),textcoords='offset points',color='w',fontsize=8)
    ax.set_aspect('equal'); ax.set_xlabel('Å'); ax.set_ylabel('Å'); ax.set_title(title,fontsize=11)
    plt.colorbar(im,ax=ax,fraction=0.046,label='density / max')

if __name__=='__main__':
    cbm_fn,vbm_fn,out=sys.argv[1:4]
    jobs=[('CBM',cbm_fn,(0,0.5,0.5),'#e6863b'),('VBM',vbm_fn,(0,0,0),'#3b7fe6')]
    for name,fn,shift,col in jobs:
        rho,L,el,F=prepare(fn,shift)
        fig=plt.figure(figsize=(16,5.8))
        for k,fr in enumerate((0.03,0.06,0.12)):
            ax=fig.add_subplot(1,3,k+1,projection='3d')
            iso_panel(ax,rho,L,el,F,fr,col,f'{name}  isosurface {int(fr*100)}% of max')
        fig.suptitle(f'Scalar-relativistic PBE-D3 {name} pseudo-density'+(' (cell shifted: Sn at centre)' if name=='CBM' else ''),fontsize=13)
        fig.tight_layout(); fig.savefig(f'{out}/{name}_isosurface_3levels.png',dpi=130); plt.close(fig)
        # slices
        fig,ax=plt.subplots(figsize=(6.4,5.4))
        if name=='CBM':
            sn=el.index('Sn'); P=F@L
            cls=[k for k,e in enumerate(el) if e=='Cl']
            d=[np.linalg.norm(P[k]-P[sn]) for k in cls]; cls=[cls[i] for i in np.argsort(d)]
            c1=cls[0]; c2=[k for k in cls if abs((P[k]-P[sn])@(P[c1]-P[sn]))<2.0][0]
            slice_panel(ax,rho,L,el,F,(sn,c1,c2),'CBM slice: Sn + 4 equatorial Cl plane')
        else:
            S_=[k for k,e in enumerate(el) if e=='S']; P=F@L
            s0=S_[0]
            nb=sorted([k for k,e in enumerate(el) if e in('C','N')],key=lambda k:np.linalg.norm(P[k]-P[s0]))
            far=sorted(nb[:9],key=lambda k:-np.linalg.norm(P[k]-P[s0]))[0]
            slice_panel(ax,rho,L,el,F,(nb[0],s0,far),'VBM slice: benzothiazolium ring plane',half=4.5)
        fig.tight_layout(); fig.savefig(f'{out}/{name}_slice.png',dpi=150); plt.close(fig)
    print('done')
