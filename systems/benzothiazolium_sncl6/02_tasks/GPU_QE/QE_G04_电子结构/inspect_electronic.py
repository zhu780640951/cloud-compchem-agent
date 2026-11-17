from pathlib import Path
p=Path('/content/qe_optimized_electronic')
for n in ['optimized_scf.out','optimized_nscf.out','dos.out','pdos.out']:
 t=(p/n).read_text(errors='replace');print('FILE',n)
 print('\n'.join(x for x in t.splitlines() if any(k in x.lower() for k in ['number of electrons','number of kohn-sham','highest occupied','lowest unoccupied','fermi energy','spilling parameter','job done']))[-1200:])
 print('TAIL',t[-1200:] if n=='optimized_nscf.out' else '')