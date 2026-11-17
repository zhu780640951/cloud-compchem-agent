import pathlib,json,subprocess,shutil,os
base=pathlib.Path('/content/drive/MyDrive')
report={'qe_build_top':[(p.name,'dir' if p.is_dir() else p.stat().st_size) for p in (base/'QE_build').iterdir()]}
for rel in ['苯并噻唑SnCl4计算/02_QE周期性DFT/scripts/setup_qe_gpu.sh','QE_PhIm2SnCl6/01_relax_PBE-D3/setup_qe_gpu.sh']:
 p=base/rel
 report[rel]=p.read_text(errors='replace') if p.exists() else None
src=base/'QE_build/qe-7.5-gpu-sm80/bin/pw.x'
dst=pathlib.Path('/content/qe_drive_restore/bin/pw.x');dst.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(src,dst);dst.chmod(0o755)
report['ldd']=subprocess.run(['ldd',str(dst)],capture_output=True,text=True,timeout=20).stdout
report['local_runtime_dirs']=[str(p) for root in ['/opt/nvidia/hpc_sdk','/usr/local/cuda','/opt','/usr/local'] for p in [pathlib.Path(root)] if p.exists()]
pathlib.Path('/content/qe_restore_inspection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))