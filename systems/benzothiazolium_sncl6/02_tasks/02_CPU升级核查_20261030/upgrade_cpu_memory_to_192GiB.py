import subprocess,json,datetime,pathlib
root=pathlib.Path(__file__).resolve().parent
cli=r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd'
common=['--project=<YOUR_GCP_PROJECT_ID>','--zone=us-central1-a','--account=<YOUR_GCP_EMAIL>']
requested='n2-custom-12-196608-ext'
record={'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'instance':'orca-cpu-16','account':'<YOUR_GCP_EMAIL>','before':{'status':'TERMINATED','machine_type':'n2-custom-12-98304','vcpus':12,'memory_GiB':96,'boot_disk_GB':100,'boot_disk_source':'https://www.googleapis.com/compute/v1/projects/<YOUR_GCP_PROJECT_ID>/zones/us-central1-a/disks/orca-cpu-16'},'requested_machine_type':requested,'requested_vcpus':12,'requested_memory_GiB':192,'start_requested':False}
change=subprocess.run([cli,'compute','instances','set-machine-type','orca-cpu-16','--machine-type='+requested,'--quiet']+common,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
record['change']={'returncode':change.returncode,'stdout':change.stdout,'stderr':change.stderr}
if change.returncode==0:
 check=subprocess.run([cli,'compute','instances','describe','orca-cpu-16','--format=json(name,status,machineType,disks)']+common,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
 record['verification_returncode']=check.returncode
 if check.returncode==0:
  after=json.loads(check.stdout);record['after']=after
  disks=after.get('disks',[])
  record['verified']=(after['machineType'].rsplit('/',1)[-1]==requested and after['status']=='TERMINATED' and any(d.get('boot') and d.get('source')==record['before']['boot_disk_source'] and str(d.get('diskSizeGb'))=='100' for d in disks))
 else: record['verification_error']=check.stderr
(root/'CPU内存升级执行记录.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
if record.get('verified'):
 text='''# CPU 内存升级完成

- 时间：'''+record['time_utc']+'''
- 实例：<YOUR_GCP_PROJECT_ID> / us-central1-a / orca-cpu-16。
- 执行账号：<YOUR_GCP_EMAIL>。
- 原规格：12 vCPU / 96 GiB，n2-custom-12-98304。
- 新规格：12 vCPU / 192 GiB，n2-custom-12-196608-ext。
- 实例状态：TERMINATED（仍关机）；本次没有启动实例。
- 启动持久盘：同一个 orca-cpu-16，100 GB，变更后描述查询确认保持不变。
- 验证范围：云端配置已更新并读回核对；尚未开机验证操作系统识别或 ORCA 运行。
- 开机计算价格：按同日官方价目表估算约 USD 1.74/小时，不含磁盘等附加费用、税费或折扣。
- 详细命令返回结果：CPU内存升级执行记录.json。
'''
 (root/'CPU内存升级完成.md').write_text(text,encoding='utf-8')
print(json.dumps({'change_returncode':change.returncode,'change_message':change.stderr.strip(),'verified':record.get('verified',False),'after_machine_type':record.get('after',{}).get('machineType'),'after_status':record.get('after',{}).get('status'),'record_saved':True},ensure_ascii=False,indent=2))
if not record.get('verified'): raise SystemExit(1)