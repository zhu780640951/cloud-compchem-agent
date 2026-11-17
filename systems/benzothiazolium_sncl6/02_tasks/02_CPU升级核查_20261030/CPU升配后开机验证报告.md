# CPU 升配后开机验证

- 时间（UTC）：2026-10-30T12:10:17.199181+00:00
- 云端实例：orca-cpu-16，us-central1-a，状态 RUNNING
- 配置机型：n2-custom-12-196608-ext（12 vCPU / 192 GiB）。
- SSH 实测：12 个逻辑 CPU；系统总内存 188.706 GiB；采样时可用内存 186.732 GiB。
- 根文件系统空闲：68.263 GiB。
- ORCA 输出版本：6.1.1；OpenMPI 路径 /opt/openmpi-4.1.8/bin/mpirun。
- H2 / HF / def2-SVP / TightSCF：1 核和 2 核均正常终止，退出码均为 0。
- 两次能量一致：-1.128893619388 Eh。
- 验证范围：扩容后的 SSH 访问、系统内存识别、ORCA 串行/双核执行。未提交晶体正式计算。
- 当前保持开机；本次没有自动停机。
- 远端测试目录：/home/y/codex_calculations/benzothiazolium_sncl6/connection_test_20261030_120648
- 详细状态与原始回传路径：CPU升配后开机验证.json、CPU升配后SSH验证.log、cpu_postboot_remote_files。
