import pathlib,tarfile,json,shutil
w=pathlib.Path('/content/qe_optimized_electronic');d=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_优化晶胞电子结构_20261031');a=w/'electronic_stage2_results.tar.gz'
files=[p for p in w.iterdir() if p.is_file() and (p.suffix in ['.in','.out','.json','.dos'] or p.name.startswith('optimized.pdos.'))]
with tarfile.open(a,'w:gz') as tar:
 for p in files:tar.add(p,arcname=p.name)
shutil.copy2(a,d/a.name);print('ARCHIVE',str(a),'bytes',a.stat().st_size,'files',len(files))