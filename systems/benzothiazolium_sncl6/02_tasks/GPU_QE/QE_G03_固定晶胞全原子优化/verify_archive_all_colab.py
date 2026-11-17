import pathlib,re,json,tarfile,shutil
w=pathlib.Path('/content/benzothiazole_qe_g03_all_relax');d=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_全原子优化_20261030');t=(w/'all_relax_resume.out').read_text(errors='replace');inp=(w/'all_relax.in').read_text()
blocks=re.findall(r'ATOMIC_POSITIONS\s*\(?crystal\)?\s*\n((?:\s*[A-Za-z]+\s+[-+\d.Ee]+\s+[-+\d.Ee]+\s+[-+\d.Ee]+[^\n]*\n){43})',t);assert blocks
coords=[l.split()[:4] for l in blocks[-1].strip().splitlines()];assert len(coords)==43
fblocks=re.findall(r'Forces acting on atoms \(cartesian axes, Ry/au\):\s*\n(.*?)(?=\n\s*Total force\s*=)',t,re.S);assert fblocks
f=[[float(v) for v in x] for x in re.findall(r'atom\s+\d+\s+type\s+\d+\s+force\s*=\s*([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)',fblocks[-1])[:43]];assert len(f)==43
maxf=max(abs(x) for a in f for x in a);e=re.findall(r'!\s+total energy\s+=\s+([-\d.]+)',t)
lines=[l.strip() for l in t.splitlines() if any(z in l.lower() for z in ['bfgs converged','total force =','gradient error','end of bfgs','maximum cpu time exceeded'])]
verify={'bfgs_converged':bool(re.search(r'bfgs converged',t,re.I)),'n_atoms':len(coords),'max_force_component_ry_bohr':maxf,'max_force_component_eV_A':maxf*25.711043,'force_target_eV_A':0.02,'energy_ry_last_scf':float(e[-1]) if e else None,'last_optimization_lines':lines[-7:],'fixed_cell':True,'notes':'Fixed input experimental cell; plane-wave PBE-D3, no SOC. Total forces extracted first force section; validate geometry before electronic structure.'}
(w/'R_fixed_final_crystal.txt').write_text('ATOMIC_POSITIONS crystal\n'+'\n'.join(' '.join(x) for x in coords)+'\n');(w/'verification.json').write_text(json.dumps(verify,indent=2));shutil.copy2(w/'R_fixed_final_crystal.txt',d/'R_fixed_final_crystal.txt');shutil.copy2(w/'verification.json',d/'verification.json')
archive=w/'all_relax_results.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for n in ['all_relax.in','all_relax.out','status.json','all_relax_resume.in','all_relax_resume.out','resume_status.json','R_fixed_final_crystal.txt','verification.json']:
  tar.add(w/n,arcname=n)
shutil.copy2(archive,d/archive.name);print('VERIFY_JSON',json.dumps(verify,indent=2));print('ARCHIVE',archive,archive.stat().st_size)