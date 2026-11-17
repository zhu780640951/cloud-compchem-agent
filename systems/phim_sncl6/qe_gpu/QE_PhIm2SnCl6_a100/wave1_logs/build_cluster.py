"""Cut an embedded cluster from the relaxed crystal.
QM  : one [SnCl6]2- + the two 2-phenylimidazolium cations and two waters most strongly H-bonded to it (neutral, 53 atoms)
MM  : all other whole molecules in a neutral block of 7x5x3 unit cells, as DFT ESP-fitted point charges (per molecule,
      constrained to the formal molecular charge); the paper used QEq charges for the same electrostatic embedding.
usage: build_cluster.py <relax.out|cif> <outdir>"""
import sys, os, json, warnings; warnings.filterwarnings("ignore")
import numpy as np
from ase.io import read, write
from ase.neighborlist import neighbor_list, natural_cutoffs
from ase import Atoms

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
a = read(src, index=-1, format="espresso-out") if src.endswith(".out") else read(src)
cell = a.cell.array
nat = len(a)

# ---- whole molecules of the reference cell (molecule assigned to the cell holding its centroid) ----
sup = a.repeat((3, 3, 3)); sup.pbc = False
i, j = neighbor_list("ij", sup, natural_cutoffs(sup, mult=1.15))
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
g = sp.coo_matrix((np.ones(len(i)), (i, j)), shape=(len(sup), len(sup)))
ncomp, lab = connected_components(g, directed=False)
inv = np.linalg.inv(cell)
mols = []
for c in range(ncomp):
    idx = np.where(lab == c)[0]
    cen = sup.positions[idx].mean(0) @ inv          # fractional in the 3x3x3 frame
    if np.all((cen >= 1) & (cen < 2)):
        pos = sup.positions[idx] - cell.sum(0)      # shift so the reference cell is [0,1)
        mols.append({"sym": [sup[k].symbol for k in idx], "pos": pos})
def kind(m):
    s = m["sym"]
    if "Sn" in s: return "SnCl6", -2
    if "N" in s: return "PhImH", +1
    return "H2O", 0
for m in mols: m["kind"], m["q"] = kind(m)
counts = {k: sum(m["kind"] == k for m in mols) for k in ("SnCl6", "PhImH", "H2O")}
assert counts == {"SnCl6": 2, "PhImH": 4, "H2O": 4}, counts
assert sum(len(m["sym"]) for m in mols) == nat

# ---- point charges: DFT electrostatic-potential (Merz-Kollman type) charges of each molecule ----
# (Open Babel's QEq gives unphysical charges for Sn, e.g. Sn -5.9 / Cl +0.6, so ESP charges are used instead;
#  they come from B3LYP/def2-SVP (Sn def2-TZVP+ECP) on each molecule in its crystal geometry, constrained to the formal charge)
from pyscf import gto, dft, lib
VDW = {"H": 1.20, "C": 1.70, "N": 1.55, "O": 1.52, "Cl": 1.75, "Sn": 2.17}
def sphere(n):
    k = np.arange(n) + 0.5; phi = np.arccos(1 - 2 * k / n); th = np.pi * (1 + 5 ** 0.5) * k
    return np.c_[np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)]
def esp_charges(m):
    mol = gto.M(atom=list(zip(m["sym"], m["pos"])), basis={"Sn": "def2-tzvp", "default": "def2-svp"},
                ecp={"Sn": "def2-tzvp"}, charge=m["q"], verbose=0)
    mf = dft.RKS(mol, xc="b3lyp").density_fit(); mf.conv_tol = 1e-8; mf.kernel()
    R = m["pos"]; rad = np.array([VDW[s] for s in m["sym"]])
    pts = []
    for f in (1.4, 1.6, 1.8, 2.0):
        for A in range(len(R)):
            r = f * rad[A]; P = R[A] + r * sphere(max(16, int(4 * np.pi * r * r * 1.0)))
            d = np.linalg.norm(P[:, None] - R[None], axis=2)
            pts.append(P[np.all(d >= f * rad[None] - 1e-6, axis=1)])
    pts = np.vstack(pts)
    B = 1 / 0.52917721092
    Vr = mol.intor("int1e_grids", grids=pts * B)                  # (ngrid, nao, nao), bohr units
    V = np.einsum("gij,ij->g", Vr, mf.make_rdm1())
    Z = mol.atom_charges()                                         # effective nuclear charges (ECP-aware)
    rinv = 1 / (np.linalg.norm(pts[:, None] - R[None], axis=2) * B)
    Vref = rinv @ Z - V
    n = len(R); Amat = np.zeros((n + 1, n + 1)); Amat[:n, :n] = rinv.T @ rinv; Amat[:n, n] = Amat[n, :n] = 1
    b = np.r_[rinv.T @ Vref, m["q"]]
    q = np.linalg.solve(Amat, b)[:n]
    rrms = np.sqrt(np.mean((rinv @ q - Vref) ** 2)) / np.sqrt(np.mean(Vref ** 2))
    return q, rrms
