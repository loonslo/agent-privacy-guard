# Privacy Review · Agent Privacy Guard

**在分享文件、导出 AI 记忆或推送代码之前，用本机规则检查隐私风险，再把脱敏的修改建议交给用户。**

AI 帮你整理的代码、笔记和对话，可能同时带上硬编码密钥、联系方式、本机路径或不适合公开的历史信息。本项目提供一个可以由你直接运行、也可以由有本机执行权限的 AI 调用的审查工具：你指定材料，它检查风险，返回位置和建议，由你决定怎么处理。

当前版本为 **v0.4.0，只读建议模式（advisory）**。审查流程在交付建议后结束；工具不修改文件、不自动修复、不提交或推送，也不安装 hook 或修改客户端设置。

> **交付状态（2026-10-10）**：Windows x64 独立规则包已完成本机构建与隔离验证，包含运行时和密钥扫描器，基础文件审核无需另装 Python、MCP、Skill 或模型。公开 Release 下载与一行入口仍待发布验收。源码 ZIP 不含可执行包。其他平台独立包、真正无 Python 的新机器及真实语义模型效果尚未验收。

## 什么情况下用它

| 你准备做的事 | 选择的检查 | 能帮助你发现什么 |
| --- | --- | --- |
| 分享几份代码、文档或笔记 | `files`，明确列出相对文件 | 疑似密钥、部分个人信息、正文中的本机路径 |
| 分享 Agent Memory 导出 | `files --source memory` | 记忆来源风险，以及导出正文中的规则命中 |
| 分享聊天记录导出 | `files --source chat_history` | 聊天来源风险，以及正文中的规则命中 |
| 提交已经暂存的改动 | `staged` | Git 暂存区实际内容中的风险 |
| 推送分支或一组提交 | `push`，指定本机 tip/base | 范围内提交的内容和提交消息，包括加入后又删除的敏感内容 |

例如：你已从当前代码中删掉密钥，但准备推送的历史提交还保留着它。只检查当前文件可能看不到这段历史；指定提交范围的 `push` 检查可以覆盖它。另一种情况是，你编辑了文件却还没重新暂存，`staged` 检查的是 index 中将要提交的版本，而非编辑器里的最新版本。

它适合在一次明确的分享或提交之前调用。指定文件模式不会递归扫描整个项目，工具也不会持续监控 AI、自动接管所有外发行为。

## 一次检查怎样进行

```text
你指定项目与文件 / 暂存区 / 本机提交范围
                    ↓
本机引擎先校验读取范围，凭据与 Agent 运行路径不读正文
                    ↓
对可检查内容运行路径、个人信息、来源与 gitleaks 密钥规则
                    ↓
返回 JSON：是否检查完整、风险、哈希位置、建议、未检查项
                    ↓
你复核建议，自行决定是否另行让 AI 修改，然后重新检查
```

CLI、Skill、MCP 是同一套本机规则的不同调用入口。Skill 告诉 AI 如何调用与解释结果；MCP 让客户端把审查当作工具调用；基础检查无需语义模型。

**数据在哪里处理？** 受检原文在本机规则引擎和本机扫描器内处理，本工具不调用云端语义服务。报告不回显原文、密钥、PII 或原始文件路径，只包含静态规则、行号、哈希定位和建议。若通过 MCP 接入，宿主会收到脱敏报告，也可能将报告放入其模型上下文。

只读指受检项目保持不变。程序运行和扫描器会使用系统临时目录；下载、解压及 `TEMP/TMP` 应位于受检项目之外。

## 开始使用

### 已有 Windows x64 独立包

将核验过的包解压到受检项目之外，在 PowerShell 中调用。把 `<工具目录>`、`<项目根目录>` 和文件列表换成你的实际范围：

```powershell
& "<工具目录>/privacy-guard.exe" --version
& "<工具目录>/privacy-guard.exe" files --repo "<项目根目录>" --paths src/example.py docs/note.md
```

`--repo` 决定检查根目录；`--paths` 只接受根目录内的相对文件，建议统一使用 `/`。普通文件审核不要求项目是 Git 仓库；Git 模式需要已有 Git，缺失时返回检查不完整。

你也可以把下面指令交给有本机命令执行权限的 AI，填好范围：

