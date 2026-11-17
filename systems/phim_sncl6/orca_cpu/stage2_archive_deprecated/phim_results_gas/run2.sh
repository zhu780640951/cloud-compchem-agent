#!/bin/bash
source /etc/profile.d/orca.sh
cd ~/phim
awk 'NR>4 && $1!="*"' phim_sncl6.inp > coords.txt
awk 'NR>4 && $1!="*" && $1!="H"{printf "  {C %d C}\n",NR-5}' phim_sncl6.inp > cons.txt
{
echo "! PBE0 D3BJ def2-SVP def2/J RIJCOSX TightSCF Opt"
echo "%pal nprocs 6 end"
echo "%maxcore 6000"
echo "%geom"
echo " MaxIter 150"
echo " Constraints"
cat cons.txt
echo " end"
echo "end"
echo "* xyz 0 1"
cat coords.txt
echo "*"
} > phim_opt.inp
/opt/orca/orca phim_opt.inp > phim_opt.out 2>&1
{
echo "! PBE0 D3BJ def2-SVP def2/J RIJCOSX TightSCF"
echo "%pal nprocs 6 end"
echo "%maxcore 6000"
echo "%tddft"
echo " nroots 15"
echo " tda false"
echo "end"
echo "* xyzfile 0 1 phim_opt.xyz"
} > phim_td.inp
/opt/orca/orca phim_td.inp > phim_td.out 2>&1
