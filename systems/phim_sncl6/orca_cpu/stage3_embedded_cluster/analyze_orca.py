#!/usr/bin/env python3
"""ORCA 输出分析：前线轨道片段组成、TDDFT 激发态性质、SOC 矩阵元。
用法: python3 analyze_orca.py job.out [更多 .out ...]
要求: 输入中含 %output Print[P_ReducedOrbPopMO_L] 1 end（轨道组成）
      %tddft 中含 TPrint 1e-4（激发态成分）
片段按原子连接自动识别：SnCl6、阳离子 A（原子 7-26）、阳离子 B（27-46）、水。"""
import sys, re, math

RAD = {'H':0.31,'C':0.76,'N':0.71,'O':0.66,'Cl':1.02,'Sn':1.39}

def fragments(at):
    n=len(at); par=list(range(n))
    def fd(x):
        while par[x]!=x: par[x]=par[par[x]]; x=par[x]
        return x
    for a in range(n):
        for b in range(a+1,n):
            if math.dist(at[a][1:],at[b][1:]) < (RAD.get(at[a][0],1.0)+RAD.get(at[b][0],1.0))*1.2:
                par[fd(a)]=fd(b)
    G={}
    for a in range(n): G.setdefault(fd(a),[]).append(a)
    names={}; c=0; w=0
    for g in sorted(G.values(),key=min):
        el={at[a][0] for a in g}
        if 'Sn' in el: nm='SnCl6'
        elif 'C' in el: nm='Cat'+'AB'[c] if c<2 else 'Cat%d'%c; c+=1
        elif 'O' in el: w+=1; nm='H2O'
        else: nm='X'
        for a in g: names[a]=nm
    return names

