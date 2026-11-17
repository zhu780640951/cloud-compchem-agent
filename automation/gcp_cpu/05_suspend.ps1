# 挂起实例（先确认没有计算在跑）。想彻底关机省内存费用：加参数 -Stop
param([switch]$Stop)
. "$PSScriptRoot\_common.ps1"
Start-Log 'suspend'
Invoke-Remote 'pgrep -af ''^/opt/orca/orca'' && echo WARNING-ORCA-STILL-RUNNING || echo no-orca-running'
if ((Get-Content $script:LogFile -Raw) -match '(?m)^WARNING-ORCA-STILL-RUNNING\s*$') { Log 'ORCA 仍在运行，未挂起。'; Close-Log; exit }
if ($Stop) { & $G compute instances stop $INST --zone=$ZONE --project=$PROJ --quiet 2>&1 | ForEach-Object { Log "$_" } }
else { & $G compute instances suspend $INST --zone=$ZONE --project=$PROJ --quiet 2>&1 | ForEach-Object { Log "$_" } }
Log "现在状态：$(Get-Status)"
Close-Log
