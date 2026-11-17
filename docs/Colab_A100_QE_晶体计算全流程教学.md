# Colab A100 + Quantum ESPRESSO 晶体计算全流程教学

Oct 22, 2026 · @zxysj

## 一、项目总览

这个项目用 Google Colab 的 A100 云显卡和开源软件 Quantum ESPRESSO（QE）7.3.1，对 2-苯基咪唑锡氯杂化晶体做了第一性原理计算，包括结构优化、能带和投影态密度三部分。结果是 PBE-D3(BJ) 带隙 2.19 eV，与你之前在 PWmat 上算的 2.211 eV 只差 0.02 eV。价带顶来自有机阳离子，导带底来自 \[SnCl₆\]²⁻。

| 项目要素 | 内容 |
| --- | --- |
| 研究对象 | (C₉H₉N₂)₂\[SnCl₆\]·2H₂O，即 2-苯基咪唑鎓六氯合锡酸盐二水合物 |
| 晶体信息 | 三斜晶系 P-1，Z = 2；a = 7.694 Å，b = 10.945 Å，c = 15.498 Å；α = 86.70°，β = 80.22°，γ = 82.51°；V = 1274.4 Å³；283 K 单晶衍射 |
| 晶胞原子数 | 106 个：Sn 2、Cl 12、O 4、N 8、C 36、H 44 |
| 价电子数 | 364 个，对应 182 条占据能带 |
| 计算方法 | DFT，PBE 泛函加 DFT-D3(BJ) 色散校正；平面波基组；超软赝势（pslibrary 1.0.0） |
| 计算软件 | Quantum ESPRESSO 7.3.1。pw.x 用 NVIDIA 官方 GPU 版；projwfc.x 是在 CPU 上自行编译的 |
| 计算平台 | Google Colab Pro，NVIDIA A100 显卡 |
| 计算步骤 | 结构优化 → 自洽 → 能带 → 非自洽 → 投影态密度 |
| 总耗时 | GPU 计算约 45 分钟（优化 31.4 分钟 + 其余约 14 分钟），环境搭建和编译另计 |
| 结果存放 | 谷歌云盘 MyDrive/QE计算结果/2-苯基咪唑SnCl6/ |

**阅读路线：**

- 只想知道算出了什么：直接看第七节（结果）和第八节（文件）。
- 想学会自己跑：按顺序读第二、三、五、六、十节。
- 想理解原理：第四节是 DFT 和 QE 的入门讲解，第五节逐行解释输入文件里每个参数的物理意义。
- 遇到不认识的词：查第十一节的速查表。

## 二、云平台 Colab 是什么

Colab 可以理解为一台临时借给你的 Linux 服务器，带一块显卡。你在浏览器里写单元格，代码实际在谷歌机房的这台虚拟机上运行。它用完就收回，硬盘上的东西也会被清空。

### 2.1 账号、计算单元和显卡

付费版 Colab 按"计算单元"（Compute Unit，CU）计费：虚拟机开着就持续扣单元，显卡越好扣得越快。注意是按开机时间扣，不是按算了多少扣。下表是 2026 年 10 月实际观察到的情况，价格和配额谷歌会调整，以 Colab 页面显示为准。

| 项目 | 实测情况 |
| --- | --- |
| 你的两个账号 | isolate 账号没有付费权益；zx 账号有 Colab Pro，当时余额约 191 个单元 |
| Google AI Pro 订阅 | 含 Colab 权益（每月 200 个单元），但只在部分地区生效，这就是 isolate 账号没有的原因 |
| A100 耗电 | 约 5.3 单元/小时，这次开机约 1.5～2 小时，估计用了 8～10 个单元 |
| 可选显卡 | T4（16 GB 显存，最便宜）、L4（24 GB）、A100（最快）；显卡紧张时可能分配不到 A100 |

**显卡在这次计算里做什么？** DFT 计算最耗时的是大量的快速傅里叶变换（FFT）和矩阵对角化。GPU 有几千个计算核心，特别擅长这类可以并行的数学运算。GPU 版 pw.x 把波函数放在显存里，这些运算都交给显卡做，CPU 只负责调度和读写文件。106 个原子的体系里，每个 k 点上有约 5 万个平面波和 200 条能带，在 A100 上一次完整的自洽计算只要 1 分钟多。

### 2.2 运行时的生命周期

1. **连接：** 点"连接"或更改运行时类型时，谷歌分配一台虚拟机，开始扣单元。
2. **使用：** 虚拟机里是 Ubuntu 系统，你是 root 用户，可以用 `apt-get` 和 `pip` 装软件。显卡驱动已经装好，在 `/usr/lib64-nvidia`。工作目录是 `/content`。
3. **断开：** 长时间没有操作、超过最长运行时间，或者你手动"断开并删除运行时"，虚拟机就会被回收。
4. **清空：** 虚拟机回收后 `/content` 里的一切都会消失，包括装好的软件和算出的结果。下次连接是一台全新的机器，环境要重新搭建。

这就引出两条工作原则：

- **环境搭建必须要脚本化。** 每次开机都从零开始，所以把安装步骤写成脚本，一条命令重建。本项目的 `setup_qe_gpu.sh` 和 `build_qe_pp.sh` 就是干这个的。
- **结果必须及时搬走。** 把谷歌云盘挂载到 `/content/drive`，结果写进去就是永久保存。但要注意，云盘是通过网络同步的，最后要运行 `drive.flush_and_unmount()` 确保写完。

### 2.3 需要知道的限制

| 限制 | 影响 | 本项目的应对 |
| --- | --- | --- |
| 没有 Docker | 不能直接运行 NVIDIA 官方的 QE 容器 | 用 skopeo 下载镜像、解压，再用 chroot 运行（第三节） |
| 单块显卡 | 没法多卡并行 | 106 原子的体系单卡足够 |
| 浏览器关闭后可能断开 | 长计算可能中断 | 用 `nohup` 后台运行，并保持网页打开；结构优化设了 3.5 小时自动安全退出，可续算 |
| 预装软件版本会变 | 比如 Colab 预装的是 CUDA 13 版 CuPy，在 T4 上不兼容 | 脚本里明确指定版本 |
| 云盘空间 | 波函数文件动辄几 GB，免费云盘只有 15 GB | 只存自洽波函数快照，可关闭 |

### 2.4 和其它平台比

| 平台 | 优点 | 缺点 |
| --- | --- | --- |
| Colab | A100 起价低，开箱即用，按需付费 | 环境每次重建，运行时长有限，需要自己管理数据 |
| PWmat / PWStudio | 图形界面，平台代管环境 | 商业软件，按机时收费，参数自由度和可复现性不如开源软件 |
| 学校或课题组服务器 | 持久环境，可长时间跑 | 通常只有 CPU，需要排队 |
| 自己电脑 WSL2 | 免费，适合学习和小体系 | 算 100 多个原子的体系很慢 |

## 三、我在云平台上具体做了什么

整个过程分两块。一块在我自己的工作区：准备结构和输入文件、写脚本。另一块是通过你的 Chrome 操作 Colab 网页：搭环境、跑计算、存结果。花时间最多的是搭环境，因为 Colab 上没有现成可用的 GPU 版 QE。

&#91;embedded content: 本项目的运行环境 · 各组件与数据流向\]

浅色底的大框就是那台临时虚拟机：里面的东西全是当场下载、当场搭建的，只有往右下角云盘同步的那一份会留下来。

### 3.1 怎么操作你的 Colab

