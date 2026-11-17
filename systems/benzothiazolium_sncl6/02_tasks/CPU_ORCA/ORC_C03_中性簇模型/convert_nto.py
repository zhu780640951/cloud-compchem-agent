import pathlib,subprocess,base64
here=pathlib.Path(__file__).parent;root=here.parents[2]
remote="""import pathlib,subprocess,json
p=pathlib.Path('/home/y/codex_calculations/benzothiazolium_sncl6/orc_c03_neutral_nto_20261031');r=[]
for i in (1,2,3):
 a=f'neutral_cluster_nto.s{i}.nto';b=f's{i}_reference.molden';q=subprocess.run(['/opt/orca/orca_2mkl',a,b,'-molden','-anyorbs'],cwd=p,capture_output=True,text=True,timeout=120);r.append({'state':i,'returncode':q.returncode,'molden_exists':(p/b).exists(),'bytes':(p/b).stat().st_size if (p/b).exists() else 0,'tail':(q.stdout+q.stderr)[-400:]})
print(json.dumps(r))
"""
cmd="python3 -c \"import base64;exec(base64.b64decode('"+base64.b64encode(remote.encode()).decode()+"'))\""
a=[r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd','compute','ssh','y@orca-cpu-16','--project=<YOUR_GCP_PROJECT_ID>','--zone=us-central1-a','--account=<YOUR_GCP_EMAIL>','--ssh-key-file='+str(root/'连接配置'/'gcp_test_key'),'--ssh-key-expire-after=30m','--quiet','--command='+cmd]
p=subprocess.run(a,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180);print(p.stdout);print(p.stderr);(here/'nto_conversion.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8');raise SystemExit(p.returncode)