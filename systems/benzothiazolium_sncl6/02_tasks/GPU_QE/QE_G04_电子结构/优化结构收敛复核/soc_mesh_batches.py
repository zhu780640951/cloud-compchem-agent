import os,pathlib,tarfile,hashlib,shutil,subprocess,time,re,json,itertools
D=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算');src=D/'Codex_SOC配对k332_20261031';dest=D/'Codex_SOC_k664分批_20261031';dest.mkdir(exist_ok=True);w=pathlib.Path('/content/qe_soc_k664_batches');w.mkdir(exist_ok=True)
checkpoint=src/'pilot_soc_on_seg1_checkpoint.tar';expected=(src/(checkpoint.name+'.sha256')).read_text().strip();actual=hashlib.sha256(checkpoint.read_bytes()).hexdigest();assert actual==expected;print('CHECKPOINT_VALID',actual,flush=True)
with tarfile.open(checkpoint) as t:t.extractall(w,filter='data')
with tarfile.open(D/'Codex_SOC赝势准备_20261031'/'soc_pseudopotentials.tar.gz') as t:t.extractall(w/'pseudo_soc',filter='data')
assert (w/'tmp'/'pilot_soc_on.save'/'data-file-schema.xml').is_file()
base=(src/'pilot_soc_on_seg2.in').read_text().replace("calculation='scf', restart_mode='restart'","calculation='scf'")
env=os.environ.copy();env['LD_LIBRARY_PATH']='/content/qe_drive_restore/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2'
def run(name,inp):
 i=w/(name+'.in');o=w/(name+'.out');i.write_text(inp);shutil.copy2(i,dest/i.name);start=time.time();print('START',name,flush=True)
 with o.open('w') as f:
  p=subprocess.Popen(['/content/qe_drive_restore/bin/pw.x','-in',i.name],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT)
  while p.poll() is None:
   time.sleep(10);f.flush();shutil.copyfile(o,dest/(name+'.live.out'));print('RUNNING',name,round(time.time()-start),flush=True)
 s=o.read_text(errors='replace');shutil.copy2(o,dest/o.name);r={'name':name,'rc':p.returncode,'seconds':round(time.time()-start,1),'job_done':'JOB DONE.' in s,'gpu_active':'GPU acceleration is ACTIVE' in s,'time_limit':'Maximum CPU time exceeded' in s,'scf_converged':'convergence has been achieved' in s};(dest/(name+'.status.json')).write_text(json.dumps(r));print('STATUS',json.dumps(r),flush=True)
 if not(r['rc']==0 and r['job_done'] and r['gpu_active'] and not r['time_limit']):raise RuntimeError('incomplete job; original output retained')
 return s
resume=base.replace("calculation='scf'","calculation='scf', restart_mode='restart'");out=run('recovered_scf',resume);assert 'convergence has been achieved' in out and 'Calculation restarted from' in out
parts=list(itertools.product(range(6),range(6),range(4)));batchsize=12;batch_total=(len(parts)+batchsize-1)//batchsize;result=[]
for n in range(0,len(parts),batchsize):
 subset=parts[n:n+batchsize];k='K_POINTS crystal\n'+str(len(subset))+'\n'+''.join(f'{i/6:.12f} {j/6:.12f} {k/4:.12f} 1.0\n' for i,j,k in subset)
 pre,post=base.split('K_POINTS automatic\n',1);old,tail=post.split('\n',1);assert old.strip()=='3 3 2 0 0 0';inp=pre.replace("calculation='scf'","calculation='nscf'").replace('noncolin=.true., lspinorb=.true.','noncolin=.true., lspinorb=.true., nosym=.true., noinv=.true.')+k+tail
 name=f'kbatch_{n//batchsize+1:02d}';saved=dest/(name+'.out');status_file=dest/(name+'.status.json')
 if saved.exists() and status_file.exists():
  z=json.loads(status_file.read_text());assert (dest/(name+'.in')).read_text()==inp and z['rc']==0 and z['job_done'] and z['gpu_active'] and not z['time_limit'];s=saved.read_text(errors='replace');assert 'JOB DONE.' in s;print('REUSE_COMPLETED',name,flush=True)
 else:s=run(name,inp)
 pat=r'k\s*=\s*([-+]?\d+\.\d+)\s*([-+]?\d+\.\d+)\s*([-+]?\d+\.\d+)\s*\(\s*\d+\s+PWs\)\s+bands \(ev\):';bands=[]
 for m in re.finditer(pat,s,re.I):
  vals=[]
  for line in s[m.end():].splitlines():
   if not line.strip():
    if vals:break
    continue
   if re.fullmatch(r'[\s+\-\d\.Ee]+',line):vals.extend(float(x) for x in line.split())
   elif vals:break
  if len(vals)==180:bands.append({'k_tpiba':list(map(float,m.groups())),'vbm':vals[161],'cbm':vals[162]})
 reported=re.search(r'number of k points\s*=\s*(\d+)',s);assert reported and len(bands)==int(reported.group(1)),(len(bands),reported.group(1) if reported else None)
 result.extend(bands);v=max(result,key=lambda x:x['vbm']);c=min(result,key=lambda x:x['cbm']);progress={'batches_completed':n//batchsize+1,'batches_total':batch_total,'points_completed':len(result),'vbm':v,'cbm':c,'gap_eV':round(c['cbm']-v['vbm'],4)};(dest/'progress.json').write_text(json.dumps(progress,indent=2));print('PROGRESS',json.dumps(progress),flush=True)
assert len(result)==len(parts)==144
(dest/'all_band_edges.json').write_text(json.dumps(result,indent=2));out=dest/'soc_k664_results.tar.gz'
with tarfile.open(out,'w:gz') as t:
 for f in sorted(dest.iterdir()):
  if f.is_file() and f!=out and not f.name.endswith('.live.out'):t.add(f,arcname=f.name)
print('ARCHIVE',json.dumps({'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}),flush=True)
