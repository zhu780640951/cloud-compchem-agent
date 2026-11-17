"""HSE06 vs PBE (same SG15 PPs) gap; EXX outer-loop timing.  usage: analyze_hse.py <dir>"""
import re, sys, os
W = sys.argv[1]
def gap(f):
    m = re.findall(r"highest occupied, lowest unoccupied level \(ev\):\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)", open(f).read())
    return tuple(map(float, m[-1])) if m else None
p, h = gap(f"{W}/pbe_sg15.out"), gap(f"{W}/hse.out") if os.path.exists(f"{W}/hse.out") else None
print("PBE (SG15, 70 Ry):  VBM %.3f  CBM %.3f  Eg %.3f eV" % (p[0], p[1], p[1] - p[0]))
if h:
    cfg = open(f"{W}/hse_config.txt").read().strip()
    print("HSE06 (%s):  VBM %.3f  CBM %.3f  Eg %.3f eV" % (cfg, h[0], h[1], h[1] - h[0]))
    print("Delta Eg (HSE06 - PBE) = %+.3f eV ; VBM shift %+.3f, CBM shift %+.3f eV" % ((h[1]-h[0]) - (p[1]-p[0]), h[0]-p[0], h[1]-p[1]))
    print("PBE(PAW, step 2) gap 2.201 eV  ->  HSE06-corrected estimate %.2f eV" % (2.201 + (h[1]-h[0]) - (p[1]-p[0])))
    t = open(f"{W}/hse.out").read()
    print("EXX outer iterations:", len(re.findall(r"est\. exchange err", t)), "| wall:", re.findall(r"PWSCF\s+:.*WALL", t)[-1:] )
