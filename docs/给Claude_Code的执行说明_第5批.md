# 给 Claude Code 的执行说明：第 5 批（补充计算 + 出图）

规则与 `给Claude_Code的执行说明.md` 第一、二节相同：不改计算输入，只按判据检查，不写结论，原样汇报数值。
本批例外：如果 `make_cubes.sh` 生成 cube 失败，允许只修改 `make_cubes.sh` 里 orca_plot 的菜单输入序列（见第 4 步）。

## 本批要做的事

| 任务 | 目的 | 预计用时 |
|---|---|---|
| 04c2_SOC_ZORA_at_T1geom | 在 T1 结构上计算 SOC，决定磷光辐射速率 | 约 1 小时 |
| 01d_diag_DKH_ANO_PC、01e_diag_DKH_ANO_gas | 诊断阶段 2 出错原因（DKH + ANO-RCC 设置，带/不带点电荷） | 约 1.5 小时 |
| make_cubes.sh | 生成论文配图用的轨道 cube 文件和 3 个 molden 文件 | 约 5 分钟 |

## 步骤

1. 运行 `01_check_env.ps1`（自动开机）。
2. 上传两个新文件：
   - `07_upload_file.ps1 -Name 04c2_SOC_ZORA_at_T1geom.inp`
   - `07_upload_file.ps1 -Name make_cubes.sh`
3. 一次启动三个计算（`-T1 CatA` 只影响 04c2，01d/01e 不受影响）：
   - `06_run_steps.ps1 -Steps "04c2 01d 01e" -T1 CatA`
   - 用你上次改写的纯英文监控方式，每 10 分钟检查一次 run_all 是否结束。
4. 三个任务都结束后，远程执行：`cd ~/stage3 && bash make_cubes.sh`
   - 输出里应有 17 行 `OK`（14 个轨道 cube + 3 个 molden），最后列出 `~/stage3/cubes.tar.gz`。
   - 如果出现 `FAIL`：先远程执行 `printf '11\n' | /opt/orca/orca_plot ~/stage3/jobs/01c_S0_wB97X_TZVP_PC/01c_S0_wB97X_TZVP_PC.gbw -i` 查看菜单编号，只修改 `make_cubes.sh` 中 `printf '1\n1\n3\n%d\n2\n%d\n4\n80\n5\n7\n10\n11\n'` 这一串（含义依次为：选绘图类型=分子轨道、选 alpha/beta、选轨道号、网格 80、格式=Gaussian cube、生成、退出），然后重跑。改了什么要汇报。
5. 下载新结果（只下这几个，不要用 04_download 下全部）：
   - `08_download_new.ps1 -Paths "jobs/04c2_SOC_ZORA_at_T1geom_CatA jobs/01d_diag_DKH_ANO_PC jobs/01e_diag_DKH_ANO_gas cubes progress.log"`
   - 确认本地 `阶段3_嵌入团簇重算_ORCA\cubes\` 里有 .cube 文件。
6. 运行 `05_suspend.ps1 -Stop`，确认状态为 TERMINATED。

## 检查点 5

| 编号 | 判据 |
|---|---|
| 5-1 | 04c2、01d、01e 都是"完成" |
| 5-2 | 04c2 的 summary 中没有低于 1.5 eV 的激发态 |
| 5-3 | 04c2 的 T1 在 2.2–2.6 eV 之间，性质为"局域 CatA" |
| 5-4 | 04c2 的 summary 末尾有"SOC 矩阵元"表格 |
| 5-5 | 01d、01e 不设数值判据，只需原样贴出各自 summary 的"前线轨道"部分（HOMO/LUMO 能量、组成、能隙） |
| 5-6 | make_cubes 有 17 行 OK（14 个 cube + 3 个 molden），cubes 已下载到本地 |

5-2 或 5-3 不通过时，不影响后续步骤，照常下载和关机，但必须汇报。
