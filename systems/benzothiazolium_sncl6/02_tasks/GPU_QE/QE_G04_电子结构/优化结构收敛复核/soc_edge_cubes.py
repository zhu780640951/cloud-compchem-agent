import os,pathlib,re,subprocess,time,shutil,json,tarfile,hashlib
D=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算');dest=D/'Codex_SOC带边密度对照_20261031';dest.mkdir(exist_ok=True);src=D/'Codex_SOC_PDOS对照_20261031';w=pathlib.Path('/content/qe_soc_k664_batches');env=os.environ.copy();env['LD_LIBRARY_PATH']='/content/qe_drive_restore/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2';summary=[]
for mode,nb,occ in [('scalar_control',105,81),('soc_on',180,162)]:
 s=(src/('pdos_nscf_'+mode+'.out')).read_text(errors='replace');pat=r'k\s*=\s*([-+]?\d+\.\d+)\s*([-+]?\d+\.\d+)\s*([-+]?\d+\.\d+)\s*\(\s*\d+\s+PWs\)\s+bands \(ev\):';rows=[]
 for m in re.finditer(pat,s,re.I):
  vals=[]
  for line in s[m.end():].splitlines():
   if not line.strip():
    if vals:break
    continue
   if re.fullmatch(r'[\s+\-\d\.Ee]+',line):vals.extend(float(x) for x in line.split())
   elif vals:break
  if len(vals)==nb:rows.append((list(map(float,m.groups())),vals))
 assert len(rows)==26
 for name,idx in [('VBM',max(range(len(rows)),key=lambda j:rows[j][1][occ-1])),('CBM',min(range(len(rows)),key=lambda j:rows[j][1][occ]))]:
  first=occ if name=='VBM' else occ+1;last=first
  if mode=='soc_on':first=occ-1 if name=='VBM' else occ+1;last=occ if name=='VBM' else occ+2;assert abs(rows[idx][1][first-1]-rows[idx][1][last-1])<1e-4
  label=mode+'_'+name;opts=f'kband(1)={first}, kband(2)={last},' if mode=='soc_on' else f'kband={first},';inp=f"&INPUTPP\n prefix='pilot_{mode}', outdir='./tmp', filplot='{label}.dat', plot_num=7, kpoint={idx+1}, {opts}\n/\n&PLOT\n nfile=1, filepp(1)='{label}.dat', weight(1)=1.0, iflag=3, output_format=6, fileout='{label}.cube',\n/\n";(w/(label+'.in')).write_text(inp);shutil.copy2(w/(label+'.in'),dest/(label+'.in'));start=time.time();print('START',label,'k',idx+1,'bands',first,last,flush=True)
  old=w/(label+'.out');reuse=old.exists() and 'JOB DONE.' in old.read_text(errors='replace')
  if not reuse:
   with old.open('w') as f:
    p=subprocess.Popen(['/content/qe_drive_restore/bin/pp.x','-in',label+'.in'],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT)
    while p.poll() is None:time.sleep(10);f.flush();shutil.copyfile(old,dest/(label+'.live.out'));print('RUNNING',label,round(time.time()-start),flush=True)
   assert p.returncode==0
  text=old.read_text(errors='replace');assert 'JOB DONE.' in text;shutil.copy2(old,dest/old.name)
  cubes=[w/(label+'.cube')] if mode!='soc_on' else [w/(label+f'.dat_K{idx+1:03d}_B{band:03d}'+label+'.cube') for band in (first,last)]
  for cube in cubes:assert cube.is_file() and cube.stat().st_size>1000,(label,str(cube));shutil.copy2(cube,dest/cube.name)
  row={'mode':mode,'edge':name,'k_index':idx+1,'k_tpiba':rows[idx][0],'bands':[first,last],'cubes':[f.name for f in cubes],'scope':'SOC Kramers-pair pseudo-wavefunction densities saved separately; sum for pair density' if mode=='soc_on' else 'pseudo-wavefunction density scalar single orbital'};summary.append(row);print('RESULT',json.dumps(row),flush=True)
(dest/'edge_manifest.json').write_text(json.dumps(summary,indent=2));out=dest/'soc_scalar_edge_cubes.tar.gz'
with tarfile.open(out,'w:gz',compresslevel=3) as t:
 for f in dest.iterdir():
  if f.is_file() and f!=out and not f.name.endswith(('.live.out','.dat')):t.add(f,arcname=f.name)
print('ARCHIVE',json.dumps({'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}),flush=True)
