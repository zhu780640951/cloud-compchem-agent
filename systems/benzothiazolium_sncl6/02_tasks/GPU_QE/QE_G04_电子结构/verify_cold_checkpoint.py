import pathlib,hashlib,json,tarfile,os
base=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_全原子优化_20261030')
p=base/'R_fixed_full_tmp.tar';expected='41f3b2b48772d8792566549f7d1149d908ae7c03c7d89083e917be1049f251b5'
assert os.path.ismount('/content/drive') and p.is_file()
h=hashlib.sha256()
with p.open('rb') as f:
 for c in iter(lambda:f.read(8*1024*1024),b''):h.update(c)
with tarfile.open(p) as t:
 names=t.getnames();required=['tmp/crystal_allrelax.bfgs','tmp/crystal_allrelax.save/data-file-schema.xml'];missing=[n for n in required if n not in names]
r={'checkpoint_sha256':h.hexdigest(),'sha256_matches':h.hexdigest()==expected,'bytes':p.stat().st_size,'missing_required':missing,'scope':'fresh runtime readback only; cross-runtime restart not yet tested'}
print(json.dumps(r));assert r['sha256_matches'] and not missing