# 架构与信任边界（当前 advisory 路线）

用户指定范围 → Skill 或 MCP 调用只读规则 API → 返回脱敏风险和修改建议 → 用户决定是否另行让 AI 修改。审查在建议交付后结束。它不注册工具前置事件，不接管命令，不替用户授权或执行修复。

| 模块 | 当前职责 |
| --- | --- |
| gitio.py | 只读 index、跟踪文件变化和本机历史；不 add/commit/push/config |
| rules.py / scanner.py | 本机路径、PII、gitleaks 规则；原文不发到云端 |
| paths.py | 读取前校验根目录、凭据名称、隐藏目录与解析后目标，所有审查入口复用 |
| semantic.py / semantic_worker.py | 可选本机分类；离线加载 safetensors，静态标签，只增补风险，失败保留规则结果 |
| advisory.py | 将检测转换为严重度、依据、suggestion、未检查项和 next_step |
| cli.py | 默认只给建议；命中正常返回；技术失败报告 review_complete=false |
| mcp_server.py | 4 个 stdio 只读 review 工具，含显式多范围 push_plan，无写入/修复/命令执行接口 |
| skills/privacy-review | 调用规则并解释结果，结束时将建议交给用户 |

## 输入和检查范围

files 仅明确给出的相对文件，不递归，不越界，不跟随 symlink。staged 检查 index；include_worktree 可追加跟踪文件工作区变化。history 遍历本机 tip/base 范围内提交，覆盖加入后删除的内容和提交消息；默认 HEAD 全部历史。不读取真实认证目录、凭据文件或 Agent 运行文件；这些路径只提示路径风险。

v0.3 新增 Memory / History 来源提示：显式 source、名称与消息 role，不因此跳过导出正文的密钥检测。凭据名称与隐藏运行目录依旧只提示，不读取。正文路径检测给出替换建议，不写副本。保护根目录在 Git 子进程或文件读取前检查；解析后完整目标再次验证。路径检查属于本机行为约束，不是操作系统权限沙箱，也不保证并发恶意改换链接时的隔离。

push_plan 在本机解析每个 tip/base 到提交 ID 后检查历史，返回脱敏 scope。最多 64 范围、合计 5000 候选；非 commit tip（如附注标签）明确不完整，避免漏查标签消息后声称完整。Git 对象定位只接受 40/64 位十六进制，子进程诊断不输出。不 fetch、不访问远端；本机 tracking ref 是否最新由用户确认，范围变化需复查。

完整改变 blob 检查可能重报旧 PII。单文件 4 MiB、最多 5000 候选/提交；不支持的编码、二进制、LFS、gitlink、超限、缺失依赖和异常均明确标为检查不完整。这里的不完整不产生提交阻断或 permissionDecision。

## 输出与权限

JSON schema v3：mode=advisory、review_complete、risk_level、scanned、findings、errors、next_step、scope、semantic_status。findings 含严重度、静态规则、哈希定位、行号/提交 ID、掩码和建议。没有执行动作字段，也没有补丁自动应用接口。CLI 参数解析失败也返回静态 JSON，不回显参数；检查完成返回 0，不完整返回 1，不能解释成拒绝用户操作。

gitleaks 使用隔离默认规则、完整 redact、两层解码、禁用文件内 allow 注释。原文走 stdin，临时报告只在本机系统临时目录生成并清理；这些短期内部文件不写到受检项目。错误不回显任意异常、路径、原文或子进程诊断。MCP 宿主接收脱敏建议，可能将其交给自己的模型；本工具仅在显式 semantic 请求时调用本机分类器，不调用云端模型。

语义使用本机已有 Transformers 隐私分类模型，local_files_only、trust_remote_code=false、use_safetensors=true；独立 CPU 子进程设置离线与禁用遥测，60 秒超时。固定 public/private/uncertain 标签、置信度阈值 0.8；private/uncertain 只增加发现，public 不撤销规则。最多 32 有内容文件、总文本 256 KiB、单文本不超过模型上下文且至多 512 tokens，不静默截断。模型不接收原始文件名；规则命中行遮盖。失败标记 incomplete 且保留规则发现。库/模型是可信本机依赖，离线加载参数不是沙箱；本次未安装语义依赖或验证真实权重质量。

MCP 用官方 Python SDK 2.x、stdio 外接进程。工具声明 read_only_hint=True、destructive_hint=False、open_world_hint=False；代码行为和目标快照测试提供实际只读证据，声明不是权限隔离机制。客户端连接由用户另行登记，此次不修改客户端配置。依赖仅安装在守卫项目的 .venv；不会安装到受检项目或修改系统 Python。

## 历史 hook 路线的处置

早期 v0.1 用 hook 阻断。用户已明确选择无侵入的建议工具，因此该路线退役：安装器拒绝执行，两个 Git hook 为空操作，Claude 配置样例为空；CLI 历史 claude-hook 模式返回空 JSON，历史 pre-push 模式不阻断。旧 adapters.py 保留内部原型供历史测试参考，未暴露给 Skill/MCP 或当前 CLI。

本次及此前均未安装真实仓库 hook。当前无需启用五个知识库 hooksPath 或 Claude PreToolUse；这些已从后续计划撤下。后续可增加规则、误报反馈、目的地上下文和解释质量，不恢复自动拦截或自动修复。

## 上游依据

2026-10-10 查阅：[gitleaks 官方说明](https://github.com/gitleaks/gitleaks)、[MCP 官方 Python SDK](https://github.com/modelcontextprotocol/python-sdk)、[只读工具 annotations](https://py.sdk.modelcontextprotocol.io/servers/tools/)。历史 hook 能力参考：[Claude hooks](https://code.claude.com/docs/en/hooks)。当前使用 MCPServer、stdio 和结构化工具输出，依赖约束 mcp>=2.3,<3，实际验证版本 2.3.0。

本地模型加载参数依据 [Transformers 离线说明](https://huggingface.co/docs/transformers/main/en/installation) 与 [Auto 类官方 API](https://huggingface.co/docs/transformers/main/en/model_doc/auto)，本次查阅日 2026-10-10；上游说明不替代本项目真实模型验收。
