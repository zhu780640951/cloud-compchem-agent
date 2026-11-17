import pathlib,subprocess,base64,json
root=pathlib.Path(__file__).resolve().parents[1];job=root/'02_计算任务'/'CPU_ORCA'/'ORC_C03_中性簇模型'/'SCF独立初猜复核_20261031'
inputs={n:base64.b64encode((job/n).read_bytes()).decode() for n in ['shell1_independent_scf.inp','expanded79_shell1.pc']}
remote="""import os,subprocess,pathlib,json,base64,time
base=pathlib.Path.home()/'codex_calculations/benzothiazolium_sncl6';p=base/'orc_c03_shell1_independent_scf_20261031';p.mkdir(exist_ok=False)
for n,b in INPUTS.items(): (p/n).write_bytes(base64.b64decode(b))
env=os.environ.copy();env['PATH']='/opt/openmpi-4.1.8/bin:/opt/orca:'+env.get('PATH','');env['LD_LIBRARY_PATH']='/opt/openmpi-4.1.8/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='1'
out=(p/'shell1_independent_scf.out').open('w');proc=subprocess.Popen(['/opt/orca/orca','shell1_independent_scf.inp'],cwd=p,env=env,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
j={'pid':proc.pid,'path':str(p),'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'scope':'shell1 single point SCF; independent default guess; no TDDFT; 12 processes'};(p/'launch.json').write_text(json.dumps(j));print(json.dumps(j))
""".replace('INPUTS',repr(inputs))
cmd='python3 -c "import base64;exec(base64.b64decode(\''+base64.b64encode(remote.encode()).decode()+'\'))"'
a=[r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd','compute','ssh','y@orca-cpu-16','--project=<YOUR_GCP_PROJECT_ID>','--zone=us-central1-a','--account=<YOUR_GCP_EMAIL>','--ssh-key-file='+str(root/'连接配置'/'gcp_test_key'),'--ssh-key-expire-after=30m','--quiet','--command='+cmd]
p=subprocess.run(a,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90);(job/'启动记录.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8');print(p.stdout);print(p.stderr)
if p.returncode==0:(job/'launch.json').write_text(p.stdout,encoding='utf-8')
raise SystemExit(p.returncode)