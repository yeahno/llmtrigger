## 问题判断
- 本地正常、Actions 报错 400 且提示“未正常接收到prompt参数”，高概率为接口期望的入参格式不一致（messages 与 completions 路由差异）、或 Secrets 未配置/为空。
- Actions 日志中被替换为 *** 属于正常的 Secrets 掩码，不代表变量为空；需通过显式存在性检查确认。

## 诊断步骤（只读与安全）
1. 在当前工作流中增加一个“调试步骤”，输出环境变量是否存在（不输出值，只输出是否为空）：API_TYPE、API_URL、MODEL_NAME、PROMPT。
2. 检查最近一次 Actions 日志的“Run LLM Script”前后是否有 Python 依赖安装异常或网络错误。
3. 记录本地与 Actions 的 Python 版本与 anthropic/openai 包版本，以排除版本差异导致的 SDK 行为不同。

## 代码层面修复方案
1. Anthropic 模式：
   - 首选 SDK messages.create：messages=[{"role":"user","content": prompt}]。
   - 若返回 400 则自动降级到 HTTP 兼容：
     - 先 POST /v1/messages（content 仍用字符串，不用块数组）；
     - 若仍报“prompt 缺失”，再 POST /v1/complete，构造 Human/Assistant 模板的 prompt（completion 路由要求）。
   - 在回退 HTTP 请求中补充 headers：x-api-key、content-type，以及可选 anthropic-version（如 2023-06-01）。
2. 将 Anthropic 模式下默认模型改为 glm-4.7（当前已处理），并允许通过 MODEL_NAME 覆盖。
3. 若仍失败，提供“改走 OpenAI 兼容”选项：将 API_TYPE=openai，API_URL= https://open.bigmodel.cn/api/paas/v4/，使用 OpenAI SDK 调用，规避接口差异。

## 工作流与配置修正
1. 在 .github/workflows/main.yml 的“Run LLM Script”步骤中，确保传入：API_TYPE、API_URL、API_KEY、MODEL_NAME、PROMPT；若未配 PROMPT，代码使用默认英文字符串（避免非 ASCII 造成代理解析问题）。
2. README 中补充“Anthropic/Completions 兼容说明”和“OpenAI 兼容改道”指南，降低使用门槛。

## 验证计划
- 本地与 Actions 各跑一次：Anthropic 模式（messages）、Anthropic 模式（自动回退 completions）、OpenAI 兼容模式（可选）。
- 观察日志：不再出现 1213 提示；返回内容存在并打印首段文本。

## 交付内容
- 更新 main.py 增强 Anthropic 兼容与回退逻辑（已设计好具体实现）。
- 在工作流添加环境存在性检查的调试步骤（不泄露敏感信息）。
- 更新 README 的使用说明与故障排查章节。