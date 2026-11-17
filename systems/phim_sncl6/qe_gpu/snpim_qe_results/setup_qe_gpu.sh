#!/usr/bin/env bash
# =============================================================================
# setup_qe_gpu.sh —— 在 Colab（A100）上准备 GPU 版 Quantum ESPRESSO
#
# 做法：从 NVIDIA NGC 官方镜像 nvcr.io/hpc/quantum_espresso 里取出编译好的
# GPU 版 pw.x 等程序，不需要自己编译。Colab 里没有 docker，所以用 skopeo
# 把镜像各层下载下来解压，再用镜像自带的动态链接器运行程序。
#
# 用法：bash setup_qe_gpu.sh [镜像标签，默认 qe-7.3.1]
# 完成后可直接用：qe pw.x -in xxx.in > xxx.out
# =============================================================================
set -euo pipefail
TAG="${1:-qe-7.3.1}"
IMG=/content/qe_img
ROOT=/content/qe_root

if [[ ! -x /usr/local/bin/qe ]]; then
  echo "[1/4] 安装 skopeo（镜像下载工具）"
  apt-get -qq update >/dev/null && apt-get -qq install -y skopeo >/dev/null

  echo "[2/4] 下载 NGC 镜像 nvcr.io/hpc/quantum_espresso:${TAG}（约 1~3 分钟）"
  rm -rf "$IMG" && skopeo copy --quiet "docker://nvcr.io/hpc/quantum_espresso:${TAG}" "dir:${IMG}"

  echo "[3/4] 解压镜像各层"
  rm -rf "$ROOT" && mkdir -p "$ROOT"
  for d in $(python3 -c "import json;print(' '.join(l['digest'].split(':')[1] for l in json.load(open('${IMG}/manifest.json'))['layers']))"); do
    tar -xf "${IMG}/${d}" -C "$ROOT" --exclude='dev/*' 2>/dev/null || true
  done

  PW=$(find "$ROOT" -name pw.x -type f | head -1)
  BIN=$(dirname "$PW")
  LDSO=$(ls "$ROOT"/lib64/ld-linux-x86-64.so.2 "$ROOT"/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 2>/dev/null | head -1)
  # 镜像里所有库目录（去掉 stubs/compat，避免顶替宿主机真正的显卡驱动）
  LIBS=$(find "$ROOT" \( -name '*.so' -o -name '*.so.*' \) -printf '%h\n' | sort -u | grep -vE 'stubs|compat' | tr '\n' ':')

  cat > /usr/local/bin/qe <<EOF
#!/usr/bin/env bash
# 用法：qe pw.x [参数]  /  qe projwfc.x [参数]  /  qe dos.x [参数]
prog="\$1"; shift
export OMP_NUM_THREADS=\${OMP_NUM_THREADS:-4}
export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
exec "${LDSO}" --library-path "/usr/lib64-nvidia:${LIBS}" "${BIN}/\${prog}" "\$@"
EOF
  chmod +x /usr/local/bin/qe
  echo "    pw.x: $PW"
fi

echo "[4/4] 检查"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
ls "$(dirname "$(find "$ROOT" -name pw.x -type f | head -1)")" | grep -E '^(pw|projwfc|dos|bands|pp)\.x$' | tr '\n' ' '; echo
echo "QE GPU 环境就绪：用法 qe pw.x -in xxx.in > xxx.out"
