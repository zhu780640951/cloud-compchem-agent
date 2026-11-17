import tarfile,pathlib,json,re,numpy as np
root=pathlib.Path(r'E:\桌面\(C₇H₆NS)₂[SnCl₆]·2H₂O计算');p=root/'02_计算任务'/'GPU_QE'/'QE_G04_电子结构'/'优化结构收敛复核';model=json.loads((root/'02_计算任务'/'00_正式计算准备_20261030'/'周期晶胞_模型.json').read_text(encoding='utf8'));atoms=model['atoms'];assert len(atoms)==43
roles=[]
for a in atoms:
 tag=a['label'].removesuffix('_inv');roles.append('inorganic' if a['element'] in ('Sn','Cl') else ('water' if tag in ('O007','H00F','H00G') else 'organic'))
edges={'scalar_control':{'vbm':0.8446,'cbm':3.4830},'soc_on':{'vbm':0.8459,'cbm':3.4908}};out={}
with tarfile.open(p/'soc_pdos_pair_results.tar.gz') as t:
 for mode,ev in edges.items():
  sums={key:{} for key in ('vbm','cbm')};windows={'vbm':(ev['vbm']-.2,ev['vbm']),'cbm':(ev['cbm'],ev['cbm']+.2)};seen=set()
  for member in t.getmembers():
   m=re.fullmatch(re.escape(mode)+r'\.pdos_atm#(\d+)\(([^)]+)\)_wfc#\d+\(([spdf])(?:_j[\d.]+)?\)',member.name)
   if not m:continue
   i=int(m.group(1))-1;el=m.group(2);orb=m.group(3);assert 0<=i<43 and atoms[i]['element']==el;seen.add(i);f=t.extractfile(member);f.readline();a=np.loadtxt(f);assert a.ndim==2 and a.shape[1]>=2
   for key,(lo,hi) in windows.items():
    mask=(a[:,0]>=lo)&(a[:,0]<=hi);val=float(a[mask,1].sum()*.02);group=roles[i];sums[key][group]=sums[key].get(group,0)+val;sums[key][el+'-'+orb]=sums[key].get(el+'-'+orb,0)+val
  assert seen==set(range(43)),(mode,len(seen));q={}
  for key in ('vbm','cbm'):
   den=sum(sums[key].get(g,0) for g in ('organic','inorganic','water'));assert den>0
   q[key]={'window_eV':windows[key],'projection_sum':den,'fractions':{g:sums[key].get(g,0)/den for g in ('organic','inorganic','water')},'element_orbital_fractions':{g:v/den for g,v in sums[key].items() if '-' in g}}
  out[mode]=q;print(mode,json.dumps(q),flush=True)
(p/'SOC前后PDOS带边窗口对照.json').write_text(json.dumps({'results':out,'limits':'Finite energy windows, projection basis/normalization and smearing affect percentages; not charge transfer or excitation-state analysis; different corresponding pseudopotentials.'},ensure_ascii=False,indent=2),encoding='utf8')