- 我通过 Chrome 浏览器扩展控制你已经登录的 Colab 标签页：在单元格里写代码、点运行、读输出，和你手动操作一样。
- 涉及授权的步骤由你完成，比如选择 zx 账号、挂载谷歌云盘时的登录确认。
- 耗时长的任务都用 `nohup … &` 放在后台跑，输出写进日志文件。我隔一段时间用 `tail` 和 `grep` 查看进度，不用一直占着单元格。
- 每一步结束时写一个标记文件，成功写 `DONE_步骤名`，失败写 `FAIL_步骤名`。只要看有哪些标记文件，就知道流程走到了哪里。

### 3.2 第一件事：拿到 GPU 版 pw.x

QE 的核心程序 pw.x 要在 GPU 上跑，必须用 NVIDIA 的 HPC SDK 编译，自己编译要半小时以上，且容易出错。NVIDIA 在它的 NGC 镜像库里提供了编译好的容器 `nvcr.io/hpc/quantum_espresso:qe-7.3.1`，这是当时的最新标签。问题是 Colab 没有 Docker，所以分三步绕过去：

1. **下载镜像。** 用 `skopeo` 把镜像的各层压缩包下载到 `/content/qe_img`。skopeo 是不需要 Docker 就能搬运容器镜像的工具。
2. **解压成一个小系统。** 把各层依次解压到 `/content/qe_root`，得到一个完整的 Linux 目录树，包含镜像自带的系统库、CUDA 运行库、FFTW 和 pw.x。
3. **chroot 进去运行。** chroot 的作用是让一个程序把 `/content/qe_root` 当成自己的根目录 `/`，这样它只会看到镜像自己的库，不会和 Colab 系统的库混在一起。

为什么非要 chroot？我最初的做法是用镜像里的动态链接器直接在 Colab 系统上启动 pw.x，结果报 `stack smashing detected`（栈溢出保护触发）。原因是两套不同版本的 glibc 被混用了，chroot 之后问题就消失了。chroot 后还要做三件事：

- **显卡驱动库复制进去。** 镜像里没有显卡驱动，驱动必须和宿主机的内核模块版本一致。把 `/usr/lib64-nvidia` 里的 `libcuda.so` 等文件复制到镜像的 `/usr/lib/x86_64-linux-gnu`，再运行 `ldconfig` 刷新库缓存。
- **系统目录挂进去。** 把 `/proc`、`/sys` 和 `/dev` 绑定挂载进镜像。其中 `/dev` 里有 `/dev/nvidia0` 这类显卡设备文件，没有它们程序就看不到 GPU。
- **工作目录挂进去。** 把 `/content/qe-snpim` 挂到镜像里的同名路径，这样镜像里的 pw.x 就能读写你的输入和输出。

这些操作被封装成一个叫 `qe` 的小命令。之后只要写 `qe pw.x -in 01_relax.in > 01_relax.out`，就是在 GPU 上跑 QE。镜像内的库搜索路径为 `/usr/local/cuda/lib:/usr/local/cuda/lib64:/usr/local/fftw/lib:/opt/nvidia/hpc_sdk/Linux_x86_64/24.7/compilers/lib`，可以看出它用的是 NVIDIA HPC SDK 24.7 编译器。

### 3.3 第二件事：在 CPU 上编译后处理程序

NGC 镜像里只有 pw.x，没有算投影态密度用的 projwfc.x。后处理程序要读 pw.x 写出的波函数文件，所以版本和文件格式都必须一致。conda-forge 上没有 7.3.1 版；它的 7.6 版链接了 HDF5，而 NGC 的 pw.x 写的是不带 HDF5 的 `.dat` 格式，两者读写格式不同。最后的办法是从 GitLab 下载 QE 7.3.1 源码，用 gfortran、OpenBLAS 和 FFTW3 在 CPU 上编译，不带 HDF5。

编译约 10～15 分钟，和 GPU 上的结构优化同时进行，不占用总时间。后处理只是做投影和积分，计算量小，用 CPU 跑完全够。

### 3.4 踩过的坑

| 问题 | 原因 | 解决 |
| --- | --- | --- |
| pw.x 报 stack smashing detected | 镜像的 glibc 和 Colab 系统的混用 | 改用 chroot 运行 |
| configure 选中了 MKL，但找不到头文件 | Colab 里有不完整的 MKL | 明确指定 OpenBLAS 和 FFTW3 |
| 编译出的 FFT 库不可用 | make.inc 里 DFLAGS 是空的 | 改成 `DFLAGS = -D__FFTW3` |
| 改配置后重编译仍然报错 | 旧的 .o 和 .mod 文件残留 | 删掉 FFTXlib 的旧目标文件，先单独编译 libfft，再编译 pp |
| PDOS 输出全是 0 | 非自洽计算用了四面体法（tetrahedra\_opt），projwfc.x 在这种组合下输出为零 | 改用高斯展宽（degauss = 0.005 Ry），重算非自洽和 PDOS |
| 画图脚本少读了最后一个 k 点 | 正则表达式的结尾判断不对 | 改成以空行作为每组本征值的结束 |
| 第一次挂载云盘失败 | 登录授权窗口超时 | 改用文件面板里的"装载 Google 云端硬盘"按钮，由你确认授权 |
| 结果压缩包没有下载到你的电脑 | Chrome 下载没有触发 | 结果已在云盘，从云盘下载 |
| 波函数没有保存就删除了运行时 | 打包时排除了 tmp/ 目录以控制体积，删除前我没有告诉你。这是我的疏忽 | 新脚本自动保存自洽波函数快照（第十节） |

顺带一提，在这之前我们用 T4 测试过分子计算程序 gpu4pyscf。它的 CUDA 13 版只支持 A100 及更新的显卡，在 T4 上会报 `failed in block_diag kernel`。解决办法是换成 CUDA 12 版，并强制重装 cupy-cuda12x。那是另一条路线（分子团簇的激发态计算），详见之前的文档《Colab 云显卡计算化学入门流程》。

## 四、DFT 与 QE 的计算原理

QE 做的事情可以概括成一句话：给定原子位置，用密度泛函理论（DFT）算出晶体中电子的基态。得到基态之后，总能量、原子受力、能带和态密度都能从中导出来。下面按计算中真正用到的顺序来讲。

### 4.1 从薛定谔方程到 Kohn-Sham 方程

晶胞里有 364 个价电子，直接解多电子薛定谔方程是不可能的。第一步是玻恩-奥本海默近似：原子核比电子重得多，可以把核的位置当成固定参数，只解电子部分。

Hohenberg-Kohn 定理说明，基态的一切性质都由电子密度 n(r) 唯一决定。这把未知量从 3N 维的波函数变成了 3 维的密度。Kohn 和 Sham 又把问题换成"一组不相互作用的电子在一个有效势中运动"，这就是 DFT 实际求解的 Kohn-Sham 方程：

```latex
\left[-\frac{\hbar^2}{2m}\nabla^2 + V_{\mathrm{ext}}(\mathbf r) + V_{\mathrm H}[n](\mathbf r) + V_{\mathrm{xc}}[n](\mathbf r)\right]\psi_i(\mathbf r) = \varepsilon_i\,\psi_i(\mathbf r),\qquad n(\mathbf r) = \sum_i f_i\,|\psi_i(\mathbf r)|^2
```

- V\_ext：原子核（实际是赝势）对电子的吸引。
- V\_H：Hartree 势，即电子云本身的经典库仑排斥。
- V\_xc：交换关联势，把所有量子多体效应都塞进这一项。它的精确形式未知，只能近似，也就是"泛函"。
- f\_i：占据数。绝缘体里占据态 f = 2（自旋上下各一个），空态 f = 0。你的体系有 364 个价电子，所以前 182 条带是占据的。