> 使用 agent-privacy-guard 审查 `<项目根目录>` 中的 `src/example.py` 和 `docs/note.md`。
> 使用已有且核验过的 Windows x64 独立包；没有包时先说明入口与发布状态。
> 不先读取受检原文，不访问真实凭据或 Agent 运行目录；让本机工具执行检查。
> 说明 review_complete、检查范围、风险、哈希位置、未检查项和修改建议。
> 将建议交给我决定，本次不执行修改。

完整的包使用与构建说明见 [独立包说明](docs/standalone.md)。

### 一行下载入口（准备中）

已有入口设计会下载固定版本 ZIP、按脚本内置 SHA256 核验，再在系统临时目录展开运行。**以下是发布完成后的调用形式，当前尚不能作为已验证的快速开始命令**：

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/loonslo/agent-privacy-guard/v0.4.0/scripts/review.ps1))) -Repo . -Paths README.md
```

其中 `-Repo .` 表示当前项目，`-Paths` 是明确文件列表。仍需验收脚本和 ZIP 的公开下载与首次调用。工具下载需要网络，受检原文不随下载请求上传。入口面向 Windows x64 / PowerShell。

### 从源码运行

源码入口需要 **Python 3.14+ 和本机 gitleaks**。在本项目根目录运行；Python 解释器必须满足项目版本要求：

```powershell
py -3 -B -m privacy_guard doctor
py -3 -B -m privacy_guard files --repo "<项目根目录>" --paths src/example.py docs/note.md
```

扫描器可以位于本项目 `.tools`、系统 PATH，或通过 `PRIVACY_GUARD_GITLEAKS` 指定。没有扫描器时，报告会标明不完整；用户可自行选择运行 `scripts/install-gitleaks.ps1` 准备本项目扫描器。`doctor` 只做扫描器自检，`scanned=0` 不表示检查过项目。

## 按场景选择范围

以下使用独立包；源码调用可将 `& "<工具目录>/privacy-guard.exe"` 换成 `py -3 -B -m privacy_guard`，并在本项目根目录执行。

```powershell
# 检查已经导出的记忆或聊天文件，不读取 Agent 运行目录
& "<工具目录>/privacy-guard.exe" files --repo "<项目根目录>" --paths exports/note.txt --source memory
& "<工具目录>/privacy-guard.exe" files --repo "<项目根目录>" --paths exports/messages.json --source chat_history

# 只检查暂存区；如需追加跟踪文件的工作区变化，可加 --all-tracked
& "<工具目录>/privacy-guard.exe" staged --repo "<Git 项目根目录>"

# 检查明确的本机提交范围，替换为本次实际 tip 与 base
& "<工具目录>/privacy-guard.exe" push --repo "<Git 项目根目录>" --push-range "<tip>" "<base>"

