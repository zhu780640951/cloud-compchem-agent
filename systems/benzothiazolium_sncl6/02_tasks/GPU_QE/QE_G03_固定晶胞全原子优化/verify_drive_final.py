import pathlib,json,hashlib
w=pathlib.Path('/content/benzothiazole_qe_g03_all_relax');d=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_全原子优化_20261030');r=json.loads((w/'checkpoint_metadata.json').read_text());h=hashlib.sha256()
with (d/r['file']).open('rb') as f:
 for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
r['drive_readback_sha256']=h.hexdigest();r['drive_readback_verified']=r['sha256']==h.hexdigest();(w/'checkpoint_readback.json').write_text(json.dumps(r,indent=2));(d/'checkpoint_readback.json').write_text(json.dumps(r,indent=2));print(json.dumps(r));assert r['drive_readback_verified']