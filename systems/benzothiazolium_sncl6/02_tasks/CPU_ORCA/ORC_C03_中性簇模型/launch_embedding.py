import pathlib,subprocess,base64,sys
here=pathlib.Path(__file__).resolve().parent;root=here.parents[2];cli=r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd';common=['--project=<YOUR_GCP_PROJECT_ID>','--zone=us-central1-a','--account=<YOUR_GCP_EMAIL>','--ssh-key-file='+str(root/'连接配置'/'gcp_test_key'),'--ssh-key-expire-after=30m','--quiet'];remote='/home/y/codex_calculations/benzothiazolium_sncl6/orc_c03_embed79_20261031'
def ssh(code):
 cmd="python3 -c \"import base64;exec(base64.b64decode('"+base64.b64encode(code.encode()).decode()+"'))\""
 p=subprocess.run([cli,'compute','ssh','y@orca-cpu-16']+common+['--command='+cmd],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90);print(p.stdout,flush=True)
 if p.returncode:print(p.stderr[-2000:],flush=True);raise SystemExit(p.returncode)
ssh('import pathlib;p=pathlib.Path('+repr(remote)+');p.mkdir(parents=True,exist_ok=False);print(p)')
p=subprocess.run([cli,'compute','scp','expanded79_shell1.inp','expanded79_shell2.inp','expanded79_shell1.pc','expanded79_shell2.pc','y@orca-cpu-16:'+remote+'/']+common,cwd=here,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
if p.returncode:print(p.stderr[-3000:]);raise SystemExit(p.returncode)
runner="""import os,pathlib,subprocess,json,time
p=pathlib.Path(__file__).parent;env=os.environ.copy();env['PATH']='/opt/openmpi-4.1.8/bin:/opt/orca:'+env.get('PATH','');env['LD_LIBRARY_PATH']='/opt/openmpi-4.1.8/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='1';rows=[]
for n in [1,2]:
 name='expanded79_shell'+str(n);start=time.time()
 with (p/(name+'.out')).open('w') as f:
  try:q=subprocess.run(['/opt/orca/orca',name+'.inp'],cwd=p,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1800);rc=q.returncode
  except subprocess.TimeoutExpired:rc=124
 text=(p/(name+'.out')).read_text(errors='replace');row={'name':name,'rc':rc,'normal':'ORCA TERMINATED NORMALLY' in text,'seconds':round(time.time()-start,1)};rows.append(row);(p/'status.json').write_text(json.dumps(rows))
 if rc or not row['normal']:break
"""
code="import pathlib,base64,subprocess,json;p=pathlib.Path("+repr(remote)+");(p/'run.py').write_bytes(base64.b64decode("+repr(base64.b64encode(runner.encode()).decode())+"));o=(p/'launcher.log').open('w');proc=subprocess.Popen(['python3','run.py'],cwd=p,stdout=o,stderr=subprocess.STDOUT,start_new_session=True);print(json.dumps({'pid':proc.pid,'path':str(p)}))"
ssh(code)