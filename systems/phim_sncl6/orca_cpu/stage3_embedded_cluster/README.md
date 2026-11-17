# 阶段 3：嵌入团簇 ORCA 重算（(PhImH)2[SnCl6]·2H2O）

详细说明见 Claude 文档《PhIm₂SnCl₆·2H₂O 重算方案：平台与步骤》。这里是速查。

## 文件
| 文件 | 作用 | 预计用时（6 核） |
|---|---|---|
| qm_cluster.xyz / mm_charges.pc | 53 原子 QM 团簇 + 11,077 个点电荷（从阶段 2 复制，未改动） | — |
| 00_basis_check_ZORA_SnCl6.inp | 只算 SnCl6²⁻，确认 ZORA + SARC-ZORA-TZVP 能用 | 1–3 分钟 |
| 01a_S0_wB97X_SVP_PC.inp | **基准**：嵌入团簇基态，确认 HOMO/LUMO | 2–5 分钟 |
| 01b_S0_wB97X_SVP_gas.inp | 对照：去掉点电荷（应看到顺序反转） | 2–5 分钟 |
| 01c_S0_wB97X_TZVP_PC.inp | 基组检验 | 10–30 分钟 |
| 01d/01e_diag_DKH_ANO_*.inp | 可选：诊断阶段 2 出错原因 | 各约 40 分钟 |
| 02a / 02b_TDA_*.inp | 单重态 + 三重态激发态（SVP 对标阶段 1，TZVP 为正式结果） | 0.5 h / 1–3 h |
| 03_SOC_ZORA_TZVP_PC.inp | SOC-TDDFT（正式） | 2–4 h |
| 03b_SOC_control_Cat*_gas.inp | 对照：单个阳离子、无重原子的 SOC | 各 10–30 分钟 |
| 04a_T1opt_UKS_free_Cat*.inp | T1 结构优化（只放开一个阳离子） | 1–3 h |
| 04b / 04c_*_at_T1geom.inp | T1 结构上的 S0 单点 / TDA 发射 | 5 分钟 / 0.5 h |
| run_all.sh | 批量运行、记录进度、自动摘要、打包 | — |
| analyze_orca.py | 读取输出：前线轨道片段组成、激发态性质、SOC、自旋布居 | — |

用时为估计值，以 progress.log 实际记录为准。

## 命令（在虚拟机上）
```bash
cd ~/stage3
nohup bash run_all.sh 00 01a 01b > run.log 2>&1 &   # 先跑基准，确认无误再继续
tail -f progress.log
cat jobs/01a_S0_wB97X_SVP_PC/01a_S0_wB97X_SVP_PC.summary.txt
nohup bash run_all.sh 01c 02a 02b 03 > run.log 2>&1 &
nohup bash run_all.sh 04a_T1opt_UKS_free_CatB > run.log 2>&1 &   # CatA 还是 CatB 由 02b 的 T1 决定
T1=CatB nohup bash run_all.sh 04b 04c > run.log 2>&1 &
```
