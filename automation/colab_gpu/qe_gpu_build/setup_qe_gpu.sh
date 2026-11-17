#!/usr/bin/env bash
# =============================================================================
# setup_qe_gpu.sh —— 在 Colab（A100）上准备 GPU 版 Quantum ESPRESSO
#
# 做法：从 NVIDIA NGC 官方镜像 nvcr.io/hpc/quantum_espresso 里取出编译好的
# GPU 版 pw.x，不需要自己编译。Colab 里没有 docker，所以用 skopeo 下载镜像各层，
# 解压成一个完整的小系统（/content/qe_root），再用 chroot 进去运行。
#
# 为什么用 chroot：直接用镜像自带的 ld.so 在宿主机上运行 pw.x 会报
# "stack smashing detected"（镜像里的 glibc 和宿主机混用）。chroot 后程序只看到
# 镜像自己的系统库，只需要把宿主机的显卡驱动库复制进去即可。
#
# 用法：bash setup_qe_gpu.sh [镜像标签，默认 qe-7.3.1]
# 完成后：在任意目录下 qe pw.x -in xxx.in > xxx.out
# =============================================================================
set -euo pipefail
TAG="${1:-qe-7.3.1}"
IMG=/content/qe_img
ROOT=/content/qe_root

if [[ ! -x /usr/local/bin/qe ]]; then
  echo "[1/5] 安装 skopeo（镜像下载工具）"
  apt-get -qq update >/dev/null && apt-get -qq install -y skopeo rsync >/dev/null

  echo "[2/5] 下载 NGC 镜像 nvcr.io/hpc/quantum_espresso:${TAG}（约 1~3 分钟）"
  rm -rf "$IMG" && skopeo copy --quiet "docker://nvcr.io/hpc/quantum_espresso:${TAG}" "dir:${IMG}"

  echo "[3/5] 解压镜像各层"
  rm -rf "$ROOT" && mkdir -p "$ROOT"
  for d in $(python3 -c "import json;print(' '.join(l['digest'].split(':')[1] for l in json.load(open('${IMG}/manifest.json'))['layers']))"); do
    tar -xf "${IMG}/${d}" -C "$ROOT" --exclude='dev/*' 2>/dev/null || true
  done
  rm -rf "$IMG"   # 镜像压缩包已解压，删掉省空间

  echo "[4/5] 把宿主机显卡驱动库复制进镜像，并刷新库缓存"
  mkdir -p "$ROOT/usr/lib/x86_64-linux-gnu"
  cp -a /usr/lib64-nvidia/*.so* "$ROOT/usr/lib/x86_64-linux-gnu/"
  chroot "$ROOT" ldconfig
  cp /etc/resolv.conf "$ROOT/etc/resolv.conf" 2>/dev/null || true

  PW=$(find "$ROOT" -name pw.x -type f | head -1)
  BIN_IN_ROOT="$(dirname "${PW#$ROOT}")"

  cat > /usr/local/bin/qe <<EOF
#!/usr/bin/env bash
# 用法：qe pw.x [参数]（在当前目录运行，当前目录会挂进镜像里同名路径）
ROOT=${ROOT}
W="\$PWD"
for d in proc dev sys; do
  mountpoint -q "\$ROOT/\$d" || { mkdir -p "\$ROOT/\$d"; mount --bind "/\$d" "\$ROOT/\$d"; }
done
mkdir -p "\$ROOT\$W"
mountpoint -q "\$ROOT\$W" || mount --bind "\$W" "\$ROOT\$W"
prog="\$1"; shift
exec chroot "\$ROOT" /usr/bin/env -i \\
  HOME=/root PATH="${BIN_IN_ROOT}:/usr/local/bin:/usr/bin:/bin" \\
  LD_LIBRARY_PATH=/usr/local/cuda/lib:/usr/local/cuda/lib64:/usr/local/fftw/lib:/opt/nvidia/hpc_sdk/Linux_x86_64/24.7/compilers/lib \\
  OMP_NUM_THREADS=\${OMP_NUM_THREADS:-4} OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1 \\
  /bin/bash -c 'cd "\$0" && exec "\$@"' "\$W" "\$prog" "\$@"
EOF
  chmod +x /usr/local/bin/qe
  cp /usr/local/bin/qe /content/qe_wrapper_used.sh   # 留一份，随结果一起存档
  echo "    pw.x: $PW"
fi

echo "[5/5] 检查：显卡 + pw.x 是否启用 GPU"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
mkdir -p /content/qe_check && cd /content/qe_check
echo "" | timeout 60 qe pw.x > pw_check.out 2>&1 || true
if grep -q "GPU acceleration is ACTIVE" pw_check.out; then
  grep -m1 "Program PWSCF" pw_check.out
  echo "QE GPU 环境就绪：用法 qe pw.x -in xxx.in > xxx.out"
else
  echo "[错误] pw.x 没有报告 GPU 加速，输出如下："; head -40 pw_check.out; exit 1
fi
