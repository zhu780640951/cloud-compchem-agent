import pathlib,math,json
p=pathlib.Path(__file__).parent
qm=[(x.split()[0],[float(z) for z in x.split()[1:4]]) for x in (p/'neutral_cluster_43.xyz').read_text().splitlines()[2:] if x.strip()]
def load(n):return [[float(z) for z in x.split()] for x in (p/f'periodic_lowdin_shell{n}.pc').read_text().splitlines()[1:] if x.strip()]
a=load(1); water_oxygens=[]
for j,(q,x,y,z) in enumerate(a):
 if q<=0:continue
 if any(el=='O' and math.dist(pos,(x,y,z))<1.8 for el,pos in qm):
  candidates=[(math.dist((x,y,z),r[1:4]),k) for k,r in enumerate(a) if r[0]<-0.3 and math.dist((x,y,z),r[1:4])<1.2]
  if candidates:
   k=min(candidates)[1]
   if k not in water_oxygens:water_oxygens.append(k)
assert len(water_oxygens)==2,water_oxygens
promoted=[]
for oi in water_oxygens:
 o=a[oi];h=sorted([(math.dist(o[1:4],r[1:4]),k) for k,r in enumerate(a) if r[0]>0 and math.dist(o[1:4],r[1:4])<1.2])
 assert len(h)==2,(oi,h)
 promoted.extend([('O',o[1:4],o[0])]+[('H',a[k][1:4],a[k][0]) for _,k in h])
assert len(promoted)==6
newqm=qm+[(e,x) for e,x,q in promoted];(p/'expanded_cluster_49.xyz').write_text('49\nNeutral diagnostic cluster; two boundary water molecules promoted; fixed crystal geometry\n'+''.join(e+' '+' '.join(f'{z:.9f}' for z in x)+'\n' for e,x in newqm))
summary=[]
for n in (1,2):
 pc=load(n);kept=[];removed=[]
 for q,x,y,z in pc:
  if any(math.dist((x,y,z),a)<1e-5 for el,a,qq in promoted):removed.append((q,x,y,z))
  else:kept.append((q,x,y,z))
 assert len(removed)==6
 net=sum(q for q,x,y,z in kept);dmin=min(math.dist((x,y,z),pos) for q,x,y,z in kept for el,pos in newqm)
 positive_min=min(math.dist((x,y,z),pos) for q,x,y,z in kept if q>0 for el,pos in newqm)
 (p/f'expanded_shell{n}.pc').write_text(str(len(kept))+'\n'+''.join(f'{q:.10f} {x:.9f} {y:.9f} {z:.9f}\n' for q,x,y,z in kept))
 summary.append({'shell':n,'pointcharges':len(kept),'net_charge':net,'nearest_any_A':dmin,'nearest_positive_A':positive_min,'promoted_atom_count':len(promoted)})
(p/'expanded_metadata.json').write_text(json.dumps({'models':summary,'promoted_waters':promoted,'purpose':'diagnostic; QM boundary enlarged to include two nearest water molecules; not validated embedding'},indent=2));print(json.dumps(summary))