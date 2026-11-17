#!/bin/bash
source /etc/profile.d/orca.sh
cd ~/phim
{
echo "! PBE0 D3BJ def2-SVP def2/J RIJCOSX TightSCF"
echo "%pal nprocs 6 end"
echo "%maxcore 6000"
echo "%output"
echo " Print[P_ReducedOrbPopMO_L] 1"
echo "end"
echo "* xyzfile 0 1 phim_opt.xyz"
} > pop.inp
/opt/orca/orca pop.inp > pop.out 2>&1
{
echo "! wB97X-D3 def2-SVP def2/J RIJCOSX TightSCF"
echo "%pal nprocs 6 end"
echo "%maxcore 6000"
echo "%tddft"
echo " nroots 15"
echo " tda false"
echo "end"
echo "%output"
echo " Print[P_ReducedOrbPopMO_L] 1"
echo "end"
echo "* xyzfile 0 1 phim_opt.xyz"
} > wb_td.inp
/opt/orca/orca wb_td.inp > wb_td.out 2>&1
