import os,pathlib,subprocess,json,time,re,shutil
w=pathlib.Path('/content/benzothiazole_qe_g01');dest=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_晶胞试算_20261030');base=(w/'scf_60_480_k222.in').read_text();exe='/content/qe_drive_restore/bin/pw.x';env=os.environ.copy();env['LD_LIBRARY_PATH']='/content/qe_drive_restore/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2'
cases=[('scf_80_640_k222',80,640,'2 2 2'),('scf_100_800_k222',100,800,'2 2 2'),('scf_80_640_k332',80,640,'3 3 2'),('scf_80_640_k443',80,640,'4 4 3')]
results=[]
for name,ecut,rho,k in cases:
 text=base.replace("prefix='crystal_g01'",f"prefix='{name}'").replace('ecutwfc=60, ecutrho=480',f'ecutwfc={ecut}, ecutrho={rho}').replace('2 2 2 0 0 0',k+' 0 0 0')
 inp=w/(name+'.in');out=w/(name+'.out');inp.write_text(text);shutil.copy2(inp,dest/inp.name)
 start=time.time();print('START',name,flush=True)
 with out.open('w') as f:
  proc=subprocess.Popen([exe,'-in',inp.name],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT)
  while proc.poll() is None:
   time.sleep(10);f.flush();shutil.copyfile(out,dest/(name+'.live.out'));print('MONITOR',name,round(time.time()-start,1),out.stat().st_size,flush=True)
 text=out.read_text(errors='replace');shutil.copy2(out,dest/out.name)
 forces=[]
 for m in re.finditer(r'atom\s+\d+\s+type\s+\d+\s+force\s*=\s*([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)',text):forces.append([float(v) for v in m.groups()])
 energy=re.findall(r'!\s+total energy\s+=\s+([-\d.]+)',text)
 row={'case':name,'ecutwfc_ry':ecut,'ecutrho_ry':rho,'kgrid':k,'elapsed_s':round(time.time()-start,2),'returncode':proc.returncode,'job_done':'JOB DONE.' in text,'converged':'convergence has been achieved' in text,'gpu_active':'GPU acceleration is ACTIVE' in text,'energy_ry':float(energy[-1]) if energy else None,'forces_ry_bohr':forces[-43:] if len(forces)>=43 else forces}
 results.append(row);(w/'convergence_progress.json').write_text(json.dumps(results,indent=2));shutil.copy2(w/'convergence_progress.json',dest/'convergence_progress.json');print('RESULT',json.dumps({k:v for k,v in row.items() if k!='forces_ry_bohr'}),flush=True)
 if not (row['returncode']==0 and row['job_done'] and row['converged'] and len(row['forces_ry_bohr'])==43):print('STOP_INVALID',name,flush=True);break
print('ALL_FINISHED',len(results),flush=True)