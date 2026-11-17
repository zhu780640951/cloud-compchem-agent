import pathlib,os,subprocess,time,shutil,json,re
base=pathlib.Path('/content/benzothiazole_qe_g01');w=pathlib.Path('/content/benzothiazole_qe_g02_h_relax');w.mkdir(exist_ok=True)
drive=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_H优化_20261030');drive.mkdir(parents=True,exist_ok=True)
shutil.copytree(base/'pseudo',w/'pseudo',dirs_exist_ok=True);(w/'tmp').mkdir(exist_ok=True)
for name in ['h_relax.in','h_relax.out','status.json']:
 old=w/name
 if old.exists(): shutil.copy2(old,drive/('failed_input_order_'+name))
t=(base/'scf_80_640_k332.in').read_text().replace("calculation='scf'","calculation='relax'").replace("prefix='scf_80_640_k332'","prefix='crystal_hrelax'")
t=t.replace("tprnfor=.true., verbosity='high',","tprnfor=.true., verbosity='low', nstep=100, forc_conv_thr=7.78d-4, max_seconds=720,")
t=t.replace('ATOMIC_SPECIES\n',"&IONS\n ion_dynamics='bfgs',\n/\nATOMIC_SPECIES\n",1)
pre,pos=t.split('ATOMIC_POSITIONS crystal\n',1);section,post=pos.split('K_POINTS automatic',1)
lines=[]
for line in section.splitlines():
 fields=line.split()
 if len(fields)>=4:
  flags='1 1 1' if fields[0]=='H' else '0 0 0';lines.append(line+' '+flags)
t=pre+"ATOMIC_POSITIONS crystal\n"+'\n'.join(lines)+'\nK_POINTS automatic'+post
assert len(lines)==43 and sum(l.split()[0]=='H' for l in lines)==16
(w/'h_relax.in').write_text(t);shutil.copy2(w/'h_relax.in',drive/'h_relax.in')
env=os.environ.copy();env['LD_LIBRARY_PATH']='/content/qe_drive_restore/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2'
out=w/'h_relax.out';start=time.time()
with out.open('w') as f:
 p=subprocess.Popen(['/content/qe_drive_restore/bin/pw.x','-in','h_relax.in'],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT)
 print('H_RELAX_STARTED',p.pid,flush=True)
 while p.poll() is None:
  time.sleep(15);f.flush();shutil.copyfile(out,drive/'h_relax.live.out')
  txt=out.read_text(errors='replace');print('H_RELAX_MONITOR',round(time.time()-start,1),'scf_completed',txt.count('convergence has been achieved'),'bytes',len(txt),flush=True)
rc=p.returncode;txt=out.read_text(errors='replace');shutil.copy2(out,drive/'h_relax.out')
result={'exit_code':rc,'elapsed_s':round(time.time()-start,2),'job_done':'JOB DONE.' in txt,'bfgs_converged':bool(re.search(r'bfgs converged',txt,re.I)),'gpu_active':'GPU acceleration is ACTIVE' in txt,'scf_convergences':txt.count('convergence has been achieved'),'user_limit_note':'max_seconds=720: partial run if timed stop'}
(w/'status.json').write_text(json.dumps(result,indent=2));shutil.copy2(w/'status.json',drive/'status.json')
if (w/'tmp'/'crystal_hrelax.save').exists():shutil.make_archive(str(w/'h_relax_checkpoint'),'gztar',w/'tmp','crystal_hrelax.save');shutil.copy2(w/'h_relax_checkpoint.tar.gz',drive/'h_relax_checkpoint.tar.gz')
print('RESULT_JSON',json.dumps(result),flush=True)