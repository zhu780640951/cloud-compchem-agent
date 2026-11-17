import os, pathlib, subprocess, json, time, glob, re, platform
root=pathlib.Path.home()/'codex_calculations'/'benzothiazolium_sncl6'/('connection_test_'+time.strftime('%Y%m%d_%H%M%S'))
root.mkdir(parents=True)
env=os.environ.copy()
mpi=sorted(glob.glob('/opt/*/bin/mpirun')+glob.glob('/opt/*/*/bin/mpirun'))
if mpi:
 bindir=str(pathlib.Path(mpi[0]).parent)
 env['PATH']=bindir+':/opt/orca:'+env.get('PATH','')
 libdir=str(pathlib.Path(bindir).parent/'lib')
 env['LD_LIBRARY_PATH']=libdir+':'+env.get('LD_LIBRARY_PATH','')
else: env['PATH']='/opt/orca:'+env.get('PATH','')
report={'remote_directory':str(root),'hostname':platform.node(),'logical_cpus':os.cpu_count(),'mpi_candidates':mpi,'tests':[]}
for ncores in (1,2):
 label='h2_hf_'+str(ncores)+'core'
 inp='! HF def2-SVP TightSCF\n%maxcore 128\n'
 if ncores>1: inp+='%pal nprocs '+str(ncores)+' end\n'
 inp+='* xyz 0 1\nH 0 0 0\nH 0 0 0.74\n*\n'
 (root/(label+'.inp')).write_text(inp)
 start=time.time()
 with (root/(label+'.out')).open('w') as out:
  p=subprocess.Popen(['/opt/orca/orca',label+'.inp'],cwd=root,stdout=out,stderr=subprocess.STDOUT,env=env)
  print('START',label,'PID',p.pid,flush=True)
  for _ in range(3):
   if p.poll() is not None: break
   time.sleep(0.5)
   print('MONITOR',label,'running',p.poll() is None,flush=True)
  try: rc=p.wait(timeout=90)
  except subprocess.TimeoutExpired:
   p.terminate();rc=p.wait(timeout=10)
 text=(root/(label+'.out')).read_text(errors='replace')
 row={'name':label,'cores':ncores,'exit_code':rc,'normal_termination':'ORCA TERMINATED NORMALLY' in text,'elapsed_seconds':round(time.time()-start,3),'energy_lines':re.findall(r'FINAL SINGLE POINT ENERGY[^\n]*',text),'version_lines':[x.strip() for x in text.splitlines() if 'Program Version' in x],'output_file':str(root/(label+'.out'))}
 report['tests'].append(row)
 print(json.dumps(row),flush=True)
 if not row['normal_termination']: print(text[-5000:],flush=True)
(root/'status.json').write_text(json.dumps(report,indent=2))
print('RESULT_JSON',json.dumps(report),flush=True)