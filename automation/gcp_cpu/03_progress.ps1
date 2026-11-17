# 随时可运行：查看进度和所有已完成任务的摘要
. "$PSScriptRoot\_common.ps1"
Start-Log 'progress'
Log "实例状态：$(Get-Status)"
Invoke-Remote 'cd ~/stage3 2>/dev/null || exit; uptime; echo ==progress; cat progress.log; echo ==running; pgrep -af orca_ || echo none; for f in jobs/*/*.summary.txt; do echo; echo ==== $f; cat $f; done; echo ==run.log-tail; tail -5 run.log'
Close-Log
