#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_inputs.py —— 结构优化结束后，生成后续计算的输入文件，并汇总结果

用法：
  python make_inputs.py from-relax 01_relax.out   # 用优化后的结构生成 02_scf / 03_nscf / 05_bands 输入
  python make_inputs.py gap 02_scf.out            # 从输出里读带隙
  python make_inputs.py pp 02_scf.out [窗口eV]     # 生成 pp.x 输入：导出电荷密度 cube 文件
  python make_inputs.py export 01_relax.out        # 导出优化后结构（cif/xyz）和优化轨迹
  python make_inputs.py summary                    # 汇总所有结果，写 summary.txt
"""
import os
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
    # 态密度用更密的 k 点
    nscf = open("header_nscf.tmpl").read().replace("occupations = 'fixed'   ! 绝缘体：电子占据固定，不用展宽", "occupations = 'smearing'   ! 高斯展宽（实测 tetrahedra_opt 时 projwfc 输出全为 0）\n  smearing = 'gaussian'\n  degauss = 0.005")
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
    # 能带计算在单独目录 tmp_bands 里做（见 run_after_relax.sh），不污染 tmp/ 里的波函数
    bands = open("header_bands.tmpl").read().replace("outdir = './tmp'", "outdir = './tmp_bands'")
    open("05_bands.in", "w").write(bands + cell + pos + path)
    open("05_bandsx.in", "w").write("&BANDS\n  prefix = 'snpim'\n  outdir = './tmp_bands'\n  filband = 'snpim.bands'\n/\n")
    print("已生成 02_scf.in、03_nscf.in、05_bands.in、05_bandsx.in")


def gap(out):
    txt = open(out, encoding="utf-8", errors="ignore").read()
    m = re.findall(r"highest occupied, lowest unoccupied level \(ev\):\s+([-\d.]+)\s+([-\d.]+)", txt)
    if m:
        vbm, cbm = map(float, m[-1])
        return vbm, cbm, cbm - vbm
    return None


def write_pp(scf_out="02_scf.out", win=0.3):
    """pp.x 输入：总电荷密度 + 价带顶/导带底附近能量窗口内的电荷分布（ILDOS），输出 Gaussian cube 格式。
    cube 文件可用 VESTA 打开画等值面（File → Open，再在 Properties → Isosurfaces 调等值面值）。"""
    vbm, cbm, g = gap(scf_out)
    os.makedirs("cube", exist_ok=True)
    jobs = [
        ("rho_total", "plot_num = 0                 ! 总价电子密度"),
        ("vbm_ildos", f"plot_num = 10                ! 能量窗口内的电荷分布（ILDOS）\n"
                      f"  emin = {vbm - win:.4f}       ! eV：价带顶以下 {win} eV\n  emax = {vbm + 0.01:.4f}"),
        ("cbm_ildos", f"plot_num = 10\n  emin = {cbm - 0.01:.4f}       ! eV：导带底以上 {win} eV\n  emax = {cbm + win:.4f}"),
    ]
    for name, body in jobs:
        open(f"06_pp_{name}.in", "w").write(f"""&INPUTPP
  prefix = 'snpim'
  outdir = './tmp'
  filplot = '{name}.dat'
  {body}
/
&PLOT
  nfile = 1
  filepp(1) = '{name}.dat'
  weight(1) = 1.0
  iflag = 3                    ! 三维
  output_format = 6            ! Gaussian cube
  fileout = 'cube/{name}.cube'
/
""")
    print(f"已生成 pp.x 输入：VBM = {vbm:.4f} eV，CBM = {cbm:.4f} eV，窗口 {win} eV")


def export(relax_out="01_relax.out"):
    """用 ASE 导出优化后结构和整条优化轨迹（轨迹可用 OVITO / Jmol 播放）。"""
    try:
        import ase.io
    except ImportError:
        os.system("pip install -q ase")
        import ase.io
    traj = ase.io.read(relax_out, index=":", format="espresso-out")
    ase.io.write("relaxed_structure.cif", traj[-1])
    ase.io.write("relaxed_structure.xyz", traj[-1])
    ase.io.write("relax_trajectory.extxyz", traj)
    print(f"已导出 relaxed_structure.cif/.xyz 和 relax_trajectory.extxyz（{len(traj)} 帧）")


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
    cubes = sorted(f for f in os.listdir("cube") if f.endswith(".cube")) if os.path.isdir("cube") else []
    if cubes:
        rows.append("cube 文件：" + "、".join(cubes))
    for t in ("wfc_scf.tar", "wfc_nscf.tar"):
        if os.path.exists(t):
            rows.append(f"波函数快照 {t}：{os.path.getsize(t) / 2**30:.2f} GB")
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
    elif cmd == "pp":
        write_pp(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 0.3)
    elif cmd == "export":
        export(sys.argv[2])
    elif cmd == "summary":
        summary()
