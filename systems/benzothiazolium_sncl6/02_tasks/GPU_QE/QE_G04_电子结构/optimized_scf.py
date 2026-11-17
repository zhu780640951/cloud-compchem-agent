import pathlib,tarfile,shutil,os,subprocess,time,json,re
D=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算');outdir=D/'Codex_优化晶胞电子结构_20261031';outdir.mkdir(exist_ok=True)
w=pathlib.Path('/content/qe_optimized_electronic');w.mkdir(exist_ok=True);(w/'tmp').mkdir(exist_ok=True)
with tarfile.open(D/'Codex_晶胞试算_20261030'/'QE_G01_results.tar.gz') as tar:
 for m in tar.getmembers():
  if m.name=='pseudo' or m.name.startswith('pseudo/'):tar.extract(m,w,filter='data')
 base=tar.extractfile('scf_80_640_k332.in').read().decode()
coords=(D/'Codex_全原子优化_20261030'/'R_fixed_final_crystal.txt').read_text();assert len([x for x in coords.splitlines()[1:] if x.strip()])==43
pre,old=base.split('ATOMIC_POSITIONS crystal\n',1);_,post=old.split('K_POINTS automatic',1)
t=pre.replace("prefix='scf_80_640_k332'","prefix='optimized_scf'")+'ATOMIC_POSITIONS crystal\n'+'\n'.join(' '.join(x.split()[:4]) for x in coords.splitlines()[1:] if x.strip())+'\nK_POINTS automatic'+post
(w/'optimized_scf.in').write_text(t);shutil.copy2(w/'optimized_scf.in',outdir/'optimized_scf.in')
env=os.environ.copy();env['LD_LIBRARY_PATH']='/content/qe_drive_restore/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2'
f=w/'optimized_scf.out';start=time.time()
with f.open('w') as output:
 p=subprocess.Popen(['/content/qe_drive_restore/bin/pw.x','-in','optimized_scf.in'],cwd=w,env=env,stdout=output,stderr=subprocess.STDOUT);print('SCF_STARTED',p.pid,flush=True)
 while p.poll() is None:
  time.sleep(10);output.flush();shutil.copyfile(f,outdir/'optimized_scf.live.out');print('MONITOR',round(time.time()-start),f.stat().st_size,flush=True)
t=f.read_text(errors='replace');shutil.copy2(f,outdir/f.name);e=re.findall(r'!\s+total energy\s+=\s+([-\d.]+)',t)
r={'rc':p.returncode,'elapsed_s':round(time.time()-start,1),'converged':'convergence has been achieved' in t,'job_done':'JOB DONE.' in t,'gpu_active':'GPU acceleration is ACTIVE' in t,'energy_ry':float(e[-1]) if e else None}
(w/'optimized_scf_status.json').write_text(json.dumps(r,indent=2));shutil.copy2(w/'optimized_scf_status.json',outdir/'optimized_scf_status.json');print('RESULT',json.dumps(r),flush=True)
if not(r['rc']==0 and r['converged'] and r['job_done']):raise RuntimeError('SCF failed')
a=w/'optimized_scf_checkpoint.tar.gz'
with tarfile.open(a,'w:gz') as tar:tar.add(w/'tmp'/'optimized_scf.save',arcname='optimized_scf.save')
shutil.copy2(a,outdir/a.name);print('SCF_CHECKPOINT',a.stat().st_size,flush=True)