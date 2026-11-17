import pathlib,tarfile,shutil,subprocess,os,time,json,hashlib,re
D=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算');src=D/'Codex_SOC配对k332_20261031';dest=D/'Codex_SOC_PDOS对照_20261031';dest.mkdir(exist_ok=True);w=pathlib.Path('/content/qe_soc_k664_batches');assert (w/'tmp'/'pilot_soc_on.save'/'data-file-schema.xml').exists();
if not (w/'pseudo_scalar').exists():
 with tarfile.open(D/'Codex_SOC赝势准备_20261031'/'scalar_pseudopotentials.tar.gz') as t:t.extractall(w/'pseudo_scalar',filter='data')
env=os.environ.copy();env['LD_LIBRARY_PATH']='/content/qe_drive_restore/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2'
def run(name,exe,inp):
 (w/(name+'.in')).write_text(inp);shutil.copy2(w/(name+'.in'),dest/(name+'.in'));o=w/(name+'.out');start=time.time();print('START',name,flush=True)
 with o.open('w') as f:
  q=subprocess.Popen(['/content/qe_drive_restore/bin/'+exe,'-in',name+'.in'],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT)
  while q.poll() is None:
   time.sleep(10);f.flush();shutil.copyfile(o,dest/(name+'.live.out'));print('RUNNING',name,round(time.time()-start),flush=True)
 s=o.read_text(errors='replace');shutil.copy2(o,dest/o.name);status={'rc':q.returncode,'job_done':'JOB DONE.' in s,'gpu_active':'GPU acceleration is ACTIVE' in s,'time_limit':'Maximum CPU time exceeded' in s,'seconds':round(time.time()-start,1)};(dest/(name+'.status.json')).write_text(json.dumps(status,indent=2));print('STATUS',name,json.dumps(status),flush=True)
 if q.returncode!=0 or not status['job_done'] or status['time_limit']:raise RuntimeError(name+' incomplete; raw log saved')
 return status
for mode in ('scalar_control','soc_on'):
 prefix='pilot_'+mode;save=w/'tmp'/(prefix+'.save');assert (save/'data-file-schema.xml').exists(),prefix
 base=(src/(prefix+'_seg1.in')).read_text();inp=base.replace("calculation='scf'","calculation='nscf'").replace("occupations='fixed'","occupations='tetrahedra'").replace('3 3 2 0 0 0','4 4 3 0 0 0').replace('max_seconds=150','max_seconds=240')
 nscf_name='pdos_nscf_'+mode;proj_name='projwfc_'+mode;prev=dest/(proj_name+'.status.json')
 if prev.exists():
  status=json.loads(prev.read_text());assert status['rc']==0 and status['job_done'] and not status['time_limit'];print('REUSE_COMPLETED',mode,flush=True)
 else:
  st=run(nscf_name,'pw.x',inp);assert st['gpu_active']
  p='&PROJWFC\n'+f" prefix='{prefix}', outdir='./tmp', filpdos='{mode}', DeltaE=0.02, Emin=-10.0, Emax=8.0,\n/\n";run(proj_name,'projwfc.x',p)
 files=list(w.glob(mode+'.pdos*'));atoms={int(m.group(1)) for f in files if (m:=re.search(r'pdos_atm#(\d+)',f.name))};assert atoms==set(range(1,44)) and any(f.name.endswith('pdos_tot') for f in files),(mode,len(files),sorted(atoms))
 for f in files:shutil.copy2(f,dest/f.name)
 print('PDOS_SAVED',mode,len(files),flush=True)
out=dest/'soc_pdos_pair_results.tar.gz'
with tarfile.open(out,'w:gz',compresslevel=3) as t:
 for f in dest.iterdir():
  if f.is_file() and f!=out and not f.name.endswith('.live.out'):t.add(f,arcname=f.name)
print('ARCHIVE',json.dumps({'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}),flush=True)
