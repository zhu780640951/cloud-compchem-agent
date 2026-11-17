import pathlib,json,math,re,shutil
w=pathlib.Path('/content/benzothiazole_qe_g01');dest=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_晶胞试算_20261030')
rows=json.loads((w/'convergence_progress.json').read_text());base=(w/'scf_60_480_k222.out').read_text(errors='replace')
f=[[float(x) for x in m.groups()] for m in re.finditer(r'atom\s+\d+\s+type\s+\d+\s+force\s*=\s*([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)',base)]
rows.insert(0,{'case':'scf_60_480_k222','energy_ry':-828.18466266,'forces_ry_bohr':f[-43:]})
by={r['case']:r for r in rows}
for name,row in by.items():
 text=(w/(name+'.out')).read_text(errors='replace')
 section=text.split('Forces acting on atoms (cartesian axes, Ry/au):',1)[1]
 matches=list(re.finditer(r'atom\s+\d+\s+type\s+\d+\s+force\s*=\s*([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)',section))
 row['forces_ry_bohr']=[[float(v) for v in m.groups()] for m in matches[:43]]
def compare(a,b):
 x,y=by[a],by[b];assert len(x['forces_ry_bohr'])==len(y['forces_ry_bohr'])==43
 diff=max(abs(v-u) for fa,fb in zip(x['forces_ry_bohr'],y['forces_ry_bohr']) for v,u in zip(fa,fb))*25.711043
 return {'cases':[a,b],'energy_meV_per_atom':abs(x['energy_ry']-y['energy_ry'])*13.605693*1000/43,'max_force_component_eV_A':diff,'energy_target_meV_atom':1,'force_target_eV_A':0.005,'passed_energy':abs(x['energy_ry']-y['energy_ry'])*13.605693*1000/43<1,'passed_force':diff<0.005}
summary={'pairs':[compare('scf_60_480_k222','scf_80_640_k222'),compare('scf_80_640_k222','scf_100_800_k222'),compare('scf_80_640_k222','scf_80_640_k332'),compare('scf_80_640_k332','scf_80_640_k443')],'limits':'Fixed original CIF geometry; total forces extracted from first total-force block, not D3 component; band gap and optimized geometry not checked; mixed PBE pseudopotentials need provenance check.'}
(w/'convergence_analysis.json').write_text(json.dumps(summary,indent=2));shutil.copy2(w/'convergence_analysis.json',dest/'convergence_analysis.json');print(json.dumps(summary,indent=2))