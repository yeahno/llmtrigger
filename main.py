import os
import sys
import datetime
from dotenv import load_dotenv
from urllib.parse import urlparse

# 加载本地 .env 文件（如果存在），方便本地调试
load_dotenv()

def get_env_variable(var_name, default=None, required=True):
    """获取环境变量：空字符串视为未设置；支持默认值与必填校验"""
    raw = os.environ.get(var_name)
    value = raw if raw is not None and raw.strip() != "" else None
    if value is None:
        if required and (default is None or str(default).strip() == ""):
            print(f"Error: 环境变量 {var_name} 未设置。")
            print("请在 GitHub Secrets 或 .env 文件中配置该变量。")
            sys.exit(1)
        return default
    return value

def debug_print_config(api_type: str, base_url: str, model_name: str, prompt: str) -> None:
    """安全打印关键配置（不打印 API_KEY，URL 仅显示域名），便于 Actions 调试"""
    prompt_info = f"len={len(prompt) if prompt else 0}"
    print("配置详情（安全）:")
    print(f"- API_TYPE: {api_type}")
    print(f"- API_URL: {base_url}")
    print(f"- MODEL_NAME: {model_name}")
    print(f"- PROMPT: {prompt_info}")

def call_openai_style(api_key, base_url, model_name, prompt):
    """使用 OpenAI SDK 调用"""
    try:
        from openai import OpenAI
    except ImportError:
        print("Error: 未安装 openai 库，请运行 pip install openai")
        sys.exit(1)

    print("正在初始化 OpenAI 客户端...")
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    except Exception as e:
        print(f"Error: 初始化 OpenAI 客户端失败: {e}")
        sys.exit(1)

    try:
        print("正在发送请求 (OpenAI Style)...")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        if response.choices:
            return response.choices[0].message.content
        else:
            return None
    except Exception as e:
        print(f"Error: OpenAI API 调用失败: {e}")
        sys.exit(1)

def call_anthropic_style(api_key, base_url, model_name, prompt):
    """使用 Anthropic SDK 调用 (用于智谱 Anthropic 兼容接口等)"""
    try:
        from anthropic import Anthropic
    except ImportError:
        print("Error: 未安装 anthropic 库，请运行 pip install anthropic")
        sys.exit(1)

    print("正在初始化 Anthropic 客户端...")
    try:
        client = Anthropic(api_key=api_key, base_url=base_url)
    except Exception as e:
        print(f"Error: 初始化 Anthropic 客户端失败: {e}")
        sys.exit(1)

    try:
        print("正在发送请求 (Anthropic Style)...")
        message = client.messages.create(
            model=model_name,
            max_tokens=1024,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        )
        # 智谱返回 content 可能为数组，取首段文本
        if getattr(message, "content", None):
            first = message.content[0]
            return getattr(first, "text", None) or str(first)
        return None
    except Exception as e:
        print(f"Error: Anthropic API 调用失败: {e}")
        # 回退到原生 HTTP 兼容调用（messages 与 completions 两种格式）
        try:
            import httpx
        except Exception:
            sys.exit(1)
        try:
            # 1) messages 兼容
            url = base_url.rstrip("/") + "/v1/messages"
            headers = {
                "x-api-key": api_key,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
            }
            payload = {
                "model": model_name,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                "stream": False,
            }
            resp = httpx.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("content") or data.get("message", {}).get("content")
                if isinstance(content, list) and content:
                    return content[0].get("text") or str(content[0])
                return str(content) if content else None
            # 2) 若服务提示需要 prompt，则尝试 completions 兼容
            url2 = base_url.rstrip("/") + "/v1/complete"
            prompt_text = f"\n\nHuman: {prompt}\n\nAssistant:"
            payload2 = {
                "model": model_name,
                "prompt": prompt_text,
                "max_tokens_to_sample": 1024,
                "stop_sequences": ["\n\nHuman:"],
            }
            resp2 = httpx.post(url2, headers=headers, json=payload2, timeout=60)
            if resp2.status_code == 200:
                data2 = resp2.json()
                return data2.get("completion")
        except Exception as e2:
            print(f"Error: Anthropic 回退调用失败: {e2}")
        sys.exit(1)

def call_anthropic_completions(api_key, base_url, model_name, prompt):
    """使用 Anthropic Completions 接口调用"""
    try:
        import httpx
    except Exception:
        print("Error: 缺少 httpx 依赖")
        sys.exit(1)
    url = base_url.rstrip("/") + "/v1/complete"
    headers = {
        "x-api-key": api_key,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": model_name,
        "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
        "max_tokens_to_sample": 512,
        "stop_sequences": ["\n\nHuman:"],
    }
    print("正在发送请求 (Anthropic Completions)...")
    resp = httpx.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code == 200:
        data = resp.json()
        return data.get("completion")
    print(f"Error: Completions 调用失败: HTTP {resp.status_code} - {resp.text}")
    sys.exit(1)

def main():
    """
    主函数：调用大模型 API
    """
    print(f"[{datetime.datetime.now()}] 开始执行大模型调用任务...")

    # 1. 获取配置
    api_key = get_env_variable("API_KEY")
    
    # 默认使用 openai 模式，如果设置为 'anthropic' 则切换模式
    api_type = get_env_variable("API_TYPE", default="openai", required=False).lower()
    
    # 根据不同模式设置默认 URL
    default_url = "https://api.openai.com/v1"
    if api_type == "anthropic":
        default_url = "https://api.anthropic.com"
        
    base_url = get_env_variable("API_URL", default=default_url, required=False)
    model_name = get_env_variable(
        "MODEL_NAME",
        default=("glm-4.7" if api_type == "anthropic" else "gpt-3.5-turbo"),
        required=False
    )
    force_comp = get_env_variable("ANTHROPIC_FORCE_COMPLETIONS", default="false", required=False).lower() == "true"
    prompt = get_env_variable("PROMPT", default="Hello from Actions", required=False)

    print(f"配置信息: Type={api_type}, URL={base_url}, Model={model_name}")
    debug_print_config(api_type, base_url, model_name, prompt)

    # 2. 根据类型调用不同的处理函数
    content = None
    if api_type == "anthropic":
        if force_comp:
            content = call_anthropic_completions(api_key, base_url, model_name, prompt)
        else:
            content = call_anthropic_style(api_key, base_url, model_name, prompt)
    else:
        content = call_openai_style(api_key, base_url, model_name, prompt)

    # 3. 输出结果
    if content:
        print("-" * 30)
        print("模型回复:")
        print(content)
        print("-" * 30)
        print("调用成功！")
    else:
        print("Error: 未收到有效回复。")

if __name__ == "__main__":
    main()
