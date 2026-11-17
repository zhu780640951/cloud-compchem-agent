import pathlib,json,shutil,socket,datetime,tempfile,tarfile
base=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_连接恢复测试/20261030T110920Z')
prior=json.loads((base/'test_report.json').read_text())
assert prior['all_passed']
recovered=pathlib.Path(tempfile.mkdtemp(prefix='codex_checkpoint_readback_',dir='/content'))
shutil.copytree(base/'codex_h2.save',recovered/'codex_h2.save')
rows=[]
for expected in prior['checkpoint_files']:
 p=recovered/'codex_h2.save'/expected['path']
 assert p.is_file() and p.stat().st_size==expected['bytes']
 with p.open('rb') as stream:
  count=0
  while block:=stream.read(1024*1024): count+=len(block)
 assert count==expected['bytes']
 rows.append({'file':expected['path'],'bytes_read':count})
archive=base/'local_results_archive.tar.gz'
with tarfile.open(archive,'r:gz') as tf:
 members=tf.getnames()
 assert any(n.endswith('h2_initial.out') for n in members)
 assert any(n.endswith('h2_from_drive_checkpoint.out') for n in members)
report={'persistence_after_a100_release_ok':True,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'new_runtime_hostname':socket.gethostname(),'old_ephemeral_run_directory_absent':not pathlib.Path(prior['run_directory']).exists(),'drive_directory':str(base),'checkpoint_readback':rows,'archive_readable':True,'original_qe_energies_Ry':[r['energy_Ry'] for r in prior['runs']],'recovered_directory':str(recovered)}
pathlib.Path('/content/drive_persistence_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
(base/'persistence_after_release.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))