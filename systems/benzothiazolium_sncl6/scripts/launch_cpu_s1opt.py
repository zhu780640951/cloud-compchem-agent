import pathlib,subprocess,base64,json
root=pathlib.Path(__file__).resolve().parents[1];job=root/'02_计算任务'/'CPU_ORCA'/'ORC_C01_S1激发态优化';job.mkdir(exist_ok=True)
pair=root/'02_计算任务'/'CPU_ORCA'/'ORC_C01_几何激发态对照'/'opt_pair.inp'
text=pair.read_text(encoding='utf-8');coords=text.split('* xyz 1 1',1)[1].rsplit('*',1)[0].strip()
inp='! PBE0 def2-SVP def2/J RIJCOSX VeryTightSCF DEFGRID3 TightOpt\n%pal nprocs 12 end\n%maxcore 4000\n%scf ConvCheckMode 0 MaxIter 300 end\n%tddft\n nroots 6\n tda true\n iroot 1\n irootmult singlet\n end\n%geom MaxIter 100 end\n* xyz 1 1\n'+coords+'\n*\n'
(job/'s1_opt.inp').write_text(inp,encoding='utf-8')
remote="""import pathlib,subprocess,json,os,time
p=pathlib.Path.home()/'codex_calculations/benzothiazolium_sncl6/orc_c01_s1opt_20261030';p.mkdir(exist_ok=False)
(p/'s1_opt.inp').write_text(INPUT)
env=os.environ.copy();env['PATH']='/opt/openmpi-4.1.8/bin:/opt/orca:'+env.get('PATH','');env['LD_LIBRARY_PATH']='/opt/openmpi-4.1.8/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='1'
f=(p/'s1_opt.out').open('w');proc=subprocess.Popen(['/opt/orca/orca','s1_opt.inp'],cwd=p,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
j={'pid':proc.pid,'path':str(p),'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())};(p/'launch.json').write_text(json.dumps(j));print(json.dumps(j))
""".replace('INPUT',repr(inp))
cmd='python3 -c "import base64;exec(base64.b64decode(\''+base64.b64encode(remote.encode()).decode()+'\'))"'
a=[r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd','compute','ssh','y@orca-cpu-16','--project=<YOUR_GCP_PROJECT_ID>','--zone=us-central1-a','--account=<YOUR_GCP_EMAIL>','--ssh-key-file='+str(root/'连接配置'/'gcp_test_key'),'--ssh-key-expire-after=30m','--quiet','--command='+cmd]
p=subprocess.run(a,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90);(job/'启动记录.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8');print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)