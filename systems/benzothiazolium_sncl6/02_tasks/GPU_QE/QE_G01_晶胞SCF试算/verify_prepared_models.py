import tarfile,pathlib,re,json,math,itertools
p=pathlib.Path(__file__).parent
with tarfile.open(p/'QE_G01_results.tar.gz') as t:
 names=t.getnames();print('files',names)
 for n in ['pseudo/N.pbe-n-kjpaw_psl.1.0.0.UPF','pseudo/C.pbe-n-kjpaw_psl.1.0.0.UPF']:
  v=t.extractfile(n).read().decode(errors='replace');print(n,'\n'.join(v.splitlines()[:22])[:1800])
root=p.parents[1];j=json.loads((root/'00_正式计算准备_20261030'/'周期晶胞_模型.json').read_text(encoding='utf-8'));a=j['atoms'];v=j['cell_vectors_A'];close=[]
for i in range(len(a)):
 for j in range(i):
  best=min(math.sqrt(sum(sum((a[i]['frac'][k]-a[j]['frac'][k]+shift[k])*v[k][t] for k in range(3))**2 for t in range(3))) for shift in itertools.product((-1,0,1),repeat=3))
  if best<0.7:close.append((a[i]['label'],a[j]['label'],best))
print('pairs_below_0.7A',close)