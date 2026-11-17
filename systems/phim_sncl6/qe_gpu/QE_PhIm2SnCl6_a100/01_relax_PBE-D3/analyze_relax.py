"""Summarize the finished relax: energies, forces, final structure (CIF/XYZ), key geometry, plot. Writes into the Drive folder."""
import glob, os, re, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ase.io import read, write
from ase.neighborlist import neighbor_list

OUT = sys.argv[1] if len(sys.argv) > 1 else "/content/drive/MyDrive/QE_PhIm2SnCl6/01_relax_PBE-D3"
parts = sorted(glob.glob(f"{OUT}/relax_part*.out")) + [f"{OUT}/relax.out"]
E, F = [], []
for p in parts:
    t = open(p).read()
    E += [float(x) for x in re.findall(r"^!\s+total energy\s+=\s+(-?\d+\.\d+)", t, re.M)]
    F += [float(x) for x in re.findall(r"Total force =\s+(\d+\.\d+)", t)]
RY = 13.605693
E = np.array(E); F = np.array(F)
final = read(f"{OUT}/relax.out", index=-1, format="espresso-out")
start = read(f"{OUT}/relax.in", format="espresso-in") if not glob.glob(f"{OUT}/relax_part*.out") else read(parts[0], index=0, format="espresso-out")
write(f"{OUT}/relaxed_structure.cif", final)
write(f"{OUT}/relaxed_structure.xyz", final)
write(f"{OUT}/start_structure.cif", start)
fmax = np.abs(final.get_forces()).max() if final.calc is not None else float("nan")

s = np.array(final.get_chemical_symbols())
i, j, d = neighbor_list("ijd", final, 3.0)
def rng(a, b, lo=0, hi=3.0):
    m = (s[i] == a) & (s[j] == b) & (d > lo) & (d < hi)
    return (d[m].min(), d[m].max()) if m.any() else (np.nan, np.nan)
lines = [
    f"ionic steps: {len(E)}",
    f"E_start = {E[0]:.6f} Ry   E_final = {E[-1]:.6f} Ry   dE = {(E[-1]-E[0])*RY:.3f} eV",
    f"E_final = {E[-1]*RY:.4f} eV",
    f"final total force = {F[-1]:.6f} Ry/Bohr;  max |F| component = {fmax:.4f} eV/A (target 0.02)",
    "converged: " + str("End final coordinates" in open(f"{OUT}/relax.out").read()),
    "Sn-Cl  %.3f-%.3f A" % rng("Sn", "Cl"),
    "N-H    %.3f-%.3f A" % rng("N", "H", 0.8, 1.2),
    "O-H    %.3f-%.3f A" % rng("O", "H", 0.8, 1.2),
    "C-H    %.3f-%.3f A" % rng("C", "H", 0.8, 1.2),
    "H...Cl %.3f-%.3f A (< 3.0)" % rng("H", "Cl", 1.5, 3.0),
]
# RMSD of heavy atoms vs. the experimental (start) structure, minimum image
heavy = s != "H"
dfrac = final.get_scaled_positions() - start.get_scaled_positions()
dfrac -= np.round(dfrac)
dcart = dfrac @ final.cell.array
lines.append("heavy-atom RMSD vs experiment = %.3f A (max %.3f A)" % (np.sqrt((dcart[heavy] ** 2).sum(1).mean()), np.sqrt((dcart[heavy] ** 2).sum(1)).max()))
open(f"{OUT}/summary.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))

fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
ax[0].plot((E - E[-1]) * RY, "o-", ms=3); ax[0].set_xlabel("ionic step"); ax[0].set_ylabel("E - E_final (eV)")
ax[1].semilogy(F, "o-", ms=3)
ax[1].set_xlabel("ionic step"); ax[1].set_ylabel("total force (Ry/Bohr)")
fig.tight_layout(); fig.savefig(f"{OUT}/relax_convergence.png", dpi=150)
