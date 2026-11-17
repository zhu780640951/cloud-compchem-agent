# 只下载指定的远程路径（相对 ~/stage3），排除大的中间文件；解压到本地阶段3文件夹
# 用法：powershell -ExecutionPolicy Bypass -File 08_download_new.ps1 -Paths "jobs/04c2_SOC_ZORA_at_T1geom_CatA cubes progress.log"
param([Parameter(Mandatory=$true)][string]$Paths)
. "$PSScriptRoot\_common.ps1"
Start-Log 'download_new'
Ensure-Running
Invoke-Remote "cd ~/stage3 && tar -czf ~/stage3_new.tar.gz --exclude=*tmp* --exclude=*.bas? --exclude=*.densities --exclude=*.cis --exclude=*.TDDFTGuess.gbw $Paths && ls -lh ~/stage3_new.tar.gz"
$Dl = Join-Path $env:TEMP ('stage3_new_' + (Get-Date -Format 'yyyyMMdd_HHmmss')); New-Item -ItemType Directory -Force -Path $Dl | Out-Null
& $G compute scp --compress --zone=$ZONE --project=$PROJ "--ssh-key-file=$KEY" --quiet "${INST}:/home/y/stage3_new.tar.gz" "$Dl" 2>&1 | Where-Object { $_ -notmatch '\| +[0-9]+ kB' } | ForEach-Object { Log "$_" }
$Tgz = Join-Path $Dl 'stage3_new.tar.gz'
if (-not (Test-Path $Tgz)) { Log '下载失败：本地没有 stage3_new.tar.gz'; Close-Log; exit }
& "$env:SystemRoot\System32\tar.exe" -xzf $Tgz -C $Dl 2>&1 | ForEach-Object { Log "$_" }
Remove-Item $Tgz
Copy-Item (Join-Path $Dl '*') $Stage3Local -Recurse -Force
Log ("已解压到 $Stage3Local ：" + ((Get-ChildItem $Dl -Recurse -File | Measure-Object).Count) + " 个文件")
Close-Log
