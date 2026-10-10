# v0.4.0 一行下载并审核

AI 基础文件审核不再需要用户分别准备 Python 和 gitleaks：新增 Windows x64
独立 ZIP，包含 privacy-guard.exe、使用说明和许可证；直接运行即可得到脱敏风险
和修改建议。无需 MCP 登记、Skill 安装或语义模型。

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/loonslo/agent-privacy-guard/v0.4.0/scripts/review.ps1))) -Repo . -Paths README.md
```

把 -Repo 替换为项目根目录，-Paths 替换为指定的相对文件。入口自动下载固定版本包，
按脚本内置 SHA256 校验并在系统临时目录展开；下载、校验或审核失败报告不完整。
ZIP 是命令内部使用的交付材料，也保留手动下载供离线使用。

下载/解压目录应在受检项目之外。使用随附 SHA256SUMS.txt 验证 ZIP。
Git 暂存区和历史审核复用环境已有 Git；缺失时明确检查不完整。独立包只提供规则
审核，不支持 --semantic；本地语义研究继续使用源码入口。

验证：Windows x64/Python 3.14 构建；100 项全量测试通过，最终包另跑 7 项通过。
单 EXE 在清空 PATH 的隔离环境中完成合成文件审核；脱敏输出和目标文件/Git
状态不变通过。新增启动入口下载替身测试 7 项通过。
尚未验收：真实无 Python 新机器、其他平台和 CI。
结果为建议，工具不修改项目、不安装 hook、不执行修复；无命中不等于安全。

发布对象：loonslo/agent-privacy-guard，tag v0.4.0，源码分支
codex/initial-implementation。资产：privacy-guard-0.4.0-windows-x64.zip
及 SHA256SUMS.txt。实际发布时间与公开调用核验记录以 docs/acceptance.md 为准。
