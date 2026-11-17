import pathlib,os,shutil,subprocess,json,time
cache=pathlib.Path('/content/drive/MyDrive/QE_build/qe-7.5-gpu-sm80')
local=pathlib.Path('/content/qe_drive_restore')
report={'cache':str(cache),'local':str(local),'build_info':(cache/'BUILD_INFO.txt').read_text() if (cache/'BUILD_INFO.txt').exists() else None,'copied_files':[]}
for sub in ['bin','lib']:
 dest=local/sub;dest.mkdir(parents=True,exist_ok=True)
 for p in sorted((cache/sub).iterdir()):
  if not p.is_file(): continue
  shutil.copyfile(p,dest/p.name)
  if sub=='bin': (dest/p.name).chmod(0o755)
  report['copied_files'].append({'name':sub+'/'+p.name,'bytes':p.stat().st_size})
  print('RESTORED',sub+'/'+p.name,p.stat().st_size,flush=True)
env=os.environ.copy();env['LD_LIBRARY_PATH']=str(local/'lib')+':'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='2'
ldd=subprocess.run(['ldd',str(local/'bin/pw.x')],env=env,capture_output=True,text=True,timeout=20)
report['ldd']=ldd.stdout
report['dependencies_resolved']='not found' not in ldd.stdout
if report['dependencies_resolved']:
 p=subprocess.run([str(local/'bin/pw.x'),'-h'],env=env,capture_output=True,text=True,timeout=30)
 report['help_returncode']=p.returncode;report['startup_output']=(p.stdout+p.stderr)[:14000]
pathlib.Path('/content/qe_restore_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)