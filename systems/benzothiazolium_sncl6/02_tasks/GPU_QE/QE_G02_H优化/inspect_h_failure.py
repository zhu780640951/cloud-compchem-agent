from pathlib import Path
print(Path('/content/benzothiazole_qe_g02_h_relax/h_relax.out').read_text(errors='replace')[-4000:])
