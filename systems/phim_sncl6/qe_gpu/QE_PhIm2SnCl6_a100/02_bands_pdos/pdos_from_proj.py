import re, sys, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
W = sys.argv[1]; VBM = float(sys.argv[2]); GAP = float(sys.argv[3])
st = re.findall(r"state #\s*(\d+): atom\s+(\d+) \((\w+)\s*\).*?\(l=(\d)", open(f"{W}/projwfc.out").read())
key = {int(i): (e, "spdf"[int(l)]) for i, a, e, l in st}
x = open(f"{W}/tmp/phim_sncl6.save/atomic_proj.xml").read()
RY = 13.605693122994
E = np.linspace(VBM - 6, VBM + 7, 2601); sig = 0.06
pd = {}; tot = np.zeros_like(E)
for blk in re.split(r"<K-POINT", x)[1:]:
    w = float(re.search(r'Weight="([-\d.Ee+]+)"', blk).group(1))
    eig = np.array(re.search(r"<E>(.*?)</E>", blk, re.S).group(1).split(), float) * RY
    g = np.exp(-(E[None, :] - eig[:, None]) ** 2 / (2 * sig ** 2)) / (sig * np.sqrt(2 * np.pi))
    tot += 2 * w * g.sum(0)
    for m in re.finditer(r'<ATOMIC_WFC index="(\d+)"[^>]*>(.*?)</ATOMIC_WFC>', blk, re.S):
        v = np.array(m.group(2).split(), float).reshape(-1, 2); c2 = (v ** 2).sum(1)
        k = key[int(m.group(1))]; pd[k] = pd.get(k, 0) + 2 * w * (c2 @ g)
Er = E - VBM
fig, ax = plt.subplots(figsize=(7, 4.2))
for k in [("Cl", "p"), ("Sn", "s"), ("Sn", "p"), ("C", "p"), ("N", "p"), ("O", "p"), ("H", "s")]:
    if k in pd: ax.plot(Er, pd[k], lw=1.2, label=f"{k[0]} {k[1]}")
ax.plot(Er, tot, c="k", lw=0.6, alpha=0.4, label="total")
ax.axvline(0, ls="--", c="gray", lw=0.8); ax.axvline(GAP, ls="--", c="gray", lw=0.8)
ax.set_xlim(-4, 6); ax.set_ylim(0, None); ax.legend(fontsize=8, ncol=2)
ax.set_xlabel("E - E$_{VBM}$ (eV)"); ax.set_ylabel("PDOS (states/eV/cell)")
ax.set_title("(2-PhImH)$_2$[SnCl$_6$]·2H$_2$O  PBE+D3, Gaussian 0.06 eV")
fig.tight_layout(); fig.savefig(f"{W}/pdos.png", dpi=200)
np.savetxt(f"{W}/pdos_by_element.dat", np.column_stack([Er, tot] + [pd[k] for k in sorted(pd)]),
           header="E-EVBM total " + " ".join(f"{a}-{b}" for a, b in sorted(pd)), fmt="%.5f")
print("pdos.png written")
