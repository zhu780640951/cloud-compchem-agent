# Colab 官方 CLI 连接测试报告

日期：2026-10-30；测试运行时间约香港时间 13:41:53–13:42:10。

## 结果

官方 Colab CLI/客户端的认证、运行时管理、远程 Python 执行、GPU 计算和文件往返通过实测。QE 软件本身尚未验证。

- 本机：Python 3.12.10，google-colab-cli 0.7.5，项目独立虚拟环境。
- Colab 账号：<YOUR_COLAB_EMAIL>，由用户在 Google 官方浏览器页面完成授权；ADC 保存于项目独立配置目录。CPU 使用的原 gcloud 登录配置保持独立。
- 本地 version、--help 与授权后的 sessions 命令通过。虽然官方 README 仍标注 Windows 不受支持，本次所用连接和执行路径在本机实测成功。
- 测试前该账号没有活跃运行时，计算单元余额约 53.64。
- 本轮创建一个临时 Tesla T4 运行时，显存 15360 MiB；没有创建 A100，也没有执行正式晶体计算。
- nvidia-smi 正常返回；测试开始时 GPU 进程为空。
- torch.cuda.is_available() 返回 True；GPU 上 0–1023 的整数求和结果 523776，正确。
- 输入 JSON 上传成功，远端 Python 读取并处理，输出 JSON 下载到本地；往返测试标记一致。
- 临时运行时已释放，随后 API 查询与官方 CLI sessions 均确认活跃运行时为 0。
- 即时余额查询前后均约 53.64；该接口的即时结果不是最终计费凭据。

## QE 的状态

在这个新建的临时运行时的 PATH、/content、/opt、/usr/local 的有限深度搜索中没有发现 pw.x。该结果只描述本次新环境，不代表用户原有 Notebook 或 Drive 中没有 QE。后续需定位并恢复原有 QE 安装/编译环境，再进行实际 GPU 版 QE 的微型 SCF 测试。本轮没有安装 QE。

本轮通过官方运行时 API 与 Jupyter 通道完成执行和传输，没有进行独立的 colab ssh 握手测试。现有证据已支持命令行下发脚本、运行 shell 子进程、查询 GPU 和回收结果；不能把它写成已验证所有 SSH 功能。

## 证据与复用

- colab_gpu_smoke_test.py：实际测试脚本；结尾释放本轮创建的运行时。
- colab_gpu_smoke_test.json：运行时生命周期与各项测试结果。
- colab_gpu_remote_result.json：从 GPU 运行时取回的诊断文件。
- colab_roundtrip_input.json：文件往返测试输入。
- colab_cli_sessions_after.log：释放后的官方 CLI 查询。
- 连接配置/Colab.cmd：项目专用 CLI 入口，例如 Colab.cmd sessions 或 Colab.cmd usage。

较早的 colab_existing_login_probe.json / colab_account_probe.json 查询的是 <YOUR_GCP_EMAIL>；用户确认这不是 Colab Pro 账号，该组结果不用于描述 Colab Pro 状态。

后续正式计算的输入、脚本、任务日志和结果仍归档在本项目文件夹。当前没有正式计算任务，也没有建立定时后台监控。