# 首次推送或无法确认 base 时，检查该 tip 的全部本机可达历史
& "<工具目录>/privacy-guard.exe" push --repo "<Git 项目根目录>" --push-range "<tip>" -
```

推送多个 ref 时重复传入 `--push-range TIP BASE`，最多 64 个范围、合计 5000 个候选。也可使用单范围 `--tip/--base`，但不能与 `--push-range` 混用；未给 base 时检查全部 tip 可达历史，tip 默认 `HEAD`。

`push` 是本机历史审查，不执行推送、不 fetch、不联系远端。不要默认目的分支是 `main`，也不要假设本机 remote-tracking ref 已最新。返回的 `scope` 固定本次解析出的 tip/base 提交 ID；后续新增提交或改变范围需复查。轻量标签按提交检查；附注标签的独立消息当前不支持，会报告不完整。删除 ref 不携带新内容，不在内容审查范围内。

## 怎样读懂结果

**先看 `review_complete`，再看 `risk_level`。** 检查是否完整与有没有发现风险是两个独立问题。

| 返回情况 | 含义 | 接下来怎么做 |
| --- | --- | --- |
| `review_complete=true`，有发现 | 所选检查完成，并发现需要复核的风险 | 阅读每项建议，决定哪些需要处理 |
| `review_complete=true`，`risk_level=none` | 所选检查完成，现有规则没有命中 | 结合分享目的人工复核；无命中不是安全保证 |
| `review_complete=false` | 有内容或步骤未完成检查，可能仍有已发现的风险 | 查看 `errors` 与未检查项，补充审查后再判断 |

以下为**说明用的 JSON 节选**：假设一个合成文档的第 3 行命中本机路径规则。哈希使用占位符，其他发现字段与顶层字段省略；这不是对真实文件的扫描结果。

```json
{
  "schema_version": 3,
  "mode": "advisory",
  "review_complete": true,
  "risk_level": "high",
  "scanned": 1,
  "findings": [
    {
      "rule": "local-path",
      "severity": "high",
      "file_ref": "<相对文件路径的 SHA256>",
      "line": 3,
      "masked": "[REDACTED]",
      "suggestion": "建议将本机路径改为 <LOCAL_PATH> 或可共享的相对路径；本工具未修改原文。"
    }
  ],
  "errors": [],
  "semantic_status": "disabled",
  "scope": []
}
```

| 字段 | 如何理解 |
| --- | --- |
| `review_complete` | 是否完成指定检查；`false` 时不能说内容安全 |
| `risk_level` / `severity` | 整体最高风险 / 单项严重度：`none`、`medium`、`high`、`critical`（单项不使用 `none`） |
| `scanned` | 已扫描的内容单元数；历史模式可能多次扫描同一文件的不同版本，不等于唯一文件数 |
| `rule` / `suggestion` | 命中规则及静态修改建议；建议尚未执行 |
| `file_ref` / `line` / `commit` | 相对路径的 SHA256、行号、历史提交 ID；`line=0` 表示来源或路径级发现 |
| `errors` | 静态错误说明，不回显任意异常或子进程诊断 |
| `scope` | 历史模式已解析的提交范围；普通文件模式为空 |
| `semantic_status` | `disabled` 为未启用；`complete` 为语义步骤完成；`incomplete` 为请求后未完成，不表示模型判断安全 |
| `next_step` | 将建议交给用户，由用户决定是否另行让 AI 修改 |

为避免报告再次泄露路径，`file_ref` 不直接显示文件名。你可在本机将已知的相对路径按 UTF-8 计算 SHA256，与报告匹配，再结合行号或提交 ID 定位；不要把原始路径或内容补回外发报告。

CLI **退出码 0 表示检查完成，可以仍有 critical 风险；退出码 1 表示检查不完整**。两者都不代表允许或拒绝提交。schema v3 没有 `allow/deny` 执行决策，建议不会自动转换为修复动作。

## 检查能力与局限

| 类别 | 当前做法 | 你需要知道的边界 |
| --- | --- | --- |
| API Key / 密钥 | 本机 gitleaks，有限编码展开 | 缺失、异常或超时标为不完整；不能保证识别所有编码和密钥格式 |
| 个人信息 | 邮箱、中国手机号上下文、身份证日期与校验位规则 | 不是完整 PII 检测；上下文与示例域名过滤用于降低误报 |
| 正文中的本机路径 | Windows 盘符、UNC、常见 POSIX 前缀 | 建议替换占位符；不解析所有路径、编码或 shell 语法 |
| Memory / Chat History | 显式来源、文件名、消息 role 提示，并继续扫描正文 | 来源提示可能误报，不代表每份导出都有秘密，也不覆盖所有导出格式 |
| 凭据与 Agent 运行路径 | 读取前检查，路径级提示或静态失败 | 不读取真实凭据、认证文件或运行目录；不能把未读内容算作已检查 |
| 可选 AI 语义 | 本机隐私分类模型，只增加风险 | 默认关闭；真实权重效果、兼容性和正式评测尚未验收 |

普通规则检查面向支持的 UTF-8 文本。二进制、不支持的编码、symlink、LFS、gitlink、单文件超过 4 MiB 或候选超限等会明确报告检查不完整。工具不会为完成检查而跟随链接、打开受保护文件或静默截断。

规则可以误报，也可能漏报；读取前约束和只读行为属于本工具实现，不能替代操作系统权限隔离。Skill 或 MCP 的接入也不能保证宿主的每次读取、分享和推送都经过审查。当前没有在真实客户端或其他仓库启用自动保护。

## 接入 AI：Skill 与 MCP

直接让 AI 调用已有 EXE 即可使用基础功能。需要重复调用或客户端工具集成时，可选择以下入口；接入与安装由用户自行决定。

| 入口 | 适用场景 | 前置条件与说明 |
| --- | --- | --- |
| [Privacy Review Skill](skills/privacy-review/SKILL.md) | 让 AI 按固定流程调用引擎并解释建议 | 仓库内随附 `scripts/review.py`；源码脚本需 Python 3.14+ 和可用扫描器 |
| [MCP 配置样例](examples/mcp-config.json) | 在支持 MCP 的客户端中作为工具调用 | Python 3.14+、MCP extra、本机扫描器；自行登记 stdio 服务 |

Skill 可用 `py -3 -B scripts/build_skill.py --include-gitleaks` 构建到 `dist/privacy-review/`，包含引擎、Windows gitleaks 和许可证，仍需 Python 3.14+。构建器拒绝覆盖已有产物，不会把包安装到客户端。外载与审查说明见 [Skill 说明](skills/privacy-review/references/coverage.md)。未打包版本可用 `PRIVACY_GUARD_HOME` 或已安装包定位引擎。

MCP 提供四个只读工具：`privacy_review_files`、`privacy_review_staged`、`privacy_review_history`、`privacy_review_push_plan`，没有写入、修复或命令执行工具。它以本地 stdio 进程运行，不启动 HTTP 服务。维护者或源码用户可在本项目准备独立环境：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[mcp]'
.\.venv\Scripts\python.exe -B scripts/run_mcp.py
```

