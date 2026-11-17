import sys, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage import measure
B = 0.529177
col = {1:'#e0e0e0', 6:'#404040', 7:'#3050f8', 8:'#ff0d0d', 17:'#1ff01f', 50:'#a0a0c0'}
rad = {1:25, 6:60, 7:60, 8:60, 17:110, 50:160}
def read(fn):
    L = open(fn).read().split('\n')
    na = int(L[2].split()[0]); org = np.array([float(x) for x in L[2].split()[1:4]])
    n = []; v = []
    for i in (3, 4, 5):
        t = L[i].split(); n.append(int(t[0])); v.append([float(x) for x in t[1:4]])
    at = []
    for i in range(abs(na)):
        t = L[6+i].split(); at.append((int(t[0]), np.array([float(x) for x in t[2:5]])))
    s = 6 + abs(na) + (1 if na < 0 else 0)
    data = np.array(' '.join(L[s:]).split(), dtype=float).reshape(n)
    return org, np.array(v), n, at, data
def draw(ax, fn, iso, title):
    org, v, n, at, d = read(fn)
    sp = (v[0][0], v[1][1], v[2][2])
    for sgn, c in ((1, '#d62728'), (-1, '#1f77b4')):
        if (d*sgn).max() < iso: continue
        vs, fs, _, _ = measure.marching_cubes(d*sgn, iso, spacing=sp)
        vs = (vs + org) * B
        pc = Poly3DCollection(vs[fs], alpha=0.55, facecolor=c, edgecolor='none')
        ax.add_collection3d(pc)
    P = np.array([a[1]*B for a in at]); Z = [a[0] for a in at]
    for i in range(len(at)):
        for j in range(i+1, len(at)):
            dd = np.linalg.norm(P[i]-P[j])
            lim = 3.0 if 50 in (Z[i], Z[j]) else (1.25 if 1 in (Z[i], Z[j]) else 1.8)
            if dd < lim and not (Z[i] == 1 and Z[j] == 1):
                ax.plot(*zip(P[i], P[j]), color='#777777', lw=1)
    ax.scatter(P[:,0], P[:,1], P[:,2], c=[col.get(z, 'k') for z in Z], s=[rad.get(z, 50) for z in Z], edgecolors='k', linewidths=0.3, depthshade=False)
    c0 = P.mean(0); r = (P.max(0)-P.min(0)).max()/2 + 1
    ax.set_xlim(c0[0]-r, c0[0]+r); ax.set_ylim(c0[1]-r, c0[1]+r); ax.set_zlim(c0[2]-r, c0[2]+r)
    ax.set_axis_off(); ax.set_title(title, fontsize=11); ax.view_init(elev=20, azim=-60)
iso = 0.03
items = [('mo147', 'HOMO-1 (MO 147)'), ('mo148', 'HOMO (MO 148)'), ('mo149', 'LUMO (MO 149)'), ('mo150', 'LUMO+1 (MO 150)')]
fig = plt.figure(figsize=(14, 12))
for k, (f, t) in enumerate(items):
    ax = fig.add_subplot(2, 2, k+1, projection='3d'); draw(ax, f + '.cube', iso, t)
    f1 = plt.figure(figsize=(7, 6)); a1 = f1.add_subplot(111, projection='3d'); draw(a1, f + '.cube', iso, t)
    f1.savefig(f + '.png', dpi=160, bbox_inches='tight'); plt.close(f1)
fig.suptitle('PBE0/def2-SVP frontier orbitals, isovalue 0.03 a.u. (red +, blue -)', fontsize=13)
fig.savefig('orbitals_2x2.png', dpi=130, bbox_inches='tight')
print('RENDER_DONE')
