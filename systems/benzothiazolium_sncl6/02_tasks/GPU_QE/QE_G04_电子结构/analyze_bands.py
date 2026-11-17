from pathlib import Path
import re
p=Path('/content/qe_optimized_electronic');t=(p/'optimized_nscf.out').read_text(errors='replace')
for l in t.splitlines():
 if 'bands (ev)' in l.lower() or 'k =' in l and 'bands' in l:print(l[:160])
print('PDOS_HEAD', (p/'optimized.pdos.pdos_tot').read_text().splitlines()[:3])
print('DOS_HEAD',(p/'optimized.dos').read_text().splitlines()[:4])