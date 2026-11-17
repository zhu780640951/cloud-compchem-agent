import json,pathlib,collections,math,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
d=json.loads((root/'01_结构分析'/'晶体结构核算.json').read_text(encoding='utf-8'))
assert d['expanded_natoms']==43 and d['sha256']=='ed23e88c8f84151de88f25c1ddd3b617e21a626e7ba6e403d5853217436c7a12'
vec=d['cell_vectors_A']; atoms=d['expanded_atoms']
def cart(a): return [sum(a['frac'][i]*vec[i][j] for i in range(3)) for j in range(3)]
def xyz(seq,comment): return str(len(seq))+'\n'+comment+'\n'+''.join(a['element']+' '+' '.join(f'{x:.9f}' for x in cart(a))+'\n' for a in seq)
organic=[a for a in atoms if a['symmetry']=='identity' and a['label'] not in {'Sn01','Cl02','Cl03','Cl04','O007','H00F','H00G'}]
assert collections.Counter(a['element'] for a in organic)=={'C':7,'H':6,'N':1,'S':1}
assert len(atoms)==43
out=root/'02_计算任务'/'00_正式计算准备_20261030';out.mkdir(exist_ok=True)
(out/'周期晶胞_43原子_XRD.xyz').write_text(xyz(atoms,'XRD fractional coordinates mapped to Cartesian Angstrom; periodic cell in separate JSON'),encoding='utf-8')
(out/'有机阳离子_15原子_XRD.xyz').write_text(xyz(organic,'C7H6NS+; charge +1 multiplicity 1; crystal geometry'),encoding='utf-8')
(out/'周期晶胞_模型.json').write_text(json.dumps({'cif_sha256':d['sha256'],'cell_vectors_A':vec,'atoms':atoms,'total_charge':0,'atom_count':43,'status':'preparation_only'},ensure_ascii=False,indent=2),encoding='utf-8')
(out/'准备说明.md').write_text('# 第一阶段模型准备\n\n- 周期模型 43 原子，零总电荷，保留结晶水，晶胞矢量保存在 JSON。\n- 有机模型 15 原子，C7H6NS+，电荷 +1，单重态；从 CIF 的同一对称单元提取，标记为实验几何。\n- 以上仅为坐标准备；需要核查键连接及周期成分，并选定赝势、泛函和资源后才生成正式计算输入。\n- 不含已完成的 DFT 计算，也没有提交 GPU 或 CPU 作业。\n',encoding='utf-8')
print(json.dumps({'periodic_atoms':len(atoms),'cation_atoms':len(organic),'cation_counts':dict(collections.Counter(a['element'] for a in organic)),'cation_charge':1,'multiplicity':1,'result_directory':str(out)},ensure_ascii=False))