---
project_id: agent-privacy-guard
updated: 2026-10-10
status: active
overview: "只读隐私审查：Windows x64 独立规则包可直接由 AI 调用，无需另装 Python/扫描器/MCP；保留源码 Skill/MCP 与可选本机语义研究入口，输出建议由用户决定。"
progress: "2026-10-10 README 已按用户要求收敛为项目介绍与简单架构，文档/命令语法及状态自检通过，本次未重跑功能测试。历史 v0.4.0 已公开发布，全量 107 项与公开一行调用已验收；CI、真实无 Python 新机器、其他平台及语义模型未验收。"
next: "验证真正无 Python 的 Windows x64 新机器、CI 和其他平台入口；继续正式评测与真实语义模型验证，保持只读建议模式。"
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
