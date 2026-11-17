"""Read-only structural audit of the supplied P -1 CIF; Python standard library."""
from pathlib import Path
import math, re, json, itertools, collections, hashlib

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / '00_原始结构' / '苯并噻唑SnCl4.cif'
raw = SOURCE.read_bytes()
text = raw.decode('utf-8-sig')
lines = text.splitlines()
def num(s): return float(re.sub(r'\([^)]*\)', '', s))
def scalar(key):
    for line in lines:
        if line.startswith(key+' '): return line[len(key):].strip().strip("'\"")
    raise KeyError(key)
def add(a,b): return [x+y for x,y in zip(a,b)]
def sub(a,b): return [x-y for x,y in zip(a,b)]
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def scale(a,s): return [x*s for x in a]
def norm(a): return math.sqrt(dot(a,a))
def cross(a,b): return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def angle(a,b): return math.degrees(math.acos(max(-1,min(1,dot(a,b)/norm(a)/norm(b)))))
a,b,c = [num(scalar('_cell_length_'+k)) for k in 'abc']
alpha,beta,gamma = [math.radians(num(scalar('_cell_angle_'+k))) for k in ['alpha','beta','gamma']]
cx=c*math.cos(beta)
cy=c*(math.cos(alpha)-math.cos(beta)*math.cos(gamma))/math.sin(gamma)
cell=[[a,0,0],[b*math.cos(gamma),b*math.sin(gamma),0],[cx,cy,math.sqrt(c*c-cx*cx-cy*cy)]]
def cart(f): return [sum(f[i]*cell[i][j] for i in range(3)) for j in range(3)]
start=lines.index('  _atom_site_label')
headers=[]
i=start
while lines[i].strip().startswith('_'):
    headers.append(lines[i].strip()); i+=1
asym=[]
while lines[i].strip():
    values=lines[i].split()
    if len(values)!=len(headers): raise ValueError(lines[i])
    d=dict(zip(headers,values))
    asym.append({'label':d['_atom_site_label'],'element':d['_atom_site_type_symbol'],
                 'frac':[num(d['_atom_site_fract_'+k]) for k in 'xyz'],
                 'occupancy':num(d['_atom_site_occupancy'])})
    i+=1
assert scalar('_space_group_IT_number')=='2'
atoms=[]
for at in asym:
    for sign,op in [(1,'identity'),(-1,'inversion')]:
        f=[(sign*v)%1 for v in at['frac']]
        if any(at['element']==p['element'] and max(abs((u-v+0.5)%1-0.5) for u,v in zip(f,p['frac']))<1e-7 for p in atoms): continue
        atoms.append({**at,'label':at['label']+('_inv' if sign==-1 else ''),'frac':f,'symmetry':op})
translations=list(itertools.product(range(-2,3),repeat=3))
def neighbors(at, elements, cutoff):
    result=[]
    for other in atoms:
        if other['element'] not in elements: continue
        for t in translations:
            vec=cart(sub(add(other['frac'],t),at['frac']))
            d=norm(vec)
            if 1e-7<d<cutoff: result.append({'label':other['label'],'element':other['element'],'shift':t,'distance':d,'vector':vec,'atom':other})
    return sorted(result,key=lambda r:r['distance'])
sn=next(p for p in atoms if p['element']=='Sn')
sncl=neighbors(sn,{'Cl'},3.2)
assert len(sncl)==6
cis=[]; trans=[]
for x,y in itertools.combinations(sncl,2):
    theta=angle(x['vector'],y['vector'])
    (trans if theta>150 else cis).append(theta)
lengths=[p['distance'] for p in sncl]
mean=sum(lengths)/6
hb=[]
for donor in atoms:
    if donor['element'] not in {'N','O'}: continue
    for h in neighbors(donor,{'H'},1.15):
        # Build the hydrogen in the same periodic image as its donor.
        hf=add(h['atom']['frac'],h['shift'])
        hh={**h['atom'],'frac':hf}
        for acc in neighbors(hh,{'N','O','Cl','S'},3.1):
            af=add(acc['atom']['frac'],acc['shift'])
            da=norm(cart(sub(af,donor['frac'])))
            theta=angle(scale(h['vector'],-1),acc['vector'])
            if da<3.8 and theta>=120:
                hb.append({'donor':donor['label'],'H':h['label'],'acceptor':acc['label'],
                           'acceptor_shift_relative_to_H_cell':acc['shift'],'D_H_Angstrom':h['distance'],
                           'H_A_Angstrom':acc['distance'],'D_A_Angstrom':da,'D_H_A_angle_deg':theta})
