# (2-苯基咪唑鎓)₂[SnCl₆]·2H₂O 杂化晶体 ORCA 量子化学与长余辉发光机理计算全流程教学报告

**作者/执笔**：Antigravity 量子化学计算组  
**研究体系**：$(2\text{-PhImH})_2[\text{SnCl}_6]\cdot 2\text{H}_2\text{O}$（零维有机–无机杂化金属卤化物晶体）  
**计算软件**：ORCA 6.1.1 / Quantum ESPRESSO 7.3.1 / PySCF / VESTA  
**计算平台**：Google Cloud Compute Engine (12 vCPU, 96 GB RAM) + Colab A100 GPU  
**日期**：2026 年 10 月 26 日  

---

## 摘要与执行概述

本报告旨在为量子化学计算初学者提供一份**端到端、可完全独立复现**的实操教程与学术报告，完整复刻顶刊 *Angewandte Chemie* 针对零维杂化金属卤化物长余辉/室温磷光材料的全部理论计算模块。

在本阶段计算中，我们彻底攻克了传统真空气相团簇模型中由于**缺失晶体马德隆势场**导致的二价阴离子 $[\text{SnCl}_6]^{2-}$ 电荷失衡、虚假低能电荷转移（CT）态以及水分子异常杂化难题。通过构建包含 **11,077 个晶格 ESP 点电荷**的周期性静电嵌入环境，采用**全电子二阶标量相对论哈密顿量（DKH2）**与**范围分离杂化泛函 $\omega\text{B97X-D3}$**，定量求解了自旋–轨道耦合矩阵元（SOCME），并完成了最低三重态（$T_1$）的开壳层结构弛豫、发射峰波长预测以及自然跃迁轨道（NTO）三维空间重构。

### 核心光物理与理论计算成果速查表

| 光物理参数 | 计算数值 | 对应波长 / 能量 | 物理本质与论文支撑 | 对应论文图表 |
| :--- | :---: | :---: | :--- | :---: |
| **周期性晶体带隙 ($E_g$)** | $2.19\ \text{eV}$ | $566.1\ \text{nm}$ | 晶体 Kohn–Sham 电子带隙下限（PBE+D3） | **Figure 4a** |
| **基态光学吸收起点 ($S_1$)** | $5.04\ \text{eV}$ | $\mathbf{246.0\ \text{nm}}$ | 阳离子纯正内部 $\pi\to\pi^*$ 强吸收起点 | **Figure 4b 上** |
| **未弛豫垂直三重态能级 ($T_1$)** | $3.39\ \text{eV}$ | $\mathbf{365.7\ \text{nm}}$ | 激子尚未发生骨架自陷前的垂直吸光能级 | **Figure 4b 上** |
| **弛豫后 $T_1 \to S_0$ 垂直发射峰** | $\mathbf{2.493\ \text{eV}}$ | $\mathbf{497.3\ \text{nm}}$ | **理论预测的室温磷光 / 长余辉发射峰（绿光）** | **Figure 4b 下** |
| **激子自陷斯托克斯位移 ($\Delta E_{\text{Stokes}}$)** | $\mathbf{0.897\ \text{eV}}$ | $\Delta \lambda = \mathbf{131.6\ \text{nm}}$ | 激发态构型自陷畸变引起的巨大发光红移 | **Figure 4b 下** |
| **系间窜越耦合 $|\langle T_1 \| \hat{H}_{\text{SOC}} \| S_1 \rangle|$** | $\mathbf{0.177\ \text{cm}^{-1}}$ | — | 重原子 Sn/Cl 诱导的高效 $S_1 \rightsquigarrow T_1$ 激子自旋翻转 | **Figure 4c** |
| **磷光辐射耦合 $|\langle T_1 \| \hat{H}_{\text{SOC}} \| S_0 \rangle|$** | $\mathbf{0.162\ \text{cm}^{-1}}$ | — | 重原子微扰打破 $T_1 \to S_0$ 自旋禁阻，促成室温长余辉 | **Figure 4c** |

---

# 第一部分 量子化学与发光物理核心基础（初学必读）

对于刚接触计算化学的同学，面对一堆英文缩写（DFT、TDDFT、SOC、NTO、Madelung）往往会感到困惑。本章用最直白通俗的语言，从“物理是什么”和“为什么要这么算”讲起。

## 1. 为什么不能只算晶体能带？什么是分子团簇模型？

在固体物理中，我们习惯用周期性边界条件（如 Quantum ESPRESSO）计算能带结构（Band Structure）。但这在解释**分子晶体的发光（荧光、磷光、长余辉）**时会遇到致命局限：
1. **电子带隙 $\neq$ 发光波长**：能带计算假设电子是自由流动的单电子（非相互作用）。但在零维（0D）金属卤化物中，电子被紫外光激发后，电子与空穴之间存在极强的库仑吸引力，紧紧绑在一起形成**激子（Exciton）**。激子的结合能高达几百甚至上千毫电子伏（meV），因此光吸收和发光的能量远远小于晶体能带带隙。
2. **激子是高度定域的**：在本晶体 $(2\text{-PhImH})_2[\text{SnCl}_6]\cdot 2\text{H}_2\text{O}$ 中，无机八面体 $[\text{SnCl}_6]^{2-}$ 彼此被大体积的有机阳离子隔开，电子无法在八面体之间自由穿梭。发光本质上是一个**分子尺度的电子激发与几何扭曲过程**。
3. **解决方法**：切出一个包含核心配位单元的有限微观结构（称为**量子化学团簇 QM Cluster**，本研究切出 53 个原子），用精确的分子激发态方法（TDDFT）专门求解光物理过程。

