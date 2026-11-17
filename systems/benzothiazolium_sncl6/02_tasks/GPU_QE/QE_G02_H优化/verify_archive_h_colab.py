import pathlib,re,json,tarfile,shutil,math
w=pathlib.Path('/content/benzothiazole_qe_g02_h_relax');d=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/Codex_H优化_20261030')
t=(w/'h_relax_resume.out').read_text(errors='replace');initial=(w/'h_relax.in').read_text();
print('RESTART_EVIDENCE')
for l in t.splitlines():
 if any(k in l.lower() for k in ['restart','reading file','bfgs converged','gradient error','total force =','end of bfgs']):print(l.strip())
blocks=re.findall(r'ATOMIC_POSITIONS\s*\(?crystal\)?\s*\n((?:\s*[A-Za-z]+\s+[-+\d.Ee]+\s+[-+\d.Ee]+\s+[-+\d.Ee]+[^\n]*\n){43})',t)
assert blocks,'no final coordinate block'
def parse(b):
 return [(x.split()[0],[float(y) for y in x.split()[1:4]]) for x in b.strip().splitlines()]
final=parse(blocks[-1]);start=initial.split('ATOMIC_POSITIONS crystal\n',1)[1].split('K_POINTS',1)[0];orig=parse(start);assert len(final)==len(orig)==43
heavy=max(abs(x-y) for (e,a),(e2,b) in zip(orig,final) if e!='H' for x,y in zip(a,b));assert all(a[0]==b[0] for a,b in zip(orig,final))
force_blocks=re.findall(r'Forces acting on atoms \(cartesian axes, Ry/au\):\s*\n(.*?)(?=\n\s*Total force\s*=)',t,re.S)
section=force_blocks[-1];matches=re.findall(r'atom\s+\d+\s+type\s+\d+\s+force\s*=\s*([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)',section);forces=[[float(x) for x in r] for r in matches[:43]]
assert len(forces)==43
maxh=max(abs(q) for (e,_),f in zip(final,forces) if e=='H' for q in f)
result={'bfgs_converged':bool(re.search(r'bfgs converged',t,re.I)),'max_h_force_component_ry_bohr':maxh,'max_h_force_component_eV_A':maxh*25.711043,'target_component_ry_bohr':0.000778,'heavy_max_fractional_change':heavy,'n_atoms':len(final),'n_H':sum(e=='H' for e,_ in final),'restart_mentions':[l.strip() for l in t.splitlines() if 'restart' in l.lower()][:12]}
(w/'R_H_final_crystal.txt').write_text('ATOMIC_POSITIONS crystal\n'+blocks[-1]);(w/'verification.json').write_text(json.dumps(result,indent=2));shutil.copy2(w/'R_H_final_crystal.txt',d/'R_H_final_crystal.txt');shutil.copy2(w/'verification.json',d/'verification.json')
archive=w/'H_relax_results.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for n in ['h_relax.in','h_relax.out','status.json','h_relax_resume.in','h_relax_resume.out','resume_status.json','R_H_final_crystal.txt','verification.json']:
  tar.add(w/n,arcname=n)
 for n in ['failed_input_order_h_relax.in','failed_input_order_h_relax.out','failed_input_order_status.json']:
  if (d/n).exists():tar.add(d/n,arcname=n)
shutil.copy2(archive,d/archive.name)
print('VERIFY_JSON',json.dumps(result),flush=True);print('ARCHIVE',archive,archive.stat().st_size)