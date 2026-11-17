import pathlib,os,subprocess,time,shutil,json,re,tarfile
w=pathlib.Path('/content/benzothiazole_qe_g02_h_relax');drive=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_H优化_20261030');tmp=w/'tmp'
required=['crystal_hrelax.bfgs','crystal_hrelax.update','crystal_hrelax.restart_scf','crystal_hrelax.save']
for n in required:
 if not (tmp/n).exists():raise FileNotFoundError(n)
print('CHECKPOINT_START',flush=True)
archive=w/'full_tmp_after_segment1.tar'
with tarfile.open(archive,'w') as tar:tar.add(tmp,arcname='tmp')
shutil.copy2(archive,drive/archive.name)
print('CHECKPOINT_SAVED',archive.stat().st_size,flush=True)
t=(w/'h_relax.in').read_text().replace("calculation='relax',", "calculation='relax', restart_mode='restart',")
(w/'h_relax_resume.in').write_text(t);shutil.copy2(w/'h_relax_resume.in',drive/'h_relax_resume.in')
env=os.environ.copy();env['LD_LIBRARY_PATH']='/content/qe_drive_restore/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2'
out=w/'h_relax_resume.out';start=time.time()
with out.open('w') as f:
 p=subprocess.Popen(['/content/qe_drive_restore/bin/pw.x','-in','h_relax_resume.in'],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT);print('RESUME_STARTED',p.pid,flush=True)
 while p.poll() is None:
  time.sleep(15);f.flush();shutil.copyfile(out,drive/'h_relax_resume.live.out');txt=out.read_text(errors='replace');print('RESUME_MONITOR',round(time.time()-start,1),'scf',txt.count('convergence has been achieved'),'bytes',len(txt),flush=True)
rc=p.returncode;txt=out.read_text(errors='replace');shutil.copy2(out,drive/out.name)
r={'exit_code':rc,'elapsed_s':round(time.time()-start,2),'job_done':'JOB DONE.' in txt,'bfgs_converged':bool(re.search(r'bfgs converged',txt,re.I)),'gpu_active':'GPU acceleration is ACTIVE' in txt,'max_time_exceeded':'Maximum CPU time exceeded' in txt,'scf_convergences':txt.count('convergence has been achieved'),'read_bfgs':'bfgs' in txt.lower()}
(w/'resume_status.json').write_text(json.dumps(r,indent=2));shutil.copy2(w/'resume_status.json',drive/'resume_status.json');print('RESUME_RESULT',json.dumps(r),flush=True)