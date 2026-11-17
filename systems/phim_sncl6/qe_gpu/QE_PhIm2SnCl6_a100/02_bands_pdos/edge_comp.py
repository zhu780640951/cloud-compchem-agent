import re, sys, numpy as np
W = sys.argv[1]
st = re.findall(r"state #\s*(\d+): atom\s+(\d+) \((\w+)\s*\).*?\(l=(\d)", open(f"{W}/projwfc.out").read())
el = {int(i): e for i, a, e, l in st}
lq = {int(i): "spdf"[int(l)] for i, a, e, l in st}
x = open(f"{W}/tmp/phim_sncl6.save/atomic_proj.xml").read()
ks = re.split(r"<K-POINT", x)[1:]
def comp(band):
    tot = {}
    for blk in ks:
        w = float(re.search(r'Weight="([-\d.Ee+]+)"', blk).group(1))
        for m in re.finditer(r'<ATOMIC_WFC index="(\d+)"[^>]*>(.*?)</ATOMIC_WFC>', blk, re.S):
            v = np.array(m.group(2).split(), float).reshape(-1, 2)
            c2 = v[band - 1, 0] ** 2 + v[band - 1, 1] ** 2
            key = (el[int(m.group(1))], lq[int(m.group(1))])
            tot[key] = tot.get(key, 0) + w * c2
    s = sum(tot.values()); byel = {}
    for (e, l), v in tot.items(): byel[e] = byel.get(e, 0) + v
    top = sorted(tot.items(), key=lambda kv: -kv[1])[:5]
    org = sum(byel.get(e, 0) for e in "CNH"); inorg = byel.get("Sn", 0) + byel.get("Cl", 0)
    return (f"band {band}: " + ", ".join(f"{k[0]}-{k[1]} {100*v/s:.0f}%" for k, v in top) + f" | [SnCl6] {100*inorg/s:.0f}%, cation {100*org/s:.0f}%, water(O) {100*byel.get('O',0)/s:.0f}%")
out = [comp(b) for b in (180, 181, 182, 183, 184, 185)]
open(f"{W}/edge_composition.txt", "w").write("\n".join(out) + "\n"); print("\n".join(out))
