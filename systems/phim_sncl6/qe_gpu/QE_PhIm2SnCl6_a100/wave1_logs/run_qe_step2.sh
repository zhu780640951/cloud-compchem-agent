#!/bin/bash
# Task A (GPU): step 2 = SCF with empty bands -> VBM/CBM |psi|^2 cubes -> NSCF DOS -> PDOS -> band path -> plots
set -eo pipefail
PROJ=/content/drive/MyDrive/QE_PhIm2SnCl6
OUT=$PROJ/02_bands_pdos
WORK=/content/work_02_bands
mkdir -p "$OUT" "$WORK"
cd "$WORK"
log () { echo "[A $(date +%H:%M:%S)] $*"; }
sync_out () { rsync -a --exclude 'tmp/' --exclude '*.dat' "$WORK/" "$OUT/"; }

log "setup QE GPU binaries (pw, pp, projwfc, bands)"
bash /content/inputs/setup_qe_gpu.sh
export PATH=/content/qe/bin:$PATH LD_LIBRARY_PATH=/content/qe/lib:${LD_LIBRARY_PATH}
export OMP_NUM_THREADS=6 OMP_STACKSIZE=512M     # leave the other 6 cores to task B
ulimit -s unlimited || true

rm -rf pseudo; cp -r "$PROJ/pseudo" ./pseudo
python3 /content/inputs/make_qe_step2.py "$PROJ/01_relax_PBE-D3/relax.out" .
cp *.in "$OUT/"

run () { local exe=$1 name=$2; log "start $exe $name"; local t0=$(date +%s)
         $exe -in $name.in > $name.out 2>&1; log "done  $exe $name ($(( $(date +%s)-t0 )) s)"; sync_out; }
run pw.x scf
grep "highest occupied, lowest unoccupied" scf.out | tail -1
run pp.x pp_vbm
run pp.x pp_cbm
run pw.x nscf
run projwfc.x projwfc
run pw.x bands
run bands.x bandsx
log "plots"
python3 /content/inputs/plot_step2.py . 2>&1 | grep -v Warning
sync_out
log "TASK A FINISHED"
