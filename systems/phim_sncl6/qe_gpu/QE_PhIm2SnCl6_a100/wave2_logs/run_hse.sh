#!/bin/bash
# Task C (GPU): HSE06 band gap.  PBE(SG15) reference SCF, then HSE06 (ACE).  Fallbacks on GPU OOM:
#   (ecutfock 120, k 3x2x2) -> (ecutfock 100, k 3x2x2) -> (ecutfock 100, k 2x2x1)
set -o pipefail
PROJ=/content/drive/MyDrive/QE_PhIm2SnCl6
OUT=$PROJ/04_hse06
WORK=/content/work_04_hse
mkdir -p "$OUT" "$WORK"; cd "$WORK"
log () { echo "[C $(date +%H:%M:%S)] $*"; }
sync_out () { rsync -a --exclude 'tmp/' "$WORK/" "$OUT/" 2>/dev/null; }
bash /content/inputs/setup_qe_gpu.sh
export PATH=/content/qe/bin:$PATH LD_LIBRARY_PATH=/content/qe/lib:${LD_LIBRARY_PATH}
export OMP_NUM_THREADS=${QE_THREADS:-2} OMP_STACKSIZE=512M
ulimit -s unlimited || true

# SG15 ONCV pseudopotentials (cached in Drive)
PPC=$PROJ/pseudo_sg15
if [ ! -f "$PPC/map.json" ]; then
  mkdir -p "$PPC" /content/sg15 && cd /content/sg15
  curl -fsSL -o sg15.tgz http://www.quantum-simulation.org/potentials/sg15_oncv/sg15_oncv_upf_2020-02-06.tar.gz \
    || curl -fsSL -o sg15.tgz https://www.quantum-simulation.org/potentials/sg15_oncv/sg15_oncv_upf_2020-02-06.tar.gz
  tar xzf sg15.tgz
  python3 - "$PPC" <<'PY'
import glob, os, re, shutil, sys, json
dst = sys.argv[1]; m = {}
for el in ["Sn", "Cl", "O", "N", "C", "H"]:
    fs = [f for f in glob.glob(f"**/{el}_ONCV_PBE-*.upf", recursive=True) if "FR" not in os.path.basename(f)]
    fs.sort(key=lambda f: [int(x) for x in re.findall(r"PBE-(\d+)\.(\d+)", f)[0]])
    shutil.copy(fs[-1], dst); m[el] = os.path.basename(fs[-1])
json.dump(m, open(f"{dst}/map.json", "w")); print("SG15:", m)
PY
  cd "$WORK"
fi
rm -rf pseudo_sg15; cp -r "$PPC" pseudo_sg15; cat pseudo_sg15/map.json; echo

gap () { grep "highest occupied, lowest unoccupied" "$1" | tail -1; }
run () { local name=$1; log "start pw.x $name"; local t0=$(date +%s)
         pw.x -in $name.in > $name.out 2>&1; local rc=$?
         log "end   pw.x $name rc=$rc ($(( $(date +%s)-t0 )) s)"; sync_out; return $rc; }

if ! grep -q "JOB DONE" "$OUT/pbe_sg15.out" 2>/dev/null; then
  python3 /content/inputs/make_hse.py "$PROJ/01_relax_PBE-D3/relax.out" . pseudo_sg15/map.json 120 3 2 2
  run pbe_sg15
else cp "$OUT/pbe_sg15.out" .; fi
log "PBE(SG15): $(gap pbe_sg15.out)"

for cfg in "120 3 2 2" "100 3 2 2" "100 2 2 1"; do
  if grep -q "JOB DONE" "$OUT/hse.out" 2>/dev/null; then cp "$OUT/hse.out" .; break; fi
  set -- $cfg
  python3 /content/inputs/make_hse.py "$PROJ/01_relax_PBE-D3/relax.out" . pseudo_sg15/map.json $1 $2 $3 $4
  echo "ecutfock=$1 k=$2x$3x$4" > hse_config.txt
  rm -rf tmp/hse.*; run hse && grep -q "JOB DONE" hse.out && break
  log "HSE failed with ecutfock $1 k $2x$3x$4:"; grep -i -m3 "error\|out of memory\|allocat" hse.out
  cp hse.out "hse_failed_${1}_${2}${3}${4}.out"
done
log "HSE06:     $(gap hse.out)   [$(cat hse_config.txt)]"
python3 /content/inputs/analyze_hse.py . | tee hse_summary.txt
sync_out
log "TASK C FINISHED"
