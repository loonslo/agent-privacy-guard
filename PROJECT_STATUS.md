---
project_id: agent-privacy-guard
updated: 2026-10-10
status: active
overview: "只读隐私审查：Windows x64 独立规则包可直接由 AI 调用，无需另装 Python/扫描器/MCP；保留源码 Skill/MCP 与可选本机语义研究入口，输出建议由用户决定。"
progress: "2026-10-10 v0.4 独立包本机构建与全量 100 项通过，最终 ZIP 另跑 7 项通过；隔离单 EXE/PATH 空环境可审核合成文件且目标不变。v0.3 源码历史已发布；v0.4 远程发布、公开下载、CI、真实无 Python 新机器与其他平台尚未验收。"
next: "用户确认后发布 v0.4.0 源码和已核验 ZIP 到指定 GitHub 仓库并验收公开下载；随后验证真正无 Python 的 Windows x64 新机器及其他平台，保持只读建议模式。"
evidence:
  - TASKS.md
  - docs/requirements.md
  - docs/acceptance.md
  - docs/architecture.md
  - docs/skill-review.md
  - docs/standalone.md
---

# 项目概览与进度

摘要维护日：2026-10-10。项目状态 active 表示继续跟进，不表示任何拦截保护已启用；当前产品只提供建议。

详细任务和验收以 evidence 中的稳定文件为正本。未自动登记或更新日常 vault，其他项目保持原状。
