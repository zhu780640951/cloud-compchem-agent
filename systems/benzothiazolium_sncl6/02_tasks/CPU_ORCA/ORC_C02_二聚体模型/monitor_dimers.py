import pathlib,subprocess,base64,json
root=pathlib.Path(__file__).resolve().parents[3];out=pathlib.Path(__file__).resolve().parent
remote="""import pathlib,json,os,re
p=pathlib.Path.home()/'codex_calculations/benzothiazolium_sncl6/orc_c02_dimers_20261031';print(json.dumps({'status':(p/'status.json').read_text() if (p/'status.json').exists() else None,'files':[(f.name,f.stat().st_size) for f in p.glob('*.out')]}))
"""
cmd="python3 -c \"import base64;exec(base64.b64decode('"+base64.b64encode(remote.encode()).decode()+"'))\""
a=[r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd','compute','ssh','y@orca-cpu-16','--project=<YOUR_GCP_PROJECT_ID>','--zone=us-central1-a','--account=<YOUR_GCP_EMAIL>','--ssh-key-file='+str(root/'连接配置'/'gcp_test_key'),'--ssh-key-expire-after=30m','--quiet','--command='+cmd]
p=subprocess.run(a,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60);print(p.stdout);print(p.stderr);(out/'dimer_monitor.json').write_text(p.stdout,encoding='utf-8');raise SystemExit(p.returncode)