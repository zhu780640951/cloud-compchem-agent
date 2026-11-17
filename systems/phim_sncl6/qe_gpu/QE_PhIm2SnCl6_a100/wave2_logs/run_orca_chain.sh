#!/bin/bash
# Task D (CPU, ORCA): one functional per chain.  usage: run_orca_chain.sh <cam|wb97x> <nprocs> <maxcore_MB>
#  1 soc_S0geom : ZORA SOC-TDDFT at the crystal (wave-1) cluster geometry  -> vertical S/T, SOCME
#  2 opt_S0     : S0 optimisation in the point-charge field
#  3 opt_T1     : UKS triplet optimisation, started from opt_S0
#  4 sp_S0_at_T1, sp_T1_at_S0 : cross single points  -> E_em, E_00, reorganisation energies
#  5 soc_T1geom : ZORA SOC-TDDFT at the T1 geometry  -> emission energy, T1 sublevel radiative rates
# Each finished job is skipped on rerun; an unfinished optimisation restarts from the last frame of its _trj.xyz.
XC=$1; NP=$2; MC=$3
PROJ=/content/drive/MyDrive/QE_PhIm2SnCl6
OUT=$PROJ/05_orca_soc_T1/$XC
WORK=/content/work_05_orca/$XC
mkdir -p "$OUT" "$WORK"; cd "$WORK"
source /content/orca_env.sh
[ -n "$ORCA_SERIAL" ] && NP=1
log () { echo "[D-$XC $(date +%H:%M:%S)] $*"; }
sync_out () { rsync -a --exclude '*.tmp*' --exclude '*.gbw' --exclude '*.densities*' --exclude '*.cis' "$WORK/" "$OUT/" 2>/dev/null; }
cp $PROJ/03_cluster_tddft/cluster/mm_charges.pc mm.pc
cp $PROJ/03_cluster_tddft/cluster/qm_cluster.xyz crystal.xyz
done_ () { grep -q "ORCA TERMINATED NORMALLY" "$OUT/$1.out" 2>/dev/null; }
runjob () {  # name job xyz
  local name=$1 job=$2 xyz=$3
  if done_ $name; then log "$name already done"; cp "$OUT/$name".* . 2>/dev/null; return 0; fi
  if [[ $job == opt* ]] && [ -f "$OUT/${name}_trj.xyz" ]; then   # restart from last frame
    python3 - "$OUT/${name}_trj.xyz" restart_$name.xyz <<'PY'
import sys; L = open(sys.argv[1]).read().split("\n"); n = int(L[0]); fr = [L[i:i+n+2] for i in range(0, len(L) - n - 1, n + 2)]
open(sys.argv[2], "w").write("\n".join(fr[-1]) + "\n"); print("restart frame", len(fr))
PY
    xyz=restart_$name.xyz
  fi
  python3 /content/inputs/make_orca.py $job $XC $xyz $NP $MC > $name.inp
  log "start $name ($job, $NP procs, maxcore $MC)"; local t0=$(date +%s)
  $ORCA/orca $name.inp > $name.out 2>&1 &
  local P=$!; while kill -0 $P 2>/dev/null; do sleep 180; sync_out; done; wait $P
  log "end   $name ($(( $(date +%s)-t0 )) s) $(grep -c 'ORCA TERMINATED NORMALLY' $name.out | sed 's/1/OK/;s/^0$/FAILED/')"
  sync_out; grep -q "ORCA TERMINATED NORMALLY" $name.out
}
runjob soc_S0geom soc crystal.xyz || log "soc_S0geom failed (continuing)"
runjob opt_S0 opt_S0 crystal.xyz || { log "opt_S0 failed"; exit 1; }
runjob opt_T1 opt_T1 opt_S0.xyz  || { log "opt_T1 failed"; exit 1; }
runjob sp_S0_at_T1 sp_S0 opt_T1.xyz
runjob sp_T1_at_S0 sp_T1 opt_S0.xyz
runjob soc_T1geom soc opt_T1.xyz
sync_out
log "CHAIN $XC FINISHED"
