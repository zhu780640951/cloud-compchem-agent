"""Wave-2 analysis of the ORCA chains (per functional) -> orca_summary.txt / .json
usage: analyze_wave2.py <05_orca_soc_T1 dir> <cluster_info.json>"""
import re, sys, os, json, math
import numpy as np
D, INFO = sys.argv[1], json.load(open(sys.argv[2]))
frag = INFO["fragments"]
HA = 27.211386245988; CM = 8065.543937; KB = 8.617333262e-5; HBAR = 6.582119569e-16  # eV s
def rd(f): return open(f).read() if os.path.exists(f) else ""
def ok(t): return "ORCA TERMINATED NORMALLY" in t
def efinal(t):
    m = re.findall(r"FINAL SINGLE POINT ENERGY\s+(-?\d+\.\d+)", t); return float(m[-1]) if m else None
def states(t, mult):
    """TDA states from the last TD-DFT block of the given multiplicity -> list of eV"""
    blocks = re.split(r"TD-DFT(?:/TDA)? EXCITED STATES \((SINGLETS|TRIPLETS)\)", t)
    want = "SINGLETS" if mult == 1 else "TRIPLETS"; e = []
    for i in range(1, len(blocks) - 1, 2):
        if blocks[i] == want:
            e = [float(x) for x in re.findall(r"STATE\s+\d+:\s+E=\s+-?[\d.]+ au\s+(-?[\d.]+) eV", blocks[i + 1].split("TD-DFT")[0])]
    return e
def socme(t):
    """<T_i|HSO|S_j> (cm-1) -> {(i, j): |SOC|}  (S index 0 = ground state)"""
    i0 = t.find("CALCULATED SOCME BETWEEN TRIPLETS AND SINGLETS")
    if i0 < 0: return {}
    out = {}
    for m in re.finditer(r"^\s*(\d+)\s+(\d+)\s+\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\)\s+\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\)\s+\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\)",
                         t[i0:i0 + 200000], re.M):
        v = [float(x) for x in m.groups()[2:]]
        out[(int(m.group(1)), int(m.group(2)))] = math.sqrt(sum(x * x for x in v))
    return out
def soc_spectrum(t):
    """SOC-corrected absorption from the SOC ground state: [(E_cm-1, fosc)] in energy order"""
    i0 = t.find("SPIN ORBIT CORRECTED ABSORPTION SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS")
    if i0 < 0: return []
    seg = t[i0:i0 + 300000].split("SPIN ORBIT CORRECTED ABSORPTION SPECTRUM VIA TRANSITION VELOCITY")[0]
    rows = []
    for l in seg.splitlines():
        m = re.match(r"\s*0-\S+\s*->\s*\d+-\S+\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+([\d.eE+-]+)", l)   # ORCA 6: eV cm-1 nm fosc
        if m: rows.append((float(m.group(2)), float(m.group(4)))); continue
        m = re.match(r"\s*\d+\s+(-?[\d.]+)\s+(-?[\d.]+)\s+([\d.eE+-]+)\s", l)                             # ORCA 5: cm-1 nm fosc
        if m and float(m.group(1)) > 1000: rows.append((float(m.group(1)), float(m.group(3))))
    return rows
def spin_by_frag(t):
    i0 = t.rfind("MULLIKEN ATOMIC CHARGES AND SPIN POPULATIONS")
    if i0 < 0: return {}
    s = {}
    for m in re.finditer(r"^\s*(\d+)\s+\w+\s*:\s+(-?[\d.]+)\s+(-?[\d.]+)", t[i0:i0 + 20000], re.M):
        k = int(m.group(1))
        if k < len(frag): s[frag[k]] = s.get(frag[k], 0) + float(m.group(3))
    return {k: round(v, 3) for k, v in s.items()}
def s2(t):
    m = re.findall(r"Expectation value of <S\*\*2>\s*:\s*([\d.]+)", t); return float(m[-1]) if m else None
def xyz(f):
    L = open(f).read().split("\n"); n = int(L[0]); return np.array([[float(x) for x in l.split()[1:4]] for l in L[2:2 + n]])
def kr(Ecm, f): return 0.6670 * Ecm ** 2 * f       # Einstein A coefficient, s^-1 (n = 1)
def marcus(soc_cm, dE, lam, T=300.0):             # dE = E_S - E_T (eV, >0 downhill), lam in eV
    V = soc_cm / CM
    return 2 * math.pi / HBAR * V * V / math.sqrt(4 * math.pi * lam * KB * T) * math.exp(-(-dE + lam) ** 2 / (4 * lam * KB * T))

