import pathlib,os,shutil,tarfile,time,subprocess,json,hashlib
D=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算');source=D/'Codex_优化晶胞电子结构_20261031';dest=D/'Codex_带边密度_20261031';dest.mkdir(exist_ok=True)
w=pathlib.Path('/content/qe_band_edge_density');w.mkdir(exist_ok=True);(w/'tmp').mkdir(exist_ok=True);qe=pathlib.Path('/content/qe_drive_restore');cache=pathlib.Path('/content/drive/MyDrive/QE_build/qe-7.5-gpu-sm80')
for sub in ('bin','lib'):
 (qe/sub).mkdir(parents=True,exist_ok=True)
 for p in (cache/sub).iterdir():
  if p.is_file():
   q=qe/sub/p.name
   if not q.exists() or q.stat().st_size!=p.stat().st_size:shutil.copyfile(p,q)
   if sub=='bin':q.chmod(0o755)
print('QE_RESTORED',flush=True)
with tarfile.open(source/'optimized_scf_checkpoint.tar.gz') as t:t.extractall(w/'tmp',filter='data')
with tarfile.open(D/'Codex_晶胞试算_20261030'/'QE_G01_results.tar.gz') as t:
 for m in t.getmembers():
  if m.name=='pseudo' or m.name.startswith('pseudo/'):t.extract(m,w,filter='data')
t=(source/'optimized_nscf.in').read_text().replace("calculation='nscf',", "calculation='nscf', max_seconds=180,")
(w/'edge_nscf.in').write_text(t);shutil.copy2(w/'edge_nscf.in',dest/'edge_nscf.in')
env=os.environ.copy();env['LD_LIBRARY_PATH']=str(qe/'lib')+':'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2'
def run(exe,inp,label):
 pth=w/(label+'.out');start=time.time();print('START',label,flush=True)
 with pth.open('w') as f:
  p=subprocess.Popen([str(qe/'bin'/exe),'-in',inp],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT)
  while p.poll() is None:
   time.sleep(10);f.flush();shutil.copyfile(pth,dest/(label+'.live.out'));print('MONITOR',label,round(time.time()-start),pth.stat().st_size,flush=True)
 txt=pth.read_text(errors='replace');shutil.copy2(pth,dest/pth.name);r={'name':label,'rc':p.returncode,'elapsed_s':round(time.time()-start,1),'done':'JOB DONE.' in txt,'timed_out':'Maximum CPU time exceeded' in txt};print('RESULT',json.dumps(r),flush=True)
 if not(r['rc']==0 and r['done']) or r['timed_out']:raise RuntimeError('unfinished '+label)
 return r
run('pw.x','edge_nscf.in','edge_nscf')
for name,k,b in [('VBM',6,81),('CBM',1,82)]:
 t=f"&INPUTPP\n prefix='optimized_scf', outdir='./tmp', filplot='{name}.dat', plot_num=7, kpoint={k}, kband={b},\n/\n&PLOT\n nfile=1, filepp(1)='{name}.dat', weight(1)=1.0, iflag=3, output_format=6, fileout='{name}.cube',\n/\n"
 (w/(name+'.in')).write_text(t);shutil.copy2(w/(name+'.in'),dest/(name+'.in'));run('pp.x',name+'.in',name)
 cube=w/(name+'.cube');assert cube.is_file() and cube.stat().st_size>1000
 shutil.copy2(cube,dest/cube.name);print('CUBE',name,cube.stat().st_size,flush=True)
print('COMPLETE pseudo-charge density plot_num=7; VBM k6 band81 CBM k1 band82; 4x4x3 NSCF irreducible ordering must verify',flush=True)