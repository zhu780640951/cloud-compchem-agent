import pathlib,tarfile,json,re,csv,itertools,hashlib,sys,numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).parent/'plotdeps'))
from skimage.measure import marching_cubes
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
root=pathlib.Path(r'E:\桌面\(C₇H₆NS)₂[SnCl₆]·2H₂O计算');p=root/'02_计算任务'/'GPU_QE'/'QE_G04_电子结构'/'优化结构收敛复核';out=pathlib.Path(r'C:\Users\y\Documents\Codex\2026-10-30\wo\outputs\QE_图件整理');out.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})
model=json.loads((root/'02_计算任务'/'00_正式计算准备_20261030'/'周期晶胞_模型.json').read_text(encoding='utf8'));atoms=model['atoms'];roles=[]
for a in atoms:
 tag=a['label'].removesuffix('_inv');roles.append('inorganic' if a['element'] in ('Sn','Cl') else ('water' if tag in ('O007','H00F','H00G') else 'organic'))
colors={'organic':'#315b91','inorganic':'#d18236','water':'#629585'};edges={'scalar_control':0.8446,'soc_on':0.8459};dos={}
with tarfile.open(p/'soc_pdos_pair_results.tar.gz') as t:
 for mode,edge in edges.items():
  data=None;energy=None;seen=set()
  for m in t.getmembers():
   k=re.fullmatch(re.escape(mode)+r'\.pdos_atm#(\d+)\(([^)]+)\)_wfc#\d+\(([spdf])(?:_j[\d.]+)?\)',m.name)
   if not k:continue
   i=int(k.group(1))-1;assert atoms[i]['element']==k.group(2);seen.add(i);f=t.extractfile(m);f.readline();a=np.loadtxt(f)
   if data is None:energy=a[:,0];data={x:np.zeros(len(energy)) for x in colors}
   assert np.allclose(a[:,0],energy);data[roles[i]]+=a[:,1]
  assert seen==set(range(43));dos[mode]=(energy-edge,data)
  with (out/(mode+'_pdos.csv')).open('w',newline='',encoding='utf8') as f:
   wr=csv.writer(f);wr.writerow(['energy_minus_vbm_eV','organic_states_per_eV','inorganic_states_per_eV','water_states_per_eV']);wr.writerows(zip(energy-edge,*(data[x] for x in colors)))
  fig,ax=plt.subplots(figsize=(5.2,3.5),layout='constrained')
  for x in colors:ax.plot(energy-edge,data[x],color=colors[x],lw=1.3,label=x.capitalize())
  ax.axvline(0,color='#666666',lw=.7,ls='--');ax.set(xlim=(-4,6),ylim=(0,None),xlabel=r'Energy − sampled VBM (eV)',ylabel='Projected DOS (states/eV)');ax.set_title('Scalar reference' if mode=='scalar_control' else 'SOC',loc='left',fontsize=10);ax.legend(fontsize=8,loc='upper left');
  for fmt in ('png','svg','pdf'):fig.savefig(out/(mode+'_pdos.'+fmt),dpi=220)
  plt.close(fig)

def read_cube(f):
 f.readline();f.readline();h=f.readline().decode().split();n=int(h[0]);assert n==43;origin=np.array(list(map(float,h[1:4])));axes=[];shape=[]
 for i in range(3):q=f.readline().decode().split();shape.append(int(q[0]));axes.append(list(map(float,q[1:4])))
 elements=[];xyz=[]
 for i in range(n):q=f.readline().decode().split();elements.append(int(q[0]));xyz.append(list(map(float,q[2:5])))
 data=np.fromstring(f.read().decode('ascii'),sep=' ');assert data.size==np.prod(shape)
 return origin,np.array(axes),np.array(xyz),elements,data.reshape(shape)
with tarfile.open(p/'soc_scalar_edge_cubes.tar.gz') as t:
 manifest=json.load(t.extractfile('edge_manifest.json'))
 for row in manifest:
  cubes=[read_cube(t.extractfile(x)) for x in row['cubes']];origin,axes,xyz,elements,data=cubes[0];density=data.copy()
  for oo,aa,xx,ee,dd in cubes[1:]:assert np.allclose(oo,origin) and np.allclose(aa,axes) and np.allclose(xx,xyz) and ee==elements;density+=dd
  grid=density[::2,::2,::2];level=float(grid.max()*.12);vertices,faces,_,_=marching_cubes(grid,level=level,step_size=1);angstrom=.529177210903;v=(origin+vertices@(axes*2))*angstrom;cell=axes*np.array(data.shape)[:,None]*angstrom;o=origin*angstrom;frac=((xyz-origin)@np.linalg.inv(axes*np.array(data.shape)[:,None]))%1;coord=o+frac@cell
  fig=plt.figure(figsize=(5,4.4));ax=fig.add_subplot(111,projection='3d');ax.add_collection3d(Poly3DCollection(v[faces],facecolor='#3f72ad' if row['edge']=='VBM' else '#dd8e45',edgecolor='none',alpha=.36))
  for el,color,size in [(1,'#eeeeee',3),(6,'#4c4c4c',10),(7,'#4267a8',13),(8,'#d75b52',13),(16,'#d2aa3c',20),(17,'#70aa72',18),(50,'#81639b',32)]:
   z=np.array(elements)==el;ax.scatter(*coord[z].T,s=size,c=color,edgecolors='k',linewidths=.2,depthshade=False)
  for k in range(3):
   others=[x for x in range(3) if x!=k]
   for u,vv in itertools.product((0,1),repeat=2):
    st=o+u*cell[others[0]]+vv*cell[others[1]];end=st+cell[k];ax.plot(*np.array([st,end]).T,color='#777777',lw=.4)
  corners=np.array([o+np.array(z)@cell for z in itertools.product((0,1),repeat=3)]);lo=corners.min(0);hi=corners.max(0);ax.set_xlim(lo[0],hi[0]);ax.set_ylim(lo[1],hi[1]);ax.set_zlim(lo[2],hi[2]);ax.set_box_aspect(hi-lo);ax.view_init(elev=19,azim=-57);ax.set_axis_off();ax.set_title(('Scalar' if row['mode']=='scalar_control' else 'SOC')+' '+row['edge']+' | isosurface 12% of max',fontsize=10)
  name=row['mode']+'_'+row['edge']+'_isosurface';fig.savefig(out/(name+'.png'),dpi=200,bbox_inches='tight');fig.savefig(out/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
  print(name,'threshold',level,'triangles',len(faces),flush=True)
(out/'图件说明.md').write_text('''# QE 图件说明\n\nPDOS 使用 4×4×3 NSCF，在各自采样价带顶置零，并按 43 原子分组汇总投影。标量与 SOC 采用同族不同赝势，水单独分类；曲线未进行面积归一化或额外平滑。\n\n三维图来自 QE plot_num=7 伪波函数密度；SOC 简并带对先相加。全部图采用各自最大密度的 12% 作为等值面，显示方式不代表精确电荷布居；原子在晶胞内周期折回，故分子可能被晶胞边界截断。相同角度不意味着可以凭图对不同轨道的强度定量比较。\n\n目前原始探索性能带采用非标准路径，不作为标准路径图。标准路径需要补做相应 k 点计算。图件仅用于基态带边解释，不是激发态电荷转移图；建议人工检查结构、伪势、能量对齐和投影窗口。\n''',encoding='utf8')
print('DONE',out)
