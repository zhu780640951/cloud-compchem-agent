import pathlib,json,subprocess,base64
root=pathlib.Path(__file__).resolve().parents[1]
job=root/'02_计算任务'/'CPU_ORCA'/'ORC_C01_几何激发态对照';job.mkdir(exist_ok=True)
old=root/'02_计算任务'/'00_正式计算准备_20261030'/'有机阳离子_15原子_XRD.xyz'
new=root/'02_计算任务'/'CPU_ORCA'/'ORC_C01_S0优化与频率'/'completed_remote_files'/'orc_c01_s0optfreq_20261030'/'s0_optfreq.xyz'
check=json.loads((new.parents[1].parent/'基态优化与频率_验收结果.json').read_text(encoding='utf-8'))
assert check['acceptance_passed']
def coords(p):
 x=p.read_text(encoding='utf-8-sig').splitlines();assert int(x[0])==15;return '\n'.join(x[2:17])
header='! PBE0 def2-SVP def2/J RIJCOSX VeryTightSCF DEFGRID3\n%pal nprocs 12 end\n%maxcore 4000\n%scf ConvCheckMode 0 MaxIter 300 end\n%tddft\n nroots 10\n tda true\n triplets true\n DoNTO true\n end\n* xyz 1 1\n'
inputs={k:header+coords(p)+'\n*\n' for k,p in [('xrd_pair.inp',old),('opt_pair.inp',new)]}
for k,v in inputs.items(): (job/k).write_text(v,encoding='utf-8')
runner='''import pathlib,subprocess,json,os,time,re
p=pathlib.Path(__file__).resolve().parent
status={'state':'running','stages':[],'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
def save(): (p/'status.json').write_text(json.dumps(status,indent=2))
env=os.environ.copy();env['PATH']='/opt/openmpi-4.1.8/bin:/opt/orca:'+env.get('PATH','');env['LD_LIBRARY_PATH']='/opt/openmpi-4.1.8/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='1'
for label in ['xrd_pair','opt_pair']:
 status['current']=label;save()
 with (p/(label+'.out')).open('w') as out:
  process=subprocess.run(['/opt/orca/orca',label+'.inp'],cwd=p,env=env,stdout=out,stderr=subprocess.STDOUT)
 t=(p/(label+'.out')).read_text(errors='replace')
 row={'label':label,'exit_code':process.returncode,'normal':'ORCA TERMINATED NORMALLY' in t,'scf':'SCF CONVERGED AFTER' in t,'residual_converged_count':t.count('CONVERGENCE OF RESIDUAL NORM REACHED')}
 status['stages'].append(row);save()
 if not (row['exit_code']==0 and row['normal'] and row['scf'] and row['residual_converged_count']>=2):
  status['state']='failed_or_needs_review';save();raise SystemExit(1)
status['state']='completed';status['finished_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());save()
'''
(job/'run_pair_remote.py').write_text(runner,encoding='utf-8')
payload={'inputs':inputs,'runner':runner}
remote="""import pathlib,subprocess,base64,json,os,time
p=pathlib.Path.home()/'codex_calculations/benzothiazolium_sncl6/orc_c01_geometry_pair_20261030';p.mkdir(exist_ok=False)
data=PAYLOAD
for name,txt in data['inputs'].items(): (p/name).write_text(txt)
(p/'run_pair_remote.py').write_text(data['runner'])
f=(p/'runner.log').open('w');proc=subprocess.Popen(['python3','run_pair_remote.py'],cwd=p,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
j={'pid':proc.pid,'path':str(p),'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())};(p/'launch.json').write_text(json.dumps(j,indent=2));print(json.dumps(j))
""".replace('PAYLOAD',repr(payload))
cmd='python3 -c "import base64;exec(base64.b64decode(\''+base64.b64encode(remote.encode()).decode()+'\'))"'
a=[r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd','compute','ssh','y@orca-cpu-16','--project=<YOUR_GCP_PROJECT_ID>','--zone=us-central1-a','--account=<YOUR_GCP_EMAIL>','--ssh-key-file='+str(root/'连接配置'/'gcp_test_key'),'--ssh-key-expire-after=30m','--quiet','--command='+cmd]
p=subprocess.run(a,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
(job/'启动记录.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8');print(p.stdout);print(p.stderr)
if p.returncode==0:(job/'launch.json').write_text(p.stdout,encoding='utf-8')
raise SystemExit(p.returncode)