stdio 启动后等待客户端协议输入，没有普通终端界面。接入时在用户本机配置中替换样例的 `<PYTHON_EXECUTABLE>` 与 `<PRIVACY_GUARD_HOME>`，不要把机器路径写回共享文件。提供配置样例不代表已经接入你的客户端。

### 可选本地语义研究

仅源码入口支持此路线：用户在独立环境自行准备 `semantic` extra 和可信的本机隐私分类模型，设置 `PRIVACY_GUARD_SEMANTIC_MODEL`，通过 `--semantic` 或 MCP `semantic=true` 启用。独立 EXE 不包含语义模型或依赖，请求语义时会保留规则发现并报告不完整。

模型要求 safetensors 权重及恰为 `public/private/uncertain` 的标签，普通情感分类器不适用。加载只用本机文件，禁止远程自定义代码；离线 CPU 子进程超时为 60 秒。规则命中行遮盖后送入模型，输出固定标签；`public` 不撤销已有风险，低置信度按 `uncertain`。

上限为 32 个有内容文件、总文本 256 KiB、单文本至多 512 tokens 且受模型上限限制，不静默截断。缺失模型、依赖、超限或超时均保留规则结果并标为不完整。详情见 [语义与覆盖说明](skills/privacy-review/references/coverage.md)；本项目尚未验收真实模型质量，不将替身测试当作效果证明。

## 项目结构与验证

| 位置 | 职责 |
| --- | --- |
| `privacy_guard/` | 读取范围校验、文件/Git 读取、规则扫描、脱敏报告、CLI/MCP 与可选语义 |
| `scripts/` | 启动、构建和交付辅助脚本；不是受检项目修复接口 |
| `skills/privacy-review/` | AI 调用流程与范围说明 |
| `tests/` | 运行时合成数据与隔离临时 Git 仓库验证 |
| `docs/` | 需求、架构、验收、交付与历史记录 |

现有验收记录包含 v0.4 本机全量 **100 项通过**、最终独立包针对性 **7 项通过**，以及文件/Git 状态保持不变、输出脱敏、风险建议和检查失败路径。这些是历史实际结果，不是正式 precision/recall，也不表示真实仓库或客户端已启用保护。实际日期、环境、命令与未验证项见 [验收记录](docs/acceptance.md)。

开发时在本项目独立环境安装开发依赖，每次 pytest 使用全新临时目录：

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[dev,mcp]'
$reviewTestTemp = Join-Path $env:TEMP ("privacy-review-" + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -B -m pytest -q --basetemp $reviewTestTemp
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

早期 hook 阻断原型已退役：安装器停止工作，Git hook 只保留不阻断的兼容空入口，Claude hook 样例为空。不要安装这些历史入口；当前产品采用按需审查与用户决策。

进一步阅读：[需求与范围](docs/requirements.md) · [架构与信任边界](docs/architecture.md) · [项目进度](PROJECT_STATUS.md) · [任务清单](TASKS.md) · [验收记录](docs/acceptance.md) · [项目规范](AGENTS.md)。