注意 V\_H 和 V\_xc 都依赖于 n，而 n 又由 ψ 算出，所以方程必须迭代求解，这就是"自洽"（4.6 节）。

### 4.2 泛函：PBE，以及它为什么低估带隙

本项目用 PBE，属于广义梯度近似（GGA）。它的 V\_xc 只依赖于当地的密度 n 和密度梯度 ∇n，计算便宜，结构和能量都比较可靠。

PBE 有一个已知的系统性问题：Kohn-Sham 带隙偏小，常见低估 30%～50%。原因是自相互作用误差：电子会感受到自己对自己的排斥，占据态被推高，带隙就被压缩。所以本项目的 2.19 eV 应当理解为实验光学带隙的下限。能带的形状和带边由哪些原子贡献，这些结论一般是可靠的。想要更准的带隙，可以换成 HSE06 杂化泛函（第九节）。

### 4.3 色散校正：DFT-D3(BJ)

PBE 几乎描述不了范德华力，而你的晶体靠氢键、π-π 堆积和阳离子与阴离子之间的色散作用堆积在一起。不加校正，结构优化会把分子推开。Grimme 的 D3 方法在 DFT 能量上加一个原子对经验项：

```latex
E_{\mathrm{tot}} = E_{\mathrm{PBE}} + E_{\mathrm{disp}},\qquad E_{\mathrm{disp}} = -\sum_{A<B}\sum_{n=6,8} s_n\,\frac{C_n^{AB}}{r_{AB}^{\,n} + \left(a_1 R_0^{AB} + a_2\right)^{n}}
```

C₆ 和 C₈ 是色散系数，r\_AB 是两个原子的距离。分母里的 (a₁R₀ + a₂) 就是 Becke-Johnson（BJ）阻尼：原子靠得很近时，它让这一项趋于常数，不会发散。QE 里对应的参数是 `vdw_corr = 'dft-d3'` 和 `dftd3_version = 4`，其中 4 表示 BJ 阻尼。

### 4.4 周期性、布洛赫定理与 k 点

晶体是周期性的。布洛赫定理告诉我们，电子波函数可以写成平面波乘以一个周期函数：

```latex
\psi_{n\mathbf k}(\mathbf r) = e^{i\mathbf k\cdot\mathbf r}\,u_{n\mathbf k}(\mathbf r),\qquad u_{n\mathbf k}(\mathbf r+\mathbf R) = u_{n\mathbf k}(\mathbf r)
```

波矢 k 只需要取在第一布里渊区内。n 是能带编号，ε\_n(k) 随 k 变化的曲线就是能带。计算总能量和电子密度时，要对整个布里渊区积分，实际做法是取一个均匀的 k 点网格来近似，即 Monkhorst-Pack 网格。

k 网格的疏密和实空间晶胞大小成反比。你的晶胞三个边分别是 7.7、10.9 和 15.5 Å，倒格子很小；又是绝缘体，能带很平。所以自洽计算用 2×2×2 就够了，态密度用更密的 4×3×2，按各边长度的反比分配。晶体有反演对称，再加上时间反演对称，k 和 −k 是等价的，4×3×2 = 24 个点最后只需算 14 个。

### 4.5 平面波基组、截断能与赝势

周期函数 u 可以展开成傅里叶级数，展开的每一项就是一个"平面波"：

```latex
\psi_{n\mathbf k}(\mathbf r) = \sum_{\mathbf G} c_{n,\mathbf k+\mathbf G}\; e^{i(\mathbf k+\mathbf G)\cdot\mathbf r},\qquad \frac{\hbar^2}{2m}\,|\mathbf k+\mathbf G|^2 \le E_{\mathrm{cut}}
```

G 是倒格子矢量。展开不可能取无穷多项，所以只保留动能低于截断能 E\_cut 的项。E\_cut 越大越准，也越贵。本项目取 `ecutwfc = 50 Ry`（1 Ry = 13.606 eV），每个 k 点约 51 300 个平面波（输出里写着 51303 PWs）。

靠近原子核的内层电子波函数振荡得很剧烈，用平面波描述需要极高的截断能。赝势的做法是把原子核和内层电子合并成一个平滑的有效势，只显式处理参与成键的价电子。本项目用的是 pslibrary 1.0.0 的超软赝势（rrkjus），价电子数如下：

| 元素 | 赝势文件 | 价电子组态 | 每原子价电子 | 晶胞内原子数 | 小计 |
| --- | --- | --- | --- | --- | --- |
| Sn | Sn.pbe-dn-rrkjus\_psl.1.0.0.UPF | 4d¹⁰ 5s² 5p² | 14 | 2 | 28 |
| Cl | Cl.pbe-n-rrkjus\_psl.1.0.0.UPF | 3s² 3p⁵ | 7 | 12 | 84 |
| O | O.pbe-n-rrkjus\_psl.1.0.0.UPF | 2s² 2p⁴ | 6 | 4 | 24 |
| N | N.pbe-n-rrkjus\_psl.1.0.0.UPF | 2s² 2p³ | 5 | 8 | 40 |
| C | C.pbe-n-rrkjus\_psl.1.0.0.UPF | 2s² 2p² | 4 | 36 | 144 |
| H | H.pbe-rrkjus\_psl.1.0.0.UPF | 1s¹ | 1 | 44 | 44 |
| 合计 |  |  |  | 106 | 364 |

超软赝势允许用较低的 ecutwfc，代价是电荷密度需要更高的截断能，一般取 8～12 倍，本项目取 `ecutrho = 400 Ry`。Sn 把 4d 也当作价电子处理（文件名里的 dn），计算更准。

### 4.6 自洽场迭代（SCF）

&#91;embedded content: 自洽迭代与结构优化的两层循环\]

每一轮迭代里：先从当前密度构造有效势，再对角化求出新的波函数和新密度，然后把新旧密度按比例混合（`mixing_beta = 0.4`），这样可以防止振荡。输入和输出密度之差小于 `conv_thr`（本项目取 10⁻⁸ Ry）时，就认为收敛了。输出文件里以 `!` 开头的 total energy 就是收敛后的总能。对角化和 FFT 占了绝大部分计算量，这部分就是交给 GPU 做的。

### 4.7 受力与结构优化（BFGS）

收敛后，每个原子受的力由 Hellmann-Feynman 定理直接给出，就是能量对原子坐标的负导数：

```latex
\mathbf F_I = -\frac{\partial E_{\mathrm{tot}}}{\partial \mathbf R_I}
```

BFGS 是一种拟牛顿法。它根据受力和历史步估计能量曲面的曲率（Hessian 矩阵），然后把原子往能量降低的方向挪动。每挪一步，就重新做一次自洽。本项目的收敛标准是：

- 所有受力分量小于 `forc_conv_thr = 1×10⁻³ Ry/Bohr`，约等于 0.026 eV/Å。
- 两步之间的能量变化小于 `etot_conv_thr = 1×10⁻⁴ Ry`。

晶胞参数固定为实验值（`calculation = 'relax'`，而不是 'vc-relax'），只优化原子位置。这是分子晶体的常见做法：实验晶胞已经很准，而开放晶胞会受色散校正误差和截断能引起的人为应力（Pulay stress）影响。

### 4.8 自洽、非自洽与能带三种计算的区别

