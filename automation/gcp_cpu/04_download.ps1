# 下载 jobs 文件夹、progress.log 和 T1 结构到本地阶段3文件夹
# 远程先打成一个 tar.gz（排除 ORCA 临时文件 *tmp*），压缩传输后在本地解压
. "$PSScriptRoot\_common.ps1"
Start-Log 'download'
Log "`n>>> 下载到 $Stage3Local"
Invoke-Remote 'cd ~/stage3 && tar -czf ~/stage3_dl.tar.gz --exclude=''*tmp*'' jobs progress.log $(ls T1_geom_*.xyz 2>/dev/null) && ls -lh ~/stage3_dl.tar.gz'
# pscp 无法写入含中文的本地路径：先下载到纯英文临时目录，再复制过去
$Dl = Join-Path $env:TEMP ('stage3_dl_' + (Get-Date -Format 'yyyyMMdd_HHmmss')); New-Item -ItemType Directory -Force -Path $Dl | Out-Null
& $G compute scp --compress --zone=$ZONE --project=$PROJ "--ssh-key-file=$KEY" --quiet "${INST}:/home/y/stage3_dl.tar.gz" "$Dl" 2>&1 | ForEach-Object { Log "$_" }
$Tgz = Join-Path $Dl 'stage3_dl.tar.gz'
if (-not (Test-Path $Tgz)) { Log '下载失败：本地没有 stage3_dl.tar.gz'; Close-Log; exit }
& "$env:SystemRoot\System32\tar.exe" -xzf $Tgz -C $Dl 2>&1 | ForEach-Object { Log "$_" }
New-Item -ItemType Directory -Force -Path (Join-Path $Stage3Local 'jobs') | Out-Null
Copy-Item (Join-Path $Dl 'jobs\*') (Join-Path $Stage3Local 'jobs') -Recurse -Force
Copy-Item (Join-Path $Dl 'progress.log') $Stage3Local -Force
Get-ChildItem $Dl -Filter 'T1_geom_*.xyz' | Copy-Item -Destination $Stage3Local -Force
Log (Get-ChildItem (Join-Path $Stage3Local 'jobs') -Recurse -File | Measure-Object Length -Sum | ForEach-Object { "已下载 {0} 个文件，{1:N1} MB" -f $_.Count, ($_.Sum/1MB) })
Close-Log
