import pathlib,subprocess,base64,json
here=pathlib.Path(__file__).parent;root=here.parents[2]
remote="""import pathlib,json,subprocess,re
p=pathlib.Path('/home/y/codex_calculations/benzothiazolium_sncl6/orc_c03_embed79_20261031');r={'status':(p/'status.json').read_text() if (p/'status.json').exists() else None,'jobs':{}}
for n in ['expanded79_shell1','expanded79_shell2']:
 f=p/(n+'.out')
 if f.exists():
  t=f.read_text(errors='replace');r['jobs'][n]={'bytes':len(t),'normal':'ORCA TERMINATED NORMALLY' in t,'tail':t[-1800:]}
r['processes']=subprocess.run(['bash','-lc',"ps -eo pid,etime,rss,args | grep '[e]xpanded79_shell'"],capture_output=True,text=True).stdout
print(json.dumps(r))
"""
cmd="python3 -c \"import base64;exec(base64.b64decode('"+base64.b64encode(remote.encode()).decode()+"'))\""
a=[r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd','compute','ssh','y@orca-cpu-16','--project=<YOUR_GCP_PROJECT_ID>','--zone=us-central1-a','--account=<YOUR_GCP_EMAIL>','--ssh-key-file='+str(root/'连接配置'/'gcp_test_key'),'--ssh-key-expire-after=30m','--quiet','--command='+cmd]
p=subprocess.run(a,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90);(here/'embedding_monitor.json').write_text(p.stdout,encoding='utf-8');print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)