import pathlib,subprocess,base64,json
here=pathlib.Path(__file__).resolve().parent;root=here.parents[2]
data={p.name:base64.b64encode(p.read_bytes()).decode() for p in [here/'dimer_1.inp',here/'dimer_2.inp']}
remote="""import pathlib,os,subprocess,json,time,base64
p=pathlib.Path.home()/'codex_calculations/benzothiazolium_sncl6/orc_c02_dimers_20261031';p.mkdir(parents=True,exist_ok=False)
files=PAYLOAD
for n,b in files.items():(p/n).write_bytes(base64.b64decode(b))
runner=\"\"\"import pathlib,os,subprocess,json,time
p=pathlib.Path(__file__).parent;env=os.environ.copy();env['PATH']='/opt/openmpi-4.1.8/bin:/opt/orca:'+env.get('PATH','');env['LD_LIBRARY_PATH']='/opt/openmpi-4.1.8/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='1';rows=[]
for label in ['dimer_1','dimer_2']:
 start=time.time()
 with (p/(label+'.out')).open('w') as out: q=subprocess.run(['/opt/orca/orca',label+'.inp'],cwd=p,env=env,stdout=out,stderr=subprocess.STDOUT)
 t=(p/(label+'.out')).read_text(errors='replace');rows.append({'name':label,'rc':q.returncode,'normal':'ORCA TERMINATED NORMALLY' in t,'elapsed_seconds':round(time.time()-start,1)});(p/'status.json').write_text(json.dumps(rows));
 if q.returncode!=0 or not rows[-1]['normal']:break
\"\"\"
(p/'run.py').write_text(runner);o=(p/'launcher.log').open('w');proc=subprocess.Popen(['python3','run.py'],cwd=p,stdout=o,stderr=subprocess.STDOUT,start_new_session=True);print(json.dumps({'pid':proc.pid,'path':str(p)}))
""".replace('PAYLOAD',repr(data))
cmd="python3 -c \"import base64;exec(base64.b64decode('"+base64.b64encode(remote.encode()).decode()+"'))\""
a=[r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd','compute','ssh','y@orca-cpu-16','--project=<YOUR_GCP_PROJECT_ID>','--zone=us-central1-a','--account=<YOUR_GCP_EMAIL>','--ssh-key-file='+str(root/'连接配置'/'gcp_test_key'),'--ssh-key-expire-after=30m','--quiet','--command='+cmd]
p=subprocess.run(a,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90);(here/'launch.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8');print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)