import pathlib,subprocess,base64,json
root=pathlib.Path(__file__).resolve().parents[3]
dir=pathlib.Path(__file__).resolve().parent
payload=base64.b64encode((dir/'cation_xrd_tda_vtight.inp').read_bytes()).decode()
remote="""import base64,pathlib,os,subprocess,json,time
p=pathlib.Path.home()/'codex_calculations/benzothiazolium_sncl6/orc_c01_xrd_vtight_20261031'
p.mkdir(parents=True,exist_ok=False)
(p/'cation_xrd_tda_vtight.inp').write_bytes(base64.b64decode(PAYLOAD))
env=os.environ.copy();env['PATH']='/opt/openmpi-4.1.8/bin:/opt/orca:'+env.get('PATH','');env['LD_LIBRARY_PATH']='/opt/openmpi-4.1.8/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='1'
out=(p/'cation_xrd_tda_vtight.out').open('w')
proc=subprocess.Popen(['/opt/orca/orca','cation_xrd_tda_vtight.inp'],cwd=p,env=env,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
(p/'launch.json').write_text(json.dumps({'pid':proc.pid,'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'path':str(p)}));print((p/'launch.json').read_text())
""".replace('PAYLOAD',repr(payload))
cmd="python3 -c \"import base64;exec(base64.b64decode('"+base64.b64encode(remote.encode()).decode()+"'))\""
args=[r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd','compute','ssh','y@orca-cpu-16','--project=<YOUR_GCP_PROJECT_ID>','--zone=us-central1-a','--account=<YOUR_GCP_EMAIL>','--ssh-key-file='+str(root/'连接配置'/'gcp_test_key'),'--ssh-key-expire-after=30m','--quiet','--command='+cmd]
p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=80)
(dir/'launch_vtight.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8');print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)