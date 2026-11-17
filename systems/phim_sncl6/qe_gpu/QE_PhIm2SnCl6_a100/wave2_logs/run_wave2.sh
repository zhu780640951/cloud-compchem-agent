#!/bin/bash
# Wave-2 orchestrator on one A100 runtime:
#   GPU : task C  = QE HSE06 (2 OpenMP threads)
#   CPU : task D  = two ORCA chains (CAM-B3LYP, wB97X-D3) in parallel, (nproc-2)/2 MPI ranks each
# Logs GPU/CPU/RAM every 30 s; prints a status line every 3 min (keeps the cell alive); all output mirrored to Drive.
PROJ=/content/drive/MyDrive/QE_PhIm2SnCl6
L=$PROJ/wave2_logs; mkdir -p "$L" "$PROJ/04_hse06" "$PROJ/05_orca_soc_T1"
cp /content/inputs/* "$L/" 2>/dev/null
pip -q install ase 2>&1 | grep -v -i "warning\|already" || true
NC=$(nproc); RAM=$(free -m | awk '/Mem/{print $2}')
NPO=$(( (NC - 2) / 2 )); [ $NPO -lt 1 ] && NPO=1
MC=$(( RAM * 70 / 100 / (2 * NPO) )); [ $MC -gt 4000 ] && MC=4000
echo "cores $NC, RAM $RAM MB -> QE 2 threads, ORCA 2 x $NPO ranks, maxcore $MC MB" | tee "$L/plan.txt"
nvidia-smi --query-gpu=timestamp,utilization.gpu,memory.used,memory.total,power.draw,temperature.gpu --format=csv -l 30 > "$L/gpu_usage.csv" 2>&1 &
G=$!
( while true; do echo "$(date +%F_%T) cpu_busy% $((100 - $(vmstat 1 2 | tail -1 | awk '{print $15}'))) ram_used_GB $(free -g | awk '/Mem/{print $3}') pw_x $(pgrep -c pw.x) orca $(pgrep -c orca_)"; sleep 30; done ) > "$L/cpu_ram_usage.log" 2>&1 &
C=$!
date > "$L/start_time.txt"
QE_THREADS=2 bash /content/inputs/run_hse.sh > "$L/taskC_hse.log" 2>&1 &
A=$!
bash /content/inputs/setup_orca.sh > "$L/orca_setup.log" 2>&1; cat "$L/orca_setup.log" | tail -3
bash /content/inputs/run_orca_chain.sh cam   $NPO $MC > "$L/taskD_cam.log" 2>&1 &
B1=$!
sleep 20
bash /content/inputs/run_orca_chain.sh wb97x $NPO $MC > "$L/taskD_wb97x.log" 2>&1 &
B2=$!
while kill -0 $A 2>/dev/null || kill -0 $B1 2>/dev/null || kill -0 $B2 2>/dev/null; do
  sleep 180
  echo "$(date +%H:%M) | C: $(grep '^\[C' "$L/taskC_hse.log" | tail -1 | cut -c1-60) | cam: $(tail -1 "$L/taskD_cam.log" | cut -c1-60) | wb97x: $(tail -1 "$L/taskD_wb97x.log" | cut -c1-60) | GPU $(tail -1 "$L/gpu_usage.csv" | cut -d, -f2,3)"
done
date > "$L/end_time.txt"; kill $G $C 2>/dev/null
python3 /content/inputs/analyze_wave2.py "$PROJ/05_orca_soc_T1" "$PROJ/03_cluster_tddft/cluster/cluster_info.json" 2>&1 | tail -60
cat "$PROJ/04_hse06/hse_summary.txt" 2>/dev/null
echo "WAVE 2 FINISHED"
