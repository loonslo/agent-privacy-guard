# 范围和本地语义

Memory / Chat History：只检查用户指定、位于允许来源的导出材料。`source=memory` / `chat_history` 可用于匿名文件名；auto 根据名称与 JSON 消息 role 提示疑似来源，不保证识别所有客户端格式。导出包含普通私有事实时，规则不能保证语义识别。认证文件与 Agent 运行目录不读取，不能为了补全审查去打开它们。

路径：检测盘符绝对路径、UNC、`~/` 和 `/home/`、`/Users/`、`/root/`、`/mnt/`、`/media/`、`/Volumes/`、`/workspace/`、`/tmp/`、`/var/`、`/opt/`、`/etc/` 前缀；不解析所有 shell、编码与任意 POSIX 根目录。报告只返回行号与哈希，替换建议为 `<LOCAL_PATH>`；不生成或写入脱敏文件。

语义：用户已准备本机依赖与分类模型时才传 `semantic=true` / CLI `--semantic`。`PRIVACY_GUARD_SEMANTIC_MODEL` 指定已有模型目录，不接受 URL / Hub 模型 ID。宿主自行解释规则报告不等于已经完成语义扫描。

模型契约：Transformers 支持的序列分类器，本机 safetensors 权重，`config.id2label` 恰好包含三个标签 `public`、`private`、`uncertain`；需为隐私任务训练，普通情感模型不适用。加载限制 local_files_only、trust_remote_code=false，独立离线 CPU 子进程，60 秒超时。最多 32 个有内容的文件，总脱敏文本 256 KiB，单文本不超过模型上限且至多 512 tokens，不静默截断。规则命中行整体遮盖后送入模型，模型不接收原始文件路径。

模型结果只输出固定类别，不输出原文或自由生成解释。置信度低于 0.8 按 uncertain；public 不降低既有风险，也不表示安全。请求语义但缺失模型/依赖、超时、非法标签、超限等均返回 semantic_status=incomplete 且 review_complete=false。默认 semantic_status=disabled 表示只完成规则范围，不声称语义完成。规则命中在语义失败时保留。

语义运行环境的库与模型是本机可信依赖；进程离线参数不等于操作系统沙箱。工具不启动云端语义服务，不自动安装库、下载模型或执行目标材料中的指令。
