import pathlib,subprocess,base64,json,datetime
root=pathlib.Path(__file__).resolve().parents[1]
job=root/'02_计算任务'/'CPU_ORCA'/'ORC_C01_S0优化与频率';job.mkdir(exist_ok=True)
xyz=(root/'02_计算任务'/'00_正式计算准备_20261030'/'有机阳离子_15原子_XRD.xyz').read_text(encoding='utf-8').splitlines()
assert int(xyz[0])==15
coords='\n'.join(xyz[2:]).strip()
settings='! PBE0 def2-SVP def2/J RIJCOSX VeryTightSCF DEFGRID3\n%pal nprocs 12 end\n%maxcore 4000\n'
inputs={
'xrd_stability.inp':settings+'%scf ConvCheckMode 0 MaxIter 300 STABPerform true end\n* xyz 1 1\n'+coords+'\n*\n',
's0_optfreq.inp':settings+'! TightOpt Freq\n%scf ConvCheckMode 0 MaxIter 300 end\n%geom MaxIter 100 end\n* xyz 1 1\n'+coords+'\n*\n'}
for name,txt in inputs.items(): (job/name).write_text(txt,encoding='utf-8')
remote='''import pathlib,subprocess,base64,json,os,time
base=pathlib.Path.home()/'codex_calculations/benzothiazolium_sncl6'
p=base/'orc_c01_s0optfreq_20261030'
p.mkdir(exist_ok=False)
for name,txt in INPUTS.items(): (p/name).write_text(txt)
env=os.environ.copy();env['PATH']='/opt/openmpi-4.1.8/bin:/opt/orca:'+env.get('PATH','');env['LD_LIBRARY_PATH']='/opt/openmpi-4.1.8/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='1'
f=(p/'xrd_stability.out').open('w');proc=subprocess.Popen(['/opt/orca/orca','xrd_stability.inp'],cwd=p,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
j={'pid':proc.pid,'path':str(p),'current_job':'xrd_stability','start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'scope':'isolated cation +1 singlet; PBE0/def2-SVP VeryTightSCF DEFGRID3'}
(p/'launch.json').write_text(json.dumps(j,indent=2));print(json.dumps(j))
'''.replace('INPUTS',repr(inputs))
cmd='python3 -c "import base64;exec(base64.b64decode(\''+base64.b64encode(remote.encode()).decode()+'\'))"'
a=[r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd','compute','ssh','y@orca-cpu-16','--project=<YOUR_GCP_PROJECT_ID>','--zone=us-central1-a','--account=<YOUR_GCP_EMAIL>','--ssh-key-file='+str(root/'连接配置'/'gcp_test_key'),'--ssh-key-expire-after=30m','--quiet','--command='+cmd]
p=subprocess.run(a,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=80)
(job/'launch_stability.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8');print(p.stdout);print(p.stderr)
if p.returncode==0: (job/'launch_stability.json').write_text(p.stdout,encoding='utf-8')
raise SystemExit(p.returncode)