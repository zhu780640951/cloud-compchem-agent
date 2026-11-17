"""Write one ORCA input for the wave-2 embedded-cluster jobs.
usage: make_orca.py <job> <xc-key> <xyz> <nprocs> <maxcore_MB> > job.inp
job   : soc (ZORA SOC-TDDFT, S0 reference) | opt_S0 | opt_T1 | sp_S0 | sp_T1
xc-key: cam  -> CAM-B3LYP (D3BJ for opt/sp)      wb97x -> wB97X-D3
Point charges: mm.pc (ORCA format, Angstrom), the same 11,077 ESP charges used in wave 1."""
import sys
job, xc, xyz, npr, mc = sys.argv[1:6]
serial = int(npr) <= 1
XC = {"cam": ("CAM-B3LYP D3BJ", "CAM-B3LYP"), "wb97x": ("wB97X-D3", "wB97X-D3")}[xc]
pal = "" if serial else f"%pal nprocs {npr} end\n"
common = f'{pal}%maxcore {mc}\n%pointcharges "mm.pc"\n%scf MaxIter 300 end\n'
if job == "soc":
    head = f"! {XC[1]} ZORA ZORA-def2-SVP SARC/J RIJCOSX TightSCF\n"
    basis = '%basis\n  NewGTO Sn "SARC-ZORA-TZVP" end\nend\n'
    td = "%tddft\n  NRoots 10\n  TDA true\n  DoSOC true\n  PrintLevel 3\nend\n"
    mult, ks = 1, ""
    body = head + basis + td + common
else:
    opt = " Opt" if job.startswith("opt") else ""
    mult = 3 if job.endswith("T1") else 1
    ks = "UKS " if mult == 3 else ""
    head = f"! {ks}{XC[0]} def2-SVP def2/J RIJCOSX TightSCF{opt}\n"
    basis = '%basis\n  NewGTO Sn "def2-TZVP" end\n  NewECP Sn "def2-ECP" end\nend\n'
    geom = "%geom MaxIter 200 end\n" if opt else ""
    body = head + basis + geom + common
print(body + f"* xyzfile 0 {mult} {xyz}\n", end="")
