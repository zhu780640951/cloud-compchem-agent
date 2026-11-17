import pathlib,tarfile,re,json
w=pathlib.Path(__file__).parent
with tarfile.open(w/'electronic_stage2_results.tar.gz') as tar:t=tar.extractfile('optimized_nscf.out').read().decode(errors='replace')
pat=r'k\s*=\s*([-+]?\d+\.\d+)\s*([-+]?\d+\.\d+)\s*([-+]?\d+\.\d+)\s*\(\s*\d+\s+PWs\)\s+bands \(ev\):'
ms=list(re.finditer(pat,t,re.I));rows=[]
for m in ms:
 part=t[m.end():];vals=[]
 for l in part.splitlines():
  if not l.strip():
   if vals:break
   continue
  if re.fullmatch(r'[\s+\-\d\.Ee]+',l):vals.extend(float(x) for x in l.split())
  elif vals:break
 if len(vals)==105:rows.append({'k_tpiba':[float(x) for x in m.groups()],'vbm':vals[80],'cbm':vals[81]})
assert len(rows)==26
res={'vbm':max(rows,key=lambda x:x['vbm']),'cbm':min(rows,key=lambda x:x['cbm']),'scope':'QE k coordinates in 2pi/alat, unrounded output 4 decimals'};print(json.dumps(res))
(w/'band_edge_kpoints.json').write_text(json.dumps(res,indent=2))