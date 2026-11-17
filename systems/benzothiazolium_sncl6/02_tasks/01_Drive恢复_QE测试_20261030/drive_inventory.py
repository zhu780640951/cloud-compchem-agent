import pathlib,os,json,re,subprocess
base=pathlib.Path('/content/drive/MyDrive')
assert base.is_dir(),'Google Drive is not mounted at /content/drive/MyDrive'
report={'drive_mounted':True,'root_directories':[],'root_files':[],'candidates':[]}
report['gpu']=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],capture_output=True,text=True,timeout=15).stdout.strip()
entries=sorted(base.iterdir(),key=lambda p:p.name.lower())
for p in entries[:150]:
 if p.is_dir(): report['root_directories'].append(p.name)
 elif any(t in p.name.lower() for t in ['qe','espresso','colab','sncl','upf','gpu']): report['root_files'].append(p.name)
roots=[p for p in entries if p.is_dir() and any(t in p.name.lower() for t in ['qe','espresso','colab','material','sncl','phim','计算','卤化','苯并'])]
for searchroot in roots:
 for current,dirs,files in os.walk(searchroot):
  depth=len(pathlib.Path(current).relative_to(searchroot).parts)
  dirs[:]=[d for d in dirs if d not in {'.git','node_modules','site-packages','__pycache__'} and depth<3]
  for name in files:
   low=name.lower()
   if low=='pw.x' or low.endswith('.upf') or (low.endswith(('.tar.gz','.tar.xz','.tgz','.zip','.sh','.ipynb','.md','.json')) and any(t in low for t in ['qe','espresso','gpu','env','restore','install','relax','readme','manifest','pseudo'])):
    p=pathlib.Path(current)/name
    report['candidates'].append({'path':str(p),'bytes':p.stat().st_size})
pathlib.Path('/content/drive_qe_inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))