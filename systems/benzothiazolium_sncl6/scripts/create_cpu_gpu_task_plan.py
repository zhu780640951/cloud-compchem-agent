import pathlib,json
root=pathlib.Path(__file__).resolve().parents[1]
tasks=[]
def add(i,platform,title,stage,deps,outputs,condition=None):
 tasks.append({'id':i,'platform':platform,'software':{'shared':None,'GPU_QE':'Quantum ESPRESSO 7.5','CPU_ORCA':'ORCA 6.1.1'}[platform],'title':title,'stage':stage,'status':'planned','dependencies':deps,'outputs':outputs,'activation_condition':condition,'auto_submit':False})
add('COMMON_MODEL','shared','统一43原子中性周期模型、标签、分子完整性和版本','准备',[],['模型清单','结构/输入哈希','晶体近邻关系'])
add('QE_G01','GPU_QE','赝势、截断能与k网格收敛','第一轮',['COMMON_MODEL'],['收敛表','资源实测','赝势哈希'])
add('QE_G02','GPU_QE','固定实验晶胞的H优化','第一轮',['QE_G01'],['R_H','受力和优化日志'])
add('QE_G03','GPU_QE','固定实验晶胞的全原子优化','第一轮',['QE_G02'],['R_fixed','结构变化表'])
add('QE_G04','GPU_QE','能带、DOS/PDOS和带边密度','第一轮',['QE_G03'],['能带/DOS/PDOS','VBM/CBM空间分布'])
add('QE_G05','GPU_QE','SOC开关电子结构对照','关键复核',['QE_G04'],['配对带隙/轨道排序','SOC参数与赝势核验'])
add('QE_G06','GPU_QE','变晶胞与固定晶胞结构对照','关键复核',['QE_G03'],['R_vc','晶格/堆积/氢键变化'])
add('QE_G07','GPU_QE','HSE06关键带边复核','关键复核',['QE_G04'],['GPU能力与资源试算','方法敏感性'],'先通过当前GPU编译版本的杂化泛函试算')
add('QE_G08','GPU_QE','含色散一致势能面的Gamma振动筛查','稳定性',['QE_G06'],['Gamma频率/模式','软模及收敛检查'],'确认受力和晶格满足所用振动方法的前提')
add('QE_G09','GPU_QE','全布里渊区声子及超胞/q网格收敛','深入',['QE_G08'],['声子色散/网格','超胞收敛与动力学稳定性范围'],'先解决Gamma筛查中的数值或真实不稳定；344原子超胞先测资源')
add('QE_G10','GPU_QE','激发态局域化与畸变的周期对照','机制触发',['QE_G03','ORC_C06','ORC_C07'],['同条件局域/非局域态对照','模型尺寸检验'],'嵌入计算出现无机或CT显著弛豫候选，且选择的受约束激发态方法经过核验')
add('QE_G11','GPU_QE','脱水反应能/自由能','实验问题触发',['QE_G06'],['反应式和参考态','能量/自由能表'],'明确脱水产物、水的参考态及温度/湿度问题')
add('QE_G12','GPU_QE','有限温度AIMD','实验问题触发',['QE_G06','QE_G08'],['温度/能量/轨迹','氢键与水动态'],'明确温区、超胞、系综和需要检验的动态问题')
add('ORC_C01','CPU_ORCA','有机阳离子基态与S/T参考','第一轮',['COMMON_MODEL'],['电荷/电子数','S/T能级','振子强度','轨道/检查点'])
add('ORC_C02','CPU_ORCA','两种实际堆积二聚体的环境激发态','第一轮',['QE_G03'],['M02A/M02B完整模型','堆积效应对照'],'R_XRD可先做环境与资源预检查；正式对照使用明确标记的几何')
add('ORC_C03','CPU_ORCA','嵌入无机参考与中性环境簇的S/T激发','第一轮',['QE_G03'],['M03/M04模型与点电荷','逐态激发能/收敛','资源实测'])
add('ORC_C04','CPU_ORCA','NTO/跃迁密度和片段电子空穴分析','第一轮',['ORC_C01','ORC_C02','ORC_C03'],['NTO图','电子/空穴片段表','候选态清单'])
add('ORC_C05','CPU_ORCA','候选态的泛函/基组/QM区/嵌入稳健性','关键复核',['ORC_C04','QE_G04'],['态排序/性质敏感性','基态稳定性','自旋检查'])
add('ORC_C06','CPU_ORCA','少量候选S/T态的优化与态跟踪','核心发光',['ORC_C05'],['激发态几何','态跟踪记录','结构重组'])
add('ORC_C07','CPU_ORCA','弛豫后发射能与结构重组','核心发光',['ORC_C06'],['发射能/波长','态性质','方法区间'])
add('ORC_C08','CPU_ORCA','全电子相对论候选态SOC与DeltaEST','核心自旋',['ORC_C06'],['SOC矩阵','明确定义几何的DeltaEST','兼容性与基组核验'],'先验证全电子相对论TDDFT-SOC路径，不使用遗漏Sn SOC积分的ECP设置作Sn作用结论')
add('ORC_C09','CPU_ORCA','频率/Hessian、振动谱与适用的跃迁速率','候选确定后',['ORC_C07','ORC_C08'],['Hessian/谱形','辐射及适用的态间速率','寿命模型范围'],'模型极小值、约束/嵌入振动处理、相关ESD功能均通过核验')
add('ORC_C10','CPU_ORCA','堆积/氢键/结晶水的机制相关对照','相互作用',['ORC_C03','ORC_C05'],['结构与激发态受控对照','相互作用分析'],'保持电荷/环境和能量参考定义清楚；不以不同组成总能量直接比较稳定性')
ids={x['id'] for x in tasks}
assert len(ids)==len(tasks)
assert all(d in ids for x in tasks for d in x['dependencies'])
seen=set();pending={x['id']:set(x['dependencies']) for x in tasks}
while pending:
 ready={i for i,deps in pending.items() if deps<=seen}
 if not ready: raise RuntimeError('Dependency cycle')
 seen|=ready
 for i in ready: del pending[i]
