import pathlib,os,json,subprocess
w=pathlib.Path('/content/benzothiazole_qe_g01');print('work',[(x.name,x.stat().st_size) for x in w.iterdir()] if w.exists() else 'absent')
p=pathlib.Path('/content/drive/MyDrive/苯并噻唑SnCl4计算/02_QE周期性DFT/pseudo')
print('drive',os.path.ismount('/content/drive'),'dir',p.is_dir())
for f in ['H.pbe-rrkjus_psl.1.0.0.UPF','C.pbe-n-kjpaw_psl.1.0.0.UPF','N.pbe-n-radius_5.UPF','O.pbe-n-kjpaw_psl.0.1.UPF','s_pbe_v1.4.uspp.F.UPF','cl_pbe_v1.4.uspp.F.UPF','Sn_pbe_v1.uspp.F.UPF']:
 print(f,(p/f).is_file())
print('meminfo',subprocess.run(['free','-h'],capture_output=True,text=True).stdout)