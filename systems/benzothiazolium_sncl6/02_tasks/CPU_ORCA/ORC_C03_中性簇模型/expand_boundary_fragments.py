import pathlib,math,json,collections
p=pathlib.Path(__file__).parent
qm=[(x.split()[0],[float(z) for z in x.split()[1:4]]) for x in (p/'neutral_cluster_43.xyz').read_text().splitlines()[2:] if x.strip()]
def load(n):
 raw=[[float(z) for z in x.split()] for x in (p/f'periodic_lowdin_shell{n}.pc').read_text().splitlines()[1:] if x.strip()];meta=json.loads((p/f'periodic_lowdin_shell{n}_atom_map.json').read_text());assert len(raw)==len(meta);return [(a,m) for a,m in zip(raw,meta)]
small=load(1);keys=set()
for (q,x,y,z),m in small:
 if min(math.dist((x,y,z),r) for el,r in qm)<1.8:keys.add((m['fragment_group'],tuple(m['translation'])))
print('promote_groups',keys);assert len(keys)==4
selected=[(row,m) for row,m in small if (m['fragment_group'],tuple(m['translation'])) in keys]
assert len(selected)==36,len(selected)
added=[(m['element'],row[1:4]) for row,m in selected];newqm=qm+added;assert len(newqm)==79
qadded=sum(row[0] for row,m in selected);assert abs(qadded-2)<1e-6,qadded
(p/'expanded_cluster_79.xyz').write_text('79\nQuantum cluster +2; four boundary fragments added; crystal geometry; diagnostic\n'+''.join(e+' '+' '.join(f'{z:.9f}' for z in x)+'\n' for e,x in newqm))
summary=[]
for n in (1,2):
 pc=load(n);removed=[x for x in pc if (x[1]['fragment_group'],tuple(x[1]['translation'])) in keys];kept=[x for x in pc if (x[1]['fragment_group'],tuple(x[1]['translation'])) not in keys];assert len(removed)==36
 net=sum(row[0] for row,m in kept);near=min(math.dist(row[1:4],q) for row,m in kept for e,q in newqm);pos=min(math.dist(row[1:4],q) for row,m in kept if row[0]>0 for e,q in newqm);assert abs(net+2)<1e-6
 (p/f'expanded79_shell{n}.pc').write_text(str(len(kept))+'\n'+''.join(' '.join(f'{v:.10f}' for v in row)+'\n' for row,m in kept))
 summary.append({'shell':n,'qm_atoms':79,'qm_charge':2,'embedding_net_charge':net,'pointcharges':len(kept),'nearest_A':near,'nearest_positive_A':pos})
(p/'expanded79_metadata.json').write_text(json.dumps({'models':summary,'promoted_fragment_keys':sorted(keys),'boundary_warning':'No Pauli repulsion for external charges; further near contacts may remain. Diagnostic only.'},indent=2));print(json.dumps(summary))