# All nine fused-ring heavy atoms in the unwrapped asymmetric unit.
ring=[p for p in asym if p['element'] in {'C','N','S'}]
ringcart=[cart(p['frac']) for p in ring]
centroid=scale([sum(p[j] for p in ringcart) for j in range(3)],1/len(ringcart))
normal=cross(sub(ringcart[1],ringcart[0]),sub(ringcart[2],ringcart[0]))
normal=scale(normal,1/norm(normal))
# Jacobi diagonalization of the symmetric 3x3 covariance: least-squares plane.
cov=[[sum((p[j]-centroid[j])*(p[k]-centroid[k]) for p in ringcart) for k in range(3)] for j in range(3)]
eigvec=[[float(j==k) for k in range(3)] for j in range(3)]
for _ in range(50):
    j,k=max([(0,1),(0,2),(1,2)],key=lambda jk:abs(cov[jk[0]][jk[1]]))
    if abs(cov[j][k])<1e-14: break
    phi=0.5*math.atan2(2*cov[j][k],cov[k][k]-cov[j][j])
    co,si=math.cos(phi),math.sin(phi)
    rot=[[float(u==v) for v in range(3)] for u in range(3)]
    rot[j][j]=rot[k][k]=co;rot[j][k]=si;rot[k][j]=-si
    tmp=[[sum(cov[u][w]*rot[w][v] for w in range(3)) for v in range(3)] for u in range(3)]
    cov=[[sum(rot[w][u]*tmp[w][v] for w in range(3)) for v in range(3)] for u in range(3)]
    eigvec=[[sum(eigvec[u][w]*rot[w][v] for w in range(3)) for v in range(3)] for u in range(3)]
imin=min(range(3),key=lambda j:cov[j][j])
normal=[eigvec[j][imin] for j in range(3)]
planarity=max(abs(dot(sub(p,centroid),normal)) for p in ringcart)
stack=[]
for sign in [1,-1]:
    for t in translations:
        if sign==1 and t==(0,0,0): continue
        other=add(scale(centroid,sign),cart(t))
        v=sub(other,centroid); dist=norm(v)
        if dist<7:
            height=abs(dot(v,normal)); offset=math.sqrt(max(0,dist*dist-height*height))
            stack.append({'symmetry':'identity' if sign==1 else 'inversion','shift':t,'centroid_distance_A':dist,'plane_distance_A':height,'lateral_offset_A':offset})
stack.sort(key=lambda p:p['centroid_distance_A'])
counts=dict(collections.Counter(p['element'] for p in atoms))
volume=abs(dot(cell[0],cross(cell[1],cell[2])))
result={'source':str(SOURCE),'sha256':hashlib.sha256(raw).hexdigest(),
        'method':'Standard-library parser for this CIF atom-site loop; P -1 identity/inversion explicitly expanded and deduplicated; neighboring cells searched over [-2,2]^3; not a checkCIF or electronic-structure calculation.',
        'formula':scalar('_chemical_formula_sum'),'space_group':scalar('_space_group_name_H-M_alt'),
        'cell_A_deg':{'a':a,'b':b,'c':c,'alpha':math.degrees(alpha),'beta':math.degrees(beta),'gamma':math.degrees(gamma)},
        'cell_vectors_A':cell,'volume_A3':volume,'Z':int(scalar('_cell_formula_units_Z')),
        'temperature_K':num(scalar('_diffrn_ambient_temperature')),
        'asymmetric_unit_sites':len(asym),'expanded_counts':counts,'expanded_natoms':len(atoms),
        'all_occupancy_one':all(p['occupancy']==1 for p in asym),
        'sn_cl_distances_A':lengths,'sn_cl_mean_A':mean,'sn_cl_distortion_delta':sum(((d-mean)/mean)**2 for d in lengths)/6,
        'cis_angles_deg':sorted(cis),'cis_angle_variance_deg2':sum((v-90)**2 for v in cis)/11,
        'trans_angles_deg':trans,'nearest_sn_sn_A':neighbors(sn,{'Sn'},12)[0]['distance'],
        'sn_NOS_within_4A':[{k:v for k,v in p.items() if k not in {'atom','vector'}} for p in neighbors(sn,{'N','O','S'},4)],
        'sn_cl_beyond_first_six_A':[p['distance'] for p in neighbors(sn,{'Cl'},6)[6:10]],
        'hydrogen_bond_candidates':hb,'ring_plane_max_deviation_least_squares_A':planarity,
        'ring_centroid_contacts':stack[:8],'expanded_atoms':atoms,
        'R1_gt':num(scalar('_refine_ls_R_factor_gt')),'wR2_all':num(scalar('_refine_ls_wR_factor_ref')),
        'GoF':num(scalar('_refine_ls_goodness_of_fit_ref'))}
assert counts=={'C':14,'H':16,'N':2,'S':2,'Cl':6,'Sn':1,'O':2}
assert abs(volume-num(scalar('_cell_volume')))<0.01
assert all(abs(x-y)<0.0002 for x,y in zip(sorted(set(round(d,6) for d in lengths)),[2.4278,2.4286,2.4326]))
assert max(abs(x-180) for x in trans)<1e-6
assert abs(norm(normal)-1)<1e-9
assert norm([sum((p[j]-centroid[j])*dot(sub(p,centroid),normal) for p in ringcart) - cov[imin][imin]*normal[j] for j in range(3)])<1e-8
out=ROOT/'01_结构分析'; out.mkdir(exist_ok=True)
(out/'晶体结构核算.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='expanded_atoms'},ensure_ascii=False,indent=2))
