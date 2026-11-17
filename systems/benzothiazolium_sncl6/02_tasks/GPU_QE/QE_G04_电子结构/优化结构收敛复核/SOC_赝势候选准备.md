# SOC 赝势初步筛选（2026-10-31）

已查看 QE 官方 PS Library 公布的候选：Sn.rel-pbe-dn-rrkjus_psl.1.0.0.UPF（USPP、PBE、全相对论、14 价电子、含 SOC）与 Cl.rel-pbe-n-rrkjus_psl.1.0.0.UPF（USPP、PBE、全相对论）。来源：

- https://pseudopotentials.quantum-espresso.org/legacy_tables/ps-library/sn
- https://pseudopotentials.quantum-espresso.org/legacy_tables/ps-library/cl
- https://pseudopotentials.quantum-espresso.org/upf_files/Sn.rel-pbe-dn-rrkjus_psl.1.0.0.UPF
- https://pseudopotentials.quantum-espresso.org/upf_files/Cl.rel-pbe-n-rrkjus_psl.1.0.0.UPF

尚未下载、运行或验证这套候选。需检查 H、C、N、O、S 的候选文件头、类型、泛函、价电子和推荐截断能；核对与现有标量模型的价电子数及对应关系，设计相同赝势族、结构、网格和截断能的 SOC 开关对照。需重新验证收敛，SOC 的变化与赝势变化要分离；不可把替换不同赝势前后的带隙差直接归为 SOC。QE SOC 要求 noncolin、lspinorb 及适合的全相对论赝势。

本轮 k 点复核脚本 `qe_kmesh_convergence.py` 已准备，在授权挂载 Drive 后才能恢复已保存的优化结构 SCF 检查点并开始 6×6×4 NSCF。原有 4×4×3 与 6×6×4 不是彼此嵌套网格，应比较带边能量及其 k 坐标，仅称采样敏感性，不能宣称全局极值。当前任务尚未开始。
