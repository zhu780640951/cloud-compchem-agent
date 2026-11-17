"""Task B: embedded-cluster TDDFT for (2-PhImH)2[SnCl6].2H2O
QM cluster (53 atoms) in ~11k ESP point charges; B3LYP / CAM-B3LYP / wB97X-D;
10 singlets (full TDDFT, oscillator strengths) + 10 triplets (TDA);
per state: NTOs + hole/electron fragment populations (Loewdin) -> IFCT-type CT decomposition; NTO cubes.
usage: run_tddft.py <cluster_dir> <out_dir> [--cpu] [--test]"""
import sys, os, json, time, warnings; warnings.filterwarnings("ignore")
import numpy as np
from pyscf import gto, lib, scf, dft, qmmm
from pyscf.tools import cubegen, molden

W, OUT = sys.argv[1], sys.argv[2]
CPU = "--cpu" in sys.argv; TEST = "--test" in sys.argv
os.makedirs(OUT, exist_ok=True)
lib.num_threads(int(os.environ.get("OMP_NUM_THREADS", "6")))
NST = 3 if TEST else 10
XCS = ["b3lyp"] if TEST else ["b3lyp", "camb3lyp", "wb97x-d"]
HA2EV = 27.211386245988
log = open(f"{OUT}/tddft_log.txt", "a")
def say(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.write(s + "\n"); log.flush()
def tonp(x):
    return x.get() if hasattr(x, "get") else np.asarray(x)

info = json.load(open(f"{W}/cluster_info.json"))
frag = np.array(info["fragments"])
basis = ({"default": "sto-3g"} if TEST else {"Sn": "def2-tzvp", "default": "def2-svp"})
mol = gto.M(atom=f"{W}/qm_cluster.xyz", basis=basis, ecp=({} if TEST else {"Sn": "def2-tzvp"}), charge=0, spin=0,
            verbose=3, max_memory=60000, output=f"{OUT}/pyscf_mol.log")
say(f"QM atoms {mol.natm}, electrons {mol.nelectron}, AO {mol.nao}, GPU={'no' if CPU else 'yes'}")
mm = np.loadtxt(f"{W}/mm_charges.txt")
if TEST: mm = mm[np.linalg.norm(mm[:, 1:], axis=1) < 9]
t0 = time.time()
h1e = qmmm.mm_charge(scf.RHF(mol), mm[:, 1:], mm[:, 0]).get_hcore()     # embedding enters via the 1-e Hamiltonian
say(f"point charges {len(mm)}, embedded hcore built in {time.time()-t0:.0f} s")

# AO -> fragment map, Loewdin S^1/2
S = mol.intor("int1e_ovlp")
w_, v_ = np.linalg.eigh(S); S12 = (v_ * np.sqrt(w_)) @ v_.T
ao_frag = np.empty(mol.nao, dtype=object)
for A, (_, _, p0, p1) in enumerate(mol.aoslice_by_atom()): ao_frag[p0:p1] = frag[A]
groups = {"SnCl6": ["SnCl6"], "cation": [f for f in set(frag) if f.startswith("PhImH")], "water": [f for f in set(frag) if f.startswith("H2O")]}
frags = sorted(set(frag))
def frag_pop(D):
    p = np.einsum("ij,ji->i", S12 @ D, S12); p = p / p.sum()
    return {f: float(p[ao_frag == f].sum()) for f in frags}
def grp(pop): return {g: sum(pop[f] for f in fs) for g, fs in groups.items()}

def build_mf(xc):
    if CPU:
        mf = dft.RKS(mol, xc=xc).density_fit(); mf.get_hcore = lambda *a, **k: h1e
    else:
        import cupy
        from gpu4pyscf import dft as gdft
        mf = gdft.RKS(mol, xc=xc).density_fit(); hg = cupy.asarray(h1e); mf.get_hcore = lambda *a, **k: hg
    mf.grids.level = 3; mf.conv_tol = 1e-9; mf.max_cycle = 200
    return mf

def osc(mf, td, xy_list, e):
    try:
        return tonp(td.oscillator_strength())
    except Exception:
        C = tonp(mf.mo_coeff); nocc = mol.nelectron // 2
        with mol.with_common_orig((0, 0, 0)): dip = mol.intor("int1e_r")
        dmo = np.einsum("xpq,pi,qa->xia", dip, C[:, :nocc], C[:, nocc:])
        f = []
        for (X, Y), ei in zip(xy_list, e):
            X, Y = tonp(X), (tonp(Y) if not np.isscalar(Y) else 0 * tonp(X))
            n = (X * X).sum() - (Y * Y).sum(); s = np.sqrt(0.5 / n)
            t = 2 * np.einsum("xia,ia->x", dmo, (X + Y) * s)
            f.append(2 / 3 * ei * (t @ t))
        return np.array(f)

rows, summary = [], {}
for xc in XCS:
    t0 = time.time()
    mf = build_mf(xc); E = mf.kernel()
    assert mf.converged, f"SCF not converged for {xc}"
    C = tonp(mf.mo_coeff); eps = tonp(mf.mo_energy); nocc = mol.nelectron // 2
    homo, lumo = C[:, nocc - 1], C[:, nocc]
    ph, pl = grp(frag_pop(np.outer(homo, homo))), grp(frag_pop(np.outer(lumo, lumo)))
    say(f"\n== {xc}: E_SCF = {E:.6f} Ha ({time.time()-t0:.0f} s); HOMO {eps[nocc-1]*HA2EV:.2f} eV "
        f"[{', '.join(f'{k} {100*v:.0f}%' for k, v in ph.items())}], LUMO {eps[nocc]*HA2EV:.2f} eV "
        f"[{', '.join(f'{k} {100*v:.0f}%' for k, v in pl.items())}]")
    if xc == "b3lyp": molden.from_scf(mf.to_cpu() if hasattr(mf, "to_cpu") else mf, f"{OUT}/scf_b3lyp.molden")
    summary[xc] = {"E_scf_Ha": float(E), "HOMO_eV": float(eps[nocc-1]*HA2EV), "LUMO_eV": float(eps[nocc]*HA2EV), "HOMO_frag": ph, "LUMO_frag": pl}

    for mult in ("S", "T"):
        t1 = time.time()
        try:
            td = mf.TDDFT() if mult == "S" else mf.TDA()
            if mult == "T": td.singlet = False
            td.nstates = NST; td.kernel()
            backend = "gpu" if not CPU else "cpu"
        except Exception as err:                       # fall back to CPU PySCF for anything gpu4pyscf lacks
            say(f"  {mult} on GPU failed ({type(err).__name__}: {str(err)[:80]}), using CPU")
            mfc = mf.to_cpu(); mfc.get_hcore = lambda *a, **k: h1e
            td = mfc.TDDFT() if mult == "S" else mfc.TDA()
            if mult == "T": td.singlet = False
            td.nstates = NST; td.kernel(); backend = "cpu"
        e = tonp(td.e); xy = td.xy
        f = osc(mf, td, xy, e) if mult == "S" else np.zeros(len(e))
        say(f"  {mult}: {len(e)} states in {time.time()-t1:.0f} s ({backend})")
        for k, (ek, fk, (X, Y)) in enumerate(zip(e, f, xy)):
            X = tonp(X); X = X / np.linalg.norm(X)
            U, s, Vt = np.linalg.svd(X, full_matrices=False); wts = s ** 2 / (s ** 2).sum()
            Dh = C[:, :nocc] @ X @ X.T @ C[:, :nocc].T
            De = C[:, nocc:] @ X.T @ X @ C[:, nocc:].T
            h, el = frag_pop(Dh), frag_pop(De)
            hg, eg = grp(h), grp(el)
            cats = groups["cation"]
            row = {"xc": xc, "mult": mult, "state": k + 1, "E_eV": ek * HA2EV, "nm": 1239.84193 / (ek * HA2EV), "f": float(fk),
                   "NTO1_weight": float(wts[0]),
                   **{f"hole_{g}": v for g, v in hg.items()}, **{f"elec_{g}": v for g, v in eg.items()},
                   "LE_SnCl6": h["SnCl6"] * el["SnCl6"], "LE_cation": sum(h[c] * el[c] for c in cats),
                   "CT_SnCl6_to_cation": h["SnCl6"] * sum(el[c] for c in cats),
                   "CT_cation_to_SnCl6": sum(h[c] for c in cats) * el["SnCl6"],
                   "CT_cation_to_cation": sum(h[a] * el[b] for a in cats for b in cats if a != b)}
            row["CT_total"] = 1 - sum(h[a] * el[a] for a in frags)
            rows.append(row)
            say(f"  {mult}{k+1:<2d} {row['E_eV']:5.2f} eV {row['nm']:5.0f} nm f={row['f']:.4f} NTO1 {wts[0]:.2f} | "
                f"hole SnCl6 {100*hg['SnCl6']:3.0f}% cat {100*hg['cation']:3.0f}% | elec SnCl6 {100*eg['SnCl6']:3.0f}% cat {100*eg['cation']:3.0f}% | "
                f"CT(SnCl6->cat) {100*row['CT_SnCl6_to_cation']:3.0f}% LE(cat) {100*row['LE_cation']:3.0f}% LE(SnCl6) {100*row['LE_SnCl6']:3.0f}%")
            # NTO cubes for S1, the brightest singlet and T1
            want = (mult == "T" and k == 0) or (mult == "S" and (k == 0 or k == int(np.argmax(f))))
            if want and xc in ("b3lyp", "wb97x-d") and not TEST:
                hole = C[:, :nocc] @ U[:, 0]; elec = C[:, nocc:] @ Vt[0]
                tag = f"{xc}_{mult}{k+1}"
                cubegen.orbital(mol, f"{OUT}/nto_{tag}_hole.cube", hole, nx=70, ny=70, nz=70, margin=3.0)
                cubegen.orbital(mol, f"{OUT}/nto_{tag}_electron.cube", elec, nx=70, ny=70, nz=70, margin=3.0)
    say(f"== {xc} done in {time.time()-t0:.0f} s")

import csv
with open(f"{OUT}/excitations.csv", "w", newline="") as fh:
    wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
json.dump(summary, open(f"{OUT}/scf_summary.json", "w"), indent=1)

# absorption spectra (Gaussian broadening, FWHM 0.3 eV)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(6, 3.6)); Eg = np.linspace(2.0, 6.0, 800)
for xc in XCS:
    rs = [r for r in rows if r["xc"] == xc and r["mult"] == "S"]
    sig = 0.3 / 2.3548
    spec = sum(r["f"] * np.exp(-(Eg - r["E_eV"]) ** 2 / (2 * sig ** 2)) for r in rs)
    ax.plot(1239.84193 / Eg, spec, label=xc)
    t1 = min(r["E_eV"] for r in rows if r["xc"] == xc and r["mult"] == "T")
    ax.axvline(1239.84193 / t1, ls=":", lw=0.8, c=ax.lines[-1].get_color())
ax.set_xlabel("wavelength (nm)"); ax.set_ylabel("oscillator strength (arb.)"); ax.set_xlim(220, 520)
ax.legend(title="dotted: T1", fontsize=8); fig.tight_layout(); fig.savefig(f"{OUT}/absorption_tddft.png", dpi=200)
say("TASK B FINISHED")
