# 验收记录

## 2026-10-10 GitHub 首次发布

用户明确授权 commit + push，并指定新建公开仓库 agent-privacy-guard。使用已认证 GitHub CLI 账号 loonslo，新建 [公开仓库](https://github.com/loonslo/agent-privacy-guard)，origin 为该仓库 HTTPS 地址。

环境：原有 Windows / Python 3.14 本机环境；首次源码提交 `e1c07d659641d9ad06f0d74570a7b30eef92193e`，分支 `codex/initial-implementation`，也是远端默认分支。`git push -u origin codex/initial-implementation` 成功，`git ls-remote --heads origin refs/heads/codex/initial-implementation` 与该源码提交一致，首次推送后工作区干净。后续任务/验收/摘要发布记录作为独立文档提交，不重写已发布历史。

发布前核对 40 个源码/说明文件，实际暂存区规则审查 review_complete=true，无 secret:* 命中；其他路径、PII、聊天格式提示经核对为合成测试或文档示例。此结果只覆盖此次提交资料，不是宿主全局防泄漏保护。扫描未启用语义。

MCP 接入样例改为解释器/部署目录占位符，原始需求移除本机工作区绝对路径；确认无真实本机根路径或用户目录进入提交。`.venv/`、`.tools/`、`dist/`、缓存与运行目录保持 Git 忽略；未提交扫描器二进制或 ZIP。提交作者使用已有 noreply 邮箱配置，未读取凭据文件。

`git diff --cached --check` 通过；MCP 样例 JSON 与发布记录结构在文档提交前复查。此前功能全量 93 项和打包针对性 1 项结果保留为历史实际验证，本次仅发布及占位符/文档调整，未重复功能测试。未部署实际客户端、安装 hook、启用语义模型或创建 GitHub Release。

## 当前：2026-10-10 v0.3 六项能力增补

用户要求增加审查中指出的内容。新增 Memory / History 指定导出来源提示、正文路径检测及静态替换建议、显式多 tip/base 本机历史检查与固定提交 scope、可选本机语义分类、独立 Skill 打包；修复受保护根目录与 CLI 参数回显。产品仍只读，不自动执行建议、安装 hook、登记客户端或推送。

环境：Windows、Python 3.14.0、本项目 `.venv`，原有 gitleaks 8.30.1 / MCP SDK 2.3.0；测试仅运行时合成数据与隔离临时 Git 仓库。未安装语义依赖、下载模型或读取真实凭据/Agent 运行目录。

| 验证 | 实际结果 |
| --- | --- |
| 首轮新增与 advisory 集成 | 全新 GUID basetemp，39 passed in 22.19s |
| 第一轮全量 | 全新 GUID basetemp，92 passed in 45.71s |
| Git 不可信对象 ID 输出校验后全量 | `.venv/Scripts/python.exe -B -m pytest -q --basetemp <系统临时目录下 privacy-coverage-final-GUID>` → **93 passed in 45.07s** |
| 许可证打包补充后针对性 | 全新 privacy-license-coverage-GUID basetemp，test_built_skill_runs_without_project_imports → **1 passed in 3.81s**；核心扫描代码此后未改 |
| Memory / History | 指定来源、文件名和消息 role 提示；导出中的合成密钥仍被扫描，原文不在报告中 |
| 正文路径 | Windows 盘符、UNC、POSIX、~/ 正样本命中；普通相对路径和网页链接负样本不命中，输出仅规则/行号/哈希与静态建议 |
| 读取前保护 | 隔离 `.codex/.claude/.ssh` 根目录在读取或 Git 调用前拒绝；auth.json 不打开；模拟解析后的受保护目标不打开 |
| CLI / Skill 错误脱敏 | 未知参数、非法 mode/source、缺失范围参数不回显测试标记，静态 JSON review_complete=false |
| 多 ref push 计划 | 合成分支与加入后删除的密钥均覆盖，返回固定 tip/base 提交 ID；非法 ref/子进程对象 ID 静态失败，附注标签明确不完整 |
| 语义接口 | 替身验证规则命中行遮盖、离线参数、固定标签、低风险标签不撤销 critical、超时/非法输出保留规则；worker 替身验证 safetensors/禁止自定义代码及 512 token 超限；真实无模型进程返回静态不完整 |
| 真实 MCP stdio | 列出 4 个只读工具，调用 source、push_plan 和请求语义但无模型失败路径均返回结构化结果 |
| 目标不变 | 新增文件/推送计划/语义/独立包及真实 MCP 调用前后，合成目标文件字节（含 .git）、status、local config 快照相同 |
| 独立包 | 实际构建 dist/privacy-review，包含本机引擎、Windows gitleaks、许可证；临时复制包用 Python -I 排除项目导入路径，扫描合成密钥成功；构建器拒绝覆盖已有目录 |
| 格式 | Ruff check / format --check；源 Skill 与分发 Skill 的 UTF-8 quick_validate 均通过，包内引擎/Skill 与源文件一致，dist 被 Git 忽略 |

本次不证明真实客户端保护已启用。尚未验收：真实隐私分类模型权重和效果、semantic extra 在当前 Python/Windows 环境的实际安装兼容性、正式 precision/recall、真实客户端 UI 与远端推送。正文路径规则覆盖常见前缀，不代表解析任意编码/shell 或所有 POSIX 路径。Memory / History 来源提示可能误报且不覆盖所有客户端格式。

默认 semantic_status=disabled，只表示规则审查；显式请求语义但失败标为 incomplete。public 或无命中不等于安全。离线加载参数与 MCP annotations 不等于 OS 沙箱或宿主全局外发强制边界。Git 本机 base 需用户确认，范围改变需复查；附注标签当前不支持。

分发包使用 Python 3.14+；普通规则模式无需语义依赖。用户若启用语义，需自行提供已准备的本机隐私分类模型。构建和本机验证均未修改实际客户端设置，未提交或推送。

交付前自检：PROJECT_STATUS 无重复键、必填字段/日期/状态/证据路径均通过；源代码与分发包逐文件一致。生成 dist/privacy-review-v0.3.0-windows.zip，ZIP 完整性与隐藏的扫描器/许可证条目检查通过。实际分发入口用 Python -I 执行 doctor 成功，scanned=0，仅证明扫描器健康，不是实际目标审查。最终 Ruff check / format --check 通过。

## 2026-10-10 六项能力与 Skill 审查

本次仅审查与维护记录，产品代码未改。详情见 docs/skill-review.md。

环境：Windows、本项目 `.venv`、Python 3.14；命令为 `.venv/Scripts/python.exe -B -m pytest -q --basetemp <系统临时目录下全新 privacy-review-audit-GUID>`。实际结果 **57 passed in 25.33s**，不是沿用上一轮结果。

另外使用运行时合成数据与隔离临时目录复现：普通 Memory / History 文本和正文路径没有专用规则命中；Agent 运行目录作为根目录时普通子文件会被打开；CLI 未知参数错误会回显测试标记。仅记录类别与布尔结果，没有读取真实凭据、真实 Agent 运行目录或修改客户端。上述缺陷未修复，回归通过不表示六项能力已完成。

本次未做真实客户端接入、真实推送、正式 precision/recall 或语义层验收。Skill 外接依赖仍需独立引擎与 gitleaks；按需检查不能保证宿主所有外发行为受约束。

## 历史：2026-10-10 v0.2 advisory 改版

依据用户澄清：无侵入的 Skill/MCP 调用规则，只读给出修改建议，交给用户后结束；用户自行决定是否另行让 AI 修改。早期 hook 路线已退役，其历史验证不代表当前产品有阻断能力。

环境：Windows、Python 3.14.0、Git 2.54.0.windows.1、本项目独立 .venv，MCP 官方 SDK 2.3.0、pytest 9.1.1、Ruff 0.17.0、PyYAML 6.0.3；密钥规则继续使用本项目 gitleaks 8.30.1。依赖未装入系统 Python 或目标项目，客户端配置未改变。

| 验证 | 实际结果 |
| --- | --- |
| 全量回归 | `.venv/Scripts/python.exe -B -m pytest -q --basetemp %TEMP%/privacy-review-20261010-07` → **57 passed in 26.22s** |
| 真实 MCP stdio | 官方客户端启动本地服务，列出 3 个只读 review 工具，实际调用返回结构化脱敏建议；无写入/修复/命令工具 |
| 目标不变 | 普通文件、暂存区、历史审查前后，目标全部文件字节（含 .git）、Git status 与本地 config 快照相同 |
| 风险命中行为 | 合成密钥返回 critical 和修改建议，完成检查退出 0；无执行 action 字段 |
| 检查失败 | 依赖缺失、超时、非法报告等标为 review_complete=false；无命令阻断或自动修复 |
| 凭据保护 | 对 .env 等路径只做路径级建议，测试替换 read_bytes/read_blob 为禁止调用后仍可提示；未读取内容 |
| Skill | 实际运行随附脚本返回 advisory JSON；quick_validate.py 使用 Python UTF-8 模式验证通过 |
| 静态检查 | Ruff 检查通过；本项目显式选择 E4/E7/E9/F，排除依赖与缓存目录 |

调试记录：首轮 advisory 回归 54 通过、3 失败，分别为 Windows JSON 管道编码、SDK list_tools 返回容器、测试 bare 远端 HEAD 与 main 不一致；已修复。随后 MCP 测试发现未限定 dict 返回类型不提供结构化输出，显式 schema 时启动失败；改为 TypedDict ReviewReport，并完成真实 stdio 复验及最终全量回归。Skill 校验器默认使用本机 GBK 读中文失败，以 `py -3 -X utf8 -B` 运行后通过，没有修改系统编码设置。

旧安装器只返回退役错误，Git hook 保留 exit 0 空入口，旧 Claude hook 返回空 JSON，不再判定权限；这些兼容入口不属于当前产品接入方案。examples/mcp-config.json 仅为配置样例；Skill 与 MCP 都未登记到真实客户端。

尚未验收：实际 Claude/Codex 等宿主 UI 的安装与展示体验；正式标注数据集的 precision/recall；目的地上下文与误报反馈。固定文件快照不变和协议工具声明验证的是本实现行为，不把声明解释为宿主的系统权限隔离。无命中不代表内容必然安全，敏感路径/二进制等明确标为未完整检查。

交付前再次核对项目状态、证据路径、Skill 格式、PowerShell 脚本语法与 Git 忽略；结果补充在本节末尾。

最终自检通过：Ruff check 与 format --check、Skill quick_validate（UTF-8）、PROJECT_STATUS 无重复键/字段类型/日期/状态/证据路径、两个 PowerShell 安装器语法、.venv 与 .tools 的 Git 忽略。仅守卫项目文件和其私有依赖环境有变更，受检项目与实际客户端设置未改。

## 历史：2026-10-10 早期 hook 原型（路线已退役）

环境：原生 Windows、Git 2.54.0.windows.1、Python 3.14.0、pytest 8.4.2、Ruff 0.15.15、PyYAML 6.0.3、gitleaks 8.30.1。

本次仅新项目及隔离临时仓库。未运行真实仓库扫描，不读取真实凭据，不部署知识库 hook，不访问 Claude 认证文件。

## 本次实际执行

| 项目 | 命令/操作 | 结果 |
| --- | --- | --- |
| 项目创建 | 独立 git init，分支 codex/initial-implementation | 成功；未提交、未推送 |
| gitleaks 安装 | scripts/install-gitleaks.ps1 | 官方 Windows x64 包 SHA256 对照发布 checksums 文件一致，本项目 .tools 安装；未修改 PATH 或其他项目 |
| 首轮测试 | py -3 -B -m pytest -q --basetemp %TEMP%/privacy-guard-test-20261010-01 | 42 通过、1 失败；Git hook 输出位于 stderr，而断言只查 stdout；已改为检查两者 |
| 最终回归 | py -3 -B -m pytest -q --basetemp %TEMP%/privacy-guard-test-20261010-02 | 51 passed in 22.02s |
| 静态检查 | py -3 -m ruff check . | All checks passed |
| 格式检查 | py -3 -m ruff format --check . | 11 files already formatted |
| 扫描器自检 | py -3 -B -m privacy_guard doctor | allow，退出 0 |
| 安装预览 | scripts/install-hooks.ps1 -Repo 本项目精确根目录 | Applied=False；未写 hooksPath |

gitleaks 发布包 SHA256：D29144DEFF3A68AA93CED33DDDF84B7FDC26070ADD4AA0F4513094C8332AFC4E。来源：[官方 v8.30.1 发布页](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1)；校验用于确认包与同一官方发布的 checksum 一致，不作为独立签名证明。

测试覆盖：暂存与工作区区分；CLI/原生 commit -a；正常提交允许；历史加入后删除的合成密钥；首次、多 ref、删除 ref；CLI/原生 pre-push 阻断且本地 bare 远端没有收到提交；提交消息；base64；隐藏目录与安全目录内容扫描；PII 正负样本与身份证校验位；最高严重度；非法输入；依赖缺失、扫描器失败、超时、非法报告；gitlink；输出不含合成密钥或原始路径；仓库扫描配置和 gitleaks:allow 注释不能关闭检测；常见绕过与未知命令形式拒绝。

测试过程中只使用隔离临时 Git 仓库与本地 bare 远端，测试失败不会误写生产远端。未安装本项目自身或知识库的 hooksPath。项目状态与 evidence 路径、PowerShell 脚本解析和 hook LF 格式在交付前自检，结果见下方。

交付前自检通过：PyYAML 解析 PROJECT_STATUS，确认无重复键、必填字段和类型、真实未加引号日期、合法状态、非空字符串与项目内 evidence 文件路径；两个 PowerShell 安装器语法解析通过；两个原生 hook 使用 LF；git check-ignore 确认本地 gitleaks 二进制不会进入 Git。

未验证边界：真实 Claude 客户端集成及超时 UI；真实五仓库部署；公开/私有策略、baseline、豁免、语义层、Codex/Cursor、插件、CI、固定评测集 precision/recall。初版检查完整改变 blob，会重报文件内旧 PII。

CLI 及 Claude hook 协议经过自动化测试，不等同于 Claude 客户端 UI 已通过。原生 pre-commit 没有 commit-msg 检查；提交消息由 Claude 预检和 push 检查覆盖。任意间接脚本执行、所有 shell 语法、读取侧泄漏和 hook 配置被有权操作者修改不在 v0.1 保护承诺内。
