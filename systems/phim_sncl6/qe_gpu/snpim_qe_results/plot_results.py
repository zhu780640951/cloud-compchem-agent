#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_results.py —— 画能带 + 按元素分解的 PDOS，并输出带隙、带边组成

能量零点取价带顶（VBM）。输出：
  fig_bands_pdos.png   能带图（左）+ PDOS（右）
  bands_vbm0.csv       能带数据（k 路径距离, 各条带能量），可直接用 Origin 画
  pdos_elements.csv    各元素 PDOS（能量, 总 DOS, Sn, Cl, O, N, C, H）
"""
import glob
import re

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def vbm_cbm(scf="02_scf.out"):
    txt = open(scf, errors="ignore").read()
    m = re.findall(r"highest occupied, lowest unoccupied level \(ev\):\s+([-\d.]+)\s+([-\d.]+)", txt)
    return tuple(map(float, m[-1]))


def read_bands(out="05_bands.out", nocc=182):
    txt = open(out, errors="ignore").read()
    part = txt.split("End of band structure calculation")[-1]
    blocks = re.findall(r"k =\s*(-?\d+\.\d+)\s*(-?\d+\.\d+)\s*(-?\d+\.\d+)\s*\(\s*\d+ PWs\)\s+bands \(ev\):\s+(.*?)(?=\n\s*\n)", part, re.S)
    ks, es = [], []
    for kx, ky, kz, e in blocks:
        ks.append([float(kx), float(ky), float(kz)])
        es.append([float(x) for x in re.findall(r"-?\d+\.\d+", e)])
    ks = np.array(ks)
    n = min(len(e) for e in es)
    es = np.array([e[:n] for e in es])
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(ks, axis=0), axis=1))]
    return d, es


def read_pdos(prefix="snpim.pdos"):
    tot = np.loadtxt(f"{prefix}.pdos_tot")
    E, dos = tot[:, 0], tot[:, 1]
    el = {}
    for f in glob.glob(f"{prefix}.pdos_atm#*"):
        sym = re.search(r"\((\w+)\)_wfc", f).group(1)
        data = np.loadtxt(f)
        el[sym] = el.get(sym, 0) + data[:, 1]
    return E, dos, el


def main():
    vbm, cbm = vbm_cbm()
    gap = cbm - vbm
    print(f"自洽计算（2×2×2 k 点）：VBM = {vbm:.3f} eV，CBM = {cbm:.3f} eV，带隙 = {gap:.3f} eV")

    d, es = read_bands()
    es = es - vbm
    occ = es[:, :182]
    emp = es[:, 182:]
    print(f"能带路径上：价带顶 {occ.max():.3f} eV（第 {occ.max(axis=1).argmax()} 个 k 点），"
          f"导带底 {emp.min():.3f} eV（第 {emp.min(axis=1).argmin()} 个 k 点），路径带隙 {emp.min() - occ.max():.3f} eV")
    np.savetxt("bands_vbm0.csv", np.column_stack([d, es]), delimiter=",", fmt="%.5f",
               header="k_path," + ",".join(f"band{i+1}" for i in range(es.shape[1])), comments="")

    have_pdos = bool(glob.glob("snpim.pdos.pdos_tot"))
    fig, axes = plt.subplots(1, 2 if have_pdos else 1, figsize=(10 if have_pdos else 6, 6),
                             sharey=True, gridspec_kw={"width_ratios": [2, 1]} if have_pdos else None)
    ax = axes[0] if have_pdos else axes
    for i in range(es.shape[1]):
        ax.plot(d, es[:, i], color="#1f4e79" if i < 182 else "#b03a2e", lw=0.8)
    ticks = [0, 30, 60, 61, 91, 121]
    labels = ["X", "Γ", "Y|Z", "", "Γ", "R"]
    tk = [d[i] for i in ticks if i < len(d)]
    ax.set_xticks(tk)
    ax.set_xticklabels(labels[:len(tk)])
    for x in tk:
        ax.axvline(x, color="0.8", lw=0.6)
    ax.axhline(0, color="0.5", ls="--", lw=0.6)
    ax.set_xlim(d[0], d[-1])
    ax.set_ylim(-4, 5)
    ax.set_ylabel("E − E_VBM (eV)")
    ax.set_title(f"PBE-D3(BJ) band structure, gap = {gap:.2f} eV")

    if have_pdos:
        E, dos, el = read_pdos()
        E = E - vbm
        cols = {"Sn": "#7b3294", "Cl": "#1a9641", "O": "#d7191c", "N": "#2c7bb6", "C": "#404040", "H": "#fdae61"}
        ax2 = axes[1]
        ax2.fill_betweenx(E, 0, dos, color="0.85", label="total")
        for sym in ["Sn", "Cl", "O", "N", "C", "H"]:
            if sym in el:
                ax2.plot(el[sym], E, color=cols[sym], lw=1, label=sym)
        ax2.axhline(0, color="0.5", ls="--", lw=0.6)
        m = (E > -4) & (E < 5)
        ax2.set_xlim(0, dos[m].max() * 1.05)
        ax2.set_xlabel("PDOS (states/eV)")
        ax2.legend(loc="upper right", fontsize=8)
        # 带边组成：VBM 以下 0.5 eV、CBM 以上 0.5 eV 内各元素的积分权重
        dE = E[1] - E[0]
        vb = (E > -0.5) & (E <= 0.05)
        cb = (E >= gap - 0.05) & (E < gap + 0.5)
        print("带边组成（各元素 PDOS 积分占比）：")
        for name, msk in (("价带顶 0.5 eV 内", vb), ("导带底 0.5 eV 内", cb)):
            tot = sum(el[s][msk].sum() for s in el) * dE
            parts = ", ".join(f"{s} {el[s][msk].sum() * dE / tot * 100:.0f}%" for s in ["Sn", "Cl", "O", "N", "C", "H"] if s in el)
            print(f"  {name}：{parts}")
        np.savetxt("pdos_elements.csv",
                   np.column_stack([E, dos] + [el.get(s, np.zeros_like(E)) for s in ["Sn", "Cl", "O", "N", "C", "H"]]),
                   delimiter=",", fmt="%.5f", header="E_minus_VBM_eV,total,Sn,Cl,O,N,C,H", comments="")
    fig.tight_layout()
    fig.savefig("fig_bands_pdos.png", dpi=200)
    print("图已保存：fig_bands_pdos.png；数据：bands_vbm0.csv" + ("、pdos_elements.csv" if have_pdos else ""))


if __name__ == "__main__":
    main()
