---
project_id: agent-privacy-guard
updated: 2026-10-10
status: active
overview: "只读隐私审查：Windows x64 独立规则包可直接由 AI 调用，无需另装 Python/扫描器/MCP；保留源码 Skill/MCP 与可选本机语义研究入口，输出建议由用户决定。"
progress: "2026-10-10 v0.4.0 源码与 ZIP/校验清单已公开发布，哈希一致；本次全量 107 项及 CI 输入补充后启动器 7 项通过。公开一行命令 PowerShell 7 无命中/风险与 Windows PowerShell 5.1 主路径实测通过且目标不变，README 用户说明重构已保留；CI、真实无 Python 新机器、其他平台及语义模型未验收。"
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