| 计算类型 | QE 里的写法 | 密度是否更新 | k 点 | 用途 |
| --- | --- | --- | --- | --- |
| 自洽 | `calculation = 'scf'` | 迭代更新到收敛 | 均匀网格 2×2×2 | 得到基态密度和总能，是后面所有计算的基础 |
| 非自洽 | `calculation = 'nscf'` | 不更新，直接读自洽的密度 | 更密的均匀网格 4×3×2 | 在更多 k 点上求本征值，用来算态密度 |
| 能带 | `calculation = 'bands'` | 不更新 | 沿高对称路径的 122 个点 | 画 ε\_n(k) 能带图 |

非自洽和能带计算可以"不更新密度"，是因为密度是对整个布里渊区的积分，用 2×2×2 已经收敛了。加密 k 点只是为了把本征值的分布看得更细。

### 4.9 态密度与投影态密度

态密度（DOS）表示单位能量间隔内有多少个电子态。把每个本征值用一个宽度为 σ 的高斯函数展宽后加起来：

```latex
g(E) = \sum_{n\mathbf k} w_{\mathbf k}\,\frac{1}{\sqrt{\pi}\,\sigma}\exp\!\left[-\frac{(E-\varepsilon_{n\mathbf k})^2}{\sigma^2}\right]
```

w\_k 是 k 点的权重，本项目的 σ = `degauss = 0.005 Ry`（约 0.07 eV）。

投影态密度（PDOS）进一步回答了这些态主要位于哪个原子的哪个轨道上。做法是把每个晶体波函数投影到原子轨道 φ\_α（比如 Sn 5s、Cl 3p）上，用重叠的平方作权重：

```latex
g_\alpha(E) = \sum_{n\mathbf k} w_{\mathbf k}\,\left|\langle\phi_\alpha|\psi_{n\mathbf k}\rangle\right|^2\,\delta_\sigma\!\left(E-\varepsilon_{n\mathbf k}\right)
```

这就是 projwfc.x 做的事。它顺便还给出 Lowdin 电荷：对占据态的投影权重求和，得到每个原子、每个轨道大约分到多少电子。

### 4.10 QE 的程序分工

| 程序 | 作用 | 本项目是否用到 | 运行位置 |
| --- | --- | --- | --- |
| pw.x | 主程序：自洽、非自洽、能带、结构优化 | 是 | GPU（NGC 镜像） |
| projwfc.x | 投影态密度和 Lowdin 电荷 | 是 | CPU（自行编译） |
| pp.x | 导出电荷密度、轨道密度等三维数据（cube 文件） | 下次用 | CPU |
| bands.x | 整理能带数据 | 未用，本征值直接从 pw.x 输出读取 | CPU |
| dos.x | 总态密度 | 未用，projwfc.x 已给出总 DOS | CPU |

## 五、结构准备与输入文件逐行讲解

输入文件是你和 QE 的全部对话：结构从你的 CIF 来，只做了一处修正，就是把氢原子拉到标准键长；其余的每一行都是一个物理或数值上的选择。

### 5.1 从 CIF 到 QE 结构

1. **读入 CIF。** 用 Python 的 ASE 库读取你的 `crystal.cif`，按 P-1 对称性展开成完整晶胞，共 106 个原子。
2. **修正氢原子位置。** X 射线衍射测的是电子密度，氢只有一个电子，而且这个电子偏向和它成键的重原子。所以 CIF 里的 C–H、N–H、O–H 键通常短 0.1 Å 左右，C–H 常写成 0.93 Å。我沿原键方向把氢原子外移到中子衍射的标准键长：C–H 1.083 Å，N–H 1.009 Å，O–H 0.983 Å。这样可以让结构优化少走很多步，结果保存在 `structure_Hnorm.xyz`。
3. **写成 QE 格式。** 晶胞用三个晶格矢量给出（`CELL_PARAMETERS`），a 沿 x 轴，b 在 xy 平面内。原子用分数坐标给出（`ATOMIC_POSITIONS crystal`），按 Sn、Cl、O、N、C、H 排序，保存在 `structure.qe`。所以原子编号是：Sn 1–2，Cl 3–14，O 15–18，N 19–26，C 27–62，H 63–106。这个编号就是 PDOS 文件名里 `atm#` 后面的数字。

### 5.2 结构优化输入 01\_relax.in 逐行解释

QE 输入文件由若干 Fortran 名单（namelist，以 `&名字` 开头、以 `/` 结束）和若干卡片（card，全大写开头的数据块）组成，`!` 后面是注释。

```text
&CONTROL
  calculation = 'relax'
  prefix = 'snpim'
  outdir = './tmp'
  pseudo_dir = './pseudo'
  verbosity = 'high'
  tprnfor = .true.
  forc_conv_thr = 1.0d-3   ! 受力收敛阈值 / (Ry/Bohr)
  etot_conv_thr = 1.0d-4
  nstep = 200
  max_seconds = 12600      ! 3.5 小时后自行安全退出，可续算
/
&SYSTEM
  ibrav = 0
  nat = 106
  ntyp = 6
  ecutwfc = 50.0
  ecutrho = 400.0
  occupations = 'fixed'
  vdw_corr = 'dft-d3'
  dftd3_version = 4
/
&ELECTRONS
  conv_thr = 1.0d-8
  mixing_beta = 0.4
/
&IONS
  ion_dynamics = 'bfgs'
/
ATOMIC_SPECIES
  Sn 118.710  Sn.pbe-dn-rrkjus_psl.1.0.0.UPF
  Cl  35.453  Cl.pbe-n-rrkjus_psl.1.0.0.UPF
  ...
CELL_PARAMETERS angstrom
     7.693900000     0.000000000     0.000000000
     1.427146179    10.851959959     0.000000000
     2.633709984     0.554016467    15.262930257
ATOMIC_POSITIONS crystal
  Sn    0.798030000   0.737190000   0.198680000
  ...共 106 行
K_POINTS automatic
  2 2 2 0 0 0
```

| 位置 | 参数 | 取值 | 含义与理由 |
| --- | --- | --- | --- |
| &CONTROL | calculation | 'relax' | 只优化原子位置，晶胞固定为实验值 |
| &CONTROL | prefix | 'snpim' | 所有中间文件的名字前缀，后续计算靠它找到自洽结果 |
| &CONTROL | outdir | './tmp' | 波函数和电荷密度存放在 `tmp/snpim.save/` |
| &CONTROL | pseudo\_dir | './pseudo' | 赝势文件所在目录 |
| &CONTROL | verbosity | 'high' | 输出更详细，包括每个 k 点的全部本征值 |
| &CONTROL | tprnfor | .true. | 打印每个原子的受力 |
| &CONTROL | forc\_conv\_thr | 1.0d-3 | 受力收敛标准，单位 Ry/Bohr，约 0.026 eV/Å |
| &CONTROL | etot\_conv\_thr | 1.0d-4 | 相邻两步的能量差收敛标准，单位 Ry |
| &CONTROL | nstep | 200 | 最多走 200 步，实际 41 步就收敛了 |
| &CONTROL | max\_seconds | 12600 | 3.5 小时后保存并退出，防止 Colab 运行时被回收时丢失全部进度 |
| &SYSTEM | ibrav | 0 | 不用 QE 的内置晶格类型，晶胞由 `CELL_PARAMETERS` 给出 |
| &SYSTEM | nat / ntyp | 106 / 6 | 原子数 / 元素种类数 |
| &SYSTEM | ecutwfc | 50.0 | 波函数截断能，单位 Ry，是 pslibrary 超软赝势的常用值 |
| &SYSTEM | ecutrho | 400.0 | 电荷密度截断能，取 ecutwfc 的 8 倍 |
| &SYSTEM | occupations | 'fixed' | 绝缘体，前 182 条带占满，其余全空，不需要展宽 |
| &SYSTEM | vdw\_corr | 'dft-d3' | 打开 Grimme D3 色散校正 |
| &SYSTEM | dftd3\_version | 4 | 4 表示 BJ 阻尼；3 是零阻尼，一般不推荐 |
| &ELECTRONS | conv\_thr | 1.0d-8 | 自洽收敛标准，单位 Ry；受力的精度取决于它，所以设得严一些 |
| &ELECTRONS | mixing\_beta | 0.4 | 新旧密度的混合比例，默认 0.7；大体系调小更稳 |
| &IONS | ion\_dynamics | 'bfgs' | 用 BFGS 算法移动原子 |
| ATOMIC\_SPECIES | 元素 质量 赝势文件 | 见上 | 质量只在分子动力学里用得到，这里不影响结果 |
| CELL\_PARAMETERS | 三个晶格矢量 | 单位 Å | 由 a、b、c、α、β、γ 换算而来 |
| ATOMIC\_POSITIONS | 元素 + 分数坐标 | crystal | 每行一个原子，分数坐标即相对晶格矢量的坐标 |
| K\_POINTS | automatic 2 2 2 0 0 0 | — | 2×2×2 Monkhorst-Pack 网格；后三个 0 表示不偏移，包含 Γ 点 |

