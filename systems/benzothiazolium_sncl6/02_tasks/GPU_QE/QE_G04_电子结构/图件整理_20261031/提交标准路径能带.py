import pathlib,tarfile,shutil,os,subprocess,time,json,re,hashlib,numpy as np
D=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算');src=D/'Codex_优化晶胞电子结构_20261031';dest=D/'Codex_规范能带_P1_20261031';dest.mkdir(exist_ok=True);w=pathlib.Path('/content/qe_standard_bands');w.mkdir(exist_ok=True);(w/'tmp').mkdir(exist_ok=True)
with tarfile.open(src/'optimized_scf_checkpoint.tar.gz') as t:t.extractall(w/'tmp',filter='data')
with tarfile.open(D/'Codex_晶胞试算_20261030'/'QE_G01_results.tar.gz') as t:
 for m in t.getmembers():
  if m.name=='pseudo' or m.name.startswith('pseudo/'):t.extract(m,w,filter='data')
assert (w/'tmp'/'optimized_scf.save'/'data-file-schema.xml').exists()
q={'GAMMA':[0,0,0],'X':[0,0,.5],'Y':[0,-.5,0],'Z':[.5,0,-.5],'R':[.5,-.5,0],'T':[.5,-.5,-.5],'U':[.5,0,0],'V':[0,-.5,.5]};path=[('GAMMA','X'),('Y','GAMMA'),('GAMMA','Z'),('R','GAMMA'),('GAMMA','T'),('U','GAMMA'),('GAMMA','V')];base=(src/'optimized_scf.in').read_text().split('K_POINTS automatic')[0].replace("calculation='scf'","calculation='bands'").replace("occupations='fixed'","occupations='fixed', nbnd=105").replace("verbosity='high'","verbosity='high', max_seconds=170")
env=os.environ.copy();env['LD_LIBRARY_PATH']='/content/qe_drive_restore/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2';records=[]
for index,(a,b) in enumerate(path,1):
 pts=np.linspace(q[a],q[b],25);k='K_POINTS crystal\n25\n'+''.join(' '.join(f'{v:.12f}' for v in p)+' 1.0\n' for p in pts);inp=base+k;name=f'segment_{index:02d}';i=w/(name+'.in');o=w/(name+'.out');i.write_text(inp);status=dest/(name+'.status.json');result=dest/(name+'.out')
 if status.exists() and result.exists():
  r=json.loads(status.read_text());assert r['done'] and r['gpu_active'] and not r['time_limit'] and (dest/i.name).read_text()==inp;print('REUSE',name,flush=True)
 else:
  shutil.copy2(i,dest/i.name);start=time.time();print('START',name,a,b,flush=True)
  with o.open('w') as f:
   p=subprocess.Popen(['/content/qe_drive_restore/bin/pw.x','-in',i.name],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT)
   while p.poll() is None:time.sleep(10);f.flush();shutil.copyfile(o,dest/(name+'.live.out'));print('RUNNING',name,round(time.time()-start),flush=True)
  s=o.read_text(errors='replace');shutil.copy2(o,result);r={'segment':index,'start':a,'end':b,'rc':p.returncode,'seconds':round(time.time()-start,1),'done':'JOB DONE.' in s,'gpu_active':'GPU acceleration is ACTIVE' in s,'time_limit':'Maximum CPU time exceeded' in s};status.write_text(json.dumps(r,indent=2));print('RESULT',json.dumps(r),flush=True)
  if not(r['rc']==0 and r['done'] and r['gpu_active'] and not r['time_limit']):raise RuntimeError('segment incomplete')
 records.append(r);(dest/'progress.json').write_text(json.dumps(records,indent=2))
(dest/'path_manifest.json').write_text(json.dumps({'code':'SeeK-path 2.2.2; spglib 2.8.0','symprec_A':1e-5,'spacegroup':'P-1','reciprocal_coordinate_basis':'input original cell','path':path,'point_coords':q,'points_per_segment':25,'method':'PBE-D3 optimized fixed cell scalar-relativistic no SOC','reference':'sampled VBM from 4x4x3 NSCF = 0.8463 eV'},indent=2))
out=dest/'standard_bands_segments.tar.gz'
with tarfile.open(out,'w:gz') as t:
 for f in dest.iterdir():
  if f.is_file() and f!=out and not f.name.endswith('.live.out'):t.add(f,arcname=f.name)
print('ARCHIVE',json.dumps({'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}),flush=True)
