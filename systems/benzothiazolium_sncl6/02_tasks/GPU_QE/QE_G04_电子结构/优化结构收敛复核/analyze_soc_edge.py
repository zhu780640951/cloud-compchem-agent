import pathlib,tarfile,json,itertools,numpy as np
p=pathlib.Path(r'E:\桌面\(C₇H₆NS)₂[SnCl₆]·2H₂O计算\02_计算任务\GPU_QE\QE_G04_电子结构\优化结构收敛复核');root=p.parents[3];model=json.loads((root/'02_计算任务'/'00_正式计算准备_20261030'/'周期晶胞_模型.json').read_text(encoding='utf8'));atoms=model['atoms'];roles=[]
for a in atoms:
 tag=a['label'].removesuffix('_inv');roles.append('inorganic' if a['element'] in ('Sn','Cl') else ('water' if tag in ('O007','H00F','H00G') else 'organic'))
data={};meta={}
with tarfile.open(p/'soc_scalar_edge_cubes.tar.gz') as tar:
 m=json.load(tar.extractfile('edge_manifest.json'))
 for row in m:
  arrays=[]
  for name in row['cubes']:
   f=tar.extractfile(name);f.readline();f.readline();head=f.readline().decode().split();nat=int(head[0]);origin=np.array(list(map(float,head[1:4])));axes=[];counts=[]
   for i in range(3):
    q=f.readline().decode().split();counts.append(int(q[0]));axes.append(list(map(float,q[1:4])))
   coords=[];els=[]
   for i in range(nat):
    q=f.readline().decode().split();els.append(int(q[0]));coords.append(list(map(float,q[2:5])))
   assert nat==43;values=np.fromstring(f.read().decode('ascii'),sep=' ');assert values.size==np.prod(counts);arrays.append(values.reshape(counts))
  density=sum(arrays);key=row['mode']+'_'+row['edge'];data[key]=density;meta[key]=(origin,np.array(axes),np.array(coords),counts,els)
result={}
for key,density in data.items():
 origin,axes,coords,counts,els=meta[key];assert els==[{'H':1,'C':6,'N':7,'O':8,'S':16,'Cl':17,'Sn':50}[a['element']] for a in atoms];cell=axes*np.array(counts)[:,None];inv=np.linalg.inv(cell);frac=((coords-origin)@inv)%1;corners=np.array([origin+np.array(x)@cell for x in itertools.product((0,1),repeat=3)]);low=corners.min(0)-6;high=corners.max(0)+6;images=[];image_roles=[]
 for shift in itertools.product((-1,0,1),repeat=3):
  xyz=origin+(frac+np.array(shift))@cell
  for i,x in enumerate(xyz):
   if np.all(x>=low) and np.all(x<=high):images.append(x);image_roles.append(roles[i])
 images=np.array(images);image_roles=np.array(image_roles);norm=(images*images).sum(1);per={}
 for stride in (3,2):
  ix=np.indices(tuple(len(range(0,n,stride)) for n in counts),dtype=np.int32).reshape(3,-1).T*stride;weights=density[ix[:,0],ix[:,1],ix[:,2]];nearest=np.empty(len(ix),dtype=np.int32)
  for start in range(0,len(ix),4000):
   pos=origin+ix[start:start+4000]@axes;dist=(pos*pos).sum(1)[:,None]+norm[None,:]-2*pos@images.T;nearest[start:start+len(pos)]=np.argmin(dist,axis=1)
  per[str(stride)]={r:float(weights[image_roles[nearest]==r].sum()/weights.sum()) for r in ('organic','inorganic','water')}
 result[key]={'grid':counts,'sampled_components':per,'min_density':float(density.min()),'density_integral':float(density.sum()*abs(np.linalg.det(axes)))};print(key,result[key],flush=True)
out={'results':result,'caveats':'Nearest-nucleus partition with periodic images; finite-grid subsampling; SOC includes summed degenerate pair, scalar a single state. Projector/pseudopotential differences and partition boundaries limit precision. Not excited-state or charge transfer density.'};(p/'SOC前后带边空间分区.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
