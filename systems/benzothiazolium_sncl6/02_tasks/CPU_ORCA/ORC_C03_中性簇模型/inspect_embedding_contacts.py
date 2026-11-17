import pathlib,math
p=pathlib.Path(__file__).parent
qm=[(x.split()[0],[float(z) for z in x.split()[1:4]]) for x in (p/'neutral_cluster_43.xyz').read_text().splitlines()[2:] if x.strip()]
pc=[[float(z) for z in x.split()] for x in (p/'periodic_lowdin_shell1.pc').read_text().splitlines()[1:] if x.strip()]
res=[]
for i,(el,pos) in enumerate(qm):
 for j,(q,x,y,z) in enumerate(pc):
  dist=math.dist(pos,(x,y,z))
  if dist<2.25:res.append((round(dist,4),i+1,el,j+1,round(q,4)))
print('contacts<2.25A:',sorted(res)[:30])