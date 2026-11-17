import os,pathlib,subprocess,shutil,time,re,json
w=pathlib.Path('/content/qe_optimized_electronic');d=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_优化晶胞电子结构_20261031');bin=pathlib.Path('/content/qe_drive_restore/bin');env=os.environ.copy();env['LD_LIBRARY_PATH']='/content/qe_drive_restore/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2'
base=(w/'optimized_scf.in').read_text();scf=(w/'optimized_scf.out').read_text(errors='replace');m=re.search(r'number of electrons\s*=\s*([\d.]+)',scf);assert m;ne=float(m.group(1));nb=int(ne/2)+24
text=base.replace("calculation='scf'","calculation='nscf'").replace('occupations=\'fixed\'','occupations=\'tetrahedra\', nbnd='+str(nb)).replace('3 3 2 0 0 0','4 4 3 0 0 0')
(w/'optimized_nscf.in').write_text(text);shutil.copy2(w/'optimized_nscf.in',d/'optimized_nscf.in')
def run(name,exe,inp,limit=600):
 out=w/(name+'.out');start=time.time();print('START',name,flush=True)
 with out.open('w') as f:
  p=subprocess.Popen([str(bin/exe),'-in',inp],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT)
  while p.poll() is None:
   time.sleep(10);f.flush();shutil.copyfile(out,d/(name+'.live.out'));print('MONITOR',name,round(time.time()-start),out.stat().st_size,flush=True)
 t=out.read_text(errors='replace');shutil.copy2(out,d/out.name);r={'case':name,'rc':p.returncode,'elapsed_s':round(time.time()-start,1),'job_done':'JOB DONE.' in t};print('RESULT',json.dumps(r),flush=True)
 if not(r['rc']==0 and r['job_done']):raise RuntimeError(name+' failed')
run('optimized_nscf','pw.x','optimized_nscf.in')
(w/'dos.in').write_text("&DOS\n prefix='optimized_scf', outdir='./tmp', fildos='optimized.dos', DeltaE=0.02,\n/\n")
(w/'pdos.in').write_text("&PROJWFC\n prefix='optimized_scf', outdir='./tmp', filpdos='optimized.pdos', DeltaE=0.02,\n/\n")
for exe,inp,name in [('dos.x','dos.in','dos'),('projwfc.x','pdos.in','pdos')]:
 if not (bin/exe).is_file():print('MISSING_EXECUTABLE',exe,flush=True);break
 run(name,exe,inp)
for p in w.glob('optimized.*'):
 if p.is_file():shutil.copy2(p,d/p.name)
print('FILES',json.dumps([p.name for p in w.glob('optimized.*') if p.is_file()]),flush=True)