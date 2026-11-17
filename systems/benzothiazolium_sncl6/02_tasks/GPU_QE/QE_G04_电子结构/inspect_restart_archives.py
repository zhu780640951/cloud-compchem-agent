import pathlib,tarfile,json
b=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_全原子优化_20261030')
for n in ['full_tmp_after_segment1.tar','R_fixed_full_tmp.tar']:
 p=b/n
 if not p.exists():print(n,'missing');continue
 with tarfile.open(p) as t:
  names=t.getnames();print(json.dumps({'archive':n,'size':p.stat().st_size,'restart_entries':[x for x in names if x.endswith(('.bfgs','.update','.restart_scf','data-file-schema.xml'))]},ensure_ascii=False))