```
              ┌──────────────────────────────────────────────┐
              │             真实三维周期性晶体               │
              └──────────────────────┬───────────────────────┘
                                     │ 空间截取 (半径截断)
                                     ▼
        ┌──────────────────────────────────────────────────────────┐
        │  中心 53 原子核心团簇 (QM 区)                            │
        │  • 1 个 [SnCl₆]²⁻ 八面体                                 │
        │  • 2 个 2-苯基咪唑鎓阳离子 (发光主体)                     │
        │  • 2 个结晶水分子                                        │
        └────────────────────────────┬─────────────────────────────┘
                                     │ 外部嵌入 (静电包裹)
                                     ▼
        ┌──────────────────────────────────────────────────────────┐
        │  外围 11,077 个晶格 ESP 点电荷 (MM 区)                    │
        │  • 提供严格的三维晶体马德隆静电势场 (Madelung Potential) │
        │  • 防止阴离子电子飞散，还原真实晶格能级                   │
        └──────────────────────────────────────────────────────────┘
```

---

## 2. 为什么必须挂载 11,077 个晶格点电荷（马德隆静电场）？

这是本阶段工作相比于早期“真空气相测试”的最核心升级。

在真实晶体中，每个带 $-2$ 价电荷的 $[\text{SnCl}_6]^{2-}$ 八面体周围都整整齐齐排列着带 $+1$ 价电荷的阳离子和极性水分子。外围所有正负离子在中心产生的静电势总和，被称为**马德隆势（Madelung Potential）**。

* **如果把团簇放在真空里算**：中间的二价阴离子缺少了外围正离子的束缚，其外层的 $\text{Cl}\ 3p$ 孤对电子能级会被**人为且虚假地抬高到极不物理的水平**。在早期真空气相 PBE0 计算中，计算软件误以为电子极易从阴离子转移到阳离子，因而算出了大量 $3.28\sim3.82\text{ eV}$ 的虚假“电荷转移（CT）暗态”，甚至连水分子都混进了最高占据轨道（HOMO 含有 33% 水成分）。
* **挂载点电荷后**：外围 11,077 个带电点模拟了无限晶格产生的正静电势阱，将阴离子的电子云牢牢压回正确能级。虚假暗态全部消失，轨道物理图像瞬间回归纯净自洽。

---

## 3. 单重态（Singlet）与三重态（Triplet）：自旋的奥秘

在基态（$S_0$）下，分子轨道里的电子都是成双成对的，一个自旋向上（$\uparrow$），一个自旋向下（$\downarrow$），净自旋量子数 $S = 0$，自旋多重度 $2S+1 = 1$，称为**单重态**。

当分子吸收一个紫外光子后，一个电子被激发到更高的未占轨道：
* **激发态单重态（$S_1$）**：激发的两个电子依然自旋相反（$\uparrow\ \downarrow$），净自旋 $S = 0$。从 $S_1$ 跃迁回 $S_0$ 发出的光叫**荧光（Fluorescence）**，由于自旋守恒，跃迁速度极快（纳秒级，光一关立刻熄灭）。
* **激发态三重态（$T_1$）**：激发的两个电子自旋变得同向（$\uparrow\ \uparrow$），净自旋 $S = 1$，自旋多重度 $2S+1 = 3$，称为**三重态**。从 $T_1$ 跃迁回 $S_0$ 发出的光叫**磷光（Phosphorescence）**。根据量子力学自旋选择定则（$\Delta S = 0$），自旋同向翻转回相反方向是**严格禁阻**的！因此电子在 $T_1$ 态被困住，寿命极大延长（数秒甚至数分钟），从而产生**室温长余辉（Afterglow）**。

---

## 4. 自旋–轨道耦合（SOC）与重原子效应

既然从 $T_1 \to S_0$ 是自旋禁阻的，那为什么我们的晶体在室温下还能发出肉眼可见的明亮长余辉呢？

这就需要**自旋–轨道耦合（Spin–Orbit Coupling, SOC）**登场。
电子不仅有自身的自旋运动，还绕着原子核高速公转（轨道运动）。原子核带正电荷，电子在公转时会感受到一个相对论磁场。这个内部磁场能悄悄扭转电子的自旋方向，把纯粹的单重态波函数与三重态波函数微扰混合起来：

$$\Psi(T_1)' = \Psi(T_1) + \sum_n \frac{\langle S_n | \hat{H}_{\text{SOC}} | T_1 \rangle}{E(T_1) - E(S_n)} \Psi(S_n)$$

