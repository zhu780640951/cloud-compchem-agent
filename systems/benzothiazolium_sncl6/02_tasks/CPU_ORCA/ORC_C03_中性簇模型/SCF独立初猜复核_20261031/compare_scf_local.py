import pathlib,tarfile,re,json,math
root=pathlib.Path(r'E:\桌面\(C₇H₆NS)₂[SnCl₆]·2H₂O计算\02_计算任务\CPU_ORCA\ORC_C03_中性簇模型')
a=tarfile.open(root/'resume_results.tar.gz'); old=a.extractfile('resume_shell1.out').read().decode(errors='replace');p=root/'SCF独立初猜复核_20261031'/'云端原始结果'/'orc_c03_shell1_independent_scf_20261031';new=(p/'shell1_independent_scf.out').read_text(errors='replace')
def extract(t):
 k=t.find('MULLIKEN ATOMIC CHARGES');sec=t[k:t.find('Sum of atomic charges',k)]
 charges={int(i):(e,float(v)) for i,e,v in re.findall(r'^\s*(\d+)\s+(\w+)\s*:\s*(-?\d+\.\d+)',sec,re.M)}
 k=t.find('ORBITAL ENERGIES');sec=t[k:k+40000];orb={int(i):(float(oc),float(en)) for i,oc,en in re.findall(r'^\s*(\d+)\s+(\d+\.\d+)\s+(-?\d+\.\d+)\s+-?\d+\.\d+',sec,re.M)}
 return charges,orb
A,ao=extract(old);B,bo=extract(new)
print('counts',len(A),len(B),len(ao),len(bo));print('frontier',json.dumps({i:{'old':ao.get(i),'new':bo.get(i)} for i in range(218,228)}))
if len(A)==len(B)==79:
 diff=[(abs(B[i][1]-A[i][1]),i,A[i],B[i]) for i in A];print('largest_charge_changes',json.dumps(sorted(diff,reverse=True)[:10]));print('charge_sum_ranges',json.dumps({f'{l}-{r}':{'old':sum(A[i][1] for i in range(l,r)),'new':sum(B[i][1] for i in range(l,r))} for l,r in [(0,7),(7,37),(37,43),(43,79)]}))