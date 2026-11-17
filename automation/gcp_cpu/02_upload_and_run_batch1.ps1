# 第二步：上传阶段3文件夹，启动第一批（00 01a 01b，约 15 分钟）
. "$PSScriptRoot\_common.ps1"
Start-Log 'batch1'
Ensure-Running
Invoke-Remote 'if [ -d ~/stage3 ]; then mv ~/stage3 ~/stage3_bak_$(date +%m%d_%H%M); echo old-stage3-moved; fi'
Log "`n>>> 上传 $Stage3Local -> /home/y/stage3"
$Up = Join-Path $env:TEMP ('stage3_up_' + (Get-Date -Format 'yyyyMMdd_HHmmss')); New-Item -ItemType Directory -Force -Path $Up | Out-Null; Copy-Item $Stage3Local (Join-Path $Up 'stage3') -Recurse; & $G compute scp --recurse --zone=$ZONE --project=$PROJ "--ssh-key-file=$KEY" --quiet (Join-Path $Up 'stage3') "${INST}:/home/y/" 2>&1 | ForEach-Object { Log "$_" }
Invoke-Remote 'cd ~/stage3 && sed -i s/\\r$// run_all.sh *.inp analyze_orca.py && ls && (setsid nohup bash run_all.sh 00 01a 01b > run.log 2>&1 < /dev/null &) ; sleep 5; cat ~/stage3/progress.log'
Close-Log