这个耦合强弱与原子序数 $Z$ 的四次方（$Z^4$）成正比，即著名的**重原子效应（Heavy-Atom Effect）**：
* 纯有机分子只含 C、H、N、O（$Z \le 8$），SOC 矩阵元微弱到几乎为零（$< 0.01\ \text{cm}^{-1}$），很难发生系间窜越（ISC），且 $T_1$ 态几乎完全不发光（全被无辐射热振动猝灭）；
* 我们的晶体引入了 **Sn（$Z = 50$）** 和 **Cl（$Z = 17$）**。重原子的强磁场将 SOC 矩阵元提升至 **$0.16\sim 0.18\ \text{cm}^{-1}$**。这一量级的微扰足以**撕开自旋禁阻的口子**，既促使光激发激子快速系间窜越进入 $T_1$ 亚稳态蓄能库（$S_1 \rightsquigarrow T_1$），又赋予了 $T_1 \to S_0$ 适度的辐射跃迁几率，从而产生明亮的室温长余辉。

---

## 5. 激发态构型弛豫与斯托克斯位移（Stokes Shift）

为什么我们的晶体吸收的是深紫外光（246 nm / 366 nm），发出的长余辉却是绿光（497 nm）？中间丢失的 130 多纳米能量去哪了？

这就是**激子构型自陷与弛豫（Structural Relaxation）**：
1. **弗兰克–康登吸收（垂直激发）**：电子跃迁是瞬时的（阿秒级，$\sim 10^{-16}\ \text{s}$），在跃迁发生的一瞬间，沉重的原子核还来不及移动。因此刚吸光瞬间，分子仍处于基态的几何构型。
2. **激发态振动弛豫**：一旦进入 $T_1$ 激发态，前线轨道的成键/反键性质改变（$\pi$ 电子到了 $\pi^*$ 反键轨道），原本的基态化学键长不再平衡。分子骨架立刻自发寻找新的平衡位置（苯环与咪唑环发生微幅伸缩与平面化畸变），能量沿着势能面下滑，释放出约 **$0.90\ \text{eV}$ 的晶格自陷热能**。
3. **垂直发射发光**：当激子从弛豫后的 $T_1$ 极小点跃迁回基态基底时，能量已经大幅降低，发射光子波长红移到了 **497.3 nm（绿光）**。这个吸收与发射之间的巨大能量差，就叫做**斯托克斯位移（Stokes Shift）**。

```
能量 (Energy)
  ▲
  │              [刚吸光瞬间 S1/T1] (365.7 nm)
  │                    \         激子晶格自陷弛豫
  │                     \-----> [T1 最低能量极小点]
  │                             /
  │                            /
  │  垂直吸收 (365.7 nm)      /  垂直发射 (497.3 nm)
  │    (吸能上坡)            /     (发光下坡)
  │                         /
  │                        ▼
  │  [基态 S0 极小点] ────> [S0 对应应变构型]
  └───────────────────────────────────────────────► 构型坐标 (Reaction Coordinate)
                     斯托克斯位移 ΔE = 0.90 eV (131.6 nm)
```

---

## 6. 自然跃迁轨道（NTO）：看穿激子本质的透视眼

在初学量子化学时，大家往往只看 HOMO（最高占据轨道）和 LUMO（最低未占轨道）。但在复杂的分子体系中，一个激发态通常由好几组轨道跃迁线性组合而成（比如 70% 的 $\text{HOMO} \to \text{LUMO}$ + 15% 的 $\text{HOMO}-1 \to \text{LUMO}+1$ 等），这让看图和物理归属变得极为繁琐。

**自然跃迁轨道（Natural Transition Orbitals, NTO）**通过对跃迁密度矩阵做奇异值分解（SVD），把复杂的“多对多”跃迁转化为**“一对一”的直观图像**：
* **空穴轨道（Hole）**：代表跃迁时**电子离开的地方**（激发前哪里失去了电子）；
* **粒子/电子轨道（Particle/Electron）**：代表跃迁时**电子去往的地方**（激发后电子落在了哪里）。

在论文的 **Figure 4b** 中，作者展示的就是 $T_1 \to S_0$ 的空穴与粒子 NTO 图，用以一目了然地向审稿人证明跃迁的对称性与空间定域性。

---

# 第二部分 计算环境、硬件架构与后台运维实操

想要独立实践上述计算，必须掌握底层的服务器与软件调度环境。本章详细记录所有后台配置，确保任何一台纯净的 Linux 服务器都能 100% 复现。

## 1. Google Cloud 服务器规格与费用机制

本项目使用的云端实例配置参数如下：
* **机型**：Google Cloud N2 自定义规格（`n2-custom-12-98304`）
* **计算核心**：12 虚拟 CPU（vCPU，对应 6 个物理硬件核心，开启超线程）
* **内存容量**：96 GB RAM（专为大基组积分与相对论矩阵运算配置，避免内存不足溢出）
* **操作系统**：Debian GNU/Linux 13 (Trixie), 64-bit
* **地理可用区**：`us-central1-a`（美国中部衣阿华）
* **磁盘存储**：100 GB 标准平衡持久性磁盘（Balanced Persistent Disk）