### 5.3 后续输入和结构优化的不同之处

后续输入都由 `make_inputs.py` 从优化结果自动生成，原子坐标取优化的最后一步，其余参数不变。只列出不同的地方：

| 文件 | 改动 | 理由 |
| --- | --- | --- |
| 02\_scf.in | `calculation = 'scf'`，增加 `nbnd = 200` | 默认只算占据带加少量空带；多算 18 条空带才能看到导带、得到带隙 |
| 03\_nscf.in | `calculation = 'nscf'`；`nbnd = 240`；`occupations = 'smearing'`、`smearing = 'gaussian'`、`degauss = 0.005`；k 点 4×3×2 | 加密 k 点算态密度。最初用四面体法，PDOS 输出全为 0，改成高斯展宽后正常 |
| 05\_bands.in | `calculation = 'bands'`；`nbnd = 200`；k 点改为路径 | 沿高对称路径画能带 |
| 04\_projwfc.in | projwfc.x 的输入：`degauss = 0.005`、`DeltaE = 0.01` | 展宽约 0.07 eV，能量步长 0.01 eV |

能带路径是这样写的：

```text
K_POINTS crystal_b
  6
  0.5 0.0 0.0  30   ! X
  0.0 0.0 0.0  30   ! G
  0.0 0.5 0.0   1   ! Y
  0.0 0.0 0.5  30   ! Z
  0.0 0.0 0.0  30   ! G
  0.5 0.5 0.5   1   ! R
```

`crystal_b` 表示坐标以倒格子矢量为单位，每行最后的数字是到下一个点之间插入多少个点。Y 后面写 1，意思是 Y 直接跳到 Z，中间不算，图上记作 Y|Z。三斜晶系 P-1 没有旋转对称，特殊点只有各分量为 0 或 ½ 的八个点。这条路径覆盖了三个轴向和体对角方向，共 122 个 k 点。

## 六、计算步骤与实际执行

五步计算一环扣一环：先把结构优化到受力很小，再在这个结构上做一次高精度自洽，然后用自洽得到的密度去算能带和态密度。GPU 上实际计算约 45 分钟，其中结构优化占了三分之二。

&#91;embedded content: 本次计算流程 · 实际用时\]

| 步骤 | 程序与硬件 | 输入 → 输出 | 实际用时 | 做了什么 |
| --- | --- | --- | --- | --- |
| 1 结构优化 | pw.x，A100 | 01\_relax.in → 01\_relax.out | 31.4 分钟 | 41 步 BFGS，每步一次自洽加一次受力计算 |
| 2 自洽 | pw.x，A100 | 02\_scf.in → 02\_scf.out | 1 分 10 秒 | 在优化后的结构上求基态密度，并给出带隙 |
| 3 能带 | pw.x，A100 | 05\_bands.in → 05\_bands.out | 9 分 46 秒 | 密度固定，沿路径在 122 个 k 点上各求 200 条带 |
| 4 非自洽 | pw.x，A100 | 03\_nscf.in → 03\_nscf.out | 1 分 27 秒 | 密度固定，在 4×3×2 网格（等价后 14 个点）上求 240 条带 |
| 5 投影态密度 | projwfc.x，CPU | 04\_projwfc.in → 04\_projwfc.out 和 pdos 文件 | 几分钟 | 把非自洽的波函数投影到各原子轨道 |
| 6 画图汇总 | plot\_results.py、make\_inputs.py | 上述输出 → 图、csv、summary.txt | 几秒 | 以价带顶为零点画能带和 PDOS，统计带边组成 |

能带一步最慢，是因为要算 122 个 k 点，是自洽的 15 倍。这次还多跑了一遍非自洽和 PDOS，因为第一次用四面体法时 PDOS 输出全为 0（见 3.4 节）。

### 6.1 每步是怎么运行的

每一步都是一条命令，放在脚本 `run_after_relax.sh` 里依次执行：

```bash
cd /content/qe-snpim
qe pw.x -in 01_relax.in > 01_relax.out 2>&1            # GPU，结构优化
python3 make_inputs.py from-relax 01_relax.out          # 取最后一步结构，生成后续输入
qe pw.x -in 02_scf.in   > 02_scf.out   2>&1             # GPU，自洽
qe pw.x -in 05_bands.in > 05_bands.out 2>&1             # GPU，能带
qe pw.x -in 03_nscf.in  > 03_nscf.out  2>&1             # GPU，非自洽
/content/q-e-qe-7.3.1/bin/projwfc.x -in 04_projwfc.in > 04_projwfc.out   # CPU，投影
python3 plot_results.py                                 # 画图、导出 csv
python3 make_inputs.py summary                          # 写 summary.txt
```

`> 文件 2>&1` 表示把屏幕输出和报错信息都写进输出文件。每步结束后，脚本用 `grep -q 'JOB DONE'` 检查输出末尾有没有正常结束的标志，没有就停下。

自洽、能带和非自洽用的是同一个 `prefix` 和 `outdir`，所以后两步会自动读取 `tmp/snpim.save/` 里的自洽电荷密度。这也是它们必须按顺序、在同一个目录里跑的原因。

### 6.2 怎么判断一步算得对不对

| 看什么 | 在哪个文件搜 | 这次的结果 | 含义 |
| --- | --- | --- | --- |
| 优化是否收敛 | 01\_relax.out 搜 `bfgs converged` | 41 步后出现 | 受力和能量都达到了收敛标准 |
| 自洽是否收敛 | 搜 `convergence has been achieved` | 每次自洽都有 | 电子步达到 conv\_thr |
| 总能量 | 搜以 `!` 开头的 total energy | −1535.820050 Ry | 优化后结构的总能 |
| 终态受力 | 搜 `Total force` | 小于收敛标准 | 原子已在能量极小点附近 |
| 带边 | 02\_scf.out 搜 `highest occupied, lowest unoccupied level` | 0.9548 eV 和 3.1412 eV | 价带顶和导带底的绝对能量，差值就是带隙 |
| GPU 是否启用 | 任一 .out 开头搜 `GPU acceleration is ACTIVE` | 有 | 确认确实是在显卡上算的 |
| 是否正常结束 | 文件末尾 `JOB DONE.` | 有 | 没有这行就是中途崩了 |

