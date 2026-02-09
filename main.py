import os
import sys
import datetime
from dotenv import load_dotenv

# 加载本地 .env 文件（如果存在），方便本地调试
load_dotenv()

def get_env_variable(var_name, default=None, required=True):
    """获取环境变量，如果必须且不存在则报错"""
    value = os.environ.get(var_name, default)
    if required and not value:
        print(f"Error: 环境变量 {var_name} 未设置。")
        print("请在 GitHub Secrets 或 .env 文件中配置该变量。")
        sys.exit(1)
    return value

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
        client = Anthropic(
            api_key=api_key,
            base_url=base_url
        )
    except Exception as e:
        print(f"Error: 初始化 Anthropic 客户端失败: {e}")
        sys.exit(1)

    try:
        print("正在发送请求 (Anthropic Style)...")
        message = client.messages.create(
            model=model_name,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }]
        )
        if message.content:
            return message.content[0].text
        else:
            return None
    except Exception as e:
        print(f"Error: Anthropic API 调用失败: {e}")
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
    prompt = get_env_variable("PROMPT", default="你好！", required=False)

    print(f"配置信息: Type={api_type}, URL={base_url}, Model={model_name}")

    # 2. 根据类型调用不同的处理函数
    content = None
    if api_type == "anthropic":
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
