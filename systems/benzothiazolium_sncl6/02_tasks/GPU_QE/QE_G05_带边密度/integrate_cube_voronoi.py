import pathlib,tarfile,json,itertools,numpy as np,time
p=pathlib.Path(__file__).parent;root=p.parents[2]
model=json.loads((root/'02_计算任务'/'00_正式计算准备_20261030'/'周期晶胞_模型.json').read_text(encoding='utf-8'));labels=model['atoms'];assert len(labels)==43
roles=[]
for a in labels:
 tag=a['label'].removesuffix('_inv');roles.append('inorganic' if a['element'] in ('Sn','Cl') else ('water' if tag in ('O007','H00F','H00G') else 'organic'))
results={}
with tarfile.open(p/'edge_density_results.tar.gz') as tar:
 for name in ('VBM','CBM'):
  f=tar.extractfile(name+'.cube');f.readline();f.readline();head=f.readline().decode().split();nat=int(head[0]);origin=np.array(list(map(float,head[1:4])));axes=[];counts=[]
  for _ in range(3):
   row=f.readline().decode().split();counts.append(int(row[0]));axes.append(list(map(float,row[1:4])))
  axes=np.array(axes);coords=[];els=[]
  for _ in range(nat):
   q=f.readline().decode().split();els.append(int(q[0]));coords.append(list(map(float,q[2:5])))
  assert nat==43 and len(coords)==43
  expected={'H':1,'C':6,'N':7,'O':8,'S':16,'Cl':17,'Sn':50};assert els==[expected[a['element']] for a in labels]
  values=np.fromstring(f.read().decode('ascii'),sep=' ');assert values.size==np.prod(counts)
  density=values.reshape(counts);cell=axes*np.array(counts)[:,None];inv=np.linalg.inv(cell);fractional=(np.array(coords)-origin)@inv;fractional%=1
  corners=np.array([origin+np.array(z)@cell for z in itertools.product((0,1),repeat=3)]);low=corners.min(0)-6;high=corners.max(0)+6
  images=[];image_roles=[]
  for shift in itertools.product((-1,0,1),repeat=3):
   xyz=origin+(fractional+np.array(shift))@cell
   for i,x in enumerate(xyz):
    if np.all(x>=low) and np.all(x<=high):images.append(x);image_roles.append(roles[i])
  images=np.array(images);sums={};
  for stride in (3,2):
   grid=np.indices(tuple(len(range(0,n,stride)) for n in counts),dtype=np.int32).reshape(3,-1).T*stride
   weights=density[grid[:,0],grid[:,1],grid[:,2]];out=np.zeros(len(grid),dtype=np.int32);norm=(images*images).sum(axis=1)
   for start in range(0,len(grid),4000):
    pt=origin+grid[start:start+4000]@axes;d2=(pt*pt).sum(1)[:,None]+norm[None,:]-2*(pt@images.T);out[start:start+len(pt)]=np.argmin(d2,axis=1)
   denom=float(weights.sum());part={g:float(weights[np.array([image_roles[i]==g for i in out])].sum()/denom) for g in ('organic','inorganic','water')};sums[str(stride)]={'fractions':part,'samples':len(grid),'sampled_density_sum':denom};print(name,stride,part,flush=True)
  results[name]={'k_state':name,'grid':counts,'classification':'nearest atomic center in periodic cartesian distance, assigned by component; no chemical partition','values':sums,'caveats':'approximate real-space Voronoi partition of pseudo-state density, individual k/band; grid subsampling and choice of boundary affect quantitative fractions; not excited electron/hole'}
(p/'带边空间分区诊断.json').write_text(json.dumps(results,indent=2));print('DONE')