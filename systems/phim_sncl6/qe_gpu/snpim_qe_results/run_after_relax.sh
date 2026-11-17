#!/usr/bin/env bash
# =============================================================================
# run_after_relax.sh —— 结构优化完成后依次执行：
#   02 自洽计算（GPU，读带隙） → 03 非自洽计算（GPU，密 k 点） → 04 PDOS（CPU）
#   → 05 能带计算（GPU） → 05 bands.x 后处理（CPU） → 汇总
# 每一步结束写 DONE_<步骤> 文件，失败写 FAIL_<步骤> 并停止。
# =============================================================================
cd /content/qe-snpim
CPU="/content/bin/micromamba run -r /content/mamba -p /content/qecpu"
step() {  # step 名称 命令...
  local name="$1"; shift
  echo "[$(date '+%H:%M:%S')] 开始 $name"
  if "$@"; then touch "DONE_$name"; echo "[$(date '+%H:%M:%S')] 完成 $name"
  else touch "FAIL_$name"; echo "[$(date '+%H:%M:%S')] 失败 $name"; exit 1; fi
}
python3 make_inputs.py from-relax 01_relax.out
step scf   bash -c "qe pw.x -in 02_scf.in > 02_scf.out 2>&1 && grep -q 'JOB DONE' 02_scf.out"
# 能带：本征值直接从 05_bands.out 读取（verbosity='high' 会打印），不依赖 bands.x
step bands bash -c "qe pw.x -in 05_bands.in > 05_bands.out 2>&1 && grep -q 'JOB DONE' 05_bands.out"
step nscf  bash -c "qe pw.x -in 03_nscf.in > 03_nscf.out 2>&1 && grep -q 'JOB DONE' 03_nscf.out"
# PDOS：NGC 镜像不含 projwfc.x，用 conda-forge 的 QE 7.6（CPU）读取 7.3.1 的结果
step pdos  bash -c "while [ ! -f /content/DONE_qe731 ]; do sleep 30; done; /content/q-e-qe-7.3.1/bin/projwfc.x -in 04_projwfc.in > 04_projwfc.out 2>&1 && ls snpim.pdos.pdos_tot"
python3 make_inputs.py summary
touch DONE_all