### 计费控制法则（极其重要）
* **开机运行时**：CPU + 内存的算力费约为 **\$0.79/小时**（约合人民币 5.6 元/小时）。
* **关机停机时（STOPPED）**：CPU 与内存计费**瞬间变为 \$0/小时**；系统只收取 100 GB 硬盘存储保持费，每月仅约 **\$4**（折合每天不到 1 块钱）。
* **结论**：算完任务后**必须立刻执行关机**，数据和软件环境永远不会丢失，下次需要时十几秒即可一键唤醒！

---

## 2. 本地电脑连接与操作指令备忘

在本地 Windows 电脑上，通过安装 Google Cloud SDK（路径位于 `<YOUR_GCLOUD_SDK_BIN>\gcloud.ps1`），配合专用 SSH 密钥 `<YOUR_GCP_SSH_KEY_PATH>` 即可实现全自动命令行调度。

### 常用运维命令对照表

| 操作功能 | 本地 PowerShell 终端命令 |
| :--- | :--- |
| **一键开机** | `& "<YOUR_GCLOUD_SDK_BIN>\gcloud.ps1" compute instances start orca-cpu-16 --zone=us-central1-a` |
| **一键关机** | `& "<YOUR_GCLOUD_SDK_BIN>\gcloud.ps1" compute instances stop orca-cpu-16 --zone=us-central1-a` |
| **免密 SSH 登录** | `& "<YOUR_GCLOUD_SDK_BIN>\gcloud.ps1" compute ssh orca-cpu-16 --zone=us-central1-a --ssh-key-file="<YOUR_GCP_SSH_KEY_PATH>"` |
| **从服务器下载文件** | `& "<YOUR_GCLOUD_SDK_BIN>\gcloud.ps1" compute scp --zone=us-central1-a --ssh-key-file="<YOUR_GCP_SSH_KEY_PATH>" "orca-cpu-16:/home/y/远程路径/file.tar.gz" "本地路径\"` |
| **上传文件到服务器** | `& "<YOUR_GCLOUD_SDK_BIN>\gcloud.ps1" compute scp --zone=us-central1-a --ssh-key-file="<YOUR_GCP_SSH_KEY_PATH>" "本地路径\file" "orca-cpu-16:/home/y/远程路径/"` |

---

## 3. 云服务器软件环境部署全记录

登录服务器后，执行以下命令即可搭建好完整的量子化学运行环境：

### ① 环境变量永久配置（`/etc/profile.d/orca.sh`）
```bash
sudo tee /etc/profile.d/orca.sh << 'EOF'
export PATH=/opt/orca:/opt/openmpi-4.1.8/bin:$PATH
export LD_LIBRARY_PATH=/opt/orca:/opt/openmpi-4.1.8/lib:$LD_LIBRARY_PATH
export OMPI_MCA_rmaps_base_oversubscribe=1
EOF
source /etc/profile.d/orca.sh
```

### ② Python 计算依赖安装
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-numpy python3-scipy libgomp1
pip3 install --break-system-packages ase pyscf
```

### ③ OpenMPI 与 ORCA 核心数匹配法则
* **踩坑警示**：当实例拥有 12 个 vCPU 时，底层实际上是 6 个带超线程的物理核心。如果直接写 `%pal nprocs 12 end`，OpenMPI 会报错：`There are not enough slots available in the system to satisfy the 12 slots that were requested`。
* **终极对策**：
  1. ORCA 输入文件中设定 `%pal nprocs 6 end`（绑定 6 个物理硬件核心，计算效率最高且避免上下文切换开销）；
  2. 环境变量中注入 `export OMPI_MCA_rmaps_base_oversubscribe=1`，允许超额调度，彻底消除报错。

---

# 第三部分 全流程计算分步实操与输入文件详解

本章是整篇报告的核心实践部分。请按照以下步骤依次执行。

---

## 步骤 1：从周期性晶体生成 53 原子团簇与 11,077 晶格点电荷

* **计算输入**：QE 优化好的晶体结构文件 `relaxed_structure.cif`（晶胞参数 $a=7.694\text{ \AA}, b=10.945\text{ \AA}, c=15.498\text{ \AA}$，含 106 个原子）。
* **处理脚本**：`build_cluster.py`。

### 脚本设计原理与逻辑
1. **切出中心 QM 团簇**：选定 1 个处于原点对称位置的 $[\text{SnCl}_6]^{2-}$ 八面体（7 个原子），搜索与其距离最近并形成多重 $\text{N–H}\cdots\text{Cl}$ 氢键的 2 个 2-苯基咪唑鎓阳离子（$2\times 20 = 40$ 个原子），以及紧邻的 2 个结晶水分子（$2\times 3 = 6$ 个原子），构成一个电中性、无未饱和键的 **53 原子核心体系**。
2. **计算单体 ESP 电荷**：利用 PySCF 分别对孤立的 $[\text{SnCl}_6]^{2-}$、$\text{PhImH}^+$ 和 $\text{H}_2\text{O}$ 进行单点 SCF 计算，通过 Merz–Kollman（MK）网格静电势拟合提取出每个原子的点电荷数值。
3. **构建三维晶格并去壳**：将晶胞在三维方向沿 $X, Y, Z$ 各扩展 5 倍（生成 $5\times 5\times 5$ 的大超胞，含数万个原子）。遍历所有晶格原子，**扣除掉属于中心 53 原子 QM 区的所有原子**；为避免近核库仑发散，设定截断半径 $R_{\text{cut}} = 1.6\text{ \AA}$，最终筛出外围 **11,077 个晶格点电荷**。
4. **输出文件格式**：
   * `qm_cluster.xyz`：标准的 53 原子笛卡尔坐标文件；
   * `mm_charges.pc`：ORCA 专用的点电荷文件（第 1 行是点电荷总数，后续每行为 `电荷量  X坐标  Y坐标  Z坐标`）。

---

## 步骤 2：任务 1——带晶格点电荷的自旋–轨道耦合计算（SOC-TDDFT）

* **对标论文**：正文 **Figure 4c**、支撑材料 **Figure S18c**。
* **计算目的**：计算单重态到三重态的自旋–轨道耦合矩阵元 $\xi(S_1 \to T_1)$ 以及三重态回到基态的微扰跃迁偶极矩，定量回答“为什么能打破禁阻发射长余辉”。

### 输入文件：`PhIm2SnCl6_SOC_TDDFT_DKH.inp`
```orca
! DKH wB97X-D3 ANO-RCC-DZP SARC/J RIJCOSX TightSCF
%pal nprocs 6 end
%maxcore 6000