def analyze(f):
    L=open(f,errors='ignore').read().splitlines()
    print('='*78); print(f)
    term=any('ORCA TERMINATED NORMALLY' in l for l in L)
    print('正常结束:', '是' if term else '否 —— 先看输出末尾的报错')
    gi=[i for i,l in enumerate(L) if l.strip()=='CARTESIAN COORDINATES (ANGSTROEM)']
    if not gi: return
    i=gi[-1]+2; at=[]
    while i<len(L) and L[i].strip():
        p=L[i].split(); at.append((p[0],float(p[1]),float(p[2]),float(p[3]))); i+=1
    names=fragments(at)
    e=[l for l in L if l.startswith('FINAL SINGLE POINT ENERGY')]
    if e: print('最终能量:', e[-1].split()[-1], 'Eh')
    # orbitals (closed shell only)
    oi=[i for i,l in enumerate(L) if l.strip()=='ORBITAL ENERGIES']
    orb={}
    if oi and 'SPIN UP' not in L[oi[-1]+2]:
        i=oi[-1]+4
        while i<len(L):
            p=L[i].split()
            if len(p)==4 and p[0].isdigit(): orb[int(p[0])]=(float(p[1]),float(p[3])); i+=1
            else: break
    comp={}
    st=[i for i,l in enumerate(L) if 'LOEWDIN REDUCED ORBITAL POPULATIONS PER MO' in l]
    if st:
        i=st[-1]+3; cur=None
        while i<len(L):
            l=L[i]; p=l.split()
            if 'MAYER' in l or l.startswith('*'): break
            if p and all(x.isdigit() for x in p) and len(p)<=6:
                cur=[int(x) for x in p]; i+=3; continue
            m=re.match(r'^\s*(\d+)\s+([A-Z][a-z]?)\s+(\S+)\s+(.*)$',l)
            if m and cur:
                try: vals=[float(x) for x in m.group(4).split()]
                except ValueError: i+=1; continue
                a=int(m.group(1))
                for k,v in zip(cur,vals):
                    comp.setdefault(k,{}); comp[k][names[a]]=comp[k].get(names[a],0)+v
            i+=1
    def label(k):
        c=comp.get(k)
        if not c: return '?'
        t=sum(c.values()); top=max(c,key=c.get)
        return top if c[top]/t>0.6 else 'mix'
    if orb:
        h=max(k for k,v in orb.items() if v[0]>0)
        print('\n前线轨道（HOMO = MO %d）'%h)
        for k in range(h-4,h+5):
            if k not in orb: continue
            tag='HOMO' if k==h else 'LUMO' if k==h+1 else ('H-%d'%(h-k) if k<h else 'L+%d'%(k-h-1))
            c=comp.get(k,{}); t=sum(c.values()) or 1
            s='  '.join('%s %.0f%%'%(n,100*v/t) for n,v in sorted(c.items(),key=lambda x:-x[1]) if v/t>0.03)
            print('  MO%4d %-5s %8.3f eV | %s'%(k,tag,orb[k][1],s))
        if comp:
            for nm in ('CatA','CatB'):
                occ=[k for k in orb if orb[k][0]>0 and label(k)==nm]
                if occ: print('  %s 最高占据 π: MO %d (%.3f eV)'%(nm,max(occ),orb[max(occ)][1]))
            vs=[k for k in orb if orb[k][0]==0 and label(k)=='SnCl6']
            if vs: print('  SnCl6 最低空轨道 σ*: MO %d (%.3f eV)'%(min(vs),orb[min(vs)][1]))
        print('  能隙 LUMO-HOMO = %.3f eV'%(orb[h+1][1]-orb[h][1]))
    # TDDFT states
    cnt={'1':0,'3':0}
    for i,l in enumerate(L):
        m=re.match(r'^STATE\s+(\d+):\s+E=\s+\S+ au\s+(\S+) eV.*Mult (\d)',l)
        if not m: continue
        E=float(m.group(2)); mult=m.group(3); cls={}; j=i+1
        if mult not in cnt: continue
        cnt[mult]+=1
        while j<len(L) and L[j].strip():
            mm=re.match(r'^\s+(\d+)a\s+->\s+(\d+)a\s+:\s+(\S+)',L[j])
            if mm:
                a,b,w=int(mm.group(1)),int(mm.group(2)),float(mm.group(3))
                la,lb=label(a),label(b)
                key=('局域 %s'%la) if la==lb else ('%s→%s'%(la,lb))
                cls[key]=cls.get(key,0)+w
            j+=1
        s='  '.join('%s %.0f%%'%(k,100*v) for k,v in sorted(cls.items(),key=lambda x:-x[1]) if v>0.05)
        print('  %s%-3d %6.3f eV %6.1f nm | %s'%('S' if mult=='1' else 'T',cnt[mult],E,1239.84/E,s))
    # SOCME
    si=[i for i,l in enumerate(L) if 'CALCULATED SOCME BETWEEN TRIPLETS AND SINGLETS' in l]
    if si:
        print('\nSOC 矩阵元 |<T|Hso|S>|（cm^-1，S=0 为基态）')
        i=si[-1]+1; rows=[]
        while i<len(L) and i<si[-1]+400:
            nums=re.findall(r'-?\d+\.\d+|-?\d+',L[i])
            if len(nums)==8 and '.' not in nums[0] and '.' not in nums[1]:
                T,S=int(nums[0]),int(nums[1]); v=[float(x) for x in nums[2:]]
                rows.append((T,S,math.sqrt(sum(x*x for x in v))))
            elif rows and not L[i].strip(): break
            i+=1
        for T,S,mag in rows:
            if S<=3 and T<=4: print('  T%-2d S%-2d %10.3f'%(T,S,mag))
    # spin population for UKS
    sp=[i for i,l in enumerate(L) if l.strip().startswith('MULLIKEN ATOMIC CHARGES AND SPIN POPULATIONS')]
    if sp:
        i=sp[-1]+2; tot={}
        while i<len(L) and not L[i].startswith('Sum'):
            p=L[i].replace(':',' ').split()
            if len(p)>=4 and p[0].isdigit(): tot[names[int(p[0])]]=tot.get(names[int(p[0])],0)+float(p[-1])
            i+=1
        print('\n自旋布居（三重态应约 2.0 集中在一个片段上）:', '  '.join('%s %.2f'%(k,v) for k,v in tot.items()))

for f in sys.argv[1:]: analyze(f)
