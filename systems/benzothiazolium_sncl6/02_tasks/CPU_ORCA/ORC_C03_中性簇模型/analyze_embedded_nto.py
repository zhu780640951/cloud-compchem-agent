import pathlib,tarfile,json,numpy as np,hashlib
p=pathlib.Path(r'E:\桌面\(C₇H₆NS)₂[SnCl₆]·2H₂O计算\02_计算任务\CPU_ORCA\ORC_C03_中性簇模型');a=p/'embedded_nto_grids_20261031.tar.gz'
meta=json.loads((p/'expanded79_metadata.json').read_text());keys={(x[0],tuple(x[1])) for x in meta['promoted_fragment_keys']};mapped=json.loads((p/'periodic_lowdin_shell1_atom_map.json').read_text());prom=[x for x in mapped if (x['fragment_group'],tuple(x['translation'])) in keys];assert len(prom)==36
roles=np.array(['inorganic']*7+['organic']*30+['water']*6+[('organic' if x['fragment_group'] in (1,2) else 'water') for x in prom]);assert len(roles)==79
data={};gridmeta={};result={}
with tarfile.open(a) as t:
 for shell in (1,2):
  for state in (1,2,3):
   for orb in (222,223):
    name=f'shell{shell}/resume_shell1.s{state}.mo{orb}a.cube';f=t.extractfile(name);f.readline();f.readline();h=f.readline().decode().split();signed=int(h[0]);assert abs(signed)==79;origin=np.array(list(map(float,h[1:4])));axes=[];counts=[]
    for _ in range(3):
     q=f.readline().decode().split();counts.append(int(q[0]));axes.append(list(map(float,q[1:4])))
    axes=np.array(axes);coords=np.array([list(map(float,f.readline().decode().split()[2:5])) for _ in range(79)])
    if signed<0:assert list(map(int,f.readline().decode().split()))==[1,orb]
    v=np.fromstring(f.read().decode('ascii'),sep=' ');assert v.size==np.prod(counts);v=v.reshape(counts);data[shell,state,orb]=v;gridmeta[shell,state,orb]=(origin,axes,coords,counts)
    norm=float((v*v).sum()*abs(np.linalg.det(axes)));idx=np.indices(counts,dtype=np.int32).reshape(3,-1).T;weight=(v*v).ravel();nearest=np.empty(len(idx),dtype=np.int32);c2=(coords*coords).sum(1)
    for start in range(0,len(idx),4000):
     pos=origin+idx[start:start+4000]@axes;dist=(pos*pos).sum(1)[:,None]+c2[None,:]-2*pos@coords.T;nearest[start:start+len(pos)]=np.argmin(dist,axis=1)
    parts={k:float(weight[roles[nearest]==k].sum()/weight.sum()) for k in ('organic','inorganic','water')};result[name]={'integral':norm,'fractions':parts};print(name,norm,parts,flush=True)
overlaps={}
for state in (1,2,3):
 for orb in (222,223):
  m1=gridmeta[1,state,orb];m2=gridmeta[2,state,orb];assert m1[3]==m2[3] and all(np.allclose(m1[i],m2[i],atol=1e-6) for i in (0,1,2));x=data[1,state,orb].ravel();y=data[2,state,orb].ravel();overlaps[f's{state}_orb{orb}']=float(abs(x@y)/np.sqrt((x@x)*(y@y)))
out={'archive_sha256':hashlib.sha256(a.read_bytes()).hexdigest(),'partitions':result,'cross_shell_absolute_orbital_overlaps':overlaps,'limits':'Nearest-nucleus Voronoi partition and finite grid, only dominant NTO pair; overlap is orbital overlap, not full transition-density or state overlap. Embedding has fixed charges, no Pauli repulsion or polarization.'}
(p/'嵌入簇NTO空间对照.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8');print('OVERLAPS',overlaps)
