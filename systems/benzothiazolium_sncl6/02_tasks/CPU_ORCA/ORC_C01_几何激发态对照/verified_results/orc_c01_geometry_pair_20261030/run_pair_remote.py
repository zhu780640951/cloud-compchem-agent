import pathlib,subprocess,json,os,time,re
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