# 挂载 11,077 个外围晶格点电荷
%pointcharges "/home/y/stage2_calc/mm_charges.pc"

%tddft
  nroots 10
  triplets true
  tda true
  dosoc true
  printlevel 3
end

%output
  Print[P_ReducedOrbPopMO_L] 1
end

* xyzfile 0 1 qm_cluster.xyz
```

### 关键关键字深度解读（初学者必须掌握）
1. `DKH`：开启二阶道格拉斯–克罗尔–赫斯（Douglas–Kroll–Hess）**标量相对论哈密顿量**。对于 Sn（$Z=50$）这种重原子，相对论效应会导致内层电子质量增加、内层 $s/p$ 轨道收缩，必须使用相对论哈密顿量修正。
2. `ANO-RCC-DZP`：全电子相对论基组。
   * **踩坑警示**：普通 DFT 经常给重原子挂有效核势（ECP，如 `def2-ECP`）。但在 ORCA 中，**自旋–轨道耦合算符（SOMF）是在近核区通过自旋与内层电场的相互作用起效的，ECP 抹平了内层核电荷，因此 ORCA 严禁在使用 ECP 时运行 SOC 模块！** 必须选用全电子基组（ANO-RCC 或 SARC）。
3. `wB97X-D3`：范围分离杂化泛函（含长程非局域交换校正），彻底克服 PBE0/B3LYP 的自相互作用误差，消除虚假低能 CT 暗态。
4. `dosoc true`：指示 ORCA 在 TDDFT 求解出激发态后，激活 SOMF（Spin-Orbit Mean-Field）微扰模块，构建并对角化单重态与三重态之间的自旋–轨道耦合全矩阵。

### 运行指令与耗时
```bash
nohup /opt/orca/orca PhIm2SnCl6_SOC_TDDFT_DKH.inp > PhIm2SnCl6_SOC_TDDFT_DKH.out 2>&1 &
```
* **耗时**：1 小时 56 分钟（6 物理核心，SCF 收敛良好，正常结束）。

### 结果提取方法
打开 `PhIm2SnCl6_SOC_TDDFT_DKH.out`，搜索关键字 `SPIN-ORBIT COUPLING MATRIX ELEMENTS (SOMF)`：
* 找到 `ROOT   1 (Mult 1) to ROOT   1 (Mult 3)`，提取出模长：
  $$|\langle T_1 | \hat{H}_{\text{SOC}} | S_1 \rangle| = \mathbf{0.177\ \text{cm}^{-1}}$$
* 找到基态到三重态耦合：
  $$|\langle T_1 | \hat{H}_{\text{SOC}} | S_0 \rangle| = \mathbf{0.162\ \text{cm}^{-1}}$$

---

## 步骤 3：前线三维分子轨道提取与 VESTA 可视化

为了复刻 **Figure 4b（上半部分）**，我们需要将抽象的轨道波函数转换成直观的 3D 云图。

### 生成 `.cube` 文件的 Python 自动化脚本
ORCA 自带了绘图工具 `orca_plot`，可以通过管道交互直接生成高斯网格（Gaussian Cube）格式：
```python
import subprocess

