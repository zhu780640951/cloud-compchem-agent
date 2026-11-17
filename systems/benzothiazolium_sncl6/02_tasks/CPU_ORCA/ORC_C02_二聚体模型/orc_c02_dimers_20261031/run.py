import pathlib,os,subprocess,json,time
p=pathlib.Path(__file__).parent;env=os.environ.copy();env['PATH']='/opt/openmpi-4.1.8/bin:/opt/orca:'+env.get('PATH','');env['LD_LIBRARY_PATH']='/opt/openmpi-4.1.8/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='1';rows=[]
for label in ['dimer_1','dimer_2']:
 start=time.time()
 with (p/(label+'.out')).open('w') as out: q=subprocess.run(['/opt/orca/orca',label+'.inp'],cwd=p,env=env,stdout=out,stderr=subprocess.STDOUT)
 t=(p/(label+'.out')).read_text(errors='replace');rows.append({'name':label,'rc':q.returncode,'normal':'ORCA TERMINATED NORMALLY' in t,'elapsed_seconds':round(time.time()-start,1)});(p/'status.json').write_text(json.dumps(rows));
 if q.returncode!=0 or not rows[-1]['normal']:break
