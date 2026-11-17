"""Independent H2 GPU execution and Drive checkpoint roundtrip smoke test."""
import pathlib,os,shutil,subprocess,json,time,re,datetime,signal
base=pathlib.Path('/content/drive/MyDrive')
cache=pathlib.Path('/content/qe_drive_restore')
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
run=pathlib.Path('/content')/('codex_qe_h2_'+stamp)
run.mkdir();(run/'pseudo').mkdir()
drive=base/'苯并噻唑SnCl4计算'/'Codex_连接恢复测试'/stamp
drive.mkdir(parents=True,exist_ok=False)
pseudo=base/'苯并噻唑SnCl4计算'/'02_QE周期性DFT'/'pseudo'/'H.pbe-rrkjus_psl.1.0.0.UPF'
shutil.copy2(pseudo,run/'pseudo'/pseudo.name)
env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(cache/'lib')+':'+env.get('LD_LIBRARY_PATH',''),OMP_NUM_THREADS='2',CUDA_VISIBLE_DEVICES='0')
report={'test_kind':'H2 single-point GPU and Drive checkpoint roundtrip, not a crystal calculation','run_directory':str(run),'drive_directory':str(drive),'pseudo_source':str(pseudo),'qe_executable':str(cache/'bin/pw.x'),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runs':[]}
def persist():
 (run/'test_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 shutil.copy2(run/'test_report.json',drive/'test_report.json')
def make_input(outdir,from_file=False):
 return """&CONTROL
 calculation='scf', prefix='codex_h2', outdir='%s', pseudo_dir='./pseudo',
 disk_io='low', verbosity='high', tprnfor=.true., max_seconds=90,
/
&SYSTEM
 ibrav=1, celldm(1)=18.89726125, nat=2, ntyp=1,
 ecutwfc=80, ecutrho=640, occupations='fixed',
/
&ELECTRONS
 conv_thr=1.0d-9, electron_maxstep=100, mixing_beta=0.3,%s
/
ATOMIC_SPECIES
 H 1.00794 %s
ATOMIC_POSITIONS angstrom
 H 5.0 5.0 4.63
 H 5.0 5.0 5.37
K_POINTS gamma
"""%(outdir," startingpot='file', startingwfc='file'," if from_file else '',pseudo.name)
def execute(label,text):
 inp=run/(label+'.in');out=run/(label+'.out');inp.write_text(text)
 shutil.copy2(inp,drive/inp.name)
 start=time.monotonic();samples=[];last_sync=-99
 with out.open('w') as stream:
  proc=subprocess.Popen([str(cache/'bin/pw.x'),'-in',inp.name],cwd=run,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  print('QE_STARTED',label,'pid',proc.pid,flush=True)
  while proc.poll() is None:
   now=time.monotonic()
   gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],capture_output=True,text=True,timeout=10)
   samples.append({'elapsed_s':round(now-start,3),'processes':gpu.stdout.strip()})
   if now-last_sync>=3:
    shutil.copy2(out,drive/out.name);last_sync=now
    print('QE_MONITOR',label,'elapsed_s',round(now-start,1),'log_bytes',out.stat().st_size,flush=True)
   if now-start>120:
    os.killpg(proc.pid,signal.SIGTERM);proc.wait(timeout=15);break
   time.sleep(0.4)
  rc=proc.wait()
 text=out.read_text(errors='replace')
 shutil.copy2(out,drive/out.name)
 energies=re.findall(r'!\s+total energy\s*=\s*([-+0-9.EeDd]+)\s+Ry',text)
 row={'label':label,'exit_code':rc,'job_done':'JOB DONE.' in text,'scf_converged':'convergence has been achieved' in text,'gpu_active':'GPU acceleration is ACTIVE' in text,'gpu_process_observed':any(re.search(r'^'+str(proc.pid)+r'\s*,',s['processes'],re.M) for s in samples),'energy_Ry':float(energies[-1].replace('D','E')) if energies else None,'elapsed_seconds':round(time.monotonic()-start,3),'monitor_samples':samples}
 report['runs'].append(row);persist();print(json.dumps(row,ensure_ascii=False),flush=True)
 if not (rc==0 and row['job_done'] and row['scf_converged'] and row['gpu_active']): raise RuntimeError('QE test did not complete with GPU and SCF convergence')
 return row
try:
 persist()
 first=execute('h2_initial',make_input('./scratch'))
 saved=run/'scratch'/'codex_h2.save'
 assert (saved/'data-file-schema.xml').exists(),'Missing checkpoint XML'
 assert list(saved.glob('wfc*')),'Missing wavefunction checkpoint'
 shutil.copytree(saved,drive/'codex_h2.save')
 shutil.copytree(run/'pseudo',drive/'pseudo')
 report['checkpoint_files']=[{'path':str(p.relative_to(saved)),'bytes':p.stat().st_size} for p in saved.rglob('*') if p.is_file()]
 restore=run/'scratch_restored'/'codex_h2.save';restore.parent.mkdir()
 shutil.copytree(drive/'codex_h2.save',restore)
 second=execute('h2_from_drive_checkpoint',make_input('./scratch_restored',True))
 report['energy_difference_Ry']=abs(first['energy_Ry']-second['energy_Ry'])
 assert report['energy_difference_Ry']<1e-6,'Checkpoint roundtrip energy mismatch'
 report['checkpoint_roundtrip_ok']=True
 report['all_passed']=True
except Exception as e:
 report.update(all_passed=False,error_type=type(e).__name__,error_message=str(e))
finally:
 report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();persist()
 archive=shutil.make_archive(str(run)+'_results','gztar',run)
 shutil.copy2(archive,drive/'local_results_archive.tar.gz')
 pointer={'run_directory':str(run),'drive_directory':str(drive),'archive':archive,'report':str(run/'test_report.json'),'all_passed':report.get('all_passed',False)}
 pathlib.Path('/content/codex_qe_test_pointer.json').write_text(json.dumps(pointer,ensure_ascii=False,indent=2))
 print('QE_TEST_RESULT',json.dumps(report,ensure_ascii=False,indent=2),flush=True)
 print('QE_TEST_POINTER',json.dumps(pointer,ensure_ascii=False),flush=True)