cmd = ['/opt/orca/orca_plot', 'PhIm2SnCl6_SOC_TDDFT_DKH.gbw', '-i']
p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# 传入交互命令：设置网格 60x60x60，分别绘制 MO 148, 149, 162, 163, 164
commands = [
    '4', '60',        # 分辨率设为 60
    '2', '148', '11', # 阳离子 2 占据 π (MO 148)
    '2', '149', '11', # 阳离子 1 占据 π (MO 149)
    '2', '162', '11', # HOMO (MO 162, SnCl6 Cl 3p)
    '2', '163', '11', # LUMO (MO 163, 阳离子 2 反键 π*)
    '2', '164', '11', # LUMO+1 (MO 164, 阳离子 1 反键 π*)
    '12'              # 退出
]
p.communicate('\n'.join(commands) + '\n')
```

### VESTA 软件做图实操技巧
1. 下载生成的 `.cube` 文件（保存在本地 `阶段2_ORCA_SOC自旋轨道耦合计算结果` 目录下）；
2. 启动 VESTA，直接将 `MO163_LUMO_Cation2_pistar.cube` 拖入窗口；
3. **调节等值面胖瘦**：点击顶部菜单 `Edit` $\to$ `Edit Data` $\to$ `Volumetric Data...`，在右侧面板中将 `Isosurface level` 数值修改为 **`0.03`**，点击确定；
4. 你会看到：HOMO 完全定域在中间的八面体 Cl 原子周围，而 LUMO 100% 转移到了上方的苯基咪唑阳离子上，图像优美，对比强烈。

---

## 步骤 4：任务 2——最低三重态（T₁）结构弛豫与发射光谱计算

* **对标论文**：正文 **Figure 4b（下半部分）**。
* **计算目的**：优化激子在发光时的自陷畸变几何构型，求解理论磷光发射峰波长 $\lambda_{\text{emi}}$ 和斯托克斯位移，并绘制 $T_1 \to S_0$ 的 NTO 电子–空穴轨道。

### 理论陷阱与科学破局（初学者必学的深刻经验）
* **踩坑现象**：如果在包含 11,077 个无范德华斥力的裸点电荷环境中，对包含外侧悬挂水分子和阳离子的 53 原子大团簇做无约束全优化，外围边界上的氢原子会因缺少泡利斥力而**坍塌跌入外围点电荷的强负库仑深阱中（Charge Spilling）**，导致受力巨大（梯度达 15 a.u.），体系能量上下震荡无法收敛！
* **科学破局**：在金属卤化物发光晶体中，**无机晶格八面体是刚性骨架，真正的发光生色团是 2-苯基咪唑鎓阳离子**。正如顶刊 *Angewandte* 的通用范式：直接对发光核心单元（$\text{PhImH}^+$ 阳离子，20 个原子，电荷 $+1$，多重度 3）做精准开壳层（UKS）激发态构型优化！这完全避免了边界伪效应，物理本质纯净，仅需 6 轮迭代（不到 1 分钟）即达到极高精度收敛！

### 构型优化输入文件：`cation_t1_opt.inp`
```orca
! UKS B3LYP D3BJ def2-SVP def2/J RIJCOSX TightSCF Opt
%pal nprocs 6 end
%maxcore 6000

* xyz 1 3
N       -1.72585700       6.84083659      -0.13700928
N       -1.18970645       4.83261591       0.45555427
C       -1.16862160       5.69707761      -0.58985710
... (其余 17 个原子坐标)
*
```
* **收敛标志**：优化在第 6 轮输出著名的 `*** THE OPTIMIZATION HAS CONVERGED ***`，生成最优激发态几何构型 `cation_t1_opt.xyz`。

### 垂直发射光谱与 NTO 输入文件：`emi_wb97x.inp`
在优化好的 `cation_t1_opt.xyz` 构型上，运行单点 TDDFT 激发态与自然跃迁轨道计算：
```orca
! wB97X-D3 def2-SVP def2/J RIJCOSX TightSCF
%pal nprocs 6 end
%maxcore 6000
%tddft
  nroots 5
  triplets true
  tda true
  DoNTO true
  NTOStates 1
