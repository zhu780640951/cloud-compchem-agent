"""Write QE inputs for step 2 (SCF with empty bands, band-decomposed densities, NSCF DOS, PDOS, band path)
from the final geometry of the step-1 relaxation.  usage: make_qe_step2.py relax.out outdir"""
import sys, os, warnings; warnings.filterwarnings("ignore")
from ase.io import read
src, out = sys.argv[1], sys.argv[2]
a = read(src, index=-1, format="espresso-out") if src.endswith(".out") else read(src, format="espresso-in")
order = ["Sn", "Cl", "O", "N", "C", "H"]
pp = {"Sn": ("118.710", "Sn.pbe-dn-kjpaw_psl.1.0.0.UPF"), "Cl": ("35.453", "Cl.pbe-n-kjpaw_psl.1.0.0.UPF"),
      "O": ("15.999", "O.pbe-n-kjpaw_psl.1.0.0.UPF"), "N": ("14.007", "N.pbe-n-kjpaw_psl.1.0.0.UPF"),
      "C": ("12.011", "C.pbe-n-kjpaw_psl.1.0.0.UPF"), "H": ("1.008", "H.pbe-kjpaw_psl.1.0.0.UPF")}
sym = a.get_chemical_symbols()
idx = sorted(range(len(a)), key=lambda i: order.index(sym[i]))
frac = a.get_scaled_positions(wrap=True)
NOCC = 182          # 364 valence electrons / 2
NBND = 210          # 28 empty bands for the conduction band and PDOS

def write(name, calc, kblock, extra_sys="", extra_ctrl=""):
    L = [f"""&CONTROL
  calculation = '{calc}'
  prefix      = 'phim_sncl6'
  outdir      = './tmp'
  pseudo_dir  = './pseudo'
  verbosity   = 'high'{extra_ctrl}
/
&SYSTEM
  ibrav = 0, nat = {len(a)}, ntyp = 6
  ecutwfc = 60, ecutrho = 480
  nbnd = {NBND}
  vdw_corr = 'dft-d3', dftd3_version = 4, dftd3_threebody = .false.{extra_sys}
/
&ELECTRONS
  conv_thr = 1.0d-9
  mixing_beta = 0.4
  diago_full_acc = .true.
/
ATOMIC_SPECIES"""]
    L += [f"  {s:2s} {pp[s][0]:>8s}  {pp[s][1]}" for s in order]
    L.append("CELL_PARAMETERS angstrom")
    L += ["  " + "  ".join(f"{x:14.8f}" for x in v) for v in a.cell.array]
    L.append("ATOMIC_POSITIONS crystal")
    L += [f"  {sym[i]:2s} " + "  ".join(f"{x:13.8f}" for x in frac[i]) for i in idx]
    L.append(kblock)
    open(os.path.join(out, name), "w").write("\n".join(L) + "\n")

# 1) SCF with empty bands (fixed occupations, insulator) on the relax k mesh
write("scf.in", "scf", "K_POINTS automatic\n  3 2 2  0 0 0", extra_sys="\n  occupations = 'fixed'")
# 2) NSCF on a denser mesh for DOS/PDOS
write("nscf.in", "nscf", "K_POINTS automatic\n  4 3 2  0 0 0", extra_sys="\n  occupations = 'tetrahedra_opt'")
# 3) band structure along a simple triclinic path G-X | G-Y | G-Z (reciprocal-crystal coordinates)
path = """K_POINTS crystal_b
 7
  0.0 0.0 0.0 12 ! G
  0.5 0.0 0.0 12 ! X
  0.0 0.0 0.0 12 ! G
  0.0 0.5 0.0 12 ! Y
  0.0 0.0 0.0 12 ! G
  0.0 0.0 0.5 12 ! Z
  0.5 0.5 0.5 1  ! R"""
write("bands.in", "bands", path, extra_sys="\n  occupations = 'fixed'")

common = "  prefix = 'phim_sncl6', outdir = './tmp'"
# band-decomposed |psi|^2 at Gamma (k-point 1 of the SCF list) for VBM and CBM, written as Gaussian cube
for tag, band in (("vbm", NOCC), ("cbm", NOCC + 1)):
    open(os.path.join(out, f"pp_{tag}.in"), "w").write(f"""&INPUTPP
{common}
  filplot = 'psi2_{tag}.dat'
  plot_num = 7
  kpoint(1) = 1
  kband(1) = {band}
  lsign = .false.
/
&PLOT
  iflag = 3
  output_format = 6
  fileout = '{tag}_band{band}_Gamma.cube'
/
""")
open(os.path.join(out, "projwfc.in"), "w").write(f"""&PROJWFC
{common}
  filpdos = 'phim'
  ngauss = 0, degauss = 0.005
  DeltaE = 0.01
/
""")
open(os.path.join(out, "bandsx.in"), "w").write(f"""&BANDS
{common}
  filband = 'bands.dat'
  lsym = .false.
/
""")
print("wrote step-2 inputs for", len(a), "atoms from", src)
