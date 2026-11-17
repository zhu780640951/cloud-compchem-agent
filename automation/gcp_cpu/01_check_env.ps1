# 第一步：只读检查，不改动虚拟机上的任何文件
. "$PSScriptRoot\_common.ps1"
Start-Log 'check_env'
Log "本地阶段3文件夹：$Stage3Local"
Ensure-Running
Invoke-Remote 'echo ==host; hostname; uptime; echo cores: $(nproc); free -g | head -2; df -h /home | tail -1; echo ==orca; ls -l /opt/orca/orca; source /etc/profile.d/orca.sh 2>/dev/null; which mpirun; mpirun --version 2>&1 | head -1; echo ==python; python3 --version; echo ==running; pgrep -af orca || echo none; echo ==home; ls -la ~; echo ==stage3; ls -la ~/stage3 2>/dev/null || echo stage3-not-present'
Close-Log
