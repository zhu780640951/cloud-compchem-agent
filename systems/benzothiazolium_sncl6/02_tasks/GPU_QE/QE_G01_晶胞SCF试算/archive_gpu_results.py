import pathlib,tarfile,json,shutil
w=pathlib.Path('/content/benzothiazole_qe_g01');d=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_晶胞试算_20261030');archive=w/'QE_G01_results.tar.gz'
files=sorted(w.glob('scf_*k*.in'))+sorted(w.glob('scf_*k*.out'))+[w/'scf_result.json',w/'convergence_analysis.json',w/'pseudo_metadata.json']
with tarfile.open(archive,'w:gz') as tar:
 for f in files:
  if f.exists():tar.add(f,arcname=f.name)
 tar.add(w/'pseudo',arcname='pseudo')
shutil.copy2(archive,d/archive.name)
print('ARCHIVE',archive,'bytes',archive.stat().st_size,'files',len(files))