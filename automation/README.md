# 云端后台调度基础设施 (`automation/`)

本目录沉淀了两套由 AI Agent 驱动、在后台异步运行计算化学任务的调度与持久化方案：

## 1. Colab GPU + Google Drive (`colab_gpu/`)

面向 **Quantum ESPRESSO 7.5 GPU（A100 `sm_80` / NVHPC）** 的周期性 DFT 计算：

- `colab_project_cli.py`：基于官方 `google-colab-cli`（测试版本 `0.7.5`）的项目级包装器，扩展了三项核心能力：
  1. 监听 `drive_auth_needed` 事件并自动在浏览器弹出 Google 官方授权页（同时保留文本链接备份）；
  2. 将 `drive.mount(..., timeout_ms=600000)` 与客户端等待超时放宽至 `900s`，适配大容量 Drive 挂载；
  3. 自动将全部 CLI 交互与状态记录到 `cli_history/*.jsonl`。
- `qe_gpu_build/`：
  - `setup_qe_gpu.sh` / `build_qe_pp.sh`：在 Colab 上配置与编译 QE GPU 版（含内置 FFT / `chmod +x` 权限修复）及后处理工具；
  - `restore_qe_cache.py` / `drive_inventory.py` / `flush_drive.py`：从 Google Drive 缓存（`MyDrive/QE_build/qe-7.5-gpu-sm80/`）恢复 `pw.x` 与动态库到临时运行盘，并在释放运行时前执行 `drive.flush_and_unmount()`，避免检查点丢失。
- `smoke_tests/`：Colab GPU 连通性、往返文件传输以及 H₂ SCF 检查点跨运行时恢复微测试。

## 2. Google Cloud Compute Engine CPU (`gcp_cpu/`)

面向 **ORCA 6.1.1（大内存多核 CPU 实例，如 12 vCPU / 192 GiB）** 的分子/嵌入团簇激发态与 SOC 计算：

- `_common.ps1.example` + `01_check_env.ps1` ~ `08_download_new.ps1`：早期的 PowerShell + `gcloud compute ssh/scp`（IAP 隧道 + 显式 `--ssh-key-file` + `--quiet`）后台批量提交、轮询进度、回传结果与自动 `suspend` 脚本集；
- `cpu_smoke_test.py`：Python 版远端 ORCA 1 核 / 2 核 H₂ 微型连通性与 MPI/PATH 校验脚本（后续在 `systems/benzothiazolium_sncl6/scripts/` 中进一步演化为 JSON 驱动的异步任务启动与验收脚本）。

## 使用前提（脱敏说明）

仓库中的所有脚本已移除真实账号邮箱、GCP 项目 ID、SSH 私钥、OAuth ADC 凭据与本地个人绝对路径。复用前请：
1. 参考根目录 `.env.example` 配置本地环境变量；
2. 复制 `Colab.cmd.example` / `login_colab.cmd.example` 或 `_common.ps1.example` 为本地脚本（已被 `.gitignore` 忽略，勿提交含凭据文件）。
