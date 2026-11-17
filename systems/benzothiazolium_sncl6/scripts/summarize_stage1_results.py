import pathlib,json,tarfile,itertools,math,collections
root=pathlib.Path(__file__).resolve().parent.parent
model=json.loads((root/'02_计算任务'/'00_正式计算准备_20261030'/'周期晶胞_模型.json').read_text(encoding='utf-8'));v=model['cell_vectors_A'];old=model['atoms']
gpu=root/'02_计算任务'/'GPU_QE'/'QE_G03_固定晶胞全原子优化'
with tarfile.open(gpu/'all_relax_results.tar.gz') as t:
 pos=t.extractfile('R_fixed_final_crystal.txt').read().decode().splitlines()[1:];verify=json.loads(t.extractfile('verification.json').read())
new=[{'element':l.split()[0],'frac':[float(x) for x in l.split()[1:4]]} for l in pos if l.strip()];assert len(new)==len(old)==43 and all(a['element']==b['element'] for a,b in zip(old,new))
def dist(a,b):return min(math.sqrt(sum(sum((a['frac'][k]-b['frac'][k]+s[k])*v[k][i] for k in range(3))**2 for i in range(3))) for s in itertools.product((-1,0,1),repeat=3))
sn=next(a for a in new if a['element']=='Sn');cls=sorted(dist(sn,a) for a in new if a['element']=='Cl')
close=[]
for i,a in enumerate(new):
 for b in new[:i]:
  q=dist(a,b)
  if q<0.7:close.append([a['element'],b['element'],q])
report={'cif_sha256':model['cif_sha256'],'fixed_cell_43_atoms':True,'qe_verify':verify,'sn_cl_A':cls,'sn_cl_mean_A':sum(cls)/6,'pairs_below_0_7A':close,'notes':'Geometry screening only; no band structure or excited-state emission assignment.'}
(gpu/'结构初步核对.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
text=f'''# 固定实验晶胞全原子优化结果

QE 7.5，A100，PBE-D3(BJ)，80/640 Ry，3×3×2 k 网格；从已收敛的 H 优化结构出发。第一段因 720 s 上限暂停，保留完整 BFGS 重启目录后继续；累计 35 次 SCF、34 个 BFGS 步。QE 报告 BFGS 收敛，最后总受力最大分量 {verify['max_force_component_eV_A']:.5f} eV/Å，低于 0.02 eV/Å 目标。保持实验晶胞，43 原子。

Sn—Cl 距离（Å）：{', '.join(f'{x:.4f}' for x in cls)}；平均 {sum(cls)/6:.4f} Å。简单周期几何核查中 <0.7 Å 原子间异常接触数：{len(close)}。这不是完整结构稳定性或化学键审计。

完整输入、两段输出、最终坐标、收敛核验收录在 all_relax_results.tar.gz。最终完整 tmp 检查点 R_fixed_full_tmp.tar 保存在 Drive 的 Codex_全原子优化_20261030，大小 649021440 字节，SHA-256 41f3b2b48772d8792566549f7d1149d908ae7c03c7d89083e917be1049f251b5，已从 Drive 读回校验一致。A100 已刷新卸载 Drive 并释放。

该结构是固定实验晶胞的基态结果，不包含 SOC，不是带隙、激发态或发光机制结论。后续计算前需检查电子结构和模型敏感性。
'''
(gpu/'全原子优化完成记录.md').write_text(text,encoding='utf-8')
man=root/'02_计算任务'/'计算任务清单_v1.json';m=json.loads(man.read_text(encoding='utf-8'))
for task in m['tasks']:
 if task['id']=='COMMON_MODEL':task['status']='completed';task['completion_note']='43原子周期模型和单体参考已准备及初步几何核查。'
 if task['id']=='QE_G01':task['status']='needs_review';task['completion_note']='原始几何的能量与受力收敛通过预设目标；带隙与优化结构敏感性、混合赝势进一步核验待做。'
 if task['id']=='QE_G02':task['status']='completed';task['completion_note']='固定实验晶胞、固定重原子；H最大受力分量0.0137922 eV/A；两段续算。'
 if task['id']=='QE_G03':task['status']='completed';task['completion_note']='固定实验晶胞，BFGS收敛；最大受力分量0.0188521 eV/A；结构及原始输出归档。'
 if task['id']=='ORC_C01':task['status']='needs_review';task['completion_note']='XRD几何孤立阳离子参考PBE0/def2-SVP TDA 10S+10T已运行；默认及ConvCheckMode=0均结束，部分密度阈值仍需复核；非晶体嵌入发光归属。'
man.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'sn_cl_A':cls,'sn_cl_mean_A':sum(cls)/6,'close_pairs':close,'force_eV_A':verify['max_force_component_eV_A'],'manifest_updated':True},ensure_ascii=False))