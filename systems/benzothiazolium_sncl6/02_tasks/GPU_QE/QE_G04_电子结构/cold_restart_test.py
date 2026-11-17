import pathlib,os,shutil,subprocess,tarfile,json,time,hashlib,re
D=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算');source=D/'Codex_全原子优化_20261030';dest=D/'Codex_冷启动续算验证_20261031';dest.mkdir(exist_ok=True)
w=pathlib.Path('/content/qe_cold_restart_test');w.mkdir(exist_ok=True);qe=pathlib.Path('/content/qe_drive_restore');cache=pathlib.Path('/content/drive/MyDrive/QE_build/qe-7.5-gpu-sm80')
for sub in ['bin','lib']:
 (qe/sub).mkdir(parents=True,exist_ok=True)
 for p in (cache/sub).iterdir():
  if p.is_file():
   target=qe/sub/p.name
   if not target.exists() or target.stat().st_size!=p.stat().st_size:shutil.copyfile(p,target)
   if sub=='bin':target.chmod(0o755)
print('QE_RESTORED',flush=True)
with tarfile.open(source/'full_tmp_after_segment1.tar') as tar:tar.extractall(w,filter='data')
with tarfile.open(D/'Codex_晶胞试算_20261030'/'QE_G01_results.tar.gz') as tar:
 for m in tar.getmembers():
  if m.name=='pseudo' or m.name.startswith('pseudo/'):tar.extract(m,w,filter='data')
text=(source/'all_relax.in').read_text().replace("calculation='relax',", "calculation='relax', restart_mode='restart',").replace('max_seconds=720','max_seconds=180')
(w/'cold_restart.in').write_text(text);shutil.copy2(w/'cold_restart.in',dest/'cold_restart.in')
env=os.environ.copy();env['LD_LIBRARY_PATH']=str(qe/'lib')+':'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2'
start=time.time();out=w/'cold_restart.out'
with out.open('w') as f:
 p=subprocess.Popen([str(qe/'bin/pw.x'),'-in','cold_restart.in'],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT);print('COLD_RESTART_STARTED',p.pid,flush=True)
 while p.poll() is None:
  time.sleep(15);f.flush();shutil.copyfile(out,dest/'cold_restart.live.out');print('MONITOR',round(time.time()-start),'bytes',out.stat().st_size,flush=True)
t=out.read_text(errors='replace');shutil.copy2(out,dest/out.name)
status={'rc':p.returncode,'elapsed_s':round(time.time()-start,1),'job_done':'JOB DONE.' in t,'max_time_exceeded':'Maximum CPU time exceeded' in t,'bfgs_converged':bool(re.search('bfgs converged',t,re.I)),'scf_count':t.count('convergence has been achieved'),'gpu_active':'GPU acceleration is ACTIVE' in t,'scope':'cross-runtime restart from preexisting intermediate checkpoint'}
(w/'status.json').write_text(json.dumps(status,indent=2));shutil.copy2(w/'status.json',dest/'status.json');print('RESULT',json.dumps(status),flush=True)
if not(status['rc']==0 and status['job_done'] and (status['max_time_exceeded'] or status['bfgs_converged'])):raise RuntimeError('restart did not terminate safely')
a=w/'segment_180s_checkpoint.tar'
with tarfile.open(a,'w') as tar:tar.add(w/'tmp',arcname='tmp')
h=hashlib.sha256()
with a.open('rb') as f:
 for c in iter(lambda:f.read(8*1024*1024),b''):h.update(c)
shutil.copy2(a,dest/a.name)
h2=hashlib.sha256()
with (dest/a.name).open('rb') as f:
 for c in iter(lambda:f.read(8*1024*1024),b''):h2.update(c)
print('CHECKPOINT',json.dumps({'size':a.stat().st_size,'sha256':h.hexdigest(),'drive_sha256':h2.hexdigest(),'verified':h.hexdigest()==h2.hexdigest()}),flush=True)
assert h.hexdigest()==h2.hexdigest()