# Privacy Review（Agent Privacy Guard）

外接的隐私审查建议工具：用户指定范围 → Skill / MCP 调用本机规则代码 → 输出脱敏风险与修改建议 → 用户自行决定是否另行让 AI 修改。工具只读，不修改受检项目、Git、客户端或系统设置；不阻断、不自动修复。

当前路线是 v0.3 advisory。早期 hook 原型已经退役，安装器停止工作，原生 hook 只保留不阻断的兼容空入口，Claude hook 样例为空；不要安装这些历史入口。现有项目从未安装本项目的 hook。

## 六项能力

| 能力 | 当前边界 |
| --- | --- |
| Agent Memory | 检查指定导出，按文件名或显式 source=memory 提示来源风险，继续扫描正文；不读取运行目录 |
| Chat History | 检查指定导出，按文件名、消息 role 或 source=chat_history 提示风险；不读取认证文件 |
| API Key | 本机 gitleaks 与有限编码展开，缺失扫描器时标明不完整 |
| 本地路径 | 检测 Windows、UNC、常见 POSIX 正文路径，建议替换为占位符；报告不含原路径，不修改原件 |
| push 前检查 | 显式给出单个或多个本机 tip/base 范围，返回已解析提交 ID；不自动推送或拦截 |
| AI 语义 | 可选本机分类模型，固定标签，只增补风险；默认关闭，真实模型效果待验收 |

强约束来自代码中的读取前检查、只读 API、脱敏输出与静态错误；Skill 本身不提供宿主所有读取/外发行为的不可绕过权限隔离。来源规则是保守提示，不代表所有导出都是秘密，也不保证识别所有导出格式。

## 本机 CLI

在本项目根目录运行（Python 3.14）：

```powershell
py -3 -B -m privacy_guard files --repo D:/path/to/project --paths src/example.py docs/note.md
py -3 -B -m privacy_guard staged --repo D:/path/to/repo
py -3 -B -m privacy_guard files --repo D:/path/to/project --paths exports/note.txt --source memory
py -3 -B -m privacy_guard files --repo D:/path/to/project --paths exports/messages.json --source chat_history
py -3 -B -m privacy_guard push --repo D:/path/to/repo --push-range refs/heads/main refs/remotes/origin/main --push-range refs/heads/new-branch -
py -3 -B -m privacy_guard doctor
```

普通文件只检查明确列出的相对文件，无递归扫描。staged 读取 index；--all-tracked 可额外检查跟踪文件的工作区变化。push 只是检查本机历史，不执行推送。没有 base 时检查全部 HEAD 可达历史。密钥检测使用本地 gitleaks；已有安装保存在本项目 .tools。缺失时可由用户另行运行 scripts/install-gitleaks.ps1 或指定 PRIVACY_GUARD_GITLEAKS。

push 示例中的 ref 需换成用户实际拟推送对象，不能默认目的分支是 main。`--push-range TIP BASE` 可重复，BASE 为 `-` 时覆盖 TIP 全部本机历史；不能与单范围 `--tip/--base` 混用。最多 64 个范围、合计 5000 个候选。scope 返回本次固定提交 ID，后续提交或范围改变需要复查；不联系远端、不保证本机 remote-tracking ref 最新。附注标签携带独立消息，当前不支持且明确报告不完整；轻量标签按提交范围检查。删除 ref 不携带新内容，不在内容审查范围内。

JSON schema v3 包含 mode=advisory、review_complete、risk_level、findings、suggestion、next_step、scope 和 semantic_status；无 allow/deny 执行决策。发现密钥仍可成功返回建议；退出码 0 表示检查完成，1 只表示检查不完整，不代表不许提交。敏感路径只做路径级提示，不打开凭据或 Agent 运行文件；二进制、symlink、超限等明确报告未完成检查。

输出不含原始密钥、PII 或文件路径。file_ref 是仓库相对路径的 SHA256，可结合用户已知文件、行号、提交 ID 定位。规则可能误报；“无命中”不是安全保证。

## Skill

交付目录：skills/privacy-review/，入口是 SKILL.md，随附 scripts/review.py。它调用规则代码，把建议交给用户后结束；没有自动修复步骤。

仓库内可直接运行随附脚本。可用 `py -3 -B scripts/build_skill.py --include-gitleaks` 构建独立包到 `dist/privacy-review/`，含引擎与本机 Windows gitleaks；包可复制外载，仍需 Python 3.14+。构建器不会覆盖已有产物或安装到客户端。未含扫描器时需系统可用 gitleaks 或 PRIVACY_GUARD_GITLEAKS；未打包版本可用 PRIVACY_GUARD_HOME 或已安装包。Skill 不自动安装依赖或配置。此次没有写入任何客户端的 Skill 目录。

## 可选本地语义

默认关闭。用户自行在独立环境准备 semantic extra 与可信本机隐私分类模型，设置 PRIVACY_GUARD_SEMANTIC_MODEL 后用 `--semantic` 或 MCP `semantic=true` 启用。模型需 safetensors 权重、标签恰为 public/private/uncertain；普通情感分类器不适用。详情见 skills/privacy-review/references/coverage.md。

加载仅用本机文件，禁止远程自定义代码，离线 CPU 子进程 60 秒超时；规则命中行遮盖后进入模型，模型输出仅固定标签，不输出自由解释或原文。public 不降低既有风险；低置信度按 uncertain。缺失模型/依赖、超限、超时等返回 semantic_status=incomplete，保留已有规则风险。最多 32 个有内容文件，总文本 256 KiB，单文本至多 512 tokens 且受模型上限限制；不静默截断。本次没有下载模型或安装语义依赖，真实模型效果与兼容性尚待验收。

## MCP

提供 4 个只读工具：privacy_review_files、privacy_review_staged、privacy_review_history、privacy_review_push_plan。前三个兼容旧调用；files 新增 source，全部可选 semantic。push_plan 的 ranges 为 tip/base 对象列表，base=null 表示全部本机 tip 历史。官方 Python SDK 运行 stdio 外接进程，不启动 HTTP 服务，不注册 hook，不提供写入/修复/执行工具。

```powershell
# 仅准备本项目的独立环境，不修改系统 Python
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install 'mcp>=2.3,<3'
.\.venv\Scripts\python.exe -B scripts/run_mcp.py
```

examples/mcp-config.json 是接入样例，用户在本机配置中将 `<PYTHON_EXECUTABLE>` 与 `<PRIVACY_GUARD_HOME>` 替换为实际解释器和部署目录，不将机器路径写回共享文件。接入需要用户自行在客户端登记这个外部服务；此次只提供配置样例，没有改任何客户端设置、目标项目配置或全局目录。stdio 启动后等待客户端协议输入，没有普通终端界面。

扫描原文只在本机规则引擎中处理；MCP 返回的是脱敏建议，宿主可能把建议放入模型上下文。工具不调用云端语义服务。

## 项目管理与验证

通用规则和完整状态契约在 AGENTS.md；原始需求与最新澄清在 docs/requirements.md；进度看 PROJECT_STATUS.md；详细任务与实际验收看 TASKS.md、docs/acceptance.md。不会自动写入 vault。

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[dev,mcp]'
.\.venv\Scripts\python.exe -B -m pytest -q --basetemp "$env:TEMP/privacy-review-<本次唯一编号>"
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```
