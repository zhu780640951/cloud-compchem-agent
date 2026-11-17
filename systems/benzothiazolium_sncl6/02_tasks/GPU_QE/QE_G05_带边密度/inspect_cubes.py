import tarfile,pathlib
p=pathlib.Path(__file__).parent
with tarfile.open(p/'edge_density_results.tar.gz') as t:
 for name in ('VBM.cube','CBM.cube'):
  f=t.extractfile(name)
  print(name,''.join(f.readline().decode() for _ in range(7)))