#!/bin/bash
# Run step 1 (PBE+D3(BJ) fixed-cell relax) on the GPU; mirror everything to Google Drive every 3 min.
# If a previous run in Drive was interrupted, continue from its last geometry.
set -eo pipefail
PROJ=/content/drive/MyDrive/QE_PhIm2SnCl6
OUT=$PROJ/01_relax_PBE-D3
WORK=/content/work_01_relax
INPUTS=/content/inputs
mkdir -p "$OUT" "$WORK/pseudo"
cd "$WORK"

# pseudopotentials (pslibrary 1.0.0 PAW, PBE), cached in Drive
mkdir -p "$PROJ/pseudo"
for p in Sn.pbe-dn-kjpaw_psl.1.0.0.UPF Cl.pbe-n-kjpaw_psl.1.0.0.UPF O.pbe-n-kjpaw_psl.1.0.0.UPF \
         N.pbe-n-kjpaw_psl.1.0.0.UPF C.pbe-n-kjpaw_psl.1.0.0.UPF H.pbe-kjpaw_psl.1.0.0.UPF; do
  if ! grep -q "<UPF\|<PP_INFO" "$PROJ/pseudo/$p" 2>/dev/null; then
    curl -fsSL -o "$PROJ/pseudo/$p" https://pseudopotentials.quantum-espresso.org/upf_files/$p
  fi
  cp "$PROJ/pseudo/$p" pseudo/
  echo "$p  $(grep -i -m1 'Suggested minimum cutoff for wavefunctions' pseudo/$p | sed 's/^ *//')"
done

# input: fresh, or continue from the last geometry of an interrupted run
if [ -f "$OUT/relax.out" ] && ! grep -q "End final coordinates" "$OUT/relax.out"; then
  N=$(ls "$OUT"/relax.out "$OUT"/relax_part*.out 2>/dev/null | wc -l)
  mv "$OUT/relax.out" "$OUT/relax_part$N.out"
  python3 /content/inputs/continue_relax.py "$OUT/relax_part$N.out" "$INPUTS/relax.in" relax.in
  echo "[run] continuing from last geometry of relax_part$N.out"
elif [ -f "$OUT/relax.out" ]; then
  echo "[run] relax already finished in Drive: $OUT/relax.out"; exit 0
else
  cp "$INPUTS/relax.in" relax.in
fi
cp relax.in "$OUT/"; cp "$INPUTS"/*.py "$INPUTS"/*.sh "$OUT/" 2>/dev/null || true
{ nvidia-smi; echo; lscpu | head -20; echo; cat /content/drive/MyDrive/QE_build/qe-*-gpu-sm80/BUILD_INFO.txt; } > "$OUT/environment.txt" 2>&1

# run pw.x on the GPU in the background
export PATH=/content/qe/bin:$PATH
export LD_LIBRARY_PATH=/content/qe/lib:${LD_LIBRARY_PATH}
export OMP_NUM_THREADS=$(nproc) OMP_STACKSIZE=512M
ulimit -s unlimited || true
date > start_time.txt
nohup pw.x -in relax.in > relax.out 2>&1 &
PW=$!
echo $PW > pw.pid

sync_drive () { rsync -a --exclude '*.wfc*' --exclude 'wfc*.dat' "$WORK/" "$OUT/" 2>/dev/null || cp -ru "$WORK/." "$OUT/"; }

# keep the cell busy (prevents idle disconnect), print progress, mirror to Drive every 3 min
while kill -0 $PW 2>/dev/null; do
  sleep 180
  sync_drive
  NSCF=$(grep -c '^!' relax.out || true)
  E=$(grep '^!' relax.out | tail -1 | awk '{print $5}')
  F=$(grep 'Total force' relax.out | tail -1 | awk '{print $4}')
  echo "$(date +%H:%M) ionic steps: $NSCF  E = $E Ry  total force = $F Ry/Bohr"
done
date > end_time.txt
sync_drive
tail -40 relax.out
grep -q "JOB DONE" relax.out && echo "[run] pw.x finished" || echo "[run] pw.x stopped - check relax.out"