带边的绝对数值本身没有物理意义，周期性计算里的能量零点是任意的。有意义的是带隙和相对位置，所以画图时统一减去价带顶 0.9548 eV，把它设为零。

## 七、计算结果与物理解读

核心结论：这是一个带隙约 2.19 eV（PBE-D3）的绝缘体。价带顶几乎全部来自 2-苯基咪唑鎓的 π 轨道，导带底来自 \[SnCl₆\]²⁻ 的 Sn 5s–Cl 3p 反键轨道。所以能量最低的电子跃迁是从有机阳离子到无机阴离子的电荷转移。

&#91;embedded content: 带边能级示意 · 组成来自 PDOS 积分，带隙来自 02\_scf.out\]

### 7.1 结构优化与能量

| 量 | 结果 |
| --- | --- |
| 收敛情况 | 41 步 BFGS 后收敛（`bfgs converged`） |
| 优化后总能 | −1535.820050 Ry = −20895.8963 eV |
| 用时 | 31.4 分钟（A100） |
| 晶胞 | 固定为实验值，未优化 |

总能的绝对值单独看没有意义，它的用处是做比较。只有在同一套参数下（同样的赝势、截断能和泛函），比较不同结构或不同组成的能量才有意义，比如判断哪种氢键排布更稳定、计算形成能或脱水能。优化前后的键长、键角变化，可以用 VESTA 对比 `crystal.cif` 和 `relaxed_structure.cif`（第八节）。

### 7.2 带隙和能带

| 量 | 结果 | 来源 |
| --- | --- | --- |
| 价带顶绝对能量 | 0.9548 eV | 02\_scf.out |
| 导带底绝对能量 | 3.1412 eV | 02\_scf.out |
| 带隙（2×2×2 网格） | 2.186 eV | 02\_scf.out |
| 带隙（高对称路径） | 2.189 eV | 05\_bands.out |
| 价带顶位置 | X 点附近 | 05\_bands.out |
| 导带底位置 | Γ 点 | 05\_bands.out |
| PWmat 对照 | 2.211 eV，相差 0.02 eV | 你之前的 PWStudio 计算 |

能带图（云盘里的 `fig_bands_pdos.png` 左半边）有三个特点：

- **价带非常平。** 价带顶那几条带几乎是水平线。能带的弯曲程度反映电子在相邻单元之间跳跃的难易，有效质量满足 1/m\* ∝ ∂²ε/∂k²。能带平意味着空穴有效质量很大，空穴被局域在单个有机阳离子上。这也说明苯基咪唑鎓之间的 π 轨道重叠很弱。
- **导带底稍有色散。** 导带底的起伏约 0.2 eV，说明相邻 \[SnCl₆\]²⁻ 之间通过 Cl···Cl 接触有少量耦合，但仍然是零维（0D）孤立八面体的典型特征。
- **导带分组出现。** 以价带顶为零点，空带集中在 2.2～2.4 eV、约 3.3 eV 和 4.3～4.6 eV 三组，分别对应各自独立的分子轨道系列。

价带顶和导带底不在同一个 k 点，严格来说是间接带隙。但价带几乎是平的，直接带隙和间接带隙差别很小。对这类 0D 杂化材料，讨论"直接还是间接"意义不大，它的光学行为更接近分子而不是半导体。

### 7.3 态密度：带边由谁贡献

| 带边（取 0.5 eV 窗口内 PDOS 积分） | 元素占比 | 对应的轨道 |
| --- | --- | --- |
| 价带顶（价带顶以下 0.5 eV） | C 91%，N 7% | 2-苯基咪唑鎓的 π 轨道（HOMO） |
| 导带底（导带底以上 0.5 eV） | Cl 55%，Sn 42% | \[SnCl₆\]²⁻ 的 Sn 5s–Cl 3p σ\* 反键轨道 |

先看导带底。Sn(IV) 是 4d¹⁰ 5s⁰ 组态，5s 轨道是空的。六个 Cl 的 3p 轨道和它组合，形成一个全对称的 a₁g 型 σ\* 轨道，这就是全锡六氯酸盐的 LUMO。Sn 和 Cl 各占一半左右，正好符合反键轨道的特征。

再看价带顶。苯基咪唑鎓的共轭 π 轨道能量比 \[SnCl₆\]²⁻ 的 Cl 3p 孤对电子更高，所以占据了价带顶。Cl 3p 的主峰在价带更深的位置。

这就是文献里常说的有机供体、无机受体型能带排列。水分子（O）对两个带边的贡献都可以忽略，它的作用主要是结构上的，用氢键把阳离子和阴离子连起来。

### 7.4 Lowdin 电荷

| 原子 | 总电子数 | s | p | d | 中性原子价电子 | 净电荷 |
| --- | --- | --- | --- | --- | --- | --- |
| Sn | 12.88 | 1.108 | 1.778 | 9.999 | 14 | 约 +1.1 |

Sn 的形式氧化态是 +4，但 Lowdin 电荷只有约 +1.1。这很正常：Sn–Cl 键有相当的共价性，Cl 把一部分电子反馈到 Sn 的 5s 和 5p 上。所以 5s 不是 0 而是 1.1，5p 是 1.8。d = 9.999 说明 4d 是满壳层，不参与成键。任何电荷划分方法都有任意性，比较不同原子之间的相对大小比看绝对值更有意义。两个 Sn 以及十二个 Cl 的电荷是否等价，可以在 `04_projwfc.out` 里自己对比。

### 7.5 与 PWmat 的对比

两次计算带隙分别是 2.19 和 2.211 eV，差 0.02 eV。两者的赝势类型和截断能都不同，但都是 GGA 加色散校正，所以这个差异在预期内。这说明 Colab 上搭建的 QE 流程是可信的，以后可以用开源 QE 代替商业软件做同类计算。

### 7.6 对实验意味着什么

- **吸收边。** 最低能吸收是有机到无机的电荷转移。PBE 通常低估带隙，实验光学带隙应该比 2.19 eV 大；对照你的紫外-可见漫反射数据（Tauc 图）就能看出低估了多少。
- **发光。** 带边态分居在有机物和 \[SnCl₆\]²⁻ 上，电子和空穴的波函数重叠小，这类电荷转移态发光一般较弱。如果实验里观察到了发光或余辉，发光中心更可能在有机阳离子自身的单重态或三重态上。平坦的价带和局域的空穴也和这一点一致。这是基于基态能带的推断，要确认发光机制，需要单独的激发态计算（第九节）。
- **怎样调带隙。** 在保持 \[SnCl₆\]²⁻ 不变的前提下，换一个 π 电子更多、HOMO 更高的有机阳离子，会进一步降低带隙。你在做的二苯基咪唑体系就是这个方向上的一个对照。

## 八、结果文件清单与查看方法