manifest={'version':'v1','date':'2026-10-30','purpose':'用户要求的CPU/ORCA与GPU/QE分工方案，非已提交队列','cif_sha256':'ed23e88c8f84151de88f25c1ddd3b617e21a626e7ba6e403d5853217436c7a12','formal_jobs_submitted_this_turn':0,'auto_submission_enabled':False,'cpu_processes_initial':12,'orca_maxcore_MB_per_process_initial':8000,'gpu_hardware':'按实际分配核验；当前方案不预留运行时','tasks':tasks}
(root/'02_计算任务'/'计算任务清单_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
for platform,label in [('CPU_ORCA','Google Cloud CPU / ORCA'),('GPU_QE','Colab GPU 平台 / Quantum ESPRESSO')]:
 dest=root/'02_计算任务'/platform;dest.mkdir(exist_ok=True)
 text=f'# {label}\n\n本目录用于后续正式任务；当前仅建立分工与清单，没有自动提交作业。\n\n'
 text+='详细方案：../../01_结构分析/CPU_GPU分工与分阶段计算方案_20261030.md。\n机器可读任务与依赖：../计算任务清单_v1.json。\n\n'
 text+='每项作业在准备输入时按任务编号建立子目录，保存输入、模型、软件参数、完整日志、检查点、状态与分析。\n\n'
 text+='\n'.join('- '+x['id']+'：'+x['title'] for x in tasks if x['platform']==platform)+'\n'
 (dest/'README.md').write_text(text,encoding='utf-8')
print(json.dumps({'tasks':len(tasks),'cpu_tasks':sum(t['platform']=='CPU_ORCA' for t in tasks),'gpu_tasks':sum(t['platform']=='GPU_QE' for t in tasks),'dependency_graph_valid':True,'all_planned':all(t['status']=='planned' for t in tasks),'submitted':0},ensure_ascii=False))