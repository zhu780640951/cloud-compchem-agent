#!/bin/bash
# Task B (GPU, gpu4pyscf): cut the embedded cluster from the relaxed crystal, then TDDFT/NTO with three functionals
set -eo pipefail
PROJ=/content/drive/MyDrive/QE_PhIm2SnCl6
OUT=$PROJ/03_cluster_tddft
WORK=/content/work_03_cluster
mkdir -p "$OUT" "$WORK"; cd "$WORK"
log () { echo "[B $(date +%H:%M:%S)] $*"; }
export OMP_NUM_THREADS=6
log "pip install gpu4pyscf"
pip -q install gpu4pyscf-cuda12x cutensor-cu12 pyscf ase 2>&1 | grep -v -i "warning\|already" || true
python3 -c "import gpu4pyscf, pyscf, cupy; print('gpu4pyscf', gpu4pyscf.__version__, 'pyscf', pyscf.__version__, 'cupy', cupy.__version__)"
log "build cluster + ESP point charges"
python3 /content/inputs/build_cluster.py "$PROJ/01_relax_PBE-D3/relax.out" "$WORK/cluster"
rsync -a "$WORK/cluster" "$OUT/"
log "TDDFT (B3LYP, CAM-B3LYP, wB97X-D)"
python3 /content/inputs/run_tddft.py "$WORK/cluster" "$WORK/tddft" &
P=$!
while kill -0 $P 2>/dev/null; do sleep 60; rsync -a "$WORK/tddft" "$OUT/"; done
wait $P
rsync -a "$WORK/tddft" "$OUT/"
log "TASK B FINISHED"
