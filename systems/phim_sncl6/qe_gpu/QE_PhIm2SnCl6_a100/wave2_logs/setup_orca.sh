#!/bin/bash
# Unpack ORCA 6.1.1 (shared, built against OpenMPI 4.1.8) and provide a working MPI.
# Order: cached OpenMPI 4.1.8 in Drive -> Ubuntu apt OpenMPI 4.1.x (tested with a 2-process water job) -> build 4.1.8 and cache it.
# Writes /content/orca_env.sh (source it before running ORCA).
set -o pipefail
D=/content/drive/MyDrive
ORCA=/content/orca
OMPI_CACHE=$D/QE_build/openmpi-4.1.8.tgz
log () { echo "[orca-setup $(date +%H:%M:%S)] $*"; }
if [ ! -f $ORCA/orca ]; then
  log "unpacking ORCA"; mkdir -p $ORCA
  tar -xJf $D/orca_6_1_1_linux_x86-64_shared_openmpi418.tar.xz -C $ORCA --strip-components=1
fi
chmod +x $ORCA/orca* 2>/dev/null
write_env () {  # $1 = MPI prefix ("" for system)
  { echo "export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1"
    echo "export OMPI_MCA_btl_vader_single_copy_mechanism=none OMPI_MCA_rmaps_base_oversubscribe=1 OMPI_MCA_btl=^openib"
    if [ -n "$1" ]; then echo "export PATH=$ORCA:$1/bin:\$PATH LD_LIBRARY_PATH=$ORCA:$ORCA/lib:$1/lib:\${LD_LIBRARY_PATH}"
    else echo "export PATH=$ORCA:\$PATH LD_LIBRARY_PATH=$ORCA:$ORCA/lib:\${LD_LIBRARY_PATH}"; fi
    echo "export ORCA=$ORCA"; } > /content/orca_env.sh; }
test_orca () {
  source /content/orca_env.sh; rm -rf /content/orca_test; mkdir -p /content/orca_test; cd /content/orca_test
  printf '! BP86 def2-SVP\n%%pal nprocs 2 end\n* xyz 0 1\nO 0 0 0\nH 0 0.76 0.59\nH 0 -0.76 0.59\n*\n' > w.inp
  timeout 300 $ORCA/orca w.inp > w.out 2>&1
  grep -q "ORCA TERMINATED NORMALLY" w.out && { log "ORCA parallel test OK ($(mpirun --version | head -1))"; cd /content; return 0; }
  log "ORCA parallel test FAILED:"; tail -5 w.out; cd /content; return 1; }

if [ -f "$OMPI_CACHE" ]; then
  log "OpenMPI 4.1.8 from Drive cache"; tar xzf "$OMPI_CACHE" -C /content; write_env /content/openmpi
  test_orca && exit 0
fi
log "trying system OpenMPI (apt)"
apt-get install -y -qq openmpi-bin libopenmpi-dev > /dev/null 2>&1
write_env ""
test_orca && exit 0
log "building OpenMPI 4.1.8 (~10 min)"
cd /content && curl -fsSL -o ompi.tar.bz2 https://download.open-mpi.org/release/open-mpi/v4.1/openmpi-4.1.8.tar.bz2
tar xjf ompi.tar.bz2 && cd openmpi-4.1.8
./configure --prefix=/content/openmpi --disable-mpi-fortran --enable-mpi1-compatibility > /content/ompi_configure.log 2>&1
make -j"$(nproc)" > /content/ompi_make.log 2>&1 && make install > /dev/null 2>&1
cd /content && tar czf "$OMPI_CACHE" openmpi
write_env /content/openmpi
test_orca || { log "MPI still failing -> ORCA will run serially"; echo "export ORCA_SERIAL=1" >> /content/orca_env.sh; }
