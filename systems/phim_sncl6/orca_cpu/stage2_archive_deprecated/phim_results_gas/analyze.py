import sys, re, math
popf, tdf = sys.argv[1], sys.argv[2]
L = open('phim_opt.xyz').read().split('\n')[2:]
at = [(l.split()[0], [float(x) for x in l.split()[1:4]]) for l in L if l.strip()]
n = len(at)
def d(i, j): return math.dist(at[i][1], at[j][1])
frag = [-1]*n; k = 0
for s in range(n):
    if frag[s] >= 0: continue
    frag[s] = k; st = [s]
    while st:
        i = st.pop()
        for j in range(n):
            if frag[j] < 0:
                cut = 1.3 if 'H' in (at[i][0], at[j][0]) else (3.0 if 'Sn' in (at[i][0], at[j][0]) else 1.9)
                if d(i, j) < cut and not (at[i][0] == 'H' and at[j][0] == 'H'): frag[j] = k; st.append(j)
    k += 1
names = {}
for f in range(k):
    mem = [at[i][0] for i in range(n) if frag[i] == f]
    if 'Sn' in mem: names[f] = 'SnCl6'
    elif 'C' in mem: names[f] = 'Cat%d' % f
    else: names[f] = 'H2O%d' % f
print('fragments:', {names[f]: sum(1 for x in frag if x == f) for f in range(k)})
# parse Loewdin MO populations (last section in pop file)
lines = open(popf).read().split('\n')
start = max(i for i, l in enumerate(lines) if 'LOEWDIN REDUCED ORBITAL POPULATIONS PER MO' in l)
pop = {}
i = start + 3; cur = []
while i < len(lines):
    l = lines[i]; t = l.split()
    if t and all(re.fullmatch(r'\d+', x) for x in t) and i + 1 < len(lines) and re.fullmatch(r'-?\d+\.\d+', lines[i+1].split()[0] if lines[i+1].split() else ''):
        cur = [int(x) for x in t]
        for m in cur: pop[m] = {f: 0.0 for f in range(k)}
        i += 4; continue
    if re.match(r'^\s*\d+\s+[A-Z][a-z]?\s+\w+', l) and cur:
        a = int(t[0]); vals = [float(x) for x in t[3:]]
        for m, v in zip(cur, vals): pop[m][frag[a]] += v
    elif t and not re.match(r'^\s*\d+\s', l) and not set(l.strip()) <= set('- '):
        if pop and len(pop) > 50 and not re.match(r'^[\s\d.\-]+$', l): break
    i += 1
def desc(m): return ' '.join('%s%.0f%%' % (names[f], v) for f, v in sorted(pop[m].items(), key=lambda x: -x[1])[:2] if v >= 5)
print('HOMO-1,HOMO,LUMO,LUMO+1:')
for m in (147, 148, 149, 150): print(' ', m, desc(m))
td = open(tdf).read()
fo = {}
sec = td.split('ABSORPTION SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS')[1]
for l in sec.split('\n'):
    mm = re.match(r'\s*0-1A\s+->\s+(\d+)-1A\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', l)
    if mm: fo[int(mm.group(1))] = (float(mm.group(2)), float(mm.group(4)), float(mm.group(5)))
    elif fo and not l.strip(): break
blocks = re.split(r'\nSTATE +(\d+):', td.split('TD-DFT EXCITED STATES')[1] if 'TD-DFT EXCITED STATES' in td else td)
print('state  E(eV) nm    f      donor -> acceptor (weight-averaged fragment %)')
for b in range(1, len(blocks), 2):
    s = int(blocks[b]); body = blocks[b+1]
    dn = {f: 0.0 for f in range(k)}; ac = {f: 0.0 for f in range(k)}; tw = 0
    for mm in re.finditer(r'(\d+)a\s+->\s+(\d+)a\s+:\s+([\d.]+)', body.split('\nSTATE')[0]):
        o, v, w = int(mm.group(1)), int(mm.group(2)), float(mm.group(3))
        if o not in pop or v not in pop: continue
        tw += w
        for f in range(k): dn[f] += w*pop[o][f]; ac[f] += w*pop[v][f]
    if tw == 0: continue
    ds = ' '.join('%s%.0f' % (names[f], dn[f]/tw) for f in sorted(dn, key=lambda x: -dn[x])[:2] if dn[f]/tw >= 5)
    as_ = ' '.join('%s%.0f' % (names[f], ac[f]/tw) for f in sorted(ac, key=lambda x: -ac[x])[:2] if ac[f]/tw >= 5)
    e = fo.get(s, (0, 0, 0))
    print('S%-3d %6.3f %6.1f %.4f  %s -> %s' % (s, e[0], e[1], e[2], ds, as_))
