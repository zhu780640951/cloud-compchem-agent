import pathlib,re,json,tarfile,hashlib,shutil
w=pathlib.Path('/content/qe_band_edge_density');d=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_带边密度_20261031');t=(w/'edge_nscf.out').read_text(errors='replace')
pat=r'k\s*=\s*([-+]?\d+\.\d+)\s*([-+]?\d+\.\d+)\s*([-+]?\d+\.\d+)\s*\(\s*\d+\s+PWs\)\s+bands \(ev\):';ms=list(re.finditer(pat,t,re.I));rows=[]
for m in ms:
 vals=[]
 for line in t[m.end():].splitlines():
  if not line.strip():
   if vals:break
   continue
  if re.fullmatch(r'[\s+\-\d\.Ee]+',line):vals.extend(float(x) for x in line.split())
  elif vals:break
 if len(vals)==105:rows.append({'k':[float(x) for x in m.groups()],'v':vals[80],'c':vals[81]})
assert len(rows)==26
vi=max(range(len(rows)),key=lambda i:rows[i]['v']);ci=min(range(len(rows)),key=lambda i:rows[i]['c']);assert (vi+1,ci+1)==(6,1)
r={'irreducible_kpoints':len(rows),'vbm_k_index':vi+1,'vbm_k_tpiba':rows[vi]['k'],'vbm_ev':rows[vi]['v'],'vbm_band':81,'cbm_k_index':ci+1,'cbm_k_tpiba':rows[ci]['k'],'cbm_ev':rows[ci]['c'],'cbm_band':82,'gap_eV':round(rows[ci]['c']-rows[vi]['v'],4),'plot_num':7,'nature':'selected-state pseudo-charge density, not full all-electron density or excited-state NTO'}
(w/'verification.json').write_text(json.dumps(r,indent=2));shutil.copy2(w/'verification.json',d/'verification.json')
a=w/'edge_density_results.tar.gz'
with tarfile.open(a,'w:gz') as tar:
 for n in ['edge_nscf.in','edge_nscf.out','VBM.in','VBM.out','VBM.cube','CBM.in','CBM.out','CBM.cube','verification.json']:tar.add(w/n,arcname=n)
shutil.copy2(a,d/a.name);print('VERIFY',json.dumps(r));print('ARCHIVE',str(a),a.stat().st_size)