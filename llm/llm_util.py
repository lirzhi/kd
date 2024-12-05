import json
from multiprocessing import Pool
import time
import requests
from . import env

def ask_llm(content="", mode="qwen"):
    if mode == "ollama":
        model = "gemma2"
        url = "http://localhost:11434/api/generate"  # 本地ollama提供的api
        data = {"model": model, "prompt": content, "stream": False, "context": []}

        headers = {"Content-Type": "application/json"}

        begin_time = time.time()
        response = requests.post(url, data=json.dumps(data), headers=headers)
        resp_time = time.time()
        full_answer = response.json()["response"]
        output_time_count = resp_time - begin_time
        print(
            f"token生成速度:{round(len(full_answer) / output_time_count, 3)}字符/秒，"
            f"token生成耗时{round(output_time_count, 3)}秒"
        )
        return full_answer
    elif mode == "gpt":
        url = "http://localhost:9012/chat"
        data = {
            "chat_history": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. 请使用中文回答问题",
                },
                {"role": "user", "content": content},
            ],
        }
        response = requests.post(url, json=data)
        return response.json()["answer"]

    elif mode == "qwen":
        url = "http://localhost:8024/fastchat"
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. 请使用中文回答问题",
                },
                {"role": "user", "content": content},
            ],
        }
        response = requests.post(url, json=data)
        return response.text

def ask_llm_by_prompt_file(file_name, data="", mode="qwen"):
    template = env.get_template(file_name)
    return ask_llm(template.render(data=data), mode)