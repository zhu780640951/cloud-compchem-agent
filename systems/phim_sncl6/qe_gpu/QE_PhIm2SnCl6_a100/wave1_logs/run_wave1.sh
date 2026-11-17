#!/bin/bash
# Wave 1 orchestrator: run task A (QE bands/PDOS) and task B (cluster TDDFT) side by side on one A100,
# log GPU/CPU/RAM every 30 s, print a status line every 2 min (keeps the Colab cell busy).
PROJ=/content/drive/MyDrive/QE_PhIm2SnCl6
mkdir -p "$PROJ/02_bands_pdos" "$PROJ/03_cluster_tddft" "$PROJ/wave1_logs"
L=$PROJ/wave1_logs
cp /content/inputs/*.sh /content/inputs/*.py "$L/" 2>/dev/null
nvidia-smi --query-gpu=timestamp,utilization.gpu,memory.used,memory.total,power.draw,temperature.gpu --format=csv -l 30 > "$L/gpu_usage.csv" 2>&1 &
G=$!
( while true; do echo "$(date +%F_%T) cpu_busy% $((100 - $(vmstat 1 2 | tail -1 | awk '{print $15}'))) ram_used_GB $(free -g | awk '/Mem/{print $3}') pw_x $(pgrep -c pw.x) python $(pgrep -c python3)"; sleep 30; done ) > "$L/cpu_ram_usage.log" 2>&1 &
C=$!
date > "$L/start_time.txt"
bash /content/inputs/run_qe_step2.sh > "$L/taskA_qe.log" 2>&1 &
A=$!
bash /content/inputs/run_cluster.sh > "$L/taskB_tddft.log" 2>&1 &
B=$!
while kill -0 $A 2>/dev/null || kill -0 $B 2>/dev/null; do
  sleep 120
  echo "$(date +%H:%M) | A: $(grep '^\[A' "$L/taskA_qe.log" | tail -1 | cut -c1-70) | B: $(tail -1 "$L/taskB_tddft.log" | cut -c1-90) | GPU $(tail -1 "$L/gpu_usage.csv" | cut -d, -f2,3)"
done
wait $A; RA=$?; wait $B; RB=$?
date > "$L/end_time.txt"
kill $G $C 2>/dev/null
echo "task A exit $RA, task B exit $RB"
echo "---- A ----"; tail -15 "$L/taskA_qe.log"
echo "---- B ----"; tail -25 "$L/taskB_tddft.log"
cat "$PROJ/02_bands_pdos/summary_step2.txt" 2>/dev/null
