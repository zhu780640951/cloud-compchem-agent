#!/usr/bin/env bash
# =============================================================================
# save_to_drive.sh —— 把计算目录同步到谷歌云盘（可反复调用，只传有变化的文件）
#
# 用法：bash save_to_drive.sh          # 中途同步（每算完一步调用一次，防止运行时意外断开）
#       bash save_to_drive.sh final    # 最后一次：另外写环境信息和文件清单
#
# 前提：笔记本里已运行过 from google.colab import drive; drive.mount('/content/drive')
# 保存位置：MyDrive/QE计算结果/<本次运行名>/
#   运行名第一次调用时确定（默认 snpim_年月日_时分），记在 .run_name 里，之后都写同一个文件夹。
#
# 不同步：tmp/、tmp_bands/（QE 工作目录，几十 GB 的中间文件）。
#         需要的波函数已由 run_after_relax.sh 打包成 wfc_*.tar，会一起同步。
# =============================================================================
set -uo pipefail
WORK="${WORK:-/content/qe-snpim}"
DRIVE_ROOT="${DRIVE_ROOT:-/content/drive/MyDrive}"
cd "$WORK" || exit 1
[[ -f .run_name ]] || echo "${RUN_NAME:-snpim_$(date +%Y%m%d_%H%M)}" > .run_name
DST="$DRIVE_ROOT/QE计算结果/$(cat .run_name)"

if [[ ! -d "$DRIVE_ROOT" ]]; then
  echo "[警告] 谷歌云盘没有挂载（$DRIVE_ROOT 不存在），本次只保存在运行时本地。"
  exit 0
fi
mkdir -p "$DST"

# 云盘剩余空间检查（挂载后 df 显示的是云盘配额）
need=$(du -sb --exclude=tmp --exclude=tmp_bands . | cut -f1)
free=$(df -B1 --output=avail "$DRIVE_ROOT" | tail -1 | tr -d ' ')
if [[ -n "$free" && "$free" -lt "$need" ]]; then
  echo "[警告] 云盘剩余 $((free/1024/1024)) MB，本目录约 $((need/1024/1024)) MB，可能放不下。"
fi

if [[ "${1:-}" == final ]]; then
  # 运行环境信息：以后复现或写论文方法部分用
  {
    echo "保存时间：$(date '+%F %T %Z')"
    echo "运行名：$(cat .run_name)"
    echo; echo "== 显卡 =="; nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv 2>/dev/null
    echo; echo "== QE 版本 =="; grep -h -m1 "Program PWSCF" 0*_*.out 2>/dev/null | sort -u
    echo; echo "== 并行/GPU 信息 =="; grep -h -m3 -E "GPU acceleration|MPI processes|threads/MPI" 02_scf.out 2>/dev/null
    echo; echo "== 赝势 =="; ls pseudo/ 2>/dev/null
    echo; echo "== 各步用时 =="; grep -H "PWSCF.*WALL" 0*_*.out 2>/dev/null
  } > ENV.txt
  [[ -f /content/qe_wrapper_used.sh ]] && cp /content/qe_wrapper_used.sh .
  # 文件清单（大小 + 校验和），确认下载完整用
  find . -path ./tmp -prune -o -path ./tmp_bands -prune -o -type f ! -name MANIFEST.txt -printf '%s\t%p\n' \
    | sort -k2 > MANIFEST.txt
fi

# 逐个复制新增或有变化的文件（不依赖 rsync；大文件只在变化时才重新上传）
n=0; rc=0
while IFS= read -r -d '' f; do
  d="$DST/${f#./}"
  if [[ ! -f "$d" || "$f" -nt "$d" || $(stat -c%s "$f") != $(stat -c%s "$d") ]]; then
    mkdir -p "$(dirname "$d")"
    cp --preserve=timestamps "$f" "$d" 2>/dev/null || cp "$f" "$d" || rc=1
    n=$((n+1))
  fi
done < <(find . \( -path ./tmp -o -path ./tmp_bands \) -prune -o -type f ! -name .run_name -print0)
echo "[$(date '+%H:%M:%S')] 已同步到 $DST：本次上传 $n 个，云盘里共 $(find "$DST" -type f | wc -l) 个文件，$(du -sh "$DST" | cut -f1)"
exit $rc
