import tarfile,pathlib
p=pathlib.Path(__file__).parent
with tarfile.open(p/'electronic_stage2_results.tar.gz') as t:
 s=t.extractfile('pdos.out').read().decode(errors='replace')
 i=s.find('Lowdin Charges');print(s[i:i+8000])