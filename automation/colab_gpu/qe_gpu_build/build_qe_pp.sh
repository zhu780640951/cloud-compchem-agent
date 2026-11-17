#!/usr/bin/env bash
# =============================================================================
# build_qe_pp.sh —— 在 CPU 上编译 QE 7.3.1 的后处理程序（projwfc.x、pp.x、dos.x、bands.x 等）
#
# 为什么要自己编：NGC 镜像里只有 pw.x。后处理程序必须和 pw.x 同版本、同样不带 HDF5，
# 才能读 pw.x 写出的 .dat 波函数（conda-forge 没有 7.3.1，7.6 又链接了 HDF5）。
# 编译约 10~15 分钟，可以在结构优化的同时后台进行。完成后写 /content/DONE_qe731。
#
# 已处理的坑（2026-10 实测）：
#   1. configure 会自动选中 Colab 里的 MKL 但找不到头文件 → 明确指定 OpenBLAS/FFTW3
#   2. 生成的 make.inc 里 DFLAGS 为空 → 改成 -D__FFTW3
#   3. IFLAGS 缺 FFTW3 头文件目录 → 补 -I/usr/include
# 用法：bash build_qe_pp.sh > /content/build_qe_pp.log 2>&1 &
# =============================================================================
set -euo pipefail
cd /content
rm -f /content/DONE_qe731 /content/FAIL_qe731
trap '[[ -f /content/DONE_qe731 ]] || touch /content/FAIL_qe731' EXIT

apt-get -qq update >/dev/null
apt-get -qq install -y gfortran libopenblas-dev libfftw3-dev >/dev/null

[[ -d q-e-qe-7.3.1 ]] || curl -sL https://gitlab.com/QEF/q-e/-/archive/qe-7.3.1/q-e-qe-7.3.1.tar.gz | tar xz
cd q-e-qe-7.3.1
./configure --disable-parallel --disable-openmp --with-hdf5=no --with-scalapack=no \
  BLAS_LIBS="-lopenblas" LAPACK_LIBS="-lopenblas" FFT_LIBS="-lfftw3" > configure.log 2>&1

python3 - <<'EOF'
import re
s = open("make.inc").read()
s = re.sub(r"^DFLAGS\s*=.*$", "DFLAGS         = -D__FFTW3", s, flags=re.M)
def fix(m):
    line = m.group(0)
    return line if "/usr/include" in line else line.rstrip() + " -I/usr/include"
s = re.sub(r"^IFLAGS\s*=.*$", fix, s, flags=re.M)
open("make.inc", "w").write(s)
EOF
grep -E "^(DFLAGS|IFLAGS|BLAS_LIBS|FFT_LIBS)" make.inc

make -j4 pp > make_pp.log 2>&1 || make -j1 pp >> make_pp.log 2>&1
ls bin/projwfc.x bin/pp.x
touch /content/DONE_qe731
echo "后处理程序编译完成：/content/q-e-qe-7.3.1/bin"
