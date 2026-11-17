# 给 Claude Code 的执行说明：PhIm₂SnCl₆·2H₂O 阶段 3 重算

你的任务是在用户的 GCP 实例 orca-cpu-16 上，按本文件执行一系列已经准备好的 ORCA 计算。你负责**执行和按判据检查**。物理解释由用户另行处理。

## 一、必须遵守的规则

1. **不修改任何计算输入**：`阶段3_嵌入团簇重算_ORCA\` 里的 .inp、qm_cluster.xyz、mm_charges.pc、run_all.sh、analyze_orca.py 一律不改。不换泛函、基组、核数、内存设置。
2. **只能修连接问题**：如果是 gcloud 路径、密钥、引号之类的连接问题，可以修改 `gcp_scripts\_common.ps1`，并在汇报里说明改了什么。
3. **按检查点执行**：每批结束后按第四节的判据逐条检查。全部通过才进入下一批；任何一条不通过，就停下，向用户汇报，不要自己想办法绕过。
4. **不写结论**：不写 README、报告或物理解释，不用"成功""吻合""确证"这类词。汇报时原样贴数值。
5. **同一时间只跑一批**：上一批没结束前不启动新批次（06 脚本会自动拒绝）。

## 二、环境

- 本地 gcloud：`<YOUR_GCLOUD_SDK_BIN>\gcloud.ps1`
- 项目 `<YOUR_GCP_PROJECT_ID>`，实例 `orca-cpu-16`，区域 `us-central1-a`，远程用户目录 `/home/y`
- 私钥（必须显式指定，不能用 `C:\Users\y\.ssh`）：`<YOUR_GCP_SSH_KEY_PATH>`
- 所有 gcloud 命令带 `--quiet`。实例无公网 IP，gcloud 会走 IAP。
- 实例状态为 SUSPENDED 时先 resume；为 TERMINATED 时先 start。脚本已自动处理。
- 远程命令里不要用双引号，因为 Windows PowerShell 5.1 传参会吞掉。脚本里一律用单引号。

## 三、工具脚本（位于 `E:\桌面\gcould Claude space\gcp_scripts\`）

统一调用方式：

```powershell
powershell -ExecutionPolicy Bypass -File "E:\桌面\gcould Claude space\gcp_scripts\<脚本名>" [参数]
```

| 脚本 | 作用 |
|---|---|
| 01_check_env.ps1 | 只读检查：状态、核数、内存、磁盘、ORCA/OpenMPI、是否有旧计算在跑、~/stage3 是否存在 |
| 02_upload_and_run_batch1.ps1 | 已有 ~/stage3 先改名备份 → 上传 → 启动 `00 01a 01b` |
| 03_progress.ps1 | 汇总 progress.log 和全部 summary.txt（随时可跑） |
| 06_run_steps.ps1 -Steps "..." [-T1 CatA或CatB] | 启动指定批次 |
| 04_download.ps1 | 下载 jobs 和 progress.log 到本地阶段 3 文件夹 |
| 05_suspend.ps1 [-Stop] | ORCA 不在运行时挂起实例（加 -Stop 为关机） |

每个脚本都把完整输出写到 `gcp_scripts\logs\`，并另存一份 `latest_<名字>.txt`。检查结果时读这些日志。

## 四、执行流程与检查点

等待计算时，每 20 分钟运行一次 03_progress.ps1。progress.log 里每个任务会依次出现"开始"和"完成"或"失败"。

### 第 1 批（约 15 分钟）

1. 运行 01_check_env.ps1。确认 ORCA 在 `/opt/orca/orca`、`mpirun` 可用、没有正在跑的 orca 进程、/home 剩余空间大于 20 GB。不满足就停下汇报。
2. 运行 02_upload_and_run_batch1.ps1，然后等 `00`、`01a`、`01b` 三个任务都显示"完成"。

**检查点 1**（读 latest_progress.txt 中对应的 summary）：

| 编号 | 判据 |
|---|---|
| 1-1 | 00、01a、01b 都是"完成"，没有"失败" |
| 1-2 | 01a 中 `HOMO` 那一行，CatA 或 CatB 的占比 ≥ 90% |
| 1-3 | 01a 中 `LUMO` 那一行，SnCl6 的占比 ≥ 80% |
| 1-4 | 01b 中 `HOMO` 那一行以 SnCl6 为主。这是预期的对照现象，若不是也照常汇报 |

1-1 到 1-3 全部通过才继续。1-4 只需记录。

### 第 2 批（约 2–4 小时）

```powershell
... 06_run_steps.ps1 -Steps "01c 02a 02b"
```

**检查点 2**：

| 编号 | 判据 |
|---|---|
| 2-1 | 三个任务都是"完成" |
| 2-2 | 01c 满足和 1-2、1-3 相同的条件 |
| 2-3 | 02a、02b 中所有 S 和 T 激发态能量都 ≥ 2.5 eV |
| 2-4 | 02b 的 T1 能量在 2.9–3.8 eV，且性质一栏为"局域 CatA"或"局域 CatB"，占比 ≥ 60% |
| 2-5 | 02a 的 T1 能量在 3.1–3.7 eV |

从 2-4 记下 T1 所在的阳离子，下文记作 **CatX**（CatA 或 CatB）。

### 第 3 批（约 4–8 小时，可以过夜）

```powershell
... 06_run_steps.ps1 -Steps "03 04a_T1opt_UKS_free_CatX"
```

把 CatX 换成检查点 2 得到的实际名字。`03` 会依次运行 03_SOC_ZORA_TZVP_PC 和两个 03b 对照任务。

**检查点 3**（SOC）：

| 编号 | 判据 |
|---|---|
| 3-1 | 03_SOC_ZORA_TZVP_PC、03b_SOC_control_CatA_gas、03b_SOC_control_CatB_gas 都是"完成" |
| 3-2 | 03 的 T1、S1 能量分别与 02b 的 T1、S1 相差 ≤ 0.3 eV |
| 3-3 | 03 中没有任何激发态低于 2.5 eV |
| 3-4 | 03 的 summary 末尾有"SOC 矩阵元"表格 |

**检查点 4**（T1 优化）：

| 编号 | 判据 |
|---|---|
| 4-1 | 04a 是"完成"，且它的 .out 里有 `THE OPTIMIZATION HAS CONVERGED` |
| 4-2 | summary 最后一行的自旋布居：CatX 在 1.8–2.2 之间，其他片段绝对值都 < 0.2 |
| 4-3 | 本地或远程 `~/stage3/T1_geom_CatX.xyz` 已生成 |

检查点 3 不通过时，不影响第 4 批，但必须汇报。检查点 4 不通过时，停下汇报。

### 第 4 批（约 0.5 小时）

```powershell
... 06_run_steps.ps1 -Steps "04b 04c" -T1 CatX
```

判据：04b、04c 都是"完成"；04c 中没有低于 1.5 eV 的激发态。

### 收尾

1. 运行 03_progress.ps1，得到最终的完整汇总。
2. 运行 04_download.ps1，确认日志里"已下载 N 个文件"的 N > 0。
3. 运行 05_suspend.ps1。

### 可选（仅当用户明确同意时执行）

`06_run_steps.ps1 -Steps "01d 01e"`：诊断阶段 2 出错的原因，约 1.5 小时。

## 五、汇报格式

每个检查点结束后，用下面的格式向用户汇报：

```text
检查点 N：通过 / 未通过
- N-1：通过（原样贴出依据的那一行）
- N-2：未通过（原样贴出依据的那一行）
...
下一步：……（或：已停止，等待用户指示）
```

全部结束后，告诉用户：把 `gcp_scripts\logs\latest_progress.txt` 交给 Claude 对话做物理分析。

## 六、出错处理

| 现象 | 处理 |
|---|---|
| gcloud 连接失败或超时 | 重试 1 次；仍失败就运行 01_check_env.ps1，把日志末尾贴给用户，然后停止 |
| 某任务"失败" | 用 `gcloud compute ssh ... --command='tail -50 ~/stage3/jobs/<任务名>/<任务名>.out'` 取出末尾 50 行，贴给用户，然后停止 |
| BUSY-run_all-still-running | 说明上一批还没结束，继续等待，不要重复启动 |
| 一批超过预计时间的 2 倍仍未结束 | 贴出 latest_progress.txt 给用户，不要终止进程 |
