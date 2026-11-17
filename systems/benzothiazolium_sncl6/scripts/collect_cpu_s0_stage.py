import pathlib,subprocess,json
root=pathlib.Path(__file__).resolve().parents[1]
job=root/'02_计算任务'/'CPU_ORCA'/'ORC_C01_S0优化与频率'
remote='y@orca-cpu-16:/home/y/codex_calculations/benzothiazolium_sncl6/orc_c01_s0optfreq_20261030/'
cli=r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd'
import base64
code="import pathlib,json,base64;p=pathlib.Path.home()/'codex_calculations/benzothiazolium_sncl6/orc_c01_s0optfreq_20261030';print(json.dumps({n:base64.b64encode((p/n).read_bytes()).decode() for n in ['xrd_stability.out','launch_optfreq.json','monitor_optfreq.json']}))"
cmd='python3 -c "import base64;exec(base64.b64decode(\''+base64.b64encode(code.encode()).decode()+'\'))"'
args=[cli,'compute','ssh','y@orca-cpu-16','--command='+cmd,'--project=<YOUR_GCP_PROJECT_ID>','--zone=us-central1-a','--account=<YOUR_GCP_EMAIL>','--ssh-key-file='+str(root/'连接配置'/'gcp_test_key'),'--ssh-key-expire-after=30m','--quiet']
p=subprocess.run(args,cwd=job,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
if p.returncode==0:
 data=json.loads(p.stdout)
 for n,b in data.items(): (job/n).write_bytes(base64.b64decode(b))
 p.stdout='Copied three selected files over SSH.'
(job/'回传记录.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
if p.returncode: print(p.stderr);raise SystemExit(p.returncode)
m=json.loads((job/'monitor_optfreq.json').read_text(encoding='utf-8'))
stability=(job/'xrd_stability.out').read_text(errors='replace')
assert 'The stability analysis shows that the wavefunction is stable' in stability
report='''# 有机单体：轨道稳定性、基态优化与频率

模型：从本项目 CIF 提取的孤立 C7H6NS+，15 原子，电荷 +1，单重态。未包含晶体静电环境、SnCl6 或水。

## 已完成

- 实验几何下重新进行 SCF 与轨道稳定性检查，PBE0/def2-SVP、RIJCOSX、VeryTightSCF、DEFGRID3、ConvCheckMode 0，12 进程、MaxCore 4000 MB/进程。
- ORCA 正常结束，耗时 35.910 秒。稳定性矩阵最低三个求解本征值约为 0.08206358、0.09998088、0.12670458 Eh，输出判定 wavefunction is stable。此结论限定于程序检查的轨道变化空间，不是完整晶体稳定性。
- SCF 仍采用程序综合收敛判断，不能宣称所有打印指标分别通过；手册说明 ConvCheckMode 0 允许部分判据未满足而其他判据超额满足。轨道稳定性检查提供了额外证据，不代表各项阈值自动改变。
- 原始完整输出保存为 xrd_stability.out。

## 当前任务

- 已提交 s0_optfreq.inp：同样方法及数值设置，TightOpt 基态优化，随后计算频率。
- 目标：孤立阳离子平衡几何，以及局部极小值的振动检验。优化正常结束还需检查明确的几何收敛标记，频率需检查非平动/转动模的虚频。
- 本次没有提交激发态几何优化、发射、SOC 或 GPU 任务。
- 当前监测快照保存于 monitor_optfreq.json。此为时间点快照，非持续后台监控。

快照时间 UTC：'''+m['checked_utc']+'\n运行状态：'+str(m['running'])+'\n最后几何优化周期：'+str(m['last_geometry_cycle'])+'\n\n后续：得到收敛结构及频率后，核验优化后电子基态并在相同设置下进行实验几何/优化几何的激发态配对与 NTO 分析，避免将几何变化和数值设置变化混在一起。\n\n参考：\n- https://www.faccts.de/docs/orca/6.1/manual/contents/essentialelements/scf.html\n- https://www.faccts.de/docs/orca/6.1/manual/contents/essentialelements/stabilityanalysis.html\n- https://www.faccts.de/docs/orca/6.1/tutorials/prop/geoopt.html\n'
(job/'任务进度与验收说明.md').write_text(report,encoding='utf-8')
print(json.dumps({'stability_passed':True,'optimization_submitted':True,'snapshot_time_utc':m['checked_utc'],'snapshot_running':m['running'],'snapshot_cycle':m['last_geometry_cycle'],'raw_stability_output_saved':True},ensure_ascii=False))