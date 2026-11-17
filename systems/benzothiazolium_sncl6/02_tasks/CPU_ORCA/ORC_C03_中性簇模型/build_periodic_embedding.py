import pathlib,json,tarfile,re,math,itertools,collections
here=pathlib.Path(__file__).resolve().parent;root=here.parents[2];base=root/'02_计算任务';m=json.loads((base/'00_正式计算准备_20261030'/'周期晶胞_模型.json').read_text(encoding='utf-8'));v=m['cell_vectors_A'];old=m['atoms']
with tarfile.open(base/'GPU_QE'/'QE_G03_固定晶胞全原子优化'/'all_relax_results.tar.gz') as t:lines=t.extractfile('R_fixed_final_crystal.txt').read().decode().splitlines()[1:]
f=[list(map(float,l.split()[1:4])) for l in lines if l.strip()];atoms=[dict(a,frac=q,index=i) for i,(a,q) in enumerate(zip(old,f))];assert len(atoms)==43
with tarfile.open(base/'GPU_QE'/'QE_G04_电子结构'/'electronic_stage2_results.tar.gz') as t:pdos=t.extractfile('pdos.out').read().decode(errors='replace')
with tarfile.open(base/'GPU_QE'/'QE_G01_晶胞SCF试算'/'QE_G01_results.tar.gz') as t:
 metadata=json.loads(t.extractfile('pseudo_metadata.json').read());val={}
 for el,info in metadata.items():
  txt=t.extractfile('pseudo/'+info['file']).read().decode(errors='replace');match=re.search(r'z_valence\s*=\s*["\']\s*([\d.]+)',txt,re.I) or re.search(r'^\s*([\d.]+)\s+Z valence',txt,re.I|re.M);assert match,el;val[el]=float(match.group(1))
occ={}
for i,x in re.findall(r'Atom\s*#\s*(\d+):\s*total charge\s*=\s*([-\d.]+)',pdos):occ[int(i)-1]=float(x)
assert set(occ)==set(range(43))
for a in atoms:a['q_raw']=val[a['element']]-occ[a['index']]
excluded={'Sn01','Cl02','Cl03','Cl04','O007','H00F','H00G'}
groups=[[a for a in atoms if a['element'] in ('Sn','Cl')]]
for sym in ('identity','inversion'):
 groups.append([a for a in atoms if a['symmetry']==sym and a['label'].removesuffix('_inv') not in excluded])
for sym in ('identity','inversion'):
 groups.append([a for a in atoms if a['symmetry']==sym and a['label'].removesuffix('_inv') in {'O007','H00F','H00G'}])
assert [len(g) for g in groups]==[7,15,15,3,3]
target=[-2,1,1,0,0];shifts=list(itertools.product(range(-2,3),repeat=3))
def cart(f):return [sum(f[k]*v[k][j] for k in range(3)) for j in range(3)]
def add(f,s):return [f[k]+s[k] for k in range(3)]
def near(f,ref):return min(shifts,key=lambda s:math.dist(cart(add(f,s)),cart(ref)))
fragments=[]
for gi,(g,q) in enumerate(zip(groups,target)):
 anchor=next(a for a in g if a['element'] in ('Sn','N','O'));raw=sum(a['q_raw'] for a in g);corr=(q-raw)/len(g);frag=[]
 for a in g:frag.append({'el':a['element'],'frac':add(a['frac'],near(a['frac'],anchor['frac'])),'q':a['q_raw']+corr,'index':a['index'],'group':gi})
 fragments.append(frag)
xyz=(here/'neutral_cluster_43.xyz').read_text().splitlines()[2:];qm=[(s.split()[0],[float(v) for v in s.split()[1:4]]) for s in xyz if s.strip()];assert len(qm)==43
summaries=[]
for n in (1,2):
 pcs=[];removed=[]
 for shift in itertools.product(range(-n,n+1),repeat=3):
  for frag in fragments:
   points=[(a['q'],cart(add(a['frac'],shift)),a) for a in frag]
   flags=[any(a['el']==el and math.dist(pos,qp)<1e-5 for el,qp in qm) for q,pos,a in points]
   if any(flags):
    if not all(flags):raise RuntimeError('partial quantum fragment overlap')
    removed.extend(points);continue
   pcs.extend((q,pos,dict(a,translation=list(shift))) for q,pos,a in points)
 assert len(removed)==43,(n,len(removed))
 net=sum(q for q,pos,a in pcs);dmin=min(math.dist(pos,qp) for q,pos,a in pcs for el,qp in qm)
 assert abs(net)<1e-7 and dmin>1.0,(n,net,dmin)
 path=here/f'periodic_lowdin_shell{n}.pc';path.write_text(str(len(pcs))+'\n'+''.join(f'{q:.10f} '+ ' '.join(f'{x:.9f}' for x in pos)+'\n' for q,pos,a in pcs))
 (here/f'periodic_lowdin_shell{n}_atom_map.json').write_text(json.dumps([{'element':a['el'],'periodic_atom_index':a['index']+1,'fragment_group':a['group'],'translation':a['translation']} for q,pos,a in pcs],indent=2))
 summaries.append({'shell':n,'pointcharges':len(pcs),'net_charge':net,'nearest_qm_distance_A':dmin,'source':'QE projwfc Lowdin populations; per-fragment neutral-cell formal-charge correction','fragment_target_charges':target,'warning':'diagnostic fixed point charges; no polarization or Pauli repulsion; finite-cube boundary and population scheme sensitivity not yet tested'})
(here/'embedding_model_metadata.json').write_text(json.dumps({'valence_electrons':val,'raw_fragment_charges':[sum(a['q_raw'] for a in g) for g in groups],'models':summaries},indent=2));print(json.dumps(summaries))
