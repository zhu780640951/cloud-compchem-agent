import pathlib,os,shutil,subprocess,json,time,hashlib,re,threading
model={
  "cif_sha256": "ed23e88c8f84151de88f25c1ddd3b617e21a626e7ba6e403d5853217436c7a12",
  "cell_vectors_A": [
    [
      7.1819,
      0,
      0
    ],
    [
      -1.4357404475455238,
      8.25193008800255,
      0
    ],
    [
      -3.5177909308058126,
      -1.0641713838708606,
      9.71399414416597
    ]
  ],
  "atoms": [
    {
      "label": "Sn01",
      "element": "Sn",
      "frac": [
        0.5,
        0.0,
        0.0
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "Cl02",
      "element": "Cl",
      "frac": [
        0.4140600000000001,
        0.70608,
        0.99564
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "Cl02_inv",
      "element": "Cl",
      "frac": [
        0.5859399999999999,
        0.29391999999999996,
        0.0043600000000000305
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "Cl03",
      "element": "Cl",
      "frac": [
        0.4065700000000001,
        0.03699000000000008,
        0.2020200000000001
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "Cl03_inv",
      "element": "Cl",
      "frac": [
        0.5934299999999999,
        0.9630099999999999,
        0.7979799999999999
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "Cl04",
      "element": "Cl",
      "frac": [
        0.8426100000000001,
        0.99832,
        0.14998
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "Cl04_inv",
      "element": "Cl",
      "frac": [
        0.15738999999999992,
        0.0016800000000000148,
        0.85002
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "S005",
      "element": "S",
      "frac": [
        0.76367,
        0.22205,
        0.57389
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "S005_inv",
      "element": "S",
      "frac": [
        0.23633000000000004,
        0.77795,
        0.42611
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "N006",
      "element": "N",
      "frac": [
        0.8277,
        0.4753,
        0.7322
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "N006_inv",
      "element": "N",
      "frac": [
        0.1723,
        0.5246999999999999,
        0.26780000000000004
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "O007",
      "element": "O",
      "frac": [
        0.8862,
        0.6828,
        0.9535
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "O007_inv",
      "element": "O",
      "frac": [
        0.11380000000000001,
        0.31720000000000004,
        0.046499999999999986
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "H00F",
      "element": "H",
      "frac": [
        0.775769,
        0.67292,
        0.968425
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "H00F_inv",
      "element": "H",
      "frac": [
        0.22423099999999996,
        0.32708000000000004,
        0.03157500000000002
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "H00G",
      "element": "H",
      "frac": [
        0.928425,
        0.78234,
        0.947212
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "H00G_inv",
      "element": "H",
      "frac": [
        0.07157500000000006,
        0.21765999999999996,
        0.052787999999999946
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "C008",
      "element": "C",
      "frac": [
        0.7874,
        0.5317,
        0.6032
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "C008_inv",
      "element": "C",
      "frac": [
        0.2126,
        0.46830000000000005,
        0.39680000000000004
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "C009",
      "element": "C",
      "frac": [
        0.7505,
        0.4052,
        0.5024
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "C009_inv",
      "element": "C",
      "frac": [
        0.24950000000000006,
        0.5948,
        0.49760000000000004
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "C00A",
      "element": "C",
      "frac": [
        0.7083,
        0.4341,
        0.3654
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "C00A_inv",
      "element": "C",
      "frac": [
        0.29169999999999996,
        0.5659000000000001,
        0.6346
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "H00A",
      "element": "H",
      "frac": [
        0.684653,
        0.349692,
        0.297152
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "H00A_inv",
      "element": "H",
      "frac": [
        0.31534700000000004,
        0.650308,
        0.7028479999999999
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "C00B",
      "element": "C",
      "frac": [
        0.7813,
        0.6909,
        0.5713
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "C00B_inv",
      "element": "C",
      "frac": [
        0.2187,
        0.30910000000000004,
        0.42869999999999997
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "H00B",
      "element": "H",
      "frac": [
        0.805427,
        0.776064,
        0.639041
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "H00B_inv",
      "element": "H",
      "frac": [
        0.194573,
        0.22393600000000002,
        0.36095900000000003
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "C00C",
      "element": "C",
      "frac": [
        0.8203,
        0.3195,
        0.7305
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "C00C_inv",
      "element": "C",
      "frac": [
        0.17969999999999997,
        0.6805,
        0.26949999999999996
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "H00C",
      "element": "H",
      "frac": [
        0.844406,
        0.266323,
        0.80966
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "H00C_inv",
      "element": "H",
      "frac": [
        0.155594,
        0.733677,
        0.19033999999999995
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "C00D",
      "element": "C",
      "frac": [
        0.7028,
        0.5906,
        0.3345
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "C00D_inv",
      "element": "C",
      "frac": [
        0.2972,
        0.4094,
        0.6655
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "H00D",
      "element": "H",
      "frac": [
        0.674789,
        0.612825,
        0.243676
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "H00D_inv",
      "element": "H",
      "frac": [
        0.32521100000000003,
        0.38717500000000005,
        0.756324
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "C00E",
      "element": "C",
      "frac": [
        0.7382,
        0.7167,
        0.4358
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "C00E_inv",
      "element": "C",
      "frac": [
        0.26180000000000003,
        0.2833,
        0.5642
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "H00E",
      "element": "H",
      "frac": [
        0.732573,
        0.821637,
        0.41114
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "H00E_inv",
      "element": "H",
      "frac": [
        0.26742699999999997,
        0.17836300000000005,
        0.5888599999999999
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    },
    {
      "label": "H006",
      "element": "H",
      "frac": [
        0.852,
        0.549,
        0.805
      ],
      "occupancy": 1.0,
      "symmetry": "identity"
    },
    {
      "label": "H006_inv",
      "element": "H",
      "frac": [
        0.14800000000000002,
        0.45099999999999996,
        0.19499999999999995
      ],
      "occupancy": 1.0,
      "symmetry": "inversion"
    }
  ],
  "total_charge": 0,
  "atom_count": 43,
  "status": "preparation_only"
}
assert len(model['atoms'])==43 and model['total_charge']==0
work=pathlib.Path('/content/benzothiazole_qe_g01');work.mkdir(exist_ok=True)
drive=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_晶胞试算_20261030');drive.mkdir(parents=True,exist_ok=True)
cache=pathlib.Path('/content/drive/MyDrive/QE_build/qe-7.5-gpu-sm80')
local=pathlib.Path('/content/qe_drive_restore')
if not (local/'bin/pw.x').is_file(): raise FileNotFoundError('QE executable not restored')
print('QE_RESTORED',flush=True)
pseudodir=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/02_QE周期性DFT/pseudo')
patterns={'H':['H.pbe-rrkjus_psl.1.0.0.UPF'],'C':['C.pbe-n-kjpaw_psl.1.0.0.UPF'],'N':['N.pbe-n-kjpaw_psl.1.0.0.UPF'],'O':['O.pbe-n-kjpaw_psl.0.1.UPF'],'S':['s_pbe_v1.4.uspp.F.UPF'],'Cl':['cl_pbe_v1.4.uspp.F.UPF'],'Sn':['Sn_pbe_v1.uspp.F.UPF']}
pps={}
for e,choices in patterns.items():
 for name in choices:
  if (pseudodir/name).is_file() or (e=='N' and (pathlib.Path('/content/drive/MyDrive/QE_PhIm2SnCl6/pseudo')/name).is_file()): pps[e]=name;break
 if e not in pps: raise FileNotFoundError(e+' no predefined pseudopotential; available='+str([p.name for p in pseudodir.glob(e+'*')][:20]))
(work/'pseudo').mkdir(exist_ok=True)
metadata={}
for e,n in pps.items():
 source=pseudodir/n
 if not source.is_file() and e=='N': source=pathlib.Path('/content/drive/MyDrive/QE_PhIm2SnCl6/pseudo')/n
 shutil.copy2(source,work/'pseudo'/n)
 b=(work/'pseudo'/n).read_bytes();metadata[e]={'file':n,'sha256':hashlib.sha256(b).hexdigest()}
(work/'pseudo_metadata.json').write_text(json.dumps(metadata,indent=2))
masses={'H':1.008,'C':12.011,'N':14.007,'O':15.999,'S':32.06,'Cl':35.45,'Sn':118.71}
header="""&CONTROL
 calculation='scf', prefix='crystal_g01', pseudo_dir='./pseudo', outdir='./tmp', tprnfor=.true., verbosity='high',
/
&SYSTEM
 ibrav=0, nat=43, ntyp=7, ecutwfc=60, ecutrho=480, occupations='fixed', vdw_corr='dft-d3', dftd3_version=4,
/
&ELECTRONS
 conv_thr=1.0d-8, electron_maxstep=120, mixing_beta=0.3,
/
ATOMIC_SPECIES
"""
header+=''.join(f'{e} {masses[e]} {pps[e]}\n' for e in pps)
header+='CELL_PARAMETERS angstrom\n'+''.join(' '.join(f'{x:.10f}' for x in v)+'\n' for v in model['cell_vectors_A'])
header+='ATOMIC_POSITIONS crystal\n'+''.join(a['element']+' '+' '.join(f'{x:.10f}' for x in a['frac'])+'\n' for a in model['atoms'])
header+='K_POINTS automatic\n2 2 2 0 0 0\n'
(work/'scf_60_480_k222.in').write_text(header)
shutil.copy2(work/'scf_60_480_k222.in',drive/'scf_60_480_k222.in');shutil.copy2(work/'pseudo_metadata.json',drive/'pseudo_metadata.json')
env=os.environ.copy();env['LD_LIBRARY_PATH']=str(local/'lib')+':'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2'
(work/'tmp').mkdir(exist_ok=True)
start=time.time();out=work/'scf_60_480_k222.out'
with out.open('w') as f:
 proc=subprocess.Popen([str(local/'bin/pw.x'),'-in','scf_60_480_k222.in'],cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT)
 print('SCF_STARTED_PID',proc.pid,flush=True)
 while proc.poll() is None:
  time.sleep(10)
  f.flush();shutil.copyfile(out,drive/'scf_60_480_k222.live.out')
  print('MONITOR elapsed=',round(time.time()-start,1),'bytes=',out.stat().st_size,flush=True)
rc=proc.returncode;txt=out.read_text(errors='replace');shutil.copy2(out,drive/out.name)
result={'returncode':rc,'elapsed_seconds':round(time.time()-start,2),'job_done':'JOB DONE.' in txt,'gpu_active':'GPU acceleration is ACTIVE' in txt,'converged':'convergence has been achieved' in txt,'energies_ry':re.findall(r'!\s+total energy\s+=\s+([-\d.]+)',txt),'pseudopotentials':metadata,'purpose':'initial test only; not convergence test','cif_sha256':model['cif_sha256']}
(work/'scf_result.json').write_text(json.dumps(result,indent=2));shutil.copy2(work/'scf_result.json',drive/'scf_result.json')
if result['job_done']:
 shutil.make_archive(str(work/'crystal_g01_save'),'gztar',work/'tmp','crystal_g01.save');shutil.copy2(work/'crystal_g01_save.tar.gz',drive/'crystal_g01_save.tar.gz')
print('RESULT_JSON',json.dumps(result),flush=True)