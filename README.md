# Agent Privacy Guard

## 项目介绍

Agent Privacy Guard 是一个供用户和 AI 调用的隐私审核工具。分享代码、文档、AI 记忆或聊天记录之前，它帮助检查疑似 API 密钥、个人信息和电脑路径，并给出修改建议；也能检查 Git 暂存区和指定提交范围，发现历史中仍然保留的敏感内容。

检查在你的电脑上完成：工具按照预设的识别规则查找风险，报告隐藏敏感原文，只返回风险类别、定位信息和建议。你决定是否修改，工具只负责审核。

在 **Windows x64 的 PowerShell** 中，一行命令即可下载并使用，无需另装 Python、扫描器、MCP 或模型：

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/loonslo/agent-privacy-guard/v0.4.0/scripts/review.ps1))) -Repo . -Paths README.md
```

`-Repo .` 表示当前项目目录，`-Paths README.md` 表示检查这个相对文件；替换成你要审核的项目和文件即可。检查多个文件时可使用 `-Paths src/app.py,docs/note.md`。Git 检查使用电脑上已有的 Git。

也可以把本仓库链接和要检查的范围交给具有本机执行权限的 AI，让它调用工具并解释修改建议。

## 简单架构

```text
用户或 AI 指定范围 → 下载并启动工具 → 检查内容 → 返回脱敏风险和建议
```

- **启动入口**：下载固定版本工具、核验文件完整性并运行，无需修改项目或客户端配置。
- **检查引擎**：校验读取范围，检查文件或 Git 内容，通过密钥扫描器和预设规则识别疑似敏感信息。
- **建议输出**：汇总风险、位置和修改建议；无法完成的检查会明确说明。

命令行、Skill 和 MCP 共用同一套检查引擎，文件内容由电脑上的工具处理。
