import numpy as np,tarfile,pathlib,json
p=pathlib.Path(r'E:\桌面\(C₇H₆NS)₂[SnCl₆]·2H₂O计算\02_计算任务\CPU_ORCA\ORC_C03_中性簇模型\orc_c03_neutral_nto_20261031')
roles=np.array(['inorganic']*7+['cation_1']*15+['cation_2']*15+['water']*6)
res={}
with tarfile.open(p/'nto_cubes_molden.tar.gz') as tar:
 for s in (1,2,3):
  for orb in (142,143):
   name=f'neutral_cluster_nto.s{s}.mo{orb}a.cube';f=tar.extractfile(name);f.readline();f.readline();head=f.readline().decode().split();signed_nat=int(head[0]);nat=abs(signed_nat);origin=np.array(list(map(float,head[1:4])));axes=[];counts=[]
   for i in range(3):
    row=f.readline().decode().split();counts.append(int(row[0]));axes.append(list(map(float,row[1:4])))
   axes=np.array(axes);coords=[]
   for i in range(nat):coords.append(list(map(float,f.readline().decode().split()[2:5])))
   assert nat==43
   if signed_nat<0:
    orbital_info=list(map(int,f.readline().decode().split()));assert orbital_info==[1,orb],orbital_info
   coords=np.array(coords);val=np.fromstring(f.read().decode('ascii'),sep=' ');assert val.size==np.prod(counts);dens=val.reshape(counts)**2
   dvol=abs(np.linalg.det(axes));row={'orbital':orb,'grid':counts,'integral_full_grid':float(dens.sum()*dvol),'partitions':{}}
   for stride in (2,1):
    ix=np.indices(tuple(len(range(0,n,stride)) for n in counts),dtype=np.int32).reshape(3,-1).T*stride;w=dens[ix[:,0],ix[:,1],ix[:,2]];out=np.zeros(len(ix),dtype=np.int32);norm=(coords*coords).sum(1)
    for start in range(0,len(ix),4000):
     pt=origin+ix[start:start+4000]@axes;d2=(pt*pt).sum(1)[:,None]+norm[None,:]-2*pt@coords.T;out[start:start+len(pt)]=np.argmin(d2,axis=1)
    row['partitions'][str(stride)]={role:float(w[roles[out]==role].sum()/w.sum()) for role in ('inorganic','cation_1','cation_2','water')}
   res[name]=row;print(name,json.dumps(row),flush=True)
(p/'nto_空间分区诊断.json').write_text(json.dumps({'results':res,'interpretation':'Each grid is the square of one dominant NTO orbital, partitioned by nearest nucleus. Finite box and grid, Voronoi boundaries, unembedded model, and other NTO pairs limit interpretation. This is not a transition density population or validated crystal mechanism.'},indent=2),encoding='utf8')
