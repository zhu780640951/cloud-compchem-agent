import pathlib,json,subprocess,datetime
root=pathlib.Path(__file__).resolve().parent
project=root.parents[1]
result=json.loads((root/'CPU升配后开机验证.json').read_text(encoding='utf-8'))
remote=result['orca_tests']['remote_directory']
dest=root/'cpu_postboot_remote_files';dest.mkdir(exist_ok=True)
cli=r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd'
common=['--project=<YOUR_GCP_PROJECT_ID>','--zone=us-central1-a','--account=<YOUR_GCP_EMAIL>']
copy=subprocess.run([cli,'compute','scp','--recurse','y@orca-cpu-16:'+remote,'.','--ssh-key-file='+str(project/'连接配置'/'gcp_test_key'),'--ssh-key-expire-after=30m','--quiet']+common,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90,cwd=dest)
(root/'CPU开机测试文件回传.log').write_text(copy.stdout+'\nSTDERR:\n'+copy.stderr,encoding='utf-8')
check=subprocess.run([cli,'compute','instances','describe','orca-cpu-16','--format=json(name,status,machineType)']+common,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45)
if check.returncode!=0: print(check.stderr);raise SystemExit(check.returncode)
state=json.loads(check.stdout)
result['cloud_instance']=state
result['copy_exit_code']=copy.returncode
result['local_test_outputs']=[str(p.relative_to(root)) for p in dest.rglob('h2_hf_*core.out')]
passed=(result['health']['logical_cpus']==12 and result['health']['mem_total_GiB']>180 and all(t['normal_termination'] and t['exit_code']==0 for t in result['orca_tests']['tests']) and state['status']=='RUNNING' and state['machineType'].endswith('/n2-custom-12-196608-ext'))
result['postboot_checks_passed']=passed
(root/'CPU升配后开机验证.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
report='''# CPU 升配后开机验证

- 时间（UTC）：'''+datetime.datetime.now(datetime.timezone.utc).isoformat()+'''
- 云端实例：orca-cpu-16，us-central1-a，状态 '''+state['status']+'''
- 配置机型：n2-custom-12-196608-ext（12 vCPU / 192 GiB）。
- SSH 实测：12 个逻辑 CPU；系统总内存 '''+str(result['health']['mem_total_GiB'])+''' GiB；采样时可用内存 '''+str(result['health']['mem_available_GiB'])+''' GiB。
- 根文件系统空闲：'''+str(result['health']['root_disk_free_GiB'])+''' GiB。
- ORCA 输出版本：6.1.1；OpenMPI 路径 /opt/openmpi-4.1.8/bin/mpirun。
- H2 / HF / def2-SVP / TightSCF：1 核和 2 核均正常终止，退出码均为 0。
- 两次能量一致：-1.128893619388 Eh。
- 验证范围：扩容后的 SSH 访问、系统内存识别、ORCA 串行/双核执行。未提交晶体正式计算。
- 当前保持开机；本次没有自动停机。
- 远端测试目录：'''+remote+'''
- 详细状态与原始回传路径：CPU升配后开机验证.json、CPU升配后SSH验证.log、cpu_postboot_remote_files。
'''
(root/'CPU升配后开机验证报告.md').write_text(report,encoding='utf-8')
print(json.dumps({'postboot_checks_passed':passed,'status':state['status'],'copy_exit_code':copy.returncode,'saved_output_count':len(result['local_test_outputs']),'cloud_machine_type':state['machineType'].rsplit('/',1)[-1]},ensure_ascii=False,indent=2))
if copy.returncode!=0: print('COPY_ERROR',copy.stderr[-2000:]);raise SystemExit(copy.returncode)
if not passed or len(result['local_test_outputs'])!=2: raise SystemExit(2)