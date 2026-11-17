import pathlib,os,subprocess,time,shutil,json,re
h=pathlib.Path('/content/benzothiazole_qe_g02_h_relax');w=pathlib.Path('/content/benzothiazole_qe_g03_all_relax');w.mkdir(exist_ok=True)
d=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_全原子优化_20261030');d.mkdir(parents=True,exist_ok=True)
v=json.loads((h/'verification.json').read_text());assert v['bfgs_converged'] and v['max_h_force_component_eV_A']<0.02 and v['heavy_max_fractional_change']<1e-8
shutil.copytree(h/'pseudo',w/'pseudo',dirs_exist_ok=True);(w/'tmp').mkdir(exist_ok=True)
t=(h/'h_relax.in').read_text().replace("prefix='crystal_hrelax'","prefix='crystal_allrelax'")
pre,pos=t.split('ATOMIC_POSITIONS crystal\n',1);_,post=pos.split('K_POINTS automatic',1)
coords=(h/'R_H_final_crystal.txt').read_text().splitlines()[1:];clean=[' '.join(x.split()[:4]) for x in coords if x.strip()]
assert len(clean)==43
t=pre+'ATOMIC_POSITIONS crystal\n'+'\n'.join(clean)+'\nK_POINTS automatic'+post
(w/'all_relax.in').write_text(t);shutil.copy2(w/'all_relax.in',d/'all_relax.in')
env=os.environ.copy();env['LD_LIBRARY_PATH']='/content/qe_drive_restore/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2'
out=w/'all_relax.out';start=time.time()
with out.open('w') as f:
 p=subprocess.Popen(['/content/qe_drive_restore/bin/pw.x','-in','all_relax.in'],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT);print('ALL_RELAX_STARTED',p.pid,flush=True)
 while p.poll() is None:
  time.sleep(15);f.flush();shutil.copyfile(out,d/'all_relax.live.out');txt=out.read_text(errors='replace');print('ALL_RELAX_MONITOR',round(time.time()-start,1),'scf',txt.count('convergence has been achieved'),'bytes',len(txt),flush=True)
txt=out.read_text(errors='replace');shutil.copy2(out,d/out.name)
status={'exit_code':p.returncode,'elapsed_s':round(time.time()-start,2),'job_done':'JOB DONE.' in txt,'bfgs_converged':bool(re.search(r'bfgs converged',txt,re.I)),'gpu_active':'GPU acceleration is ACTIVE' in txt,'max_time_exceeded':'Maximum CPU time exceeded' in txt,'scf_convergences':txt.count('convergence has been achieved')}
(w/'status.json').write_text(json.dumps(status,indent=2));shutil.copy2(w/'status.json',d/'status.json')
print('ALL_RELAX_RESULT',json.dumps(status),flush=True)