import pathlib,subprocess,base64,json,datetime
root=pathlib.Path(__file__).resolve().parent
project=root.parents[1]
smoke=(project/'02_计算任务'/'00_连接测试_20261030'/'cpu_smoke_test.py').read_text(encoding='utf-8-sig')
health='''import os,json,pathlib,platform,shutil,time
mem={line.split(':',1)[0]:int(line.split(':',1)[1].strip().split()[0]) for line in pathlib.Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemTotal:','MemAvailable:'))}
health={'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'hostname':platform.node(),'logical_cpus':os.cpu_count(),'mem_total_kib':mem['MemTotal'],'mem_total_GiB':round(mem['MemTotal']/1024**2,3),'mem_available_GiB':round(mem['MemAvailable']/1024**2,3),'orca_exists':pathlib.Path('/opt/orca/orca').is_file(),'root_disk_total_GiB':round(shutil.disk_usage('/').total/1024**3,3),'root_disk_free_GiB':round(shutil.disk_usage('/').free/1024**3,3),'uptime_seconds':float(pathlib.Path('/proc/uptime').read_text().split()[0])}
print('HEALTH_JSON',json.dumps(health),flush=True)
'''
remote=health+'\n'+smoke+"\n(root/'health.json').write_text(json.dumps(health,indent=2))\n"
(root/'cpu_memory_postboot_remote.py').write_text(remote,encoding='utf-8')
payload=base64.b64encode(remote.encode()).decode()
command='python3 -c "import base64;exec(base64.b64decode(\''+payload+'\'))"'
cli=r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd'
args=[cli,'compute','ssh','y@orca-cpu-16','--project=<YOUR_GCP_PROJECT_ID>','--zone=us-central1-a','--account=<YOUR_GCP_EMAIL>','--ssh-key-file='+str(project/'连接配置'/'gcp_test_key'),'--ssh-key-expire-after=30m','--quiet','--command='+command]
p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
(root/'CPU升配后SSH验证.log').write_text(p.stdout+'\nSTDERR:\n'+p.stderr,encoding='utf-8')
result={'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ssh_exit_code':p.returncode}
for line in p.stdout.splitlines():
 if line.startswith('HEALTH_JSON '): result['health']=json.loads(line[len('HEALTH_JSON '):])
 if line.startswith('RESULT_JSON '): result['orca_tests']=json.loads(line[len('RESULT_JSON '):])
(root/'CPU升配后开机验证.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
if p.returncode!=0: print('SSH_ERROR',p.stderr[-5000:]);print(p.stdout[-2000:]);raise SystemExit(p.returncode)
if not result.get('orca_tests'): print('MISSING_TEST_RESULT',p.stdout[-4000:]);raise SystemExit(2)