本次结果在谷歌云盘 `MyDrive/QE计算结果/2-苯基咪唑SnCl6/`，共 28 项，37 MB。下载到 Windows 时要放在纯英文路径下，比如 `E:\qe\snpim\`，否则 GaussView 等软件会因为中文路径读不了。`.out` 是纯文本，用记事本或 VS Code 打开；它不是 Gaussian 的输出，GaussView 打不开。

| 想看什么 | 文件 | 用什么打开 | 怎么看 |
| --- | --- | --- | --- |
| 一眼看全部结果 | fig\_bands\_pdos.png | 图片查看器 | 左边能带，右边按元素分解的 PDOS，价带顶为 0 |
| 自己画能带 | bands\_vbm0.csv | Origin / Excel | 第 1 列是 k 路径坐标，其余 200 列各是一条带（eV，价带顶为 0）。高对称点在第 0、30、60/61、91、121 个点，依次是 X、Γ、Y\|Z、Γ、R |
| 自己画态密度 | pdos\_elements.csv | Origin / Excel | 列为能量（价带顶为 0）、总 DOS、Sn、Cl、O、N、C、H |
| 单个原子、单个轨道的 PDOS | pdos/snpim.pdos.pdos\_atm#N(元素)\_wfc#M(轨道) | Origin（空格分隔文本） | 能量是绝对值，用时减 0.9548 eV。p 轨道文件含总量及 pz、px、py 三列 |
| 优化后的结构 | relaxed\_structure.cif / .xyz | VESTA、Mercury | 和 crystal.cif 对比 Sn–Cl 键长、Cl–Sn–Cl 键角、N–H···Cl 和 O–H···Cl 氢键 |
| 优化过程 | 01\_relax.out | 文本编辑器；XCrySDen 可动画播放 | 搜 `!` 看每步能量，搜 `Total force` 看受力下降 |
| 带隙和总能 | 02\_scf.out | 文本编辑器 | 搜 `highest occupied`、`!`、`Dispersion Correction` |
| 每个 k 点的本征值 | 03\_nscf.out、05\_bands.out | 文本编辑器 | 每个 k 点一组 200 或 240 个能量 |
| 每个态由哪些原子轨道组成、Lowdin 电荷 | 04\_projwfc.out | 文本编辑器 | 搜 `Lowdin Charges`；每个态下面的 `psi = 0.4*[#27]+…` 表示第 27 号轨道占 40% |
| 一页汇总 | summary.txt | 文本编辑器 | 收敛情况、能量、带隙、每步用时 |
| 重复或修改计算 | *.in、*.tmpl、*.py、*.sh | 文本编辑器 | 写论文方法部分时照着 \*.in 写参数 |

### 8.1 几个值得自己做的分析

1. **结构可靠性。** 在 VESTA 里量优化前后的 Sn–Cl 键长和氢键距离，列一个"实验 / 计算 / 偏差"表。Sn–Cl 偏差在 1%～2% 内就说明计算方法合理。氢键的变化通常会大一些。
2. **导带底是 Sn 5s 还是 5p。** 把 `atm#1(Sn)` 和 `atm#2(Sn)` 的 s 轨道与 p 轨道文件画在一起，应该看到导带底以 5s 为主。
3. **价带顶是咪唑环还是苯环。** 在 `02_scf.in` 的 ATOMIC\_POSITIONS 里确认哪些 C 属于咪唑环、哪些属于苯环，把对应的 PDOS 文件分组相加后比较。
4. **色散作用有多重要。** `02_scf.out` 里的 Dispersion Correction 项是整个晶胞的 D3 能量，和总的结合能比一下，就能体会范德华力对分子晶体的作用。

### 8.2 这次没有保存的东西

`tmp/snpim.save/` 里的波函数和电荷密度文件没有保存，运行时删除后就没有了。按本体系的规模估算：每个 k 点约 51 300 个平面波，200 条带，每个系数是 16 字节的复数，所以每个 k 点约 160 MB。自洽 8 个 k 点约 1.3 GB，非自洽 14 个点约 2.7 GB。已经算出的能带、态密度和 PDOS 都不需要它们，但画轨道形状、电荷密度分布，或者算光学性质时需要。重新生成很便宜：用优化后的结构重跑一次自洽，约 1 分钟。新脚本已经会自动保存（第十节）。

## 九、方法局限与下一步

这次计算回答了基态电子结构是什么样的问题，但带隙的绝对值偏小，也没有涉及激发态。要写进论文，最值得补的是收敛性测试和一次杂化泛函带隙。

| 局限 | 影响 | 怎么改进 | 大致代价 |
| --- | --- | --- | --- |
| PBE 低估带隙 | 2.19 eV 只是下限，不能直接和实验光学带隙比 | 在优化好的结构上用 HSE06 杂化泛函算一次自洽 | 比 PBE 贵几十倍，A100 上预计数小时 |
| 没做收敛性测试 | 截断能和 k 点是否足够，审稿人可能会问 | ecutwfc 取 40/50/60 Ry、k 点取 1×1×1/2×2×2/3×2×2，各算一次自洽，看总能和带隙的变化 | 每次几分钟 |
| 没有自旋轨道耦合 | Sn 和 Cl 不算很重，导带底又是 s 轨道为主，影响很小 | 一般不需要；如换成 Pb、Bi、Sb 体系就必须考虑 | — |
| 晶胞未优化 | 计算结构是 283 K 实验晶胞，而 DFT 算的是 0 K | 对分子晶体这是常规做法，可不改；确有需要可用 vc-relax | 数小时 |
| 没有光吸收谱 | 无法直接和吸收谱比较 | QE 自带的 epsilon.x 只支持模守恒赝势，需要换赝势重算；也可以用 Yambo 等专门软件 | 中等 |
| 没有激发态和激子 | 解释不了发光位置、斯托克斯位移、自陷激子 | 切一个分子团簇，用 gpu4pyscf 做 TDDFT：基态优化、吸收、三重态优化、发射，就是之前文档里的第二条路线 | 每步数十分钟 |
| 没有实空间轨道图 | 只能从 PDOS 推断带边位置，缺少直观图像 | 用 pp.x 导出价带顶和导带底的电荷分布 cube，在 VESTA 里画等值面 | 约 1～2 个计算单元，新脚本已包含 |

### 9.1 写进论文时的方法描述（参考）

> First-principles calculations were performed with Quantum ESPRESSO 7.3.1 using a plane-wave basis and ultrasoft pseudopotentials from pslibrary 1.0.0. Exchange-correlation was treated with the PBE functional, and van der Waals interactions were included with the DFT-D3 method with Becke-Johnson damping. Kinetic energy cutoffs of 50 Ry and 400 Ry were used for wavefunctions and charge density. Atomic positions were relaxed within the experimental cell until residual forces were below 10⁻³ Ry/Bohr, with a 2×2×2 Monkhorst-Pack k-mesh. Density of states was computed on a 4×3×2 mesh with 0.005 Ry Gaussian smearing.

引用时至少列出 QE、PBE、DFT-D3 和 BJ 阻尼、pslibrary 的原始文献，见第十一节。

## 十、下次怎么跑

下次只要运行五个单元格，从开机到结果全部进云盘都是自动的。这套脚本叫 `qe-snpim-scripts.zip`，已经发给你了。把它放到云盘的 `MyDrive/QE计算结果/脚本/` 下。新脚本是按这次跑通的做法重新整理的，还没有完整跑过一遍。第一步会自检，确认显示"QE GPU 环境就绪"后再往下走。

### 10.1 脚本包里有什么

| 文件 | 作用 |
| --- | --- |
| setup\_qe\_gpu.sh | 下载 NGC 镜像、解压、复制显卡驱动、生成 `qe` 命令；最后检查 pw.x 是否报告"GPU acceleration is ACTIVE" |
| build\_qe\_pp.sh | 在 CPU 上编译 QE 7.3.1 后处理程序（projwfc.x、pp.x 等），已经处理了第三节列出的编译问题 |
| run\_all.sh | 总入口：缺赝势就自动下载，后台编译后处理程序，同时在 GPU 上做结构优化，然后调用下一个脚本 |
| run\_after\_relax.sh | 自洽 → 导出 cube → 打包自洽波函数 → 非自洽 → PDOS → 能带 → 画图、导出结构、汇总 |
| save\_to\_drive.sh | 把工作目录同步到云盘，只传新增或变化的文件；每算完一步调用一次 |
| make\_inputs.py | 从优化结果生成后续输入、pp.x 输入、导出结构和轨迹、写汇总 |
| plot\_results.py | 画能带和 PDOS，导出 csv，统计带边组成 |
| 01\_relax.in、header\_\*.tmpl、04\_projwfc.in、structure.qe | 本体系的输入；换体系时替换这些 |
| README.md | 单元格步骤速查 |

### 10.2 五个单元格

1. **挂载云盘**，会弹出授权窗口：

   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```
2. **取脚本并搭环境**，约 3～5 分钟：

   ```bash
   %%bash
   mkdir -p /content/qe-snpim && cd /content/qe-snpim
   unzip -oq "/content/drive/MyDrive/QE计算结果/脚本/qe-snpim-scripts.zip" -d /content/qe-snpim
   bash setup_qe_gpu.sh
   ```
3. **后台启动全流程**：

   ```bash
   %%bash
   cd /content/qe-snpim
   RUN_NAME=snpim_$(date +%Y%m%d) SAVE_WFC=scf nohup bash run_all.sh > run_all.log 2>&1 &
   ```
4. **随时查看进度**，可反复运行：

   ```bash
   %%bash
   cd /content/qe-snpim; ls DONE_* FAIL_* 2>/dev/null; tail -5 run_all.log; tail -2 save_to_drive.log
   ```
5. **看到 DONE\_all 后收尾**：先写完云盘缓存再断开，在网页版云盘里确认文件都在，然后再删除运行时：

   ```python
   from google.colab import drive
   drive.flush_and_unmount()
   ```

### 10.3 可调的开关

| 变量 | 默认 | 作用 |
| --- | --- | --- |
| RUN\_NAME | snpim\_年月日\_时分 | 云盘里的结果文件夹名 |
| SAVE\_WFC | scf | scf：保存自洽波函数快照（约 1.3 GB）；all：再加非自洽快照（另约 2.7 GB）；none：不存波函数 |
| CUBE\_WIN | 0.3 | 价带顶和导带底电荷分布取的能量窗口宽度，单位 eV |

### 10.4 下次云盘里会多出的东西

- `cube/rho_total.cube`、`cube/vbm_ildos.cube`、`cube/cbm_ildos.cube`：总电荷密度、价带顶和导带底附近的电荷分布。用 VESTA 打开，在 Properties → Isosurfaces 里调等值面，就能看到空穴在苯基咪唑鎓上、电子在 \[SnCl₆\]²⁻ 上。
- `wfc_scf.tar`：自洽波函数和电荷密度。解压到 `tmp/` 后，就能接着跑后处理或非自洽，不必重做优化和自洽。
- `relax_trajectory.extxyz`：整个优化过程的轨迹，可用 OVITO 播放。
- `ENV.txt`、`MANIFEST.txt`、`qe_wrapper_used.sh`：显卡和版本信息、文件清单、实际用的 `qe` 命令。

### 10.5 换一个晶体时要改什么

1. 用新的 CIF 生成结构：修正氢原子位置，写成 `structure.qe`。这一步可以让我来做。
2. 修改 `01_relax.in` 和三个 header 模板里的 `nat`、`ntyp`、`ATOMIC_SPECIES`。
3. 按新的价电子数改 `nbnd`：占据带数等于价电子数除以 2，再多加约 10% 的空带。同时把 `plot_results.py` 里的 182 改成新的占据带数。
4. 按新晶胞的边长调 k 点，按新晶系调能带路径。

## 十一、名词速查与参考资料

| 名词 | 英文 | 一句话解释 |
| --- | --- | --- |
| 密度泛函理论 | DFT | 用电子密度而不是多电子波函数来求基态的方法 |
| 泛函 | functional | 交换关联能的近似形式，如 PBE、HSE06 |
| 色散校正 | dispersion correction, D3(BJ) | 给 DFT 补上范德华力的经验项 |
| 平面波 | plane wave | e^{iG·r} 形式的基函数，天然适合周期性体系 |
| 截断能 | cutoff energy, ecutwfc / ecutrho | 平面波展开保留到多高的动能，单位 Ry |
| 赝势 / 超软赝势 | pseudopotential / USPP | 代替原子核和内层电子的平滑有效势 |
| k 点 | k-point | 布里渊区里的采样点，用来做布里渊区积分 |
| 布里渊区 / Γ 点 | Brillouin zone / Gamma | 倒空间的原胞；Γ 是它的中心 k = 0 |
| 自洽 / 非自洽 | SCF / NSCF | 迭代更新密度直到收敛 / 固定密度只求本征值 |
| BFGS | Broyden–Fletcher–Goldfarb–Shanno | 结构优化用的拟牛顿法 |
| 价带顶 / 导带底 | VBM / CBM | 最高占据态 / 最低未占据态，差值为带隙 |
| 态密度 / 投影态密度 | DOS / PDOS | 单位能量内的态数 / 按原子轨道分解后的态数 |
| Lowdin 电荷 | Löwdin charge | 按投影权重给每个原子分配电子数的一种方法 |
| cube 文件 | Gaussian cube | 存三维网格数据（如电荷密度）的文本格式，VESTA 可画等值面 |
| 计算单元 | compute unit, CU | Colab 的计费单位，按开机时间和显卡型号扣 |
| 运行时 | runtime | Colab 分配给你的临时虚拟机 |
| NGC | NVIDIA GPU Cloud | NVIDIA 的软件容器库，提供编译好的 GPU 版科学软件 |
| chroot | change root | 让程序把某个目录当作根目录运行，用来隔离两套系统库 |

单位换算：1 Ry = 13.6057 eV；1 Bohr = 0.529177 Å；1 Ry/Bohr = 25.71 eV/Å。

### 官方文档（已核对）

- [pw.x 输入参数说明（Quantum ESPRESSO 官网）](https://www.quantum-espresso.org/Doc/INPUT_PW.html)：所有参数的权威解释。其中写明 `dftd3_version = 4` 是带 BJ 阻尼的 D3，默认值 3 是零阻尼。
- [NVIDIA NGC Quantum ESPRESSO 容器](https://catalog.ngc.nvidia.com/orgs/hpc/containers/quantum_espresso)：最新标签为 qe-7.3.1，也就是本项目使用的版本。

### 方法原始文献（写论文时引用）

1. Giannozzi P. et al., J. Phys.: Condens. Matter 21, 395502 (2009)；J. Phys.: Condens. Matter 29, 465901 (2017)。Quantum ESPRESSO。
2. Giannozzi P. et al., J. Chem. Phys. 152, 154105 (2020)。QE 的 GPU 版本。
3. Kohn W., Sham L. J., Phys. Rev. 140, A1133 (1965)。Kohn-Sham 方程。
4. Perdew J. P., Burke K., Ernzerhof M., Phys. Rev. Lett. 77, 3865 (1996)。PBE 泛函。
5. Grimme S. et al., J. Chem. Phys. 132, 154104 (2010)。DFT-D3。
6. Grimme S., Ehrlich S., Goerigk L., J. Comput. Chem. 32, 1456 (2011)。BJ 阻尼。
7. Vanderbilt D., Phys. Rev. B 41, 7892 (1990)。超软赝势。
8. Dal Corso A., Comput. Mater. Sci. 95, 337 (2014)。pslibrary 赝势库。
9. Monkhorst H. J., Pack J. D., Phys. Rev. B 13, 5188 (1976)。k 点网格。

文献信息来自我的知识，引用前请在数据库里核对卷号和页码。
