#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_inputs.py —— 结构优化结束后，生成后续计算的输入文件，并汇总结果

用法：
  python make_inputs.py from-relax 01_relax.out   # 用优化后的结构生成 02_scf / 03_nscf / 05_bands 输入
  python make_inputs.py gap 02_scf.out            # 从输出里读带隙
  python make_inputs.py summary                    # 汇总所有结果，写 summary.txt
"""
import re
import sys

RY2EV = 13.605693122994


def last_structure(out):
    """从 relax 输出里取最后一组晶胞（固定）和原子坐标。"""
    txt = open(out, encoding="utf-8", errors="ignore").read()
    blocks = re.findall(r"ATOMIC_POSITIONS \(crystal\)\n(.*?)(?:\n\s*\n|End final coordinates)", txt, re.S)
    if not blocks:
        raise SystemExit("输出里没有找到 ATOMIC_POSITIONS，优化可能还没走完第一步")
    pos = "ATOMIC_POSITIONS crystal\n" + "\n".join(l for l in blocks[-1].strip().splitlines() if l.strip()) + "\n"
    converged = "End of BFGS Geometry Optimization" in txt or "bfgs converged" in txt
    return pos, converged, txt.count("!    total energy")


def cell_block():
    lines = open("structure.qe").read().split("ATOMIC_POSITIONS")[0]
    return lines


def write_inputs(pos):
    cell = cell_block()
    scf = open("header_scf.tmpl").read().replace("occupations = 'fixed'   ! 绝缘体：电子占据固定，不用展宽", "occupations = 'fixed'   ! 绝缘体：电子占据固定，不用展宽\n  nbnd = 200              ! 多算一些空带，才能得到带隙")
    open("02_scf.in", "w").write(scf + cell + pos + "K_POINTS automatic\n  2 2 2 0 0 0\n")
    # 态密度用更密的 k 点和四面体积分
    nscf = open("header_nscf.tmpl").read().replace("occupations = 'fixed'   ! 绝缘体：电子占据固定，不用展宽", "occupations = 'tetrahedra_opt'   ! 四面体积分，态密度更平滑")
    open("03_nscf.in", "w").write(nscf + cell + pos + "K_POINTS automatic\n  4 3 2 0 0 0\n")
    # 三斜晶系能带路径：X–Γ–Y | Z–Γ–R（各高对称点为倒格子坐标）
    path = """K_POINTS crystal_b
  6
  0.5 0.0 0.0  30   ! X
  0.0 0.0 0.0  30   ! G
  0.0 0.5 0.0   1   ! Y
  0.0 0.0 0.5  30   ! Z
  0.0 0.0 0.0  30   ! G
  0.5 0.5 0.5   1   ! R
"""
    bands = open("header_bands.tmpl").read()
    open("05_bands.in", "w").write(bands + cell + pos + path)
    open("05_bandsx.in", "w").write("&BANDS\n  prefix = 'snpim'\n  outdir = './tmp'\n  filband = 'snpim.bands'\n/\n")
    print("已生成 02_scf.in、03_nscf.in、05_bands.in、05_bandsx.in")


def gap(out):
    txt = open(out, encoding="utf-8", errors="ignore").read()
    m = re.findall(r"highest occupied, lowest unoccupied level \(ev\):\s+([-\d.]+)\s+([-\d.]+)", txt)
    if m:
        vbm, cbm = map(float, m[-1])
        return vbm, cbm, cbm - vbm
    return None


def summary():
    rows = []
    try:
        pos, conv, n = last_structure("01_relax.out")
        e = re.findall(r"!\s+total energy\s+=\s+([-\d.]+)", open("01_relax.out").read())
        rows.append(f"结构优化：{'已收敛' if conv else '未收敛'}，共 {n} 次 SCF，最终总能 {float(e[-1]):.6f} Ry = {float(e[-1])*RY2EV:.4f} eV")
    except Exception as ex:
        rows.append(f"结构优化：读取失败（{ex}）")
    for f in ("02_scf.out", "03_nscf.out"):
        try:
            g = gap(f)
            if g:
                rows.append(f"{f}：VBM = {g[0]:.4f} eV，CBM = {g[1]:.4f} eV，带隙 = {g[2]:.3f} eV")
        except FileNotFoundError:
            pass
    for f in ("01_relax.out", "02_scf.out", "03_nscf.out", "05_bands.out"):
        try:
            t = re.findall(r"PWSCF\s+:\s+(.*?)WALL", open(f).read())
            if t:
                rows.append(f"{f} 用时：{t[-1].strip()}")
        except FileNotFoundError:
            pass
    open("summary.txt", "w", encoding="utf-8").write("\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "from-relax":
        pos, conv, n = last_structure(sys.argv[2])
        print(f"读取到第 {n} 步的结构；优化{'已收敛' if conv else '尚未收敛（将用最后一步结构）'}")
        write_inputs(pos)
    elif cmd == "gap":
        print(gap(sys.argv[2]))
    elif cmd == "summary":
        summary()
