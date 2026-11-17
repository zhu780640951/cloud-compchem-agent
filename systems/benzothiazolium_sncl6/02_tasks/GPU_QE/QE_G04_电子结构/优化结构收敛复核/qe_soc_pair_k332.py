import os,pathlib,tarfile,shutil,subprocess,time,re,json,hashlib
D=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算');dest=D/'Codex_SOC配对k332_20261031';dest.mkdir(exist_ok=True)
w=pathlib.Path('/content/qe_soc_pair_k332');w.mkdir(exist_ok=True);(w/'tmp').mkdir(exist_ok=True)
for kind in ('scalar','soc'):
 (w/('pseudo_'+kind)).mkdir(exist_ok=True)
 with tarfile.open(D/'Codex_SOC赝势准备_20261031'/(kind+'_pseudopotentials.tar.gz')) as t:t.extractall(w/('pseudo_'+kind),filter='data')
base=(D/'Codex_优化晶胞电子结构_20261031'/'optimized_scf.in').read_text();pre,rest=base.split('ATOMIC_SPECIES\n',1);species,post=rest.split('CELL_PARAMETERS angstrom\n',1)
base=pre+'ATOMIC_SPECIES\n'+species+'CELL_PARAMETERS angstrom\n'+post
assert 'ecutwfc=80, ecutrho=640' in base and '3 3 2 0 0 0' in base
base=base.replace('tprnfor=.true.','tprnfor=.false.').replace('verbosity=\'high\'','verbosity=\'high\', max_seconds=150')
env=os.environ.copy();env['LD_LIBRARY_PATH']='/content/qe_drive_restore/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2';results=[]
for mode in ('scalar_control','soc_on'):
 kind='soc' if mode=='soc_on' else 'scalar';manifest=json.loads((w/('pseudo_'+kind)/(kind+'_pseudo_manifest.json')).read_text());names={x['element']:x['file'] for x in manifest};assert len(names)==7
 for x in manifest:assert hashlib.sha256((w/('pseudo_'+kind)/x['file']).read_bytes()).hexdigest()==x['sha256']
 sp=[]
 for line in species.splitlines():
  a=line.split()
  if len(a)>=3:assert a[0] in names;sp.append(f'{a[0]} {a[1]} {names[a[0]]}')
 assert len(sp)==7
 pre2,rest2=base.split('ATOMIC_SPECIES\n',1);_,post2=rest2.split('CELL_PARAMETERS angstrom\n',1);input_base=pre2+'ATOMIC_SPECIES\n'+'\n'.join(sp)+'\nCELL_PARAMETERS angstrom\n'+post2
 name='pilot_'+mode;inp=input_base.replace("prefix='optimized_scf'",f"prefix='{name}'").replace("pseudo_dir='./pseudo'",f"pseudo_dir='./pseudo_{kind}'")
 if mode=='soc_on':inp=inp.replace("occupations='fixed'","occupations='fixed', noncolin=.true., lspinorb=.true., nbnd=180")
 else:inp=inp.replace("occupations='fixed'","occupations='fixed', nbnd=105")
 for segment in range(1,5):
  text=inp if segment==1 else inp.replace("calculation='scf'","calculation='scf', restart_mode='restart'")
  i=w/f'{name}_seg{segment}.in';o=w/f'{name}_seg{segment}.out';i.write_text(text);shutil.copy2(i,dest/i.name);start=time.time();print('START',name,'segment',segment,flush=True)
  with o.open('w') as f:
   p=subprocess.Popen(['/content/qe_drive_restore/bin/pw.x','-in',i.name],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT)
   while p.poll() is None:
    time.sleep(10);f.flush();shutil.copyfile(o,dest/(name+'.live.out'));print('RUNNING',name,segment,round(time.time()-start),flush=True)
  out=o.read_text(errors='replace');shutil.copy2(o,dest/o.name)
  row={'mode':mode,'segment':segment,'rc':p.returncode,'elapsed_s':round(time.time()-start,1),'job_done':'JOB DONE.' in out,'gpu_active':'GPU acceleration is ACTIVE' in out,'converged':'convergence has been achieved' in out,'max_seconds_stop':bool(re.search(r'maximum.*time|time limit|stopping.*time',out,re.I))};results.append(row);(dest/'pilot_progress.json').write_text(json.dumps(results,indent=2));print('SEGMENT',json.dumps(row),flush=True)
  if row['converged'] and row['job_done'] and row['gpu_active'] and row['rc']==0:break
  checkpoint=w/'tmp'/(name+'.save');schema=checkpoint/'data-file-schema.xml'
  if not(row['rc']==0 and row['job_done'] and row['gpu_active'] and schema.exists()):raise RuntimeError('Pilot did not complete or provide a usable checkpoint; inspect original output')
  local=w/(name+f'_seg{segment}_checkpoint.tar');temp=dest/(local.name+'.part');final=dest/local.name
  with tarfile.open(local,'w') as t:t.add(w/'tmp',arcname='tmp')
  with tarfile.open(local) as t:assert any(m.name.endswith('data-file-schema.xml') for m in t.getmembers())
  digest=hashlib.sha256(local.read_bytes()).hexdigest();shutil.copyfile(local,temp);assert hashlib.sha256(temp.read_bytes()).hexdigest()==digest;os.replace(temp,final);(dest/(final.name+'.sha256')).write_text(digest);print('CHECKPOINT',final.name,final.stat().st_size,digest,flush=True)
 else:raise RuntimeError('Segment limit reached')
print('PAIRED_SCF_PILOTS_FINISHED',flush=True)
