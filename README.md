# LLM Trigger（模型触发器）
[![LLM Trigger Status](https://github.com/OWNER/REPO/actions/workflows/llm_scheduler.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/llm_scheduler.yml)

这是一个用于定期调用大模型 API 的 Python 脚本，通过 GitHub Actions 自动运行。主要用于模拟活跃度、定时测试 API 连通性或作为简单的定时任务模板。

## 功能特点

- **自动定时运行**: 利用 GitHub Actions 的 Cron 功能，无需自备服务器。
- **配置灵活**: 支持自定义 API URL、Key、模型名称和 Prompt。
- **双模式支持**: 同时支持 **OpenAI** (默认) 和 **Anthropic** 两种 SDK 调用模式。
- **广泛兼容**: 兼容 OpenAI、DeepSeek、Claude (via OneAPI)、智谱 (OpenAI/Anthropic 模式) 等多种服务。

## 快速开始

### 1. Fork 本仓库

点击右上角的 **Fork** 按钮，将本仓库复制到你自己的 GitHub 账号下。

### 2. 配置 Secrets

在你的 GitHub 仓库页面中，进入 **Settings** -> **Secrets and variables** -> **Actions**，点击 **New repository secret** 添加以下变量：

| Secret Name | 必填 | 描述 | 示例 |
|---|---|---|---|
| `API_KEY` | 是 | 大模型服务的 API Key | `sk-xxxxxxxx` |
| `API_URL` | 否 | API 基础地址 | 见下文配置指南 |
| `API_TYPE` | 否 | 接口类型: `openai` (默认) 或 `anthropic` | `anthropic` |
| `MODEL_NAME`| 否 | 模型名称 (默认为 `gpt-3.5-turbo`) | `glm-4` 或 `claude-3-opus` |
| `PROMPT` | 否 | 发送给模型的自定义提示词 | `Hi, report status.` |

### 配置指南

#### 1. 使用 OpenAI 兼容接口 (推荐 / 默认)
适用于 OpenAI, DeepSeek, 智谱 (OpenAI 模式), OneAPI 等。
- `API_TYPE`: 不填 (默认为 `openai`)
- `API_URL`: 填写对应的 Base URL (通常以 `/v1` 结尾)
  - OpenAI: `https://api.openai.com/v1` (默认)
  - DeepSeek: `https://api.deepseek.com`
  - 智谱: `https://open.bigmodel.cn/api/paas/v4/`

#### 2. 使用智谱 Anthropic 兼容接口
如果你想使用智谱提供的 Claude 兼容接口 `https://open.bigmodel.cn/api/anthropic`：
- `API_TYPE`: `anthropic`
- `API_URL`: `https://open.bigmodel.cn/api/anthropic`
- `MODEL_NAME`: `glm-4` (或其他智谱模型)
- `API_KEY`: 你的智谱 API Key

### 3. 启用 GitHub Actions

1. 进入 **Actions** 标签页。
2. 如果看到警告 "Workflows aren't being run on this forked repository"，点击绿色按钮启用。
3. 你可以点击左侧的 **LLM Trigger**，然后点击 **Run workflow** 手动触发一次测试。

### 4. 修改定时频率

默认频率为每天 **6:00 (UTC)** 执行。如需修改：
1. 编辑 `.github/workflows/llm_scheduler.yml` 文件。
2. 修改 `cron: '0 6 * * *'` 部分为你需要的表达式。
   - 每小时: `'0 * * * *'`
   - 每天 北京时间 6 点: `'0 22 * * *'` (UTC 时间换算：UTC+8)
   - 每天 北京时间 8 点: `'0 0 * * *'` (UTC 时间换算：UTC+8)

## 本地运行

如果你想在本地测试：

1. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```
2. 创建 `.env` 文件并配置变量:
   ```ini
   API_KEY=your_key
   API_TYPE=openai
   API_URL=https://your-api-url.com/v1
   ```
3. 运行脚本:
   ```bash
   python main.py
   ```

## 注意事项

- 请确保你的 API 额度充足。
- GitHub Actions 的定时任务可能有 5-15 分钟的延迟，属于正常现象。
- 请勿将 API Key 直接写入代码中，务必使用 Secrets。

## 故障排查
- Anthropic 400 且提示“未正常接收到prompt参数”：
  - 确认在 Actions 中 `PROMPT` 是否已设置；若未设置，脚本会使用英文默认值以避免编码问题。
  - 智谱 Anthropic 兼容接口存在 messages/completions 两种路由差异；脚本已内置自动回退至 `/v1/complete` 并构造 `Human/Assistant` 模板。
  - 若仍失败，建议改用 OpenAI 兼容接口：`API_TYPE=openai`，`API_URL=https://open.bigmodel.cn/api/paas/v4/`。
- 查看环境变量是否存在：工作流已添加“Debug env presence (masked)”步骤，只显示是否设置，不输出具体值。
