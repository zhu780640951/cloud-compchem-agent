import json,subprocess,shutil,pathlib,os,time
report={'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'hostname':os.uname().nodename,'python_execution':'ok'}
if shutil.which('nvidia-smi'):
 p=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu,driver_version','--format=csv,noheader'],capture_output=True,text=True,timeout=15)
 report['gpu_returncode']=p.returncode
 report['gpu_info']=p.stdout.strip()
 p=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],capture_output=True,text=True,timeout=15)
 report['gpu_processes']=p.stdout.strip()
else: report['gpu_info']='nvidia-smi not found'
paths=[]
pw=shutil.which('pw.x')
if pw: paths.append(pw)
for root in ['/content','/opt','/usr/local']:
 for current,dirs,files in os.walk(root):
  depth=len(pathlib.Path(current).relative_to(root).parts)
  dirs[:]=[d for d in dirs if d not in {'drive','node_modules','.git','site-packages','lib'} and depth<3]
  if 'pw.x' in files: paths.append(str(pathlib.Path(current)/'pw.x'))
report['qe_candidates']=sorted(set(paths))
print(json.dumps(report,indent=2))