lib.num_threads(int(os.environ.get("OMP_NUM_THREADS", "4")))
for m in mols:
    m["chg"], m["rrms"] = esp_charges(m)
    print(f"ESP charges {m['kind']:6s} sum={m['chg'].sum():+.3f}  fit RRMS={m['rrms']:.3f}  " +
          " ".join(f"{s}{c:+.2f}" for s, c in zip(m["sym"], m["chg"]) if s in ("Sn", "Cl", "N", "O"))[:160], flush=True)

# ---- block of 7x5x3 cells, translated copies of the reference molecules ----
block = []
for n1 in range(-3, 4):
    for n2 in range(-2, 3):
        for n3 in range(-1, 2):
            T = n1 * cell[0] + n2 * cell[1] + n3 * cell[2]
            for im, m in enumerate(mols):
                block.append({"ref": im, "T": (n1, n2, n3), "pos": m["pos"] + T, **{k: m[k] for k in ("sym", "kind", "q", "chg")}})

# ---- QM selection around the first SnCl6 of the reference cell ----
core = next(b for b in block if b["kind"] == "SnCl6" and b["T"] == (0, 0, 0))
cl = core["pos"][[k for k, s in enumerate(core["sym"]) if s == "Cl"]]
def hb(b):   # shortest H...Cl contact from molecule b to the core anion
    h = b["pos"][[k for k, s in enumerate(b["sym"]) if s == "H"]]
    return np.min(np.linalg.norm(h[:, None, :] - cl[None, :, :], axis=2))
cats = sorted([b for b in block if b["kind"] == "PhImH"], key=hb)[:2]
wats = sorted([b for b in block if b["kind"] == "H2O"], key=hb)[:2]
qm = [core] + cats + wats
qm_ids = {id(b) for b in qm}
mm = [b for b in block if id(b) not in qm_ids]
assert sum(b["q"] for b in qm) == 0 and abs(sum(b["chg"].sum() for b in mm)) < 1e-2

# ---- write ----
sym = sum((b["sym"] for b in qm), []); pos = np.vstack([b["pos"] for b in qm])
center = core["pos"][core["sym"].index("Sn")]
pos -= center
frag = sum(([f"{b['kind']}{'' if b['kind']=='SnCl6' else (k)}"] * len(b["sym"]) for k, b in enumerate(qm)), [])
write(f"{out}/qm_cluster.xyz", Atoms(sym, pos))
mpos = np.vstack([b["pos"] for b in mm]) - center; mchg = np.concatenate([b["chg"] for b in mm])
np.savetxt(f"{out}/mm_charges.txt", np.column_stack([mchg, mpos]), fmt="%10.5f", header="q  x  y  z (Angstrom, QM Sn at origin)")
# ORCA point-charge file (same charges) for the later SOC step
with open(f"{out}/mm_charges.pc", "w") as f:
    f.write(f"{len(mchg)}\n"); [f.write(f"{q:10.5f} {x:12.6f} {y:12.6f} {z:12.6f}\n") for q, (x, y, z) in zip(mchg, mpos)]
info = {"n_qm": len(sym), "n_mm": int(len(mchg)), "qm_charge": 0,
        "fragments": frag, "hb_contacts_A": {"cation1": hb(cats[0]), "cation2": hb(cats[1]), "water1": hb(wats[0]), "water2": hb(wats[1])},
        "mm_total_charge": float(mchg.sum()), "min_qm_mm_distance_A": float(np.min(np.linalg.norm(pos[:, None] - mpos[None], axis=2))),
        "esp_charges_reference": {m["kind"] + str(k): dict(zip(m["sym"], [round(x, 3) for x in m["chg"]])) for k, m in enumerate(mols) if k in (0, 2, 6)}}
json.dump(info, open(f"{out}/cluster_info.json", "w"), indent=1, default=float)
print(json.dumps({k: v for k, v in info.items() if k not in ("fragments", "esp_charges_reference")}, indent=1, default=float))
print("ESP charges on [SnCl6]2-:", np.round(mols[0]["chg"], 3))
