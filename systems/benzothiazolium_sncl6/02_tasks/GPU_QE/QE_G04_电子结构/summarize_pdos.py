import pathlib,re,json,collections
w=pathlib.Path('/content/qe_optimized_electronic');d=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_优化晶胞电子结构_20261031');text=(w/'optimized_nscf.out').read_text(errors='replace');parts=text.split('bands (ev):')[1:];levels=[]
for block in parts:
 vals=[]
 for line in block.splitlines():
  if not line.strip():
   if vals:break
   continue
  if re.fullmatch(r'[\s+\-\d\.Ee]+',line):vals.extend(float(x) for x in line.split())
  elif vals:break
 if len(vals)==105:levels.append(vals)
assert len(levels)>0,(len(parts),[len(levels)])
vbm=max(x[80] for x in levels);cbm=min(x[81] for x in levels)
windows={'valence':[vbm-0.2,vbm+0.03],'conduction':[cbm-0.03,cbm+0.2]};groups={}
for label,(lo,hi) in windows.items():
 totals=collections.defaultdict(float)
 for f in w.glob('optimized.pdos.pdos_atm#*'):
  m=re.search(r'\((\w+)\)_wfc#\d+\((\w+)\)',f.name)
  if not m:continue
  for l in f.read_text().splitlines():
   if l.startswith('#'):continue
   cols=l.split()
   if len(cols)>1 and lo<=float(cols[0])<=hi:totals[m.group(1)+'-'+m.group(2)]+=float(cols[1])
 total=sum(totals.values());groups[label]={'range_eV':[lo,hi],'fraction_of_projected_dos':{k:round(v/total,4) for k,v in sorted(totals.items(),key=lambda x:-x[1])} if total else {}}
r={'kpoints_analyzed':len(levels),'occupied_bands':81,'vbm_ev':vbm,'cbm_ev':cbm,'indirect_sampled_gap_ev':round(cbm-vbm,4),'gap_scope':'4x4x3 sampled Kohn-Sham PBE-D3 scalar-relativistic; no SOC; not optical gap or emission energy','pdos_window_analysis':groups,'warning':'Finite-window, projected-DOS normalized contributions; orbital projection and energy-grid window dependent, not excitation character.'}
(w/'bandedge_summary.json').write_text(json.dumps(r,indent=2));(d/'bandedge_summary.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))