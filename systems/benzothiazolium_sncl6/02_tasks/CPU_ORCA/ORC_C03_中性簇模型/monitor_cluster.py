import pathlib,subprocess,base64,json
root=pathlib.Path(__file__).resolve().parents[3];out=pathlib.Path(__file__).resolve().parent
remote="""import pathlib,json,os,re
p=pathlib.Path.home()/'codex_calculations/benzothiazolium_sncl6/orc_c03_neutral_pilot_20261031';j=json.loads((p/'launch.json').read_text());txt=(p/'neutral_cluster_pilot.out').read_text(errors='replace');status=pathlib.Path('/proc')/str(j['pid'])/'status';j.update({'running':status.exists() and 'State:\\tZ' not in status.read_text(),'normal_termination':'ORCA TERMINATED NORMALLY' in txt,'tail':txt[-5000:],'output_bytes':len(txt)});print(json.dumps(j))
"""
cmd="python3 -c \"import base64;exec(base64.b64decode('"+base64.b64encode(remote.encode()).decode()+"'))\""
a=[r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd','compute','ssh','y@orca-cpu-16','--project=<YOUR_GCP_PROJECT_ID>','--zone=us-central1-a','--account=<YOUR_GCP_EMAIL>','--ssh-key-file='+str(root/'连接配置'/'gcp_test_key'),'--ssh-key-expire-after=30m','--quiet','--command='+cmd]
p=subprocess.run(a,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60);print(p.stdout);print(p.stderr);(out/'cluster_monitor.json').write_text(p.stdout,encoding='utf-8');raise SystemExit(p.returncode)