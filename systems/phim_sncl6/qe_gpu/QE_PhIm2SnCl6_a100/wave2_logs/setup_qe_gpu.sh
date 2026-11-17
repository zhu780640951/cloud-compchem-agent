#!/bin/bash
# Build GPU (OpenACC/CUDA) Quantum ESPRESSO pw.x on Colab once, cache binary + runtime libs on Google Drive.
# Later sessions only copy the cache (no NVHPC install, no compile).
set -eo pipefail
QE_VER=7.5
CACHE=/content/drive/MyDrive/QE_build/qe-${QE_VER}-gpu-sm80
LOCAL=/content/qe
LOG=/content/drive/MyDrive/QE_build/build_log_$(date +%Y%m%d_%H%M%S).txt
mkdir -p /content/drive/MyDrive/QE_build

if [ -f "$CACHE/bin/pw.x" ] && [ -f "$CACHE/bin/projwfc.x" ] && [ -f "$CACHE/bin/pp.x" ]; then
  echo "[setup] cached GPU build found in Drive -> copying to $LOCAL"
  rm -rf "$LOCAL"; mkdir -p "$LOCAL"; cp -r "$CACHE/bin" "$CACHE/lib" "$LOCAL/"
  chmod +x "$LOCAL/bin/"*
  exit 0
fi

exec > >(tee -a "$LOG") 2>&1
echo "[setup] no cache; building QE $QE_VER GPU. log: $LOG"
nvidia-smi
DRV_CUDA=$(nvidia-smi | grep -oP 'CUDA Version: \K[0-9]+\.[0-9]+')
echo "[setup] driver supports CUDA $DRV_CUDA"

# 1) NVIDIA HPC SDK from NVIDIA's apt repository
if [ ! -d /opt/nvidia/hpc_sdk ]; then
  curl -fsSL https://developer.download.nvidia.com/hpc-sdk/ubuntu/DEB-GPG-KEY-NVIDIA-HPC-SDK \
    | gpg --dearmor --yes -o /usr/share/keyrings/nvidia-hpcsdk-archive-keyring.gpg
  echo 'deb [signed-by=/usr/share/keyrings/nvidia-hpcsdk-archive-keyring.gpg] https://developer.download.nvidia.com/hpc-sdk/ubuntu/amd64 /' \
    > /etc/apt/sources.list.d/nvhpc.list
  apt-get update -qq
  PKG=nvhpc-25-7
  if ! apt-cache show $PKG >/dev/null 2>&1; then
    PKG=$(apt-cache search --names-only '^nvhpc-2[5-6]-[0-9]+$' | awk '{print $1}' | sort -V | head -1)
  fi
  echo "[setup] installing $PKG"
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $PKG
fi
NVHPC=$(ls -d /opt/nvidia/hpc_sdk/Linux_x86_64/2* | sort -V | tail -1)
export PATH=$NVHPC/compilers/bin:$PATH
# pick the newest bundled CUDA 12.x (runs on any CUDA-12 driver via minor-version compatibility)
CUDA_VER=$(ls $NVHPC/cuda | grep -E '^12\.[0-9]+$' | sort -V | tail -1)
echo "[setup] NVHPC=$NVHPC  bundled CUDA for build: $CUDA_VER"
nvfortran --version | head -2

# 2) QE source
cd /content
[ -f q-e-qe-$QE_VER.tar.gz ] || curl -fsSL -o q-e-qe-$QE_VER.tar.gz https://gitlab.com/QEF/q-e/-/archive/qe-$QE_VER/q-e-qe-$QE_VER.tar.gz
rm -rf q-e-qe-$QE_VER && tar xzf q-e-qe-$QE_VER.tar.gz
cd q-e-qe-$QE_VER && mkdir -p build && cd build
pip -q install "cmake>=3.21" >/dev/null 2>&1 || true
hash -r

# FFTW3 for the CPU-side FFTs (the GPU uses cuFFT)
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libfftw3-dev >/dev/null

# 3) configure: single GPU, no MPI (one rank per GPU anyway), OpenMP for the CPU side
cmake .. \
  -DCMAKE_Fortran_COMPILER=nvfortran -DCMAKE_C_COMPILER=nvc -DCMAKE_CXX_COMPILER=nvc++ \
  -DQE_ENABLE_CUDA=ON -DQE_ENABLE_OPENACC=ON -DQE_ENABLE_OPENMP=ON -DQE_ENABLE_MPI=OFF \
  -DNVFORTRAN_CUDA_CC=80 -DNVFORTRAN_CUDA_VERSION=$CUDA_VER \
  -DBLAS_LIBRARIES=$NVHPC/compilers/lib/libblas.so -DLAPACK_LIBRARIES=$NVHPC/compilers/lib/liblapack.so \
  -DQE_FFTW_VENDOR=Internal -DQE_ENABLE_SCALAPACK=OFF -DQE_ENABLE_ELPA=OFF -DQE_ENABLE_LIBXC=OFF \
  -DQE_ENABLE_HDF5=OFF -DQE_ENABLE_PLUGINS="" -DCMAKE_BUILD_TYPE=Release

# 4) build pw.x and the post-processing tools (pp.x, projwfc.x, bands.x, dos.x)
make -j$(nproc) pw pp
ls -la bin/pw.x bin/pp.x bin/projwfc.x bin/bands.x

# 5) cache binary + every NVHPC/CUDA shared library it needs
mkdir -p "$CACHE/bin" "$CACHE/lib"
cp bin/pw.x bin/pp.x bin/projwfc.x bin/bands.x bin/dos.x "$CACHE/bin/"
ldd bin/pw.x bin/pp.x bin/projwfc.x bin/bands.x | awk '/=> \/opt\/nvidia/ {print $3}' | sort -u | while read L; do cp -L "$L" "$CACHE/lib/"; done
echo "QE $QE_VER GPU sm_80, NVHPC $(basename $NVHPC), CUDA $CUDA_VER, built $(date)" > "$CACHE/BUILD_INFO.txt"
du -sh "$CACHE"
rm -rf "$LOCAL"; mkdir -p "$LOCAL"; cp -r "$CACHE/bin" "$CACHE/lib" "$LOCAL/"
chmod +x "$LOCAL/bin/"*   # Drive does not keep the executable bit
echo "[setup] done"
