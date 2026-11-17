#!/bin/bash
# 在虚拟机 ~/stage3 下运行：bash make_cubes.sh
# 为论文配图生成 Gaussian cube 文件，统一放到 ~/stage3/cubes/
source /etc/profile.d/orca.sh 2>/dev/null
P=/opt/orca/orca_plot
OUT=~/stage3/cubes; mkdir -p $OUT
mo () {  # 用法: mo <作业目录> <gbw或nto文件> <轨道号> <a或b>
  local d=$1 f=$2 n=$3 s=$4 op=0; [ "$s" = b ] && op=1
  ( cd ~/stage3/jobs/$d && printf '1\n1\n3\n%d\n2\n%d\n4\n80\n11\n12\n' $op $n | $P $f -i > /dev/null 2>&1 )
  local c=$(ls -t ~/stage3/jobs/$d/*mo${n}${s}.cube 2>/dev/null | head -1)
  if [ -n "$c" ]; then cp "$c" "$OUT/${d}__$(basename $c)"; echo "OK   $d $f MO$n$s"; else echo "FAIL $d $f MO$n$s"; fi
}
# 1) 基态前线轨道（嵌入团簇，TZVP）：H-2 H-1 HOMO LUMO L+1 L+2
for n in 146 147 148 149 150 151; do mo 01c_S0_wB97X_TZVP_PC 01c_S0_wB97X_TZVP_PC.gbw $n a; done
# 2) 气相对照（轨道顺序反转）：HOMO LUMO
for n in 148 149; do mo 01b_S0_wB97X_SVP_gas 01b_S0_wB97X_SVP_gas.gbw $n a; done
# 3) T1 结构上的两个单占据轨道（UKS，alpha 148、149）
for n in 148 149; do mo 04a2_T1opt_UKS_free_CatA 04a2_T1opt_UKS_free_CatA.gbw $n a; done
# 4) S1 的自然跃迁轨道（空穴 148、电子 149），基态结构与 T1 结构各一组
for n in 148 149; do mo 02b_TDA_wB97X_TZVP_PC 02b_TDA_wB97X_TZVP_PC.s1.nto $n a; done
for n in 148 149; do mo 04c_TDA_at_T1geom_CatA 04c_TDA_at_T1geom.s1.nto $n a; done
# 5) 导出 molden 文件，供本地 Multiwfn 做全部单/三重态的 NTO 与空穴-电子分析
for j in 02b_TDA_wB97X_TZVP_PC:02b_TDA_wB97X_TZVP_PC 04c_TDA_at_T1geom_CatA:04c_TDA_at_T1geom 04c2_SOC_ZORA_at_T1geom_CatA:04c2_SOC_ZORA_at_T1geom; do
  d=${j%%:*}; b=${j##*:}
  ( cd ~/stage3/jobs/$d && /opt/orca/orca_2mkl $b -molden > /dev/null 2>&1 )
  if [ -f ~/stage3/jobs/$d/$b.molden.input ]; then cp ~/stage3/jobs/$d/$b.molden.input $OUT/; cp ~/stage3/jobs/$d/$b.out $OUT/; echo "OK   molden $b"; else echo "FAIL molden $b"; fi
done
ls -la $OUT; tar -czf ~/stage3/cubes.tar.gz -C ~/stage3 cubes && ls -lh ~/stage3/cubes.tar.gz
