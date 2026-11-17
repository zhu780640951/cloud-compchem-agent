import os,pathlib,tarfile,shutil,subprocess,time,re,json,hashlib
D=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算');old=D/'Codex_优化晶胞电子结构_20261031';dest=D/'Codex_带边k点收敛_20261031';dest.mkdir(exist_ok=True)
w=pathlib.Path('/content/qe_kmesh_check');w.mkdir(exist_ok=True);(w/'tmp').mkdir(exist_ok=True)
with tarfile.open(D/'Codex_晶胞试算_20261030'/'QE_G01_results.tar.gz') as tar:
 for m in tar.getmembers():
  if m.name=='pseudo' or m.name.startswith('pseudo/'):tar.extract(m,w,filter='data')
print('RESTORING_SCF_CHECKPOINT',flush=True)
with tarfile.open(old/'optimized_scf_checkpoint.tar.gz') as tar:tar.extractall(w/'tmp',filter='data')
assert (w/'tmp'/'optimized_scf.save'/'data-file-schema.xml').is_file()
base=(old/'optimized_scf.in').read_text();assert "prefix='optimized_scf'" in base and 'ecutwfc=80, ecutrho=640' in base and '3 3 2 0 0 0' in base
env=os.environ.copy();env['LD_LIBRARY_PATH']='/content/qe_drive_restore/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2';rows=[]
for label,mesh in [('k664','6 6 4')]:
 inp=base.replace("calculation='scf'","calculation='nscf'").replace("occupations='fixed'","occupations='tetrahedra', nbnd=105").replace('3 3 2 0 0 0',mesh+' 0 0 0')
 name='optimized_nscf_'+label;(w/(name+'.in')).write_text(inp);shutil.copy2(w/(name+'.in'),dest/(name+'.in'));out=w/(name+'.out');start=time.time();print('START',name,flush=True)
 with out.open('w') as f:
  p=subprocess.Popen(['/content/qe_drive_restore/bin/pw.x','-in',name+'.in'],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT)
  while p.poll() is None:
   time.sleep(10);f.flush();shutil.copyfile(out,dest/(name+'.live.out'));print('RUNNING',name,round(time.time()-start),flush=True)
 s=out.read_text(errors='replace');shutil.copy2(out,dest/out.name);status={'mesh':mesh,'seconds':round(time.time()-start,2),'returncode':p.returncode,'job_done':'JOB DONE.' in s,'gpu_active':'GPU acceleration is ACTIVE' in s};(dest/(name+'.status.json')).write_text(json.dumps(status,indent=2));print('STATUS',json.dumps(status),flush=True)
 if not(status['returncode']==0 and status['job_done'] and status['gpu_active']):raise RuntimeError('NSCF failed; original log preserved')
 pat=r'k\s*=\s*([-+]?\d+\.\d+)\s*([-+]?\d+\.\d+)\s*([-+]?\d+\.\d+)\s*\(\s*\d+\s+PWs\)\s+bands \(ev\):';bands=[]
 for m in re.finditer(pat,s,re.I):
  vals=[]
  for line in s[m.end():].splitlines():
   if not line.strip():
    if vals:break
    continue
   if re.fullmatch(r'[\s+\-\d\.Ee]+',line):vals.extend(float(x) for x in line.split())
   elif vals:break
  if len(vals)==105:bands.append({'k_tpiba':list(map(float,m.groups())),'vbm':vals[80],'cbm':vals[81]})
 reported=re.search(r'number of k points\s*=\s*(\d+)',s);assert reported and len(bands)==int(reported.group(1)),(len(bands),reported.group(1) if reported else None)
 v=max(bands,key=lambda x:x['vbm']);c=min(bands,key=lambda x:x['cbm']);result={'mesh':mesh,'cutoff_ry':[80,640],'vbm':v,'cbm':c,'gap_eV':round(c['cbm']-v['vbm'],4),'n_irreducible_k':len(bands),'scope':'sampled scalar-relativistic PBE Kohn-Sham gap, 4 decimals, no SOC'};rows.append(result);(dest/'kmesh_analysis.json').write_text(json.dumps(rows,indent=2));print('RESULT',json.dumps(result),flush=True)
archive=dest/'kmesh_results.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for f in dest.iterdir():
  if f.is_file() and not f.name.endswith('.live.out') and f!=archive:tar.add(f,arcname=f.name)
print('ARCHIVE',json.dumps({'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}),flush=True)
