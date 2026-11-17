import pathlib,sys,json,tarfile,re,numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).parent/'seekpath_deps'))
import seekpath,spglib
root=pathlib.Path(r'E:\桌面\(C₇H₆NS)₂[SnCl₆]·2H₂O计算');p=root/'02_计算任务'/'GPU_QE'/'QE_G04_电子结构'/'electronic_stage2_results.tar.gz'
with tarfile.open(p) as t:s=t.extractfile('optimized_scf.in').read().decode()
cellpart=s.split('CELL_PARAMETERS angstrom\n')[1].split('ATOMIC_POSITIONS crystal\n')[0];cell=[list(map(float,l.split()[:3])) for l in cellpart.splitlines() if l.strip()];xyzpart=s.split('ATOMIC_POSITIONS crystal\n')[1].split('K_POINTS automatic')[0];xyz=[l.split() for l in xyzpart.splitlines() if l.strip()];nums={'H':1,'C':6,'N':7,'O':8,'S':16,'Cl':17,'Sn':50};structure=(cell,[list(map(float,x[1:4])) for x in xyz],[nums[x[0]] for x in xyz]);assert len(xyz)==43
results=[]
for tol in (1e-5,1e-3,1e-2):
 q=seekpath.get_path_orig_cell(structure,symprec=tol);results.append({'symprec_A':tol,'spacegroup':q['spacegroup_international'],'number':q['spacegroup_number'],'bravais':q['bravais_lattice'],'point_coords':q['point_coords'],'path':q['path'],'has_inversion':q['has_inversion_symmetry']})
print(json.dumps({'seekpath':seekpath.__version__,'spglib':spglib.__version__,'results':results},indent=2));(pathlib.Path(__file__).parent/'standard_path.json').write_text(json.dumps({'seekpath':seekpath.__version__,'spglib':spglib.__version__,'results':results},indent=2))
