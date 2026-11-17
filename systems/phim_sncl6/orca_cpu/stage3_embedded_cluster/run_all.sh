#!/bin/bash
# 阶段 3：嵌入团簇 ORCA 重算（在 GCloud 虚拟机 orca-cpu-16 上运行）
# 用法：
#   nohup bash run_all.sh 00 01a 01b > run.log 2>&1 &      # 只跑指定步骤（按文件名前缀匹配）
#   nohup bash run_all.sh > run.log 2>&1 &                 # 不给参数 = 默认 00 01a 01b 01c 02a 02b 03
#   T1=CatB nohup bash run_all.sh 04b 04c > run.log 2>&1 & # 第 4 步后半段：指定用哪个阳离子的 T1 结构
# 进度：tail -f progress.log    每个任务的摘要：jobs/<任务名>/<任务名>.summary.txt
source /etc/profile.d/orca.sh 2>/dev/null
ORCA=${ORCA:-/opt/orca/orca}
BASE=$(cd "$(dirname "$0")" && pwd)
STEPS=${*:-"00 01a 01b 01c 02a 02b 03"}
cd "$BASE"

run_one () {
  local inp=$1 name=${1%.inp} sfx=""
  case $name in 04b*|04c*) [ -z "$T1" ] && { echo "第 4 步后半段需要 T1=CatA 或 T1=CatB"; return; }; sfx="_$T1";; esac
  local d="$BASE/jobs/$name$sfx"; mkdir -p "$d"
  cp "$BASE/$inp" "$BASE/qm_cluster.xyz" "$BASE/mm_charges.pc" "$d/"
  [ -n "$sfx" ] && cp "$BASE/T1_geom_$T1.xyz" "$d/T1_geom.xyz"
  cd "$d"
  echo "[$(date '+%F %T')] 开始 $name$sfx" | tee -a "$BASE/progress.log"
  "$ORCA" "$inp" > "$name.out" 2>&1
  if grep -q "ORCA TERMINATED NORMALLY" "$name.out"; then st="完成"; else st="失败（看 $name.out 末尾）"; fi
  echo "[$(date '+%F %T')] $st $name$sfx  $(grep -h 'TOTAL RUN TIME' "$name.out" | sed 's/TOTAL RUN TIME: //')" | tee -a "$BASE/progress.log"
  python3 "$BASE/analyze_orca.py" "$name.out" > "$name.summary.txt" 2>&1
  case $name in 04a_*) [ -f "$name.xyz" ] && cp "$name.xyz" "$BASE/T1_geom_${name##*_}.xyz";; esac
  rm -f *.tmp* 2>/dev/null
  cd "$BASE"
}

for s in $STEPS; do
  for f in $(ls ${s}*.inp 2>/dev/null); do run_one "$f"; done
done
tar -czf "results_$(date +%Y%m%d_%H%M).tar.gz" jobs progress.log T1_geom_*.xyz 2>/dev/null
echo "[$(date '+%F %T')] 全部结束，结果已打包" | tee -a "$BASE/progress.log"
