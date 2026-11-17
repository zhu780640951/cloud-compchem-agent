# 启动指定批次的计算。用法示例：
#   powershell -ExecutionPolicy Bypass -File 06_run_steps.ps1 -Steps "01c 02a 02b"
#   powershell -ExecutionPolicy Bypass -File 06_run_steps.ps1 -Steps "04b 04c" -T1 CatB
param([Parameter(Mandatory=$true)][string]$Steps, [string]$T1 = '')
. "$PSScriptRoot\_common.ps1"
Start-Log 'run_steps'
Ensure-Running
$envT1 = ''
if ($T1) { $envT1 = "T1=$T1 " }
$cmd = "cd ~/stage3 || exit; if pgrep -f '^bash run_all' >/dev/null; then echo BUSY-run_all-still-running; exit; fi; ($envT1" + "setsid nohup bash run_all.sh $Steps > run.log 2>&1 < /dev/null &); sleep 5; tail -3 progress.log"
Invoke-Remote $cmd
Close-Log