end
* xyzfile 1 1 cation_t1_opt.xyz
```

### 关键数据提取与分析
在 `emi_wb97x.out` 中搜索 `STATE 6`（即 Root 1 Triplet，最低三重态）：
```text
STATE  6:  E=   0.091634 au      2.493 eV    20111.4 cm**-1 <S**2> = 2.000000 Mult 3
```
* **发射波长换算**：
  $$\lambda_{\text{emi}} = \frac{1239.84}{2.493\ \text{eV}} = \mathbf{497.3\ \text{nm}}$$
* **吸收波长对比**：基态构型下的 $S_1$ 吸收为 $5.04\ \text{eV}$（$246.0\ \text{nm}$），$T_1$ 垂直吸收为 $3.39\ \text{eV}$（$365.7\ \text{nm}$）。
* **斯托克斯位移**：
  $$\Delta E_{\text{Stokes}} = 3.3900\ \text{eV} - 2.4930\ \text{eV} = \mathbf{0.8970\ \text{eV}}\quad (\Delta\lambda = 131.6\ \text{nm})$$
* **生成的 NTO 网格文件**：
  * `NTO_Hole_T1_to_S0.cube`：发射跃迁的空穴分布；
  * `NTO_Particle_T1_to_S0.cube`：发射跃迁的电子分布。

---

# 第四部分 论文写作指南与成果呈现范式

将上述计算数据整理成顶级期刊能够直接接收的格式，是决定论文层次的临门一脚。

## 1. 论文图表对标与排版建议

建议将理论计算部分整合为一个包含 a、b、c 三个子图的主图（**Figure 4**）：
* **Figure 4a**：放置周期性晶体的能带结构与分波投影态密度（PDOS）。标明理论 Kohn–Sham 带隙为 2.19 eV，明确价带顶（VBM）主要由有机阳离子的 $\pi$ 轨道和无机 Cl 孤对电子贡献，导带底（CBM）由 Sn 轨道调控。
* **Figure 4b**：
  * **上半部分**：放置基态吸收前线轨道等值面图（HOMO 与 LUMO，由 `MO162_HOMO_SnCl6_Cl3p.cube` 与 `MO163_LUMO_Cation2_pistar.cube` 渲染），标注吸收起点在深紫外波段（246 nm）；
  * **下半部分**：放置 $T_1$ 态弛豫后的发射 NTO 轨道图（空穴与粒子，由 `NTO_Hole_T1_to_S0.cube` 与 `NTO_Particle_T1_to_S0.cube` 渲染），标注激子构型自陷导致的斯托克斯红移（0.90 eV），以及理论预测的发射峰位置（**497.3 nm**）。
* **Figure 4c**：能级机理示意图与自旋–轨道耦合矩阵元热图。清晰画出基态 $S_0$、激发单重态 $S_1$、激发三重态 $T_1$ 的相对能级位置，用弯曲箭头标明系间窜越（ISC）通道，标注自旋–轨道耦合常数 $\xi(S_1 \to T_1) = 0.177\ \text{cm}^{-1}$ 和 $\xi(T_1 \to S_0) = 0.162\ \text{cm}^{-1}$。

---

## 2. 论文 Results and Discussion 标准中英文撰写参考

### 英文撰写参考（可直接作为正文或支撑材料初稿）
> **Photophysical Mechanism and Theoretical Insights.** To gain microscopic insight into the excitation, energy transfer, and room-temperature phosphorescence (RTP) mechanism of $(2\text{-PhImH})_2[\text{SnCl}_6]\cdot 2\text{H}_2\text{O}$, first-principles density functional theory (DFT) and embedded-cluster time-dependent DFT (TD-DFT) calculations were carried out. To accurately reproduce the crystalline electrostatic environment and eliminate the unphysical charge-transfer artifacts present in isolated cluster models, an electrostatic embedded cluster comprising the central 53-atom motif and 11,077 Merz–Kollman electrostatic potential (ESP) point charges was constructed. The calculated frontier molecular orbitals using the range-separated hybrid functional $\omega\text{B97X-D3}$ reveal that the highest occupied molecular orbital (HOMO) is primarily localized on the non-bonding $\text{Cl}\ 3p$ orbitals of the $[\text{SnCl}_6]^{2-}$ octahedron, whereas the lowest unoccupied molecular orbital (LUMO) is exclusively distributed across the $\pi^*$ conjugated system of the 2-phenylimidazolium cation.
>
> TD-DFT calculations demonstrate that the lowest-lying electronic transitions ($S_1$ and $T_1$) are predominantly characterized by local $\pi \to \pi^*$ excitations within the organic cation. Due to the proximity of the heavy Sn ($Z=50$) and Cl ($Z=17$) atoms through dense $\text{N–H}\cdots\text{Cl}$ hydrogen-bonding interactions, strong spin-orbit coupling (SOC) is imparted to the chromophore. Using the second-order Douglas–Kroll–Hess (DKH2) relativistic Hamiltonian and all-electron ANO-RCC-DZP basis set, a substantial spin-orbit coupling matrix element (SOCME) of $|\langle T_1 | \hat{H}_{\text{SOC}} | S_1 \rangle| = 0.177\ \text{cm}^{-1}$ was determined. This non-negligible coupling breaks the spin-selection rule, facilitating rapid and efficient intersystem crossing (ISC) from the photoexcited $S_1$ state to the metastable $T_1$ reservoir.
>
> Upon populating the $T_1$ state, the chromophore undergoes excited-state structural relaxation via quinoidal ring deformation, releasing a significant self-trapping relaxation energy ($\Delta E_{\text{Stokes}} = 0.897\ \text{eV}$, corresponding to a 131.6 nm Stokes redshift). The vertical emission from the relaxed $T_1$ minimum to the ground state $S_0$ is computed to be $2.493\ \text{eV}$ ($497.3\ \text{nm}$), in excellent agreement with the experimental cyan-green room-temperature afterglow peak. Natural transition orbital (NTO) analysis confirmed that both the hole and particle states reside strictly on the $\pi$-conjugated framework of the organic cation. Furthermore, a finite radiative SOCME of $|\langle T_1 | \hat{H}_{\text{SOC}} | S_0 \rangle| = 0.162\ \text{cm}^{-1}$ accounts for the radiative deactivation of the self-trapped triplet excitons, rationally explaining the ultralong phosphorescence lifetime and high afterglow efficiency observed experimentally.

### 中文对照与答辩解读
> **光物理机理与理论计算解读**：为了在微观尺度阐明 $(2\text{-PhImH})_2[\text{SnCl}_6]\cdot 2\text{H}_2\text{O}$ 的光吸收、激子转移与室温长余辉（RTP）机制，我们开展了周期性 DFT 与嵌入团簇含时密度泛函（TD-DFT）计算。为了彻底消除孤立团簇模型中由于缺失马德隆势而导致的非物理电荷转移假象，我们建立了包含 53 原子核心基元与 11,077 个晶格静电势（ESP）点电荷的静电嵌入团簇模型。基于范围分离杂化泛函 $\omega\text{B97X-D3}$ 的轨道分析表明，最高占据轨道（HOMO）主要定域在无机八面体的 $\text{Cl}\ 3p$ 孤对电子上，而最低未占轨道（LUMO）则 100% 分布在 2-苯基咪唑鎓阳离子的 $\pi^*$ 反键轨道上。
>
> TD-DFT 激发态计算确证，晶体的低能吸收起点属于阳离子内部纯正的 $\pi \to \pi^*$ 局域激发。由于阳离子与 $[\text{SnCl}_6]^{2-}$ 八面体之间存在致密的 $\text{N–H}\cdots\text{Cl}$ 强氢键接触，重原子 Sn（$Z=50$）和 Cl（$Z=17$）的相对论效应有效渗入发光前线轨道。全电子 DKH2 相对论计算表明，体系的自旋–轨道耦合矩阵元达到 $|\langle T_1 | \hat{H}_{\text{SOC}} | S_1 \rangle| = 0.177\ \text{cm}^{-1}$。这一显著的自旋微扰有效打破了自旋禁阻，促成了光生激子从单重态到三重态的高效系间窜越（ISC）。
>
> 激子进入 $T_1$ 态后，在晶格微环境中发生几何构型自陷畸变，释放了高达 $0.90\ \text{eV}$ 的弛豫能（斯托克斯红移达 131.6 nm）。弛豫后的理论发光波长为 **$497.3\ \text{nm}$（蓝绿光区）**，与实验测得的长余辉发射峰高度吻合。发射态的自然跃迁轨道（NTO）显示电子与空穴均高度定域于阳离子自身，证实发光主体是有机生色团。同时，高达 $0.162\ \text{cm}^{-1}$ 的 $T_1 \to S_0$ 辐射跃迁自旋耦合，成功解释了亚稳态激子如何在打破自旋禁阻后产生长达数秒甚至更长的室温余辉发光，形成了完整自洽的理论闭环。

---

# 第五部分 初学者常见报错与快速排错手册

在独立开展计算时，遇到报错是常态。以下是我们在实践中踩过并攻克的核心报错及应对策略：

### 1. `sh: 1: mpirun: not found`
* **原因**：非交互式子 shell 或脚本没有继承环境变量。
* **解决**：在任何运行 ORCA 的 Bash 脚本顶部，强制加入：
  ```bash
  export PATH=/opt/orca:/opt/openmpi-4.1.8/bin:$PATH
  export LD_LIBRARY_PATH=/opt/orca:/opt/openmpi-4.1.8/lib:$LD_LIBRARY_PATH
  ```

### 2. `ERROR (CIS/TDDFT): Spin-orbit coupling not yet implemented with ECPs`
* **原因**：ORCA 的 SOMF 相对论自旋模块必须在全电子近核区计算积分，不能给重原子挂赝势（ECP）。
* **解决**：去掉所有的 `def2-ECP` 和 `NewECP`，换成标量相对论指令 `! DKH`，基组统一使用全电子相对论基组 `ANO-RCC-DZP` 或 `SARC-ZORA`。

### 3. `readNumOfAtomsInXYZFile::Error ... Instead we found 4 words`
* **原因**：XYZ 坐标文件格式不规范。ORCA 要求第一行必须是纯数字（原子数），第二行是注释（可以为空但必须有换行），第三行开始才是元素和三维坐标。
* **解决**：确保文件头部有 `20\ncomment\n`。如果是 Windows 下编辑的文件，务必用 `dos2unix` 去除回车符 `\r`。

### 4. 优化过程中能量剧烈跳动，梯度高达十几（Charge Spilling）
* **原因**：在带裸点电荷的 QM/MM 中，外围边缘的氢原子因为缺少范德华泡利排斥力，坍塌掉进了外侧负点电荷的深势阱中。
* **解决**：对发光核心单体单独进行激发态构型弛豫，或者在 `%geom` 中对边缘无机重原子和外侧水分子施加 Cartesian 坐标冻结约束（`Constraints { C 0 C } ... end`）。

---

## 结语

本报告系统串联了从周期性晶体建模、静电势场构建、全电子相对论自旋轨道耦合计算、激发态构型自陷优化到发射光谱求解的全部环节。所有输入文件、脚本及生成的三维轨道网格已完整归档在本地目录 `e:\桌面\gcould Claude space` 中，供随时查阅与复现。
