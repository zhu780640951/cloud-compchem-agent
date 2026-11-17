"""Band gap, element/orbital-resolved PDOS, band-edge composition and band structure plot for step 2."""
import glob, os, re, sys
import numpy as np
trapz = getattr(np, "trapezoid", None) or np.trapz
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

W = sys.argv[1] if len(sys.argv) > 1 else "."
txt = open(f"{W}/scf.out").read()
m = re.findall(r"highest occupied, lowest unoccupied level \(ev\):\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)", txt)
vbm, cbm = map(float, m[-1])
lines = [f"SCF (k 3x2x2): VBM = {vbm:.3f} eV, CBM = {cbm:.3f} eV, gap = {cbm - vbm:.3f} eV (PBE, underestimates)"]

# ---- PDOS grouped by element and l ----
L = "spdf"
groups = {}
E = None
for f in glob.glob(f"{W}/phim.pdos_atm#*"):
    el = re.search(r"\((\w+)\)_wfc", f).group(1)
    l = re.search(r"wfc#\d+\((\w)\)", f).group(1)
    d = np.loadtxt(f)
    E = d[:, 0]
    groups[(el, l)] = groups.get((el, l), 0) + d[:, 1]   # column 2 = ldos summed over m
tot = np.loadtxt(f"{W}/phim.pdos_tot")
Er = E - vbm
fig, ax = plt.subplots(figsize=(7, 4.2))
order = [("Cl", "p"), ("Sn", "s"), ("Sn", "p"), ("Sn", "d"), ("C", "p"), ("N", "p"), ("O", "p"), ("H", "s")]
for key in order:
    if key in groups and groups[key].max() > 0.05:
        ax.plot(Er, groups[key], lw=1.2, label=f"{key[0]} {key[1]}")
ax.plot(Er, tot[:, 2], color="k", lw=0.6, alpha=0.4, label="total")
ax.axvline(0, ls="--", c="gray", lw=0.8); ax.axvline(cbm - vbm, ls="--", c="gray", lw=0.8)
ax.set_xlim(-4, 6); ax.set_ylim(0, None)
ax.set_xlabel("E - E$_{VBM}$ (eV)"); ax.set_ylabel("PDOS (states/eV)"); ax.legend(fontsize=8, ncol=2)
ax.set_title("(2-PhImH)$_2$[SnCl$_6$]·2H$_2$O  PBE+D3")
fig.tight_layout(); fig.savefig(f"{W}/pdos.png", dpi=200)

def edge_comp(lo, hi, label):
    sel = (Er >= lo) & (Er <= hi)
    w = {k: trapz(v[sel], Er[sel]) for k, v in groups.items()}
    s = sum(w.values())
    top = sorted(w.items(), key=lambda kv: -kv[1])[:6]
    lines.append(f"{label} [{lo:+.2f},{hi:+.2f}] eV composition: " + ", ".join(f"{k[0]}-{k[1]} {100*v/s:.0f}%" for k, v in top))
    el = {}
    for (e, l), v in w.items(): el[e] = el.get(e, 0) + v
    lines.append(f"    by element: " + ", ".join(f"{e} {100*v/s:.0f}%" for e, v in sorted(el.items(), key=lambda kv: -kv[1])))
    org = sum(el.get(e, 0) for e in ("C", "N", "H")); inorg = el.get("Sn", 0) + el.get("Cl", 0); wat = el.get("O", 0)
    lines.append(f"    by part: [SnCl6] {100*inorg/s:.0f}%, organic cation {100*org/s:.0f}%, water(O) {100*wat/s:.0f}%")
edge_comp(-0.30, 0.05, "VBM")
g = cbm - vbm
edge_comp(g - 0.05, g + 0.30, "CBM")

# ---- band structure ----
gnu = f"{W}/bands.dat.gnu"
if os.path.exists(gnu):
    blocks = open(gnu).read().strip().split("\n\n")
    fig, ax = plt.subplots(figsize=(5, 4.2))
    for b in blocks:
        d = np.array([list(map(float, l.split())) for l in b.splitlines() if l.strip()])
        ax.plot(d[:, 0], d[:, 1] - vbm, c="k", lw=0.8)
    x = d[:, 0]
    hs = re.findall(r"high-symmetry point:.*x coordinate\s+(-?\d+\.\d+)", open(f"{W}/bandsx.out").read())
    ticks = [float(t) for t in hs] if len(hs) == 7 else np.linspace(x.min(), x.max(), 7)
    ax.set_xticks(ticks); ax.set_xticklabels(["Γ", "X", "Γ", "Y", "Γ", "Z", "R"])
    for t in ticks: ax.axvline(t, c="gray", lw=0.4)
    ax.axhline(0, ls="--", c="tab:blue", lw=0.8)
    ax.set_ylim(-3, 5); ax.set_xlim(x.min(), x.max()); ax.set_ylabel("E - E$_{VBM}$ (eV)")
    fig.tight_layout(); fig.savefig(f"{W}/bands.png", dpi=200)
    # band widths of VBM and CBM (flatness -> localization)
    bands = [np.array([list(map(float, l.split())) for l in b.splitlines() if l.strip()])[:, 1] for b in blocks]
    vb, cb = bands[181], bands[182]
    lines.append(f"band dispersion along path: VBM band width {1000*(vb.max()-vb.min()):.0f} meV, CBM band width {1000*(cb.max()-cb.min()):.0f} meV")
open(f"{W}/summary_step2.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