res, txt = {}, []
for xc, name in (("cam", "CAM-B3LYP"), ("wb97x", "wB97X-D3")):
    W = f"{D}/{xc}"; r = {}; P = lambda s: txt.append(s)
    P(f"\n================ {name} ================")
    a, b = rd(f"{W}/soc_S0geom.out"), rd(f"{W}/soc_T1geom.out")
    for tag, t in (("S0geom (crystal, vertical absorption)", a), ("T1geom (emission)", b)):
        if not ok(t): P(f"[{tag}] not finished"); continue
        S, T, soc, sp = states(t, 1), states(t, 3), socme(t), soc_spectrum(t)
        key = "S0geom" if "S0" in tag else "T1geom"
        r[key] = {"S": S, "T": T, "SOC_T_S": {f"T{i}-S{j}": round(v, 2) for (i, j), v in sorted(soc.items())}, "soc_spectrum": sp[:12]}
        P(f"[{tag}]  S1 {S[0]:.3f} eV  T1 {T[0]:.3f} eV  dE_ST {S[0]-T[0]:.3f} eV")
        P("  singlets: " + " ".join(f"{x:.2f}" for x in S)); P("  triplets: " + " ".join(f"{x:.2f}" for x in T))
        if soc:
            P("  |<T|HSO|S0>| cm-1: " + "  ".join(f"T{i} {soc.get((i,0),0):.1f}" for i in range(1, 6)))
            P("  |<T|HSO|S1>| cm-1: " + "  ".join(f"T{i} {soc.get((i,1),0):.1f}" for i in range(1, 11)))
        if len(sp) >= 3:
            sub = sorted(sp, key=lambda x: x[0])[:3]
            ks = [kr(E, f) for E, f in sub]; kavg = sum(ks) / 3
            r[key]["T1_sublevels"] = [{"E_cm": E, "E_eV": E / CM, "f": f, "kr_s-1": k} for (E, f), k in zip(sub, ks)]
            r[key]["kr_avg"] = kavg
            P("  T1 sublevels (SOC states 1-3): " + "; ".join(f"{E/CM:.3f} eV f={f:.2e} kr={k:.2e} s-1" for (E, f), k in zip(sub, ks)))
            P(f"  k_r(avg, high-T limit) = {kavg:.3e} s-1  ->  tau_r = {1/kavg if kavg>0 else float('inf'):.3e} s")
    e = {k: efinal(rd(f"{W}/{k}.out")) for k in ("opt_S0", "opt_T1", "sp_S0_at_T1", "sp_T1_at_S0")}
    if all(e.values()):
        Eem = (e["opt_T1"] - e["sp_S0_at_T1"]) * HA; E00 = (e["opt_T1"] - e["opt_S0"]) * HA
        Eabs = (e["sp_T1_at_S0"] - e["opt_S0"]) * HA
        lS = (e["sp_S0_at_T1"] - e["opt_S0"]) * HA; lT = (e["sp_T1_at_S0"] - e["opt_T1"]) * HA
        r["dSCF"] = {"E_abs_T1_vert": Eabs, "E_00": E00, "E_em": Eem, "lambda_S0": lS, "lambda_T1": lT,
                     "spin_T1": spin_by_frag(rd(f"{W}/opt_T1.out")), "S2_T1": s2(rd(f"{W}/opt_T1.out"))}
        P(f"[dSCF, def2-SVP/TZVP-Sn + D3]  T1 vertical {Eabs:.3f} eV | E00 {E00:.3f} eV | emission {Eem:.3f} eV ({1239.84/Eem:.0f} nm)")
        P(f"  lambda_S0 {lS:.3f} eV, lambda_T1 {lT:.3f} eV, Stokes(T1 vert - em) {Eabs-Eem:.3f} eV; <S2> {r['dSCF']['S2_T1']}")
        P(f"  T1 spin density by fragment: {r['dSCF']['spin_T1']}")
        g0, g1 = xyz(f"{W}/opt_S0.xyz"), xyz(f"{W}/opt_T1.xyz"); gc = xyz(f"{W}/crystal.xyz")
        fr = np.array(frag)
        P("  RMSD opt_S0 vs crystal (A): " + ", ".join(f"{f} {np.sqrt(((g0[fr==f]-gc[fr==f])**2).sum(1).mean()):.3f}" for f in sorted(set(frag))))
        P("  RMSD opt_T1 vs opt_S0 (A): " + ", ".join(f"{f} {np.sqrt(((g1[fr==f]-g0[fr==f])**2).sum(1).mean()):.3f}" for f in sorted(set(frag))))
        if "S0geom" in r:
            S, T = r["S0geom"]["S"], r["S0geom"]["T"]; soc = socme(a); lam = max(lT, 0.05)
            P(f"  Marcus k_ISC estimates S1 -> Tn (lambda = lambda_T1 = {lam:.3f} eV, 300 K):")
            for n, Et in enumerate(T, 1):
                if Et <= S[0] + 0.3 and soc.get((n, 1), 0) > 0:
                    P(f"    T{n}: dE {S[0]-Et:+.3f} eV, SOC {soc[(n,1)]:.2f} cm-1, k_ISC ~ {marcus(soc[(n,1)], S[0]-Et, lam):.2e} s-1")
    else:
        P("[dSCF] incomplete: " + ", ".join(k for k, v in e.items() if not v))
    res[xc] = r
open(f"{D}/orca_summary.txt", "w").write("\n".join(txt) + "\n")
json.dump(res, open(f"{D}/orca_summary.json", "w"), indent=1, default=float)
print("\n".join(txt))
