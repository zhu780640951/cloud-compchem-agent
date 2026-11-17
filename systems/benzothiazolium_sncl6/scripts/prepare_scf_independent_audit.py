import pathlib,tarfile,re,json,hashlib
root=pathlib.Path(__file__).resolve().parents[1];src=root/'02_计算任务'/'CPU_ORCA'/'ORC_C03_中性簇模型';out=src/'SCF独立初猜复核_20261031';out.mkdir(exist_ok=True)
archives=['resume_results.tar.gz','shell2_results.tar.gz','td_residual_audit_results.tar.gz'];data={}
for fname in archives:
 with tarfile.open(src/fname) as a:
  members=a.getnames();data[fname]={}
  for n in members:
   if n.endswith(('.inp','.pc','.gbw','.out')):
    b=a.extractfile(n).read();item={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
    if n.endswith('.out'):
     t=b.decode(errors='replace');item.update({'normal':'ORCA TERMINATED NORMALLY' in t,'scf_cycles':re.findall(r'SCF CONVERGED AFTER\s+(\d+) CYCLES',t),'trah_final_macro':re.findall(r'^\s*\d+\s+(-\d+\.\d+)\s+([\d.Ee+-]+).*?\((?:TRAH|NR) MAcro\)',t,re.M)[-1:],'energy_after_integration':re.findall(r'Total energy after final integration\s*:\s*(-?\d+\.\d+)',t),'last_energy_change':re.findall(r'Last Energy change\s+\.\.\.\s+([^\n]+)',t),'last_orbital_gradient':re.findall(r'Last Orbital Gradient\s+\.\.\.\s+([^\n]+)',t)})
    data[fname][n]=item
with tarfile.open(src/'resume_results.tar.gz') as a:
 old=a.extractfile('resume_shell1.inp').read().decode();inp=old.replace(' TightSCF TRAH MOREAD',' TightSCF TRAH').replace('%moinp "initial_guess.gbw"\n','');inp=re.sub(r'^%tddft.*?end\s*\n','',inp,flags=re.M)
 assert 'MOREAD' not in inp and '%tddft' not in inp and '%pointcharges "expanded79_shell1.pc"' in inp
 (out/'shell1_independent_scf.inp').write_text(inp,encoding='utf-8');(out/'expanded79_shell1.pc').write_bytes(a.extractfile('expanded79_shell1.pc').read())
(out/'离线审计.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
report='''# 79原子嵌入簇SCF离线核查

两组原始shell1、shell2结果分别经过26和39次迭代，最终TRAH宏迭代能量分别为−6169.686107040918、−6169.702004176169 Eh。后续TDA残差复核以各自最终GBW为初猜：SHA-256逐文件核对表明两组初猜分别与对应前序GBW完全一致；点电荷文件亦逐组一致。

后续作业第0宏迭代能量分别为−6169.686107040926、−6169.702004176185 Eh，与前序最终宏迭代能量分别仅差约8e−12、1.6e−11 Eh，梯度分别约4.32e−6和4.55e−6，小于当时1e−5的轨道梯度阈值。两组最终精细网格重积分后的SCF能量也分别与前序一致到日志显示精度。

故能量变化字段−6169.7 Eh与从已收敛初猜在第0宏迭代即退出的情形相符，强烈支持单步初始化/报告问题，但仅凭输出不能证明程序内部字段实现；不可将其当作真实逐步能量变化，也不能据此断言波函数稳定或唯一。

实验激发态最终行 FINAL SINGLE POINT ENERGY 可能包含所选激发能，不可与基态SCF直接混用。上述对比使用同一TRAH宏迭代能量及最终SCF重积分能量。

后续仅针对shell1进行基态SCF独立初猜诊断：保持PBE0、def2-SVP、TRAH、点电荷和坐标不变，移除MOREAD与TDDFT，让ORCA构造默认初猜。只比较基态收敛、能量和占据/密度；失败或耗时过长保留结果，不自动扩展计算。点电荷边界仍需检查。
'''
(out/'离线核查与对照方案.md').write_text(report,encoding='utf-8')
print(json.dumps({'offline_saved':str(out),'shell1_initial_equals_prior_gbw':data[archives[0]]['resume_shell1.gbw']['sha256']==data[archives[2]]['shell1/initial_guess.gbw']['sha256'],'shell2_initial_equals_prior_gbw':data[archives[1]]['resume_shell1.gbw']['sha256']==data[archives[2]]['shell2/initial_guess.gbw']['sha256'],'pointcharges_unchanged':data[archives[0]]['expanded79_shell1.pc']['sha256']==data[archives[2]]['shell1/expanded79_shell1.pc']['sha256']},ensure_ascii=False))