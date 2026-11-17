import pathlib,tarfile,shutil,hashlib,json
w=pathlib.Path('/content/benzothiazole_qe_g03_all_relax');d=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_全原子优化_20261030');p=w/'R_fixed_full_tmp.tar'
with tarfile.open(p,'w') as t:t.add(w/'tmp',arcname='tmp')
h=hashlib.sha256()
with p.open('rb') as f:
 for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
shutil.copy2(p,d/p.name)
r={'file':p.name,'bytes':p.stat().st_size,'sha256':h.hexdigest(),'drive_file_bytes':(d/p.name).stat().st_size,'note':'full final tmp; Drive size verified, full readback hash pending'}
(w/'checkpoint_metadata.json').write_text(json.dumps(r,indent=2));shutil.copy2(w/'checkpoint_metadata.json',d/'checkpoint_metadata.json');print(json.dumps(r))