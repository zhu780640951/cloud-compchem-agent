"""Write QE inputs for the HSE06 band-gap correction on the step-1 (PBE+D3) relaxed structure.
SG15 ONCV norm-conserving pseudopotentials (hybrid functionals are most mature with NC PPs in QE).
pbe_sg15.in : PBE SCF, same PPs/cutoffs/k-mesh  -> reference gap
hse.in      : HSE06 SCF (ACE), nq = 1x1x1
usage: make_hse.py <relax.out> <outdir> <pseudo-map.json> <ecutfock> <k1 k2 k3>"""
import sys, os, json, warnings; warnings.filterwarnings("ignore")
from ase.io import read
src, out, ppmap, ecutfock = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3])), sys.argv[4]
k = sys.argv[5:8]
a = read(src, index=-1, format="espresso-out") if src.endswith(".out") else read(src, format="espresso-in")
order = ["Sn", "Cl", "O", "N", "C", "H"]
mass = {"Sn": 118.710, "Cl": 35.453, "O": 15.999, "N": 14.007, "C": 12.011, "H": 1.008}
sym = a.get_chemical_symbols(); idx = sorted(range(len(a)), key=lambda i: order.index(sym[i]))
frac = a.get_scaled_positions(wrap=True)
NBND = 190            # 182 occupied (364 valence e with SG15: Sn 14, Cl 7, O 6, N 5, C 4, H 1) + 8 empty
def write(name, prefix, hybrid):
    sys_extra = (f"\n  input_dft = 'hse'\n  nqx1 = 1, nqx2 = 1, nqx3 = 1\n  ecutfock = {ecutfock}\n"
                 "  exxdiv_treatment = 'gygi-baldereschi', x_gamma_extrapolation = .true.") if hybrid else ""
    L = [f"""&CONTROL
  calculation = 'scf'
  prefix      = '{prefix}'
  outdir      = './tmp'
  pseudo_dir  = './pseudo_sg15'
  verbosity   = 'high'
  max_seconds = 39000
/
&SYSTEM
  ibrav = 0, nat = {len(a)}, ntyp = 6
  ecutwfc = 70, ecutrho = 280
  nbnd = {NBND}
  occupations = 'fixed'{sys_extra}
/
&ELECTRONS
  conv_thr = 1.0d-8
  mixing_beta = 0.4
  electron_maxstep = 200
/
ATOMIC_SPECIES"""]
    L += [f"  {s:2s} {mass[s]:9.3f}  {ppmap[s]}" for s in order]
    L.append("CELL_PARAMETERS angstrom")
    L += ["  " + "  ".join(f"{x:14.8f}" for x in v) for v in a.cell.array]
    L.append("ATOMIC_POSITIONS crystal")
    L += [f"  {sym[i]:2s} " + "  ".join(f"{x:13.8f}" for x in frac[i]) for i in idx]
    L.append(f"K_POINTS automatic\n  {k[0]} {k[1]} {k[2]}  0 0 0")
    open(os.path.join(out, name), "w").write("\n".join(L) + "\n")
write("pbe_sg15.in", "pbe_sg15", False)
write("hse.in", "hse", True)
print("wrote pbe_sg15.in, hse.in  ecutfock", ecutfock, "k", k)
