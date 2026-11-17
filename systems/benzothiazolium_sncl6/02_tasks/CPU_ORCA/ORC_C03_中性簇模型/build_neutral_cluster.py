import pathlib,json,tarfile,itertools,math,collections
root=pathlib.Path(__file__).resolve().parents[3];out=pathlib.Path(__file__).parent
model=json.loads((root/'02_计算任务'/'00_正式计算准备_20261030'/'周期晶胞_模型.json').read_text(encoding='utf-8'));v=model['cell_vectors_A'];old=model['atoms']
with tarfile.open(root/'02_计算任务'/'GPU_QE'/'QE_G03_固定晶胞全原子优化'/'all_relax_results.tar.gz') as tar:lines=tar.extractfile('R_fixed_final_crystal.txt').read().decode().splitlines()[1:]
new=[[float(z) for z in l.split()[1:4]] for l in lines if l.strip()];atoms=[dict(a,frac=f) for a,f in zip(old,new)];assert len(atoms)==43
shifts=list(itertools.product(range(-2,3),repeat=3))
def cart(f):return [sum(f[k]*v[k][j] for k in range(3)) for j in range(3)]
def add(f,s):return [f[k]+s[k] for k in range(3)]
def nearest(f,ref):return min(shifts,key=lambda s:math.dist(cart(add(f,s)),cart(ref)))
def unwrap(group,anchor_el):
 anchor=next(x['frac'] for x in group if x['element']==anchor_el)
 return [(x['element'],add(x['frac'],nearest(x['frac'],anchor)),x['label']) for x in group]
def center(group):
 h=[f for e,f,l in group if e!='H'];return [sum(q[k] for q in h)/len(h) for k in range(3)]
sn=next(x for x in atoms if x['element']=='Sn');ref=sn['frac'];parts=[('Sn',ref,sn['label'])]
for x in atoms:
 if x['element']=='Cl':parts.append(('Cl',add(x['frac'],nearest(x['frac'],ref)),x['label']))
excluded={'Sn01','Cl02','Cl03','Cl04','O007','H00F','H00G'}
organics=[];waters=[]
for sym in ('identity','inversion'):
 group=[x for x in atoms if x['symmetry']==sym and x['label'].removesuffix('_inv') not in excluded];assert len(group)==15
 organics.append(unwrap(group,'N'))
 wat=[x for x in atoms if x['symmetry']==sym and x['label'].removesuffix('_inv') in {'O007','H00F','H00G'}];assert len(wat)==3
 waters.append(unwrap(wat,'O'))
def choose(groups,num):
 cs=[]
 for gi,g in enumerate(groups):
  c=center(g)
  for s in shifts:cs.append((math.dist(cart(add(c,s)),cart(ref)),gi,s,g))
 cs.sort(key=lambda q:q[0]);return cs[:num]
org=choose(organics,2);wat=choose(waters,2)
for _,gi,s,g in org+wat:parts.extend((e,add(f,s),label) for e,f,label in g)
counts=collections.Counter(e for e,f,l in parts);assert counts=={'C':14,'H':16,'N':2,'S':2,'Sn':1,'Cl':6,'O':2}
coords=[(e,cart(f),l) for e,f,l in parts];short=[]
for i,(e,a,l) in enumerate(coords):
 for e2,b,l2 in coords[:i]:
  if math.dist(a,b)<0.7:short.append([l,l2,math.dist(a,b)])
assert not short,short
xyz=''.join(e+' '+' '.join(f'{x:.9f}' for x in pos)+'\n' for e,pos,l in coords)
(out/'neutral_cluster_43.xyz').write_text('43\nNeutral unembedded quantum cluster; +1+1-2, crystal geometry; diagnostic only\n'+xyz)
meta={'atoms':43,'formal_charge':0,'multiplicity':1,'counts':dict(counts),'organic_centroid_distances_A':[x[0] for x in org],'water_O_distances_A':[x[0] for x in wat],'org_sym_and_shifts':[(x[1],x[2]) for x in org],'water_sym_and_shifts':[(x[1],x[2]) for x in wat],'coordinates_origin':'fixed-cell relaxed geometry','embedding':'none; boundary and electrostatic environment require future validation','short_contacts_lt_0_7_A':short}
(out/'model_metadata.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta))