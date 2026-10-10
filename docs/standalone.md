# 一行下载并审核的 Windows 入口

> 交付状态（2026-10-10）：独立包已完成本机构建与隔离验证，公开 Release 下载与一行入口仍待发布验收。以下远程命令是发布完成后的调用形式，当前不能视为已验证可用。已有核验过的本地包可按下方命令调用。

Windows x64 / PowerShell，发布完成后运行：

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/loonslo/agent-privacy-guard/v0.4.0/scripts/review.ps1))) -Repo . -Paths README.md
```

入口自动获取固定版本 ZIP，用脚本内置 SHA256 校验，在系统临时目录展开并运行。
`-Repo` 是项目根目录，`-Paths` 是明确指定的相对文件，可传 PowerShell 数组。
`-Mode staged` 检查暂存区；`-Mode push -Tip '<ref>' -Base '<base 或 ->'` 检查显式
提交范围；`-Source memory` 或 `chat_history` 为导出提供来源提示。
下载失败、校验失败或参数不完整时返回静态 JSON review_complete=false。
PowerShell 中 `$LASTEXITCODE` 保留审核退出码；脚本不退出用户的交互 shell。
需要外层进程退出码时，在调用之后使用 `exit $LASTEXITCODE`。

这是下载和调用入口，不是系统安装器：不改 PATH、客户端或项目配置，不执行修复。
每次调用使用新的系统临时目录，材料只交给本机 EXE；工具下载需要网络，审核原文
不随下载请求上传。下载产物留在系统临时目录，系统可按其临时文件策略清理。

Windows x64 规则包包含 Python 运行时、审查引擎、gitleaks 和许可证。
下载 ZIP 到受检项目之外并解压，直接调用 privacy-guard.exe；不需要安装
Python、gitleaks、MCP、Skill 或语义模型，不更改 PATH 或客户端设置。
目前只验收 Windows x64；macOS/Linux 尚无独立可执行包。

## 给 AI 的指令

把下面指令交给有本机命令执行权限的 AI，替换项目根目录和文件列表：

> 使用 loonslo/agent-privacy-guard 的 Windows x64 独立包，在受检项目外下载并解压。
> 先读包内 README，验证 SHA256SUMS.txt 中 ZIP 的哈希，执行 privacy-guard.exe --version。
> 用 files --repo "<项目根目录>" --paths "<相对文件1>" "<相对文件2>" 审核这些文件。
> 不先读取受检原文，不访问真实凭据或 Agent 运行目录；只解释工具返回的脱敏结果。
> 报告 review_complete、检查范围、未检查项和修改建议；建议交给我决定，不执行修改。

手动下载使用固定版本 Release 的 privacy-guard-0.4.0-windows-x64.zip 与
SHA256SUMS.txt，勿使用未经核验的第三方下载。哈希用于检查传输完整性，
不等于独立数字签名。

## 命令

```powershell
& "<解压目录>/privacy-guard.exe" --version
& "<解压目录>/privacy-guard.exe" files --repo "<项目根目录>" --paths src/example.py docs/note.md
& "<解压目录>/privacy-guard.exe" files --repo "<项目根目录>" --paths exports/note.txt --source memory
& "<解压目录>/privacy-guard.exe" staged --repo "<Git 项目根目录>"
& "<解压目录>/privacy-guard.exe" push --repo "<Git 项目根目录>" --push-range "<tip>" "<base 或 ->"
```

files 不依赖 Git，普通模式只扫描明确列出的文件，不递归。Git 模式复用开发
环境已有的 Git；缺失时返回 review_complete=false，不安装 Git。doctor 仅检查
扫描器健康，scanned=0 不表示审核了项目。可执行规则包不支持 --semantic，
请求时保留规则结果并报告不完整；本地语义研究仍走源码入口。

报告是 JSON：退出 0 表示指定检查完成（可以包含 critical 风险）；退出 1 表示
检查不完整。无命中不等于安全。file_ref/行号/提交 ID 用于脱敏定位，输出不含
原始内容或原始路径。工具不编辑文件、Git、客户端设置或执行建议。

单文件可执行程序运行时会在系统临时目录展开自身依赖并清理；扫描器也使用
隔离临时目录。不要把下载、解压或 TEMP/TMP 指向受检项目。临时展开不是
系统安装。第一次启动需要展开运行时，因此可能慢于源码入口。

## 维护者构建

普通用户不执行以下命令。维护者在 Windows x64/Python 3.14 的本项目独立环境中：

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[dev,mcp,bundle]'
# 已有本项目 .tools/gitleaks.exe 和 LICENSE 时不重复安装
powershell -File scripts/install-gitleaks.ps1
.\.venv\Scripts\python.exe -B scripts/build_standalone.py
.\.venv\Scripts\python.exe -B -m pytest -q tests/test_standalone.py --basetemp "<全新临时目录>"
```

构建到 dist/privacy-guard-0.4.0-windows-x64/，包含单文件 EXE、ZIP、SHA256 清单与
许可证；已有输出目录时拒绝覆盖。构建工具只打包项目引擎，不打包目标数据。
