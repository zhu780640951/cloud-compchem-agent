# 把一个本地文件上传到虚拟机 ~/stage3/（先复制到纯英文临时目录，避开 pscp 的中文路径问题）
# 用法：powershell -ExecutionPolicy Bypass -File 07_upload_file.ps1 -Name 04a2_T1opt_UKS_free_CatA.inp
param([Parameter(Mandatory=$true)][string]$Name)
. "$PSScriptRoot\_common.ps1"
Start-Log 'upload_file'
Ensure-Running
$Src = Join-Path $Stage3Local $Name
if (-not (Test-Path $Src)) { Log "找不到 $Src"; Close-Log; exit }
$Tmp = Join-Path $env:TEMP $Name
Copy-Item $Src $Tmp -Force
& $G compute scp --zone=$ZONE --project=$PROJ "--ssh-key-file=$KEY" --quiet "$Tmp" "${INST}:/home/y/stage3/" 2>&1 | ForEach-Object { Log "$_" }
Invoke-Remote "sed -i s/\\r$// ~/stage3/$Name; ls -l ~/stage3/$Name; head -3 ~/stage3/$Name"
Close-Log
