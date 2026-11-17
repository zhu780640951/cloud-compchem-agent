#!/usr/bin/env bash
# =============================================================================
# run_all.sh —— 一条命令跑完整个流程（在 Colab 终端或笔记本单元格里后台运行）
#
#   nohup bash run_all.sh > run_all.log 2>&1 &
#
# 顺序：后台编译后处理程序（CPU） ‖ 结构优化（GPU） → run_after_relax.sh
# 前提：已运行 setup_qe_gpu.sh；谷歌云盘已挂载（赝势缺了会自动下载）。
# =============================================================================
cd /content/qe-snpim
# 赝势：按 01_relax.in 里 ATOMIC_SPECIES 列出的文件名，缺哪个从 QE 官网赝势库下载哪个
mkdir -p pseudo
for upf in $(awk '/ATOMIC_SPECIES/{f=1;next} f&&NF==3{print $3} f&&NF!=3{f=0}' 01_relax.in); do
  [[ -s pseudo/$upf ]] || curl -sfL "https://pseudopotentials.quantum-espresso.org/upf_files/$upf" -o "pseudo/$upf" \
    || { echo "赝势 $upf 下载失败"; exit 1; }
done
[[ -f /content/DONE_qe731 ]] || nohup bash build_qe_pp.sh > /content/build_qe_pp.log 2>&1 &
# 每 30 秒记录一次显存占用和 GPU 利用率，用来判断该选哪种显卡（随结果一起存进云盘）
nohup nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu \
  --format=csv -l 30 > gpu_usage.csv 2>/dev/null &

bash save_to_drive.sh >> save_to_drive.log 2>&1   # 先把输入文件存一份，确定运行名
echo "[$(date '+%H:%M:%S')] 开始 relax"
if qe pw.x -in 01_relax.in > 01_relax.out 2>&1 && grep -q 'JOB DONE' 01_relax.out; then
  touch DONE_relax; echo "[$(date '+%H:%M:%S')] 完成 relax"
else
  touch FAIL_relax; echo "[$(date '+%H:%M:%S')] relax 未正常结束（可能到了 max_seconds），看 01_relax.out"
  bash save_to_drive.sh >> save_to_drive.log 2>&1
  grep -q "bfgs converged" 01_relax.out || exit 1   # 没收敛就停下，由人判断是否续算
fi
bash save_to_drive.sh >> save_to_drive.log 2>&1
bash run_after_relax.sh
