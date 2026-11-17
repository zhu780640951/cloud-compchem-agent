import pathlib,tarfile,json,re,hashlib
p=pathlib.Path(r'E:\桌面\(C₇H₆NS)₂[SnCl₆]·2H₂O计算\02_计算任务\GPU_QE\QE_G04_电子结构'); d=p/'优化结构收敛复核';a=d/'qe_optimized_convergence_results.tar.gz'
with tarfile.open(p/'electronic_stage2_results.tar.gz') as t:baseline=t.extractfile('optimized_scf.out').read().decode(errors='replace')
with tarfile.open(a) as t:rows=json.load(t.extractfile('progress.json'))
energy=float(re.findall(r'!\s+total energy\s+=\s+([-\d.]+)',baseline)[-1]);m=re.search(r'Forces acting on atoms\s*\(cartesian axes, Ry/au\):(.+?)(?:Total force|The non-local)',baseline,re.S);f=re.findall(r'atom\s+\d+\s+type\s+\d+\s+force\s*=\s*([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)',m.group(1));assert len(f)==43
f=[[float(x) for x in v] for v in f];out=[]
for r in rows:
 assert len(r['forces_ry_bohr'])==43 and all(r[k] for k in ('job_done','converged','gpu_active'))
 diff=max(abs(r['forces_ry_bohr'][i][j]-f[i][j]) for i in range(43) for j in range(3))*25.7110430954
 out.append({'case':r['case'],'energy_difference_meV_per_atom':(r['energy_ry']-energy)*13605.693122994/43,'max_force_component_difference_eV_per_A':diff,'elapsed_s':r['elapsed_s']})
result={'baseline':'optimized_scf 80/640 Ry 3x3x2','baseline_energy_Ry':energy,'tests':out,'thresholds':{'energy_meV_per_atom':1,'force_component_eV_per_A':0.005},'interpretation':'Energy and force checks on optimized fixed-cell structure; does not prove band-gap, unoccupied-band, functional, or SOC convergence.','archive_sha256':hashlib.sha256(a.read_bytes()).hexdigest()}
(d/'优化结构收敛分析.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False,indent=2))
