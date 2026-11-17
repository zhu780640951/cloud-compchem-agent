import pathlib,tarfile,json,re,csv,numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
out=pathlib.Path(r'C:\Users\y\Documents\Codex\2026-10-30\wo\outputs\QE_图件整理')
archive=out/'standard_bands_segments.tar.gz'
ref=pathlib.Path(r'E:\桌面\(C₇H₆NS)₂[SnCl₆]·2H₂O计算\02_计算任务\GPU_QE\QE_G04_电子结构\electronic_stage2_results.tar.gz')
with tarfile.open(ref) as t:inp=t.extractfile('optimized_scf.in').read().decode()
cell=np.array([list(map(float,l.split()[:3])) for l in inp.split('CELL_PARAMETERS angstrom\n')[1].split('ATOMIC_POSITIONS crystal\n')[0].splitlines() if l.strip()]);alat=np.linalg.norm(cell[0]); reciprocal=2*np.pi*np.linalg.inv(cell).T
pat=r'k\s*=\s*([-+]?\d+\.\d+)\s*([-+]?\d+\.\d+)\s*([-+]?\d+\.\d+)\s*\(\s*\d+\s+PWs\)\s+bands \(ev\):'
fig,ax=plt.subplots(figsize=(6.5,4.1),layout='constrained'); allrows=[];ticks=[0.0];labels=[r'$\Gamma$'];x0=0.;vbm=.8463
with tarfile.open(archive) as t:
 manifest=json.load(t.extractfile('path_manifest.json'));path=manifest['path'];coords=manifest['point_coords']; assert len(path)==7
 for ix,(a,b) in enumerate(path,1):
  status=json.load(t.extractfile(f'segment_{ix:02d}.status.json'));assert status['done'] and status['gpu_active'] and not status['time_limit']
  text=t.extractfile(f'segment_{ix:02d}.out').read().decode(errors='replace');assert 'JOB DONE.' in text
  ms=list(re.finditer(pat,text,re.I));assert len(ms)==25,(ix,len(ms)); data=[];actual=[]
  for m in ms:
   vals=[]
   for line in text[m.end():].splitlines():
    if not line.strip():
     if vals:break
     continue
    if re.fullmatch(r'[\s+\-\d\.Ee]+',line):vals.extend(map(float,line.split()))
    elif vals:break
   assert len(vals)==105,(ix,len(vals));data.append(vals);actual.append(list(map(float,m.groups())))
  frac=np.linspace(coords[a],coords[b],25);expected=frac@np.linalg.inv(cell).T*alat;assert np.allclose(actual,expected,atol=8e-5),(ix,np.max(np.abs(np.array(actual)-expected)))
  dist=np.linalg.norm(np.diff(frac@reciprocal,axis=0),axis=1);xx=x0+np.r_[0,np.cumsum(dist)]; data=np.array(data)
  for band in range(105):ax.plot(xx,data[:,band]-vbm,color='#315b91',lw=.8)
  for j in range(25):
   for band in range(105):allrows.append([ix,a,b,j+1,*frac[j],xx[j],band+1,data[j,band],data[j,band]-vbm])
  x0=xx[-1];ticks.append(x0)
  def lab(q):return r'$\Gamma$' if q=='GAMMA' else q
  labels.append(lab(b) if ix==len(path) or path[ix][0]==b else lab(b)+' | '+lab(path[ix][0]))
ax.axhline(0,color='#777777',ls='--',lw=.7)
for x in ticks:ax.axvline(x,color='#c5c5c5',lw=.5)
ax.set(xticks=ticks,xticklabels=labels,xlim=(0,x0),ylim=(-4,6),ylabel='Energy − sampled VBM (eV)',xlabel=r'Wave vector along path ($\AA^{-1}$)');ax.set_title('Scalar-relativistic band structure',loc='left',fontsize=10)
ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False);plt.rcParams.update({'pdf.fonttype':42,'svg.fonttype':'none'})
for fmt in ('png','pdf','svg'):fig.savefig(out/('标准路径能带.'+fmt),dpi=220)
with (out/'标准路径能带数据.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['segment','start','end','point','k1_frac','k2_frac','k3_frac','path_A_inv','band_1based','energy_eV','energy_minus_vbm_eV']);w.writerows(allrows)
print('verified 7 segments, 175 k-points, 105 bands, reciprocal coordinate agreement; rows',len(allrows))
