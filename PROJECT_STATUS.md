---
project_id: agent-privacy-guard
updated: 2026-10-10
status: active
overview: "只读隐私审查：Windows x64 独立规则包可直接由 AI 调用，无需另装 Python/扫描器/MCP；保留源码 Skill/MCP 与可选本机语义研究入口，输出建议由用户决定。"
progress: "2026-10-10 README 用户说明重构已保留；v0.4 源码 3c9e779 已推送，一行 PowerShell 下载/校验/审核入口本次全量 107 项通过，CI 固定资产输入增补后启动器 7 项通过。公开发布与调用待核验；CI、真实无 Python 新机器、其他平台及语义模型尚未验收。"
next: "按已授权发布任务完成 v0.4.0 资产交付并验收公开一行调用；随后验证真正无 Python 的 Windows x64 新机器、CI 及其他平台，保持只读建议模式。"
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
