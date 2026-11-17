import pathlib,json,tarfile,itertools,math,collections
root=pathlib.Path(__file__).resolve().parents[3];out=pathlib.Path(__file__).resolve().parent
model=json.loads((root/'02_计算任务'/'00_正式计算准备_20261030'/'周期晶胞_模型.json').read_text(encoding='utf-8'));v=model['cell_vectors_A'];old=model['atoms']
with tarfile.open(root/'02_计算任务'/'GPU_QE'/'QE_G03_固定晶胞全原子优化'/'all_relax_results.tar.gz') as tar:
 lines=tar.extractfile('R_fixed_final_crystal.txt').read().decode().splitlines()[1:]
new=[[float(z) for z in line.split()[1:4]] for line in lines if line.strip()];assert len(new)==43
atoms=[dict(a,frac=x) for a,x in zip(old,new)]
exclude={'Sn01','Cl02','Cl03','Cl04','O007','H00F','H00G'}
a=[x for x in atoms if x['symmetry']=='identity' and x['label'] not in exclude];b=[x for x in atoms if x['symmetry']=='inversion' and x['label'].removesuffix('_inv') not in exclude]
assert len(a)==len(b)==15 and collections.Counter(x['element'] for x in a)=={'C':7,'H':6,'N':1,'S':1}
def cart(f):return [sum(f[k]*v[k][j] for k in range(3)) for j in range(3)]
def unwrap(group):
 anchor=next(x['frac'] for x in group if x['element']=='N');out=[]
 for x in group:
  f=x['frac'];shift=min(itertools.product(range(-1,2),repeat=3),key=lambda z:sum(q*q for q in cart([f[k]+z[k]-anchor[k] for k in range(3)])))
  out.append((x['element'],[f[k]+shift[k] for k in range(3)]))
 return out
a=unwrap(a);b=unwrap(b)
def center(g):
 q=[cart(f) for e,f in g if e in ('C','N','S')];return [sum(x[j] for x in q)/len(q) for j in range(3)]
ca=center(a);candidates=[]
for shift in itertools.product(range(-2,3),repeat=3):
 trans=[(e,[f[k]+shift[k] for k in range(3)]) for e,f in b];cb=center(trans);dist=math.dist(ca,cb);candidates.append((dist,shift,trans))
candidates.sort(key=lambda x:x[0]);selected=[]
for x in candidates:
 if not selected or abs(x[0]-selected[-1][0])>0.04:selected.append(x)
 if len(selected)==2:break
assert len(selected)==2 and selected[1][0]<6
meta=[]
for idx,(dist,shift,bb) in enumerate(selected,1):
 allcoords=a+bb;xyz=''.join(e+' '+' '.join(f'{z:.9f}' for z in cart(f))+'\n' for e,f in allcoords)
 label=f'dimer_{idx}';(out/(label+'.xyz')).write_text('30\nCrystal geometry, charge +2, no embedding; diagnostic reference\n'+xyz)
 inp='! PBE0 def2-SVP def2/J RIJCOSX TightSCF\n%pal nprocs 12 end\n%maxcore 4000\n%scf ConvCheckMode 0 MaxIter 200 end\n%tddft nroots 10 tda true triplets true end\n* xyz 2 1\n'+xyz+'*\n'
 (out/(label+'.inp')).write_text(inp);meta.append({'id':label,'centroid_distance_A':dist,'translation':shift,'charge':2,'atoms':30,'environment':'vacuum diagnostic, not crystal embedded','source':'fixed-cell optimized geometry'})
(out/'model_metadata.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta))