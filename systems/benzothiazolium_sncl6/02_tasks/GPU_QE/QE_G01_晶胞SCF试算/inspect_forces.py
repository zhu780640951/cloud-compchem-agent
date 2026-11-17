import pathlib,re
w=pathlib.Path('/content/benzothiazole_qe_g01')
for name in ['scf_60_480_k222','scf_80_640_k222','scf_100_800_k222']:
 t=(w/(name+'.out')).read_text(errors='replace')
 print('CASE',name)
 for line in t.splitlines():
  if ('force =' in line and ('atom    1 ' in line or 'atom   10 ' in line)) or 'Forces acting on atoms' in line or 'contribution' in line.lower() and 'force' in line.lower():print(line)