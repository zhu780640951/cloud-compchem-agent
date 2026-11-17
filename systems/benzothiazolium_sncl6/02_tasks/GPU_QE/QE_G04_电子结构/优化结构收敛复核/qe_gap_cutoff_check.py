import os,pathlib,subprocess,time,shutil,tarfile,json,re
D=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算');outdir=D/'Codex_优化结构带隙截断复核_20261031';outdir.mkdir(exist_ok=True)
w=pathlib.Path('/content/qe_gap_cutoff');w.mkdir(exist_ok=True);(w/'tmp').mkdir(exist_ok=True)
with tarfile.open(D/'Codex_晶胞试算_20261030'/'QE_G01_results.tar.gz') as t:
 for m in t.getmembers():
  if m.name=='pseudo' or m.name.startswith('pseudo/'):t.extract(m,w,filter='data')
 base=t.extractfile('scf_80_640_k332.in').read().decode()
coords=(D/'Codex_全原子优化_20261030'/'R_fixed_final_crystal.txt').read_text();xyz=[' '.join(x.split()[:4]) for x in coords.splitlines()[1:] if x.strip()];assert len(xyz)==43
pre,old=base.split('ATOMIC_POSITIONS crystal\n',1);_,post=old.split('K_POINTS automatic',1)
base=pre+'ATOMIC_POSITIONS crystal\n'+'\n'.join(xyz)+'\nK_POINTS automatic'+post
base=base.replace("prefix='scf_80_640_k332'","prefix='gap100'").replace('ecutwfc=80, ecutrho=640','ecutwfc=100, ecutrho=800')
env=os.environ.copy();env['LD_LIBRARY_PATH']='/content/qe_drive_restore/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2'
def run(name,inp):
 (w/(name+'.in')).write_text(inp);shutil.copy2(w/(name+'.in'),outdir/(name+'.in'));fpath=w/(name+'.out');start=time.time();print('START',name,flush=True)
 with fpath.open('w') as f:
  p=subprocess.Popen(['/content/qe_drive_restore/bin/pw.x','-in',name+'.in'],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT)
  while p.poll() is None:
   time.sleep(10);f.flush();shutil.copyfile(fpath,outdir/(name+'.live.out'));print('RUNNING',name,round(time.time()-start),flush=True)
 s=fpath.read_text(errors='replace');shutil.copy2(fpath,outdir/fpath.name);r={'name':name,'seconds':round(time.time()-start,1),'rc':p.returncode,'job_done':'JOB DONE.' in s,'gpu_active':'GPU acceleration is ACTIVE' in s,'scf_converged':'convergence has been achieved' in s};(outdir/(name+'.status.json')).write_text(json.dumps(r,indent=2));print('RESULT',json.dumps(r),flush=True)
 if not(r['rc']==0 and r['job_done'] and r['gpu_active']):raise RuntimeError(name+' failed')
 return s
s=run('gap100_scf',base);assert 'convergence has been achieved' in s
e=float(re.search(r'number of electrons\s*=\s*([\d.]+)',s).group(1));assert e==162;nb=int(e/2)+24
nscf=base.replace("calculation='scf'","calculation='nscf'").replace("occupations='fixed'",f"occupations='tetrahedra', nbnd={nb}").replace('3 3 2 0 0 0','4 4 3 0 0 0')
s=run('gap100_nscf',nscf)
pat=r'k\s*=\s*([-+]?\d+\.\d+)\s*([-+]?\d+\.\d+)\s*([-+]?\d+\.\d+)\s*\(\s*\d+\s+PWs\)\s+bands \(ev\):';rows=[]
for m in re.finditer(pat,s,re.I):
 vals=[]
 for line in s[m.end():].splitlines():
  if not line.strip():
   if vals:break
   continue
  if re.fullmatch(r'[\s+\-\d\.Ee]+',line):vals.extend(float(x) for x in line.split())
  elif vals:break
 if len(vals)==nb:rows.append({'k_tpiba':list(map(float,m.groups())),'vbm':vals[80],'cbm':vals[81]})
assert len(rows)==26,(len(rows),nb)
v=max(rows,key=lambda x:x['vbm']);c=min(rows,key=lambda x:x['cbm']);r={'cutoff_ry':[100,800],'scf_mesh':[3,3,2],'nscf_mesh':[4,4,3],'vbm':v,'cbm':c,'sampled_gap_eV':c['cbm']-v['vbm'],'qualification':'scalar-relativistic PBE; four-decimal band output, k-sampled KS gap, no SOC'};(outdir/'gap100_analysis.json').write_text(json.dumps(r,indent=2));print('GAP',json.dumps(r),flush=True)
with tarfile.open(outdir/'gap_cutoff_results.tar.gz','w:gz') as t:
 for f in outdir.iterdir():
  if f.is_file() and f.name!='gap_cutoff_results.tar.gz' and not f.name.endswith('.live.out'):t.add(f,arcname=f.name)
print('DONE',flush=True)
