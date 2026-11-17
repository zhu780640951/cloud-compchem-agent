import pathlib,tarfile,json,hashlib,shutil
w=pathlib.Path('/content/qe_cold_restart_test');d=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_冷启动续算验证_20261031');p=w/'restart_test_evidence.tar.gz'
with tarfile.open(p,'w:gz') as t:
 for n in ['cold_restart.in','cold_restart.out','status.json']:t.add(w/n,arcname=n)
shutil.copy2(p,d/p.name)
s=(w/'cold_restart.out').read_text(errors='replace');print('BFGS progress', [x.strip() for x in s.splitlines() if 'number of bfgs steps' in x.lower()][-3:]);print('archive',str(p),p.stat().st_size)