import os,pathlib,subprocess,json,time,re,shutil,tarfile
D=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算')
dest=D/'Codex_优化结构收敛复核_20261031';dest.mkdir(exist_ok=True)
w=pathlib.Path('/content/qe_optimized_convergence');w.mkdir(exist_ok=True);(w/'tmp').mkdir(exist_ok=True)
with tarfile.open(D/'Codex_晶胞试算_20261030'/'QE_G01_results.tar.gz') as t:
 for m in t.getmembers():
  if m.name=='pseudo' or m.name.startswith('pseudo/'):t.extract(m,w,filter='data')
 base=t.extractfile('scf_80_640_k332.in').read().decode()
coords=(D/'Codex_全原子优化_20261030'/'R_fixed_final_crystal.txt').read_text()
xyz=[' '.join(x.split()[:4]) for x in coords.splitlines()[1:] if x.strip()];assert len(xyz)==43
pre,old=base.split('ATOMIC_POSITIONS crystal\n',1);_,post=old.split('K_POINTS automatic',1)
base=pre+'ATOMIC_POSITIONS crystal\n'+'\n'.join(xyz)+'\nK_POINTS automatic'+post
env=os.environ.copy();env['LD_LIBRARY_PATH']='/content/qe_drive_restore/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2'
cases=[('opt_80_640_k443',80,640,'4 4 3'),('opt_100_800_k332',100,800,'3 3 2')]
results=[]
for name,cut,rho,k in cases:
 inp=base.replace("prefix='scf_80_640_k332'",f"prefix='{name}'").replace('ecutwfc=80, ecutrho=640',f'ecutwfc={cut}, ecutrho={rho}').replace('3 3 2 0 0 0',k+' 0 0 0')
 assert f'prefix=\'{name}\'' in inp and f'ecutwfc={cut}, ecutrho={rho}' in inp and k+' 0 0 0' in inp
 (w/(name+'.in')).write_text(inp);shutil.copy2(w/(name+'.in'),dest/(name+'.in'))
 start=time.time();out=w/(name+'.out');print('START',name,flush=True)
 with out.open('w') as f:
  p=subprocess.Popen(['/content/qe_drive_restore/bin/pw.x','-in',name+'.in'],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT)
  while p.poll() is None:
   time.sleep(10);f.flush();shutil.copyfile(out,dest/(name+'.live.out'));print('RUNNING',name,round(time.time()-start),flush=True)
 text=out.read_text(errors='replace');shutil.copy2(out,dest/out.name)
 energy=re.findall(r'!\s+total energy\s+=\s+([-\d.]+)',text)
 match=re.search(r'Forces acting on atoms\s*\(cartesian axes, Ry/au\):(.+?)(?:Total force|The non-local)',text,re.S)
 forces=re.findall(r'atom\s+\d+\s+type\s+\d+\s+force\s*=\s*([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)',match.group(1)) if match else []
 row={'case':name,'ecutwfc_ry':cut,'ecutrho_ry':rho,'kgrid':k,'elapsed_s':round(time.time()-start,2),'returncode':p.returncode,'job_done':'JOB DONE.' in text,'converged':'convergence has been achieved' in text,'gpu_active':'GPU acceleration is ACTIVE' in text,'energy_ry':float(energy[-1]) if energy else None,'forces_ry_bohr':[[float(a) for a in force] for force in forces]}
 results.append(row);(dest/'progress.json').write_text(json.dumps(results,indent=2));print('RESULT',json.dumps({k:v for k,v in row.items() if k!='forces_ry_bohr'}),flush=True)
 if not(row['returncode']==0 and row['job_done'] and row['converged'] and row['gpu_active'] and len(forces)==43):raise RuntimeError('Calculation did not pass validation; see logs')
print('FINISHED',len(results),flush=True)
