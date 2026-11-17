# 体系一：`(PhImH)₂[SnCl₆]·2H₂O`（2-苯基咪唑杂化锡氯酸盐）

本目录归并整理自桌面早期两个研究工作区：`Google colab 云显卡环境计算`（Colab A100 + QE 周期性 DFT）与 `gcould Claude space`（GCloud `orca-cpu-16` + ORCA 分子/嵌入团簇激发态与 SOC）。

## 目录结构

- `qe_gpu/`
  - `notebooks/`：Colab CPU/T4/A100 环境检测、`gpu4pyscf` 试测，以及 `01_relax_PhIm2SnCl6_PBE-D3.ipynb`、`02_qe_snpim_a100_workflow.ipynb` 完整运行笔记本；
  - `qe_snpim_scripts/`：输入生成、PBE-D3 弛豫/SCF/NSCF/PDOS/Bands 一键脚本与结果绘图代码；
  - `snpim_qe_results/`：QE 计算输入、输出日志（`01_relax.out`、`04_projwfc.out` 等）、能带与 PDOS 数据（`bands_vbm0.csv`、`pdos_elements.csv`、`fig_bands_pdos.png`）；
  - `QE_PhIm2SnCl6_a100/`：从 Colab A100 完整归档提取的非二进制输入、日志、HSE06 对照与后处理脚本。
- `orca_cpu/`
  - `stage3_embedded_cluster/`：**有效定稿主线**（53 原子 QM 团簇 + 11,077 个点电荷，ωB97X-D3 / ZORA-TZVP）。包含全部 `.inp`、核心 `.out`/`.summary.txt`、`analyze_orca.py`、`run_all.sh`、`figures/` 科研图件、`PhIm2SnCl6_计算图解.pdf`、`计算方法对照_Angew与本工作.pdf` 及 `阶段3_结果汇总.md`。
  - `stage2_archive_deprecated/`：**已作废过程归档（含 `00_已作废_请勿引用.md`）**。保留早期 DKH + ANO-RCC 与点电荷结合导致"电子溢出（electron spill-out）"异常及无点电荷气相对照的原始记录，仅作为排错教材与方法对照，**不可用于论文引用**。

## 关键发现摘要（见 `stage3_embedded_cluster/阶段3_结果汇总.md`）

1. **电子结构一致性**：周期 QE（PBE 带隙 2.20 eV，HSE06 带隙 2.96 eV）与阶段 3 嵌入团簇（HOMO = CatA π，LUMO = [SnCl₆]²⁻ σ*）结论一致；去掉点电荷会导致轨道顺序反转。
2. **三重态发光机理**：T₁ 弛豫定域在有机阳离子（CatA），呈现醌式键长弛豫；ZORA/TZVP 垂直发射估计为 **2.346 eV（528 nm）**，`[SnCl₆]²⁻` 通过重原子自旋–轨道耦合（SOC）影响激发态系间窜越通道。
