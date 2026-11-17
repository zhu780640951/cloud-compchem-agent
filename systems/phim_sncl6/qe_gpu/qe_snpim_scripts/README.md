# Colab A100 上用 Quantum ESPRESSO 算晶体（2-苯基咪唑 SnCl6 体系模板）

## 笔记本里依次运行的单元格

```python
# 1. 挂载谷歌云盘（会弹出授权）
from google.colab import drive
drive.mount('/content/drive')
```

```bash
%%bash
# 2. 把脚本和输入从云盘拷到运行时（脚本包放在 MyDrive/QE计算结果/脚本/ 下）
mkdir -p /content/qe-snpim && cd /content/qe-snpim
unzip -oq "/content/drive/MyDrive/QE计算结果/脚本/qe-snpim-scripts.zip" -d /content/qe-snpim
# 换体系时：替换 crystal.cif / structure.qe / 01_relax.in，并把 pseudo/ 里的赝势备好
bash setup_qe_gpu.sh            # 约 3~5 分钟；最后应显示 "QE GPU 环境就绪"
```

```bash
%%bash
# 3. 后台跑完整流程（关掉浏览器也会继续，直到运行时被回收）
cd /content/qe-snpim
RUN_NAME=snpim_$(date +%Y%m%d) SAVE_WFC=scf nohup bash run_all.sh > run_all.log 2>&1 &
```

```bash
%%bash
# 4. 随时查看进度
cd /content/qe-snpim; ls DONE_* FAIL_* 2>/dev/null; tail -5 run_all.log; tail -2 save_to_drive.log
```

```python
# 5. 看到 DONE_all 后：把云盘缓存全部写完再断开。
#    先在网页版云盘里确认文件都在，再删除运行时。
from google.colab import drive
drive.flush_and_unmount()
```

## 云盘里会得到什么（MyDrive/QE计算结果/<运行名>/）

| 内容 | 文件 |
| --- | --- |
| 全部输入、输出 | `01_relax` ～ `06_pp_*` 的 `.in` / `.out` |
| 结构 | `relaxed_structure.cif/.xyz`；`relax_trajectory.extxyz`（优化轨迹） |
| 能带、态密度 | `fig_bands_pdos.png`、`bands_vbm0.csv`、`pdos_elements.csv`、`pdos/`（逐原子逐轨道） |
| 电荷分布（VESTA 打开） | `cube/rho_total.cube`（总电荷密度）<br>`cube/vbm_ildos.cube`（价带顶 0.3 eV 内）<br>`cube/cbm_ildos.cube`（导带底 0.3 eV 内） |
| 波函数快照 | `wfc_scf.tar`（自洽结果，约 1~2 GB）。解压到 `tmp/` 即可直接跑 pp.x、nscf、bands 等后续计算，不必重做优化和自洽 |
| 复现信息 | `ENV.txt`（显卡、QE 版本、赝势、用时）、`qe_wrapper_used.sh`、全部脚本、`MANIFEST.txt`（文件清单和大小） |

每算完一步就同步一次，所以运行时中途断开时，已完成的部分也都在云盘里。

## 注意

- 文件夹放到 Windows 本地时用纯英文路径，比如 `E:\qe\...`。GaussView 等老软件读不了中文路径。
- `.out` 是 QE 的文本输出，用记事本或 VS Code 打开，不要用 GaussView。
- 云盘空间紧张时设 `SAVE_WFC=none`；想同时保留非自洽波函数，用 `SAVE_WFC=all`（再加约 2~3 GB）。
