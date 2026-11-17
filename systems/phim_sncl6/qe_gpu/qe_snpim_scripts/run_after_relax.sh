#!/usr/bin/env bash
# =============================================================================
# run_after_relax.sh —— 结构优化完成后依次执行，并把结果完整保存到谷歌云盘：
#   02 自洽（GPU） → 06 导出 cube（CPU pp.x：总电荷密度、价带顶/导带底电荷分布）
#   → 打包自洽波函数 → 03 非自洽（GPU） → 04 PDOS（CPU projwfc.x）
#   → 05 能带（GPU，单独目录，算完删掉） → 画图、导出结构、汇总 → 最终同步
# 每算完一步写 DONE_<步骤>（失败写 FAIL_<步骤> 并停止），并立即同步一次云盘，
# 所以即使运行时中途断开，已完成的部分也都在云盘里。
#
# 环境变量：
#   SAVE_WFC=scf   （默认）保存自洽波函数快照 wfc_scf.tar（约 1~2 GB）。
#                  有了它，以后画轨道、重算态密度/能带/光学性质都不用重跑结构优化和自洽。
#   SAVE_WFC=all   另外保存非自洽波函数快照 wfc_nscf.tar（再加约 2~3 GB）
#   SAVE_WFC=none  不存波函数（云盘空间紧张时）
#   CUBE_WIN=0.3   价带顶/导带底电荷分布取的能量窗口宽度（eV）
# =============================================================================
cd /content/qe-snpim
PP=/content/q-e-qe-7.3.1/bin
SAVE_WFC="${SAVE_WFC:-scf}"
CUBE_WIN="${CUBE_WIN:-0.3}"

step() {  # step 名称 命令...
  local name="$1"; shift
  echo "[$(date '+%H:%M:%S')] 开始 $name"
  if "$@"; then touch "DONE_$name"; echo "[$(date '+%H:%M:%S')] 完成 $name"
  else touch "FAIL_$name"; echo "[$(date '+%H:%M:%S')] 失败 $name"; sync_drive; exit 1; fi
}
sync_drive() { bash save_to_drive.sh "$@" >> save_to_drive.log 2>&1 || true; }
wait_pp()    { while [ ! -f /content/DONE_qe731 ]; do
                 [ -f /content/FAIL_qe731 ] && { echo "后处理程序编译失败，见 /content/build_qe_pp.log"; return 1; }
                 sleep 30; done; }
pw()         { qe pw.x -in "$1.in" > "$1.out" 2>&1 && grep -q 'JOB DONE' "$1.out"; }

run_cubes() {
  wait_pp || return 1
  for f in 06_pp_*.in; do
    "$PP/pp.x" -in "$f" > "${f%.in}.out" 2>&1 || return 1
  done
  rm -f ./*_ildos.dat rho_total.dat   # 中间文件，cube 已包含全部信息
  ls cube/*.cube
}
snapshot()   { rm -f "wfc_$1.tar"; tar -cf "wfc_$1.tar" -C tmp snpim.save && ls -lh "wfc_$1.tar"; }
run_pdos()   { wait_pp || return 1; "$PP/projwfc.x" -in 04_projwfc.in > 04_projwfc.out 2>&1 && ls snpim.pdos.pdos_tot; }
run_bands()  {
  # 能带算 122 个 k 点，波函数有十几 GB 且用不上：放在单独目录 tmp_bands，算完删除，
  # 免得残留文件混进 tmp/ 里的波函数
  rm -rf tmp_bands && mkdir -p tmp_bands/snpim.save
  find tmp/snpim.save -maxdepth 1 -type f ! -name 'wfc*.dat' -exec cp {} tmp_bands/snpim.save/ \;
  pw 05_bands; local rc=$?
  rm -rf tmp_bands
  return $rc
}

python3 make_inputs.py from-relax 01_relax.out
sync_drive

step scf    pw 02_scf
sync_drive
python3 make_inputs.py pp 02_scf.out "$CUBE_WIN"
step cube   run_cubes
[[ "$SAVE_WFC" != none ]] && step snap_scf snapshot scf
sync_drive

step nscf   pw 03_nscf
step pdos   run_pdos
[[ "$SAVE_WFC" == all ]] && step snap_nscf snapshot nscf
sync_drive

step bands  run_bands
sync_drive

# 画图、导出结构、整理 PDOS 文件、汇总
python3 plot_results.py > plot_results.log 2>&1
mkdir -p pdos && mv snpim.pdos.pdos_* pdos/ 2>/dev/null
python3 make_inputs.py export 01_relax.out
python3 make_inputs.py summary
sync_drive final
touch DONE_all
echo "[$(date '+%H:%M:%S')] 全部完成，已同步到云盘：MyDrive/QE计算结果/$(cat